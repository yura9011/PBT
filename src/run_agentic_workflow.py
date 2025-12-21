import streamlit as st
import logging
from typing import Dict, Any, Generator
import google.generativeai as genai

from .api_handler import (
    agent_generate_initial_prompt,
    agent_evaluate_compliance,
    agent_refine_prompt,
    agent_generate_examples,
    agent_generate_test_guidance,
    validate_prompt_title,
    agent_generate_description,
    agent_categorize_prompt,
    agent_analyze_template,
    agent_reverse_engineer_from_image
)
from .utils import save_output_to_json

logger = logging.getLogger(__name__)

def run_workflow(
    api_key: str,
    generator_model_name: str,
    evaluator_model_name: str,
    prompts_config: Dict[str, Any],
    user_inputs: Dict[str, Any],
    compliance_threshold: int = 35
) -> Generator[Dict[str, Any], None, None]:
    """
    Runs the full agentic workflow, yielding the state at each step.
    """
    try:
        genai.configure(api_key=api_key)
        generator_model = genai.GenerativeModel(generator_model_name)
        evaluator_model = genai.GenerativeModel(evaluator_model_name)

        input_mode = user_inputs.get("input_mode", "Generation")

        # --- Step 1: Initial Prompt Generation OR Reverse Engineering ---
        if input_mode == "Reverse":
             yield {"status": "running", "step": "Reverse Engineering", "output": "Analyzing template..."}
             prompt_package = agent_analyze_template(
                model=generator_model,
                prompts_config=prompts_config,
                template_content=user_inputs.get("template", ""),
                content_type=user_inputs.get("content_type", "Image"),
                platform=user_inputs.get("platform", "General")
            )
        elif input_mode == "ReverseImage":
             yield {"status": "running", "step": "Image Analysis", "output": "Analyzing image with Vision Model..."}
             # For vision, we might want to use the specific model requested by user if set in user_inputs/session
             # But here generator_model is passed in. We assume ui.py sets the right model name.
             prompt_package = agent_reverse_engineer_from_image(
                model=generator_model,
                prompts_config=prompts_config,
                image_data=user_inputs.get("image_data"),
                additional_context=user_inputs.get("user_context", "")
             )
        else:
            yield {"status": "running", "step": "Initial Generation", "output": "Generating initial prompt..."}

            # Filter out keys that are not expected by agent_generate_initial_prompt
            gen_inputs = {k: v for k, v in user_inputs.items() if k in ["topic", "content_type", "style", "use_case", "model_platform"]}
            prompt_package = agent_generate_initial_prompt(
                model=generator_model,
                prompts_config=prompts_config,
                **gen_inputs
            )
            
        if 'error' in prompt_package:
            yield {"status": "error", "output": prompt_package['error']}
            return
        
        yield {"status": "running", "step": "Initial Generation", "output": "Base prompt package defined.", "prompt_package": prompt_package}

        # --- Step 1.5: Title Validation ---
        yield {"status": "running", "step": "Title Validation", "output": "Validating title against market patterns..."}
        title_validation_results = validate_prompt_title(prompt_package.get("topic", ""))
        prompt_package['title_validation'] = title_validation_results
        if title_validation_results.get("score", 1.0) < 0.7:
            issues = ", ".join(title_validation_results.get("issues", []))
            yield {"status": "running", "step": "Title Validation", "output": f"Title issues found: {issues}. Suggestions: {', '.join(title_validation_results.get('suggestions',[]))}", "prompt_package": prompt_package}
        else:
            yield {"status": "running", "step": "Title Validation", "output": "Title meets quality standards.", "prompt_package": prompt_package}


        # --- Step 2: Compliance Evaluation ---
        yield {"status": "running", "step": "Compliance Evaluation", "output": "Evaluating for PromptBase compliance..."}
        evaluation = agent_evaluate_compliance(evaluator_model, prompts_config, prompt_package)
        if 'error' in evaluation:
            yield {"status": "error", "output": evaluation['error']}
            return
        prompt_package['evaluation'] = evaluation
        yield {"status": "running", "step": "Compliance Evaluation", "output": "Evaluation complete.", "prompt_package": prompt_package}

        # --- Step 3: Refinement (Conditional) ---
        total_score = evaluation.get("total_score", 0)
        if total_score < compliance_threshold:
            yield {"status": "running", "step": "Refinement", "output": f"Score of {total_score} is below threshold. Refining..."}
            refined_package = agent_refine_prompt(generator_model, prompt_package, evaluation)
            if 'error' in refined_package:
                yield {"status": "error", "output": refined_package['error']}
                return
            prompt_package = refined_package
            yield {"status": "running", "step": "Refinement", "output": "Prompt refined.", "prompt_package": prompt_package}
        else:
            yield {"status": "running", "step": "Refinement", "output": f"Score of {total_score} meets threshold. No refinement needed."}

        # --- Step 4: Generate Examples ---
        yield {"status": "running", "step": "Example Generation", "output": "Generating diverse examples..."}
        examples = agent_generate_examples(generator_model, prompt_package)
        if examples and isinstance(examples, list) and examples[0] and isinstance(examples[0], dict) and 'error' in examples[0]:
            yield {"status": "error", "output": examples[0]['error']}
            return
        prompt_package['examples'] = examples
        yield {"status": "running", "step": "Example Generation", "output": "Examples generated.", "prompt_package": prompt_package}

        # --- Step 5: Generate Test Guidance ---
        yield {"status": "running", "step": "Test Guidance", "output": "Creating testing guide..."}
        test_guidance = agent_generate_test_guidance(prompt_package)
        prompt_package['test_guidance'] = test_guidance
        yield {"status": "running", "step": "Test Guidance", "output": "Testing guide created.", "prompt_package": prompt_package}

        # --- Step 6: Generate Commercial Description ---
        yield {"status": "running", "step": "Commercial Description", "output": "Generating commercial description..."}
        commercial_description = agent_generate_description(generator_model, prompts_config, prompt_package)
        prompt_package['commercial_description'] = commercial_description
        yield {"status": "running", "step": "Commercial Description", "output": "Description generated.", "prompt_package": prompt_package}

        # --- Step 7: Categorization ---
        yield {"status": "running", "step": "Categorization", "output": "Assigning category..."}
        category = agent_categorize_prompt(generator_model, prompts_config, prompt_package)
        prompt_package['category'] = category
        yield {"status": "running", "step": "Categorization", "output": f"Category assigned: {category}", "prompt_package": prompt_package}

        # --- Step 8: Quality Enhancement (Counter-Strategies) ---
        yield {"status": "running", "step": "Quality Enhancement", "output": "Running quality checks and enhancements..."}
        try:
            from .quality_enhancers import (
                validate_title_pattern, 
                fix_title, 
                validate_examples, 
                check_abstract_examples,
                inject_abstract_examples
            )
            
            enhancement_log = []
            
            # 8a. Title validation and fixing
            title_validation = validate_title_pattern(prompt_package.get("topic", ""))
            if not title_validation["is_valid"]:
                title_result = fix_title(generator_model, prompt_package.get("topic", ""))
                if title_result["was_changed"]:
                    prompt_package["_original_topic"] = prompt_package["topic"]
                    prompt_package["topic"] = title_result["fixed_title"]
                    enhancement_log.append(f"Title fixed: {title_result['original_title']} -> {title_result['fixed_title']}")
            
            # 8b. Example count validation
            example_validation = validate_examples(prompt_package)
            if not example_validation["is_valid"]:
                enhancement_log.append(f"Warning: Only {example_validation['current_count']} examples (need {example_validation['required_count']})")
                prompt_package["_needs_more_examples"] = example_validation["deficit"]
            
            # 8c. Abstract example check and injection
            abstract_check = check_abstract_examples(prompt_package)
            if not abstract_check["has_abstract"]:
                prompt_package = inject_abstract_examples(generator_model, prompt_package)
                if prompt_package.get("_abstract_injected"):
                    enhancement_log.append(f"Injected {prompt_package['_abstract_injected']} abstract examples")
            
            prompt_package["enhancement_log"] = enhancement_log
            yield {"status": "running", "step": "Quality Enhancement", "output": f"Enhancements applied: {len(enhancement_log)} fixes", "prompt_package": prompt_package}
        except ImportError:
            yield {"status": "running", "step": "Quality Enhancement", "output": "Quality enhancers not available, skipping...", "prompt_package": prompt_package}
        except Exception as qe:
            logger.warning(f"Quality enhancement failed: {qe}")
            yield {"status": "running", "step": "Quality Enhancement", "output": f"Enhancement skipped due to error: {qe}", "prompt_package": prompt_package}

        # --- Final Step: Save and Complete ---
        output_path = save_output_to_json(prompt_package, f"prompt_package_{user_inputs.get('topic', 'untitled')}")
        final_message = f"Workflow finished. Final prompt package saved to `{output_path}`"
        
        yield {"status": "completed", "step": "Complete", "output": final_message, "prompt_package": prompt_package}

    except Exception as e:
        logger.error(f"An unexpected error occurred in the workflow: {e}", exc_info=True)
        yield {"status": "error", "output": f"An unexpected error occurred: {e}"}

