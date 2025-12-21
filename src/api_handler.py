
import google.generativeai as genai
from google.generativeai import types as genai_types
from typing import List, Dict, Any
import re
import json
import logging
import requests

logger = logging.getLogger(__name__)

# --- Core Helper Functions ---

def _generate_response(model: genai.GenerativeModel, prompt: str) -> Dict[str, Any]:
    """
    Generates a response from the Gemini model with a standardized configuration.
    Robustly handles cases where the model returns no text (e.g., safety block, max tokens).
    """
    try:
        generation_config = genai_types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=8192,
            top_p=0.95,
            top_k=40
        )
        response = model.generate_content(prompt, generation_config=generation_config)
        
        # Check if we have a valid candidate
        if not response.candidates:
             return {"error": "The model returned no candidates."}

        candidate = response.candidates[0]
        
        # Check for safety blocking or other finish reasons that prevent text generation
        # Finish Reason 2 is MAX_TOKENS, which usually has text, but sometimes might not if it was instant?
        # Finish Reason 3 is SAFETY.
        if candidate.finish_reason == 3: # Safety
             return {"error": "The model response was blocked due to safety concerns."}
        
        if candidate.finish_reason == 4: # Recitation
             return {"error": "The model response was blocked due to recitation check."}

        # Try to access text safely
        if candidate.content and candidate.content.parts:
            return {"text": candidate.content.parts[0].text}
        elif hasattr(response, 'text'):
             # Fallback to the property if it works
             return {"text": response.text}
        else:
             return {"error": f"The model returned no text content. Finish Reason: {candidate.finish_reason}"}

    except ValueError as ve:
        # Specific catch for the "Invalid operation: The `response.text` quick accessor..." error
        logger.error(f"Gemini API ValueError (likely safety or max tokens): {ve}", exc_info=True)
        # Try to extract partial text if possible or just report the error
        return {"error": f"Model generation failed (invalid response structure): {str(ve)}"}

    except Exception as e:
        logger.error(f"Gemini API Generation Error: {e}", exc_info=True)
        return {"error": str(e)}

def _parse_json_from_response(response_text: str) -> Dict[str, Any]:
    """
    Robustly parses a JSON object from a string.
    """
    try:
        json_match = re.search(r'''```json\s*([\s\S]*?)\s*```''', response_text)
        if json_match:
            json_string = json_match.group(1)
        else:
            start_index = response_text.find('{')
            end_index = response_text.rfind('}')
            if start_index != -1 and end_index != -1 and end_index > start_index:
                json_string = response_text[start_index : end_index + 1]
            else:
                raise ValueError("No valid JSON structure found in the response.")
        return json.loads(json_string)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(f"Failed to parse JSON response: {e}\nRaw Response:\n{response_text}")
        return {"error": "The AI model returned a response that could not be understood."}

# --- Agent Functions ---

def agent_analyze_market(
    model: genai.GenerativeModel,
    prompts_config: Dict[str, Any],
    url: str
) -> Dict[str, Any]:
    """
    Agent: Fetches content from a URL using the requests library and analyzes it.
    """
    logger.info(f"Agent 'analyze_market' starting for URL: {url}")

    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()  # Raise an exception for bad status codes
        html_content = response.text
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to {url} failed: {e}", exc_info=True)
        return {"error": f"Failed to fetch content from URL: {url}. Reason: {e}"}

    meta_prompt_template = prompts_config.get("market_analysis_prompt")
    if not meta_prompt_template:
        return {"error": "No 'market_analysis_prompt' found in prompts configuration."}

    meta_prompt = meta_prompt_template.format(html_content=html_content)
    
    model_response = _generate_response(model, meta_prompt)
    if "error" in model_response:
        return model_response

    parsed_json = _parse_json_from_response(model_response["text"])
    if "error" in parsed_json:
        return parsed_json

    logger.info("Agent 'analyze_market' completed successfully.")
    return parsed_json

def agent_generate_concepts(
    model: genai.GenerativeModel,
    prompts_config: Dict[str, Any],
    theme: str,
    market_analysis: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Agent: Generates creative prompt concepts based on a theme and market analysis.
    """
    logger.info(f"Agent 'generate_concepts' starting for theme: {theme}")
    
    meta_prompt_template = prompts_config.get("idea_generation_meta_prompt")
    if not meta_prompt_template:
        return {"error": "No 'idea_generation_meta_prompt' found in prompts configuration."}

    meta_prompt = meta_prompt_template.format(
        market_analysis=json.dumps(market_analysis, indent=2),
        theme=theme
    )

    response = _generate_response(model, meta_prompt)
    if "error" in response:
        return response

    parsed_json = _parse_json_from_response(response["text"])
    if "error" in parsed_json:
        return parsed_json
    
    logger.info("Agent 'generate_concepts' completed successfully.")
    return parsed_json

def agent_generate_initial_prompt(
    model: genai.GenerativeModel,
    prompts_config: Dict[str, Any],
    topic: str,
    content_type: str,
    style: str,
    use_case: str,
    model_platform: str
) -> Dict[str, Any]:
    """
    Agent 1: Generates the initial prompt template package.
    """
    logger.info(f"Agent 'generate_initial_prompt' starting for topic: {topic}")
    
    meta_prompt_key = f"{content_type.lower()}_meta_prompt"
    meta_prompt_template = prompts_config.get(meta_prompt_key)
    
    if not meta_prompt_template:
        return {"error": f"No meta-prompt found for content type '{content_type}'"}

    meta_prompt = meta_prompt_template.format(
        model_platform=model_platform,
        topic=topic,
        style=style,
        use_case=use_case,
        reference_examples=""
    )

    response = _generate_response(model, meta_prompt)
    if "error" in response:
        return response

    parsed_json = _parse_json_from_response(response["text"])
    if "error" in parsed_json:
        return parsed_json

    template = parsed_json.get("template", "")
    variables = list(set(re.findall(r'\[(.*?)\]', template)))
    
    initial_prompt_package = {
        "topic": topic,
        "content_type": content_type,
        "platform": model_platform,
        "style": style,
        "use_case": use_case,
        "template": template,
        "variables": variables,
        "variable_explanations": parsed_json.get("variables_explanation", {}),
        "examples": parsed_json.get("example_prompts", []),
        "tips": parsed_json.get("technical_tips", []),
        "description": parsed_json.get("description", ""),
        "instructions": parsed_json.get("instructions", ""),
        "raw_response": response["text"]
    }
    
    logger.info("Agent 'generate_initial_prompt' completed successfully.")
    return initial_prompt_package

def agent_analyze_template(
    model: genai.GenerativeModel,
    prompts_config: Dict[str, Any],
    template_content: str,
    content_type: str = "Image",
    platform: str = "General"
) -> Dict[str, Any]:
    """
    Agent: Reverse engineers a prompt package from a raw template string.
    Uses inline self-evaluation to assess and optionally enhance the template.
    """
    logger.info("Agent 'analyze_template' starting.")
    
    meta_prompt_template = prompts_config.get("reverse_engineer_meta_prompt")
    if not meta_prompt_template:
        return {"error": "No 'reverse_engineer_meta_prompt' found in configuration."}
        
    meta_prompt = meta_prompt_template.format(template=template_content)
    
    response = _generate_response(model, meta_prompt)
    if "error" in response:
        return response

    parsed_json = _parse_json_from_response(response["text"])
    if "error" in parsed_json:
        return parsed_json
    
    # Use enhanced template if model provided one, otherwise use original
    template_to_use = parsed_json.get("template", template_content)
    original_template = parsed_json.get("original_template", template_content)
    self_eval = parsed_json.get("self_evaluation", {})
    
    # Construct a package compatible with the rest of the workflow
    # Use user-provided content_type and platform, falling back to AI inference
    package = {
        "topic": parsed_json.get("topic", "Unknown Topic"),
        "content_type": content_type,  # Use user-provided value
        "platform": platform,  # Use user-provided value
        "style": parsed_json.get("style", "General"),
        "use_case": parsed_json.get("use_case", "General"),
        "template": template_to_use,
        "original_template": original_template,
        "variables": list(set(re.findall(r'\[(.*?)\]', template_to_use))),
        "variable_explanations": parsed_json.get("variables_explanation", {}),
        "examples": parsed_json.get("example_prompts", []),
        "tips": parsed_json.get("technical_tips", []),
        "description": parsed_json.get("description", ""),
        "instructions": parsed_json.get("instructions", ""),
        "prompt_metadata": parsed_json.get("prompt_metadata", {}), # For Veo 3.1
        "self_evaluation": self_eval  # Include for transparency
    }
    
    logger.info(f"Agent 'analyze_template' completed. Self-eval score: {self_eval.get('overall_score', 'N/A')}")
    return package

# --- New Vision Agent ---

def agent_reverse_engineer_from_image(
    model: genai.GenerativeModel,
    prompts_config: Dict[str, Any],
    image_data: Any, # PIL.Image
    additional_context: str = ""
) -> Dict[str, Any]:
    """
    Agent: Reverse engineers a prompt template from an image using a Vision model.
    Uses inline self-evaluation to assess quality without extra API calls.
    """
    logger.info("Agent 'reverse_engineer_from_image' starting.")

    meta_prompt_template = prompts_config.get("reverse_engineer_image_prompt")
    if not meta_prompt_template:
        return {"error": "No 'reverse_engineer_image_prompt' found in configuration."}
        
    # Format the prompt with additional context if available
    context_str = f"User provided additional context: {additional_context}" if additional_context else "No additional user context provided."
    meta_prompt = meta_prompt_template.format(additional_context=context_str)

    # For vision models, we pass a list [prompt, image]
    try:
        response = model.generate_content([meta_prompt, image_data])
    except Exception as e:
        logger.error(f"Vision API Error: {e}")
        return {"error": f"Error interacting with Vision model: {e}"}

    try:
        parsed_json = _parse_json_from_response(response.text)
    except Exception as e:
         return {"error": f"Failed to parse Vision response: {e}"}
         
    if "error" in parsed_json:
        return parsed_json

    # Handle self-evaluation: use improved_template if model scored itself low
    template_to_use = parsed_json.get("template", "")
    self_eval = parsed_json.get("self_evaluation", {})
    if self_eval.get("overall_score", 10) < 7 and parsed_json.get("improved_template"):
        logger.info("Model self-evaluation < 7, using improved_template.")
        template_to_use = parsed_json.get("improved_template")

    # Normalize output to match workflow expectations
    package = {
        "topic": parsed_json.get("topic", "Image Analysis"),
        "content_type": "Image",
        "platform": "Midjourney/DALL-E", # Vision models infer general style
        "style": ", ".join(parsed_json.get("style", [])) if isinstance(parsed_json.get("style"), list) else parsed_json.get("style", ""),
        "use_case": parsed_json.get("use_case", "General"),
        "template": template_to_use,
        "variables": list(set(re.findall(r'\[(.*?)\]', template_to_use))),
        "variable_explanations": parsed_json.get("variables_explanation", {}),
        "examples": parsed_json.get("example_prompts", []),
        "tips": parsed_json.get("technical_tips", []),
        "description": parsed_json.get("description", ""),
        "instructions": "Use this template to generate similar images.",
        "input_source": "image_upload",
        "self_evaluation": self_eval  # Include for transparency
    }

    logger.info(f"Agent 'reverse_engineer_from_image' completed. Self-eval score: {self_eval.get('overall_score', 'N/A')}")
    return package



def agent_normalize_data(
    model: genai.GenerativeModel,
    prompts_config: Dict[str, Any],
    raw_text: str
) -> List[Dict[str, Any]]:
    """
    Agent: Normalizes unstructured text into structured JSON data for the Knowledge Base.
    """
    logger.info("Agent 'normalize_data' starting.")

    meta_prompt_template = prompts_config.get("data_normalization_prompt")
    if not meta_prompt_template:
        return [{"error": "No 'data_normalization_prompt' found."}]
    
    meta_prompt = meta_prompt_template.format(raw_text=raw_text)

    try:
        response = _generate_response(model, meta_prompt)
    except Exception as e:
        return [{"error": f"LLM Error: {e}"}]

    if "error" in response:
        return [{"error": response["error"]}]
    
    parsed_json = _parse_json_from_response(response["text"])
    
    if "error" in parsed_json:
        return [{"error": parsed_json["error"]}]
        
    return parsed_json.get("items", [])

def agent_evaluate_compliance(
    evaluator_model: genai.GenerativeModel,

    prompts_config: Dict[str, Any], # Added prompts_config
    prompt_package: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Agent 2: Evaluates the prompt against the detailed, weighted criteria from the config.
    """
    logger.info("Agent 'evaluate_compliance' starting with new scoring model.")

    evaluation_prompt_template = prompts_config.get("agent_quality_evaluation")
    if not evaluation_prompt_template:
        return {"error": "No 'agent_quality_evaluation' prompt found in prompts configuration."}

    # Prepare the data for the evaluation prompt
    evaluation_prompt = evaluation_prompt_template.format(
        prompt_title=prompt_package.get('topic', ''),
        prompt_template=prompt_package.get('template', ''),
        variable_examples=json.dumps(prompt_package.get('examples', []), indent=2),
        commercial_description=prompt_package.get('commercial_description', '')
    )
    
    response = _generate_response(evaluator_model, evaluation_prompt)
    if "error" in response:
        return response
        
    parsed_json = _parse_json_from_response(response["text"])
    logger.info("Agent 'evaluate_compliance' completed.")
    return parsed_json


def agent_refine_prompt(
    model: genai.GenerativeModel,
    prompt_package: Dict[str, Any],
    evaluation_results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Agent 3: Refines the prompt based on evaluation feedback.
    """
    logger.info("Agent 'refine_prompt' starting.")
    
    original_vars = prompt_package.get('variables', [])
    
    refinement_prompt = f"""
    You are an expert prompt engineer. Improve a prompt template based on a quality review.

    CURRENT PROMPT:
    {prompt_package.get('template', '')}

    EVALUATION FEEDBACK:
    - Total Score: {evaluation_results.get('total_score', 'N/A')} / 50
    - Key Issues to Fix: {', '.join(evaluation_results.get('priority_improvements', []))}

    YOUR TASK:
    1.  Rewrite the prompt template to address the "Key Issues to Fix".
    2.  You MUST keep the exact same variables: {original_vars}.
    3.  Return ONLY a JSON object with the single key "improved_template".
    """
    
    response = _generate_response(model, refinement_prompt)
    if "error" in response:
        return response
        
    parsed_json = _parse_json_from_response(response["text"])
    if "error" in parsed_json:
        return parsed_json

    refined_package = prompt_package.copy()
    refined_package["template"] = parsed_json.get("improved_template", prompt_package["template"])
    refined_package["variables"] = list(set(re.findall(r'\[(.*?)\]', refined_package["template"])))
    if set(refined_package["variables"]) != set(original_vars):
        logger.warning("Refinement agent changed variables. Reverting to original variables.")
        refined_package["template"] = prompt_package["template"]
        refined_package["variables"] = original_vars

    logger.info("Agent 'refine_prompt' completed.")
    return refined_package


def agent_generate_examples(
    model: genai.GenerativeModel,
    prompt_package: Dict[str, Any],
    num_examples: int = 9
) -> List[Dict[str, Any]]: # Return type changed
    """
    Agent 4: Generates a diverse set of examples for the given prompt template.
    Now returns a list of objects, each with variables and the resulting prompt.
    """
    logger.info("Agent 'generate_examples' starting.")
    
    examples_prompt = f"""
    You are a creative assistant specializing in demonstrating the full potential of prompt templates.
    Your task is to generate {num_examples} exceptionally diverse and inspiring examples for the given prompt template.

    PROMPT TEMPLATE:
    {prompt_package.get('template')}

    VARIABLES IN TEMPLATE:
    {prompt_package.get('variables')}

    INSTRUCTIONS:
    - For each of the {num_examples} examples, you must invent values for the variables.
    - **CRITICAL**: The examples must be "pleasant" and "client-friendly".
    - **CRITICAL**: Use simple, high-level concepts for the variables (e.g., "A cozy cabin", "A majestic lion").
    - **CRITICAL**: Do NOT use overly complex or technical variable values. The template handles the complexity.
    - The goal is to show the user how EASY it is to get a great result.

    STRATEGY FOR VARIABLE VALUES:
    1.  **Mix Literal and Abstract:** For some examples, use simple, direct values.
    2.  **Use Conceptual Ideas:** For other examples, use abstract or poetic values.
    3.  **Demonstrate Range:** Ensure the {num_examples} examples are substantively different.

    OUTPUT FORMAT:
    - You will return a JSON object containing a single key: "examples".
    - The value of "examples" must be a list of {num_examples} JSON objects.
    - Each object in the list must have two keys:
      1. "variables": A JSON object mapping each variable name to the specific value you chose for this example.
      2. "prompt": The final, complete prompt string after filling the template with the chosen variable values.

    Ensure your entire output is a single, valid JSON object.
    """
    
    response = _generate_response(model, examples_prompt)
    if "error" in response:
        return [{"error": response["error"]}]
        
    parsed_json = _parse_json_from_response(response["text"])
    if "error" in parsed_json:
        return [{"error": parsed_json["error"]}]
        
    logger.info("Agent 'generate_examples' completed successfully.")
    return parsed_json.get("examples", [])

def agent_manage_examples(
    model: genai.GenerativeModel,
    prompt_package: Dict[str, Any],
    action: str,
    target_total: int = 9,
    example_to_regenerate: str = "",
    example_index: int = -1
) -> List[str]:
    """Agent for completing or regenerating examples for a prompt package."""
    logger.info(f"Agent 'manage_examples' starting with action: {action}")
    
    existing_examples = prompt_package.get("examples", [])
    template = prompt_package.get("template", "")
    variables = prompt_package.get("variables", [])
    
    if action == "complete":
        num_to_generate = target_total - len(existing_examples)
        if num_to_generate <= 0:
            logger.info("No examples to generate, already at or above target.")
            return existing_examples

        prompt = f"""You are a creative assistant. Your task is to generate {num_to_generate} new, diverse example prompts based on a template. These new examples MUST be different from the provided list of existing examples.\n\nPROMPT TEMPLATE:\n{template}\n\nVARIABLES:\n{variables}\n\nEXISTING EXAMPLES (DO NOT REPEAT THESE):\n{json.dumps(existing_examples, indent=2)}\n\nYOUR TASK:\n- Generate exactly {num_to_generate} new, high-quality, and diverse examples.\n- Return ONLY a JSON object with a single key \"new_examples\", which is a list of strings."""
        
        response = _generate_response(model, prompt)
        if "error" in response:
            return [response["error"]]
        
        parsed_json = _parse_json_from_response(response["text"])
        if "error" in parsed_json:
            return [parsed_json["error"]]
            
        new_examples = parsed_json.get("new_examples", [])
        return existing_examples + new_examples

    elif action == "regenerate_one":
        if not example_to_regenerate or example_index == -1:
            return {"error": "Missing example or index for regeneration."}

        prompt = f"""You are a creative assistant. Your task is to regenerate a single prompt example. The new example must be high-quality, diverse, and substantively different from all other examples in the provided list.\n\nPROMPT TEMPLATE:\n{template}\n\nFULL LIST OF CURRENT EXAMPLES:\n{json.dumps(existing_examples, indent=2)}\n\nEXAMPLE TO REPLACE:\n\"{example_to_regenerate}\"\n\nYOUR TASK:\n- Generate exactly one new example to replace the specified one.\n- The new example must be creative and distinct from all other examples in the full list.\n- Return ONLY a JSON object with a single key \"new_example\", which is a single string."""

        response = _generate_response(model, prompt)
        if "error" in response:
            return response

        parsed_json = _parse_json_from_response(response["text"])
        if "error" in parsed_json:
            return parsed_json

        new_example = parsed_json.get("new_example", "")
        if new_example:
            updated_examples = existing_examples[:]
            updated_examples[example_index] = new_example
            return updated_examples
        else:
            return {"error": "The model did not return a new example."}

    else:
        return {"error": f"Invalid action specified: {action}"}



def agent_generate_test_guidance(prompt_package: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Agent 5: Generates a standardized testing guide for the user.
    """
    logger.info("Agent 'generate_test_guidance' starting.")
    
    content_type = prompt_package.get("content_type", "").lower()
    model_platform = prompt_package.get("platform", "").lower()
    
    test_guidance = {
        "test_instructions": [
            "Fill in each variable with different values to test versatility.",
            "Try using the first example prompt exactly as written as your baseline.",
            "Test at least 3-5 different variations to ensure consistent style."
        ],
        "quality_checklist": [],
        "common_issues": []
    }

    if content_type == "image":
        test_guidance["quality_checklist"].extend([
            "Style Consistency: Does the style remain consistent?",
            "Composition: Does the output match your compositional expectations?",
            "Visual Quality: Is the output high-quality?",
            "Variable Impact: Does changing variables produce meaningful differences?"
        ])
        test_guidance["common_issues"].extend([
            "Subject distortion or anatomical problems.",
            "Style 'bleeding' or inconsistency."
        ])
    elif content_type == "text":
        test_guidance["quality_checklist"].extend([
            "Tone & Style: Is the tone and style consistent?",
            "Structure: Does the output follow the desired structure?",
            "Coherence: Is the text logical and coherent?",
            "Variable Adaptation: Does the text adapt properly to different inputs?"
        ])
        test_guidance["common_issues"].extend([
            "Repetitive phrasing.",
            "Inconsistent tone."
        ])
    
    if "midjourney" in model_platform:
        test_guidance["test_instructions"].append("Experiment with Midjourney parameters like `--ar` or `--stylize`.")
    elif "dall-e" in model_platform:
        test_guidance["test_instructions"].append("Try reordering clauses in the prompt to see how it affects element priority.")

    logger.info("Agent 'generate_test_guidance' completed.")
    return test_guidance

def validate_prompt_title(title: str) -> dict:
    """
    Validates the prompt title against patterns of success.
    
    Returns:
        dict: {
            'score': float (0-1),
            'issues': list[str],
            'suggestions': list[str]
        }
    """
    score = 1.0
    issues = []
    suggestions = []
    
    # Pattern: 3-6 words
    word_count = len(title.split())
    if word_count < 3:
        score -= 0.3
        issues.append("Title too short (less than 3 words)")
        suggestions.append("Add style descriptor or use case")
    elif word_count > 6:
        score -= 0.2
        issues.append("Title too long (more than 6 words)")
        suggestions.append("Condense to essential elements")
    
    # Must include emotional/visual descriptor
    emotional_words = {
        'whimsical', 'ethereal', 'bold', 'playful', 'cozy', 'mysterious',
        'soft', 'vibrant', 'muted', 'luminous', 'epic', 'cinematic',
        'elegant', 'rustic', 'modern', 'vintage', 'dreamy', 'surreal'
    }
    if not any(word.lower() in emotional_words for word in title.split()):
        score -= 0.25
        issues.append("Missing emotional/visual descriptor")
        suggestions.append(f"Consider: {', '.join(list(emotional_words)[:5])}")
    
    # Must include content type or format
    format_words = {
        'art', 'illustration', 'photo', 'pattern', 'design', 'cover',
        'poster', 'wallpaper', 'texture', 'scene', 'portrait', 'landscape'
    }
    if not any(word.lower() in format_words for word in title.split()):
        score -= 0.25
        issues.append("Missing format/type specification")
        suggestions.append(f"Add: {', '.join(list(format_words)[:5])}")
    
    return {
        'score': max(0, score),
        'issues': issues,
        'suggestions': suggestions
    }

def agent_generate_description(
    model: genai.GenerativeModel,
    prompts_config: Dict[str, Any],
    prompt_package: dict
) -> str:
    """
    Agent: Generates a commercially optimized marketplace description using an LLM.
    """
    logger.info("Agent 'generate_description' starting.")

    description_prompt_template = prompts_config.get("product_description_prompt")
    if not description_prompt_template:
        logger.warning("No 'product_description_prompt' found. Using fallback.")
        return "Professional AI Prompt Template. Easy to use and high quality."

    meta_prompt = description_prompt_template.format(
        topic=prompt_package.get('topic', 'this amazing prompt'),
        content_type=prompt_package.get('content_type', 'Content'),
        use_cases=", ".join(prompt_package.get('use_cases', ['general use']))
    )

    response = _generate_response(model, meta_prompt)
    if "error" in response:
        logger.error(f"Description agent failed: {response['error']}")
        return "Professional AI Prompt Template. Easy to use and high quality."

    return response["text"].strip()

def agent_categorize_prompt(
    model: genai.GenerativeModel,
    prompts_config: Dict[str, Any],
    prompt_package: Dict[str, Any]
) -> str:
    """
    Agent: Assigns a category to a prompt package.
    """
    logger.info(f"Agent 'categorize_prompt' starting for topic: {prompt_package.get('topic')}")

    categorization_prompt_template = prompts_config.get("agent_categorize_prompt")
    category_list = prompts_config.get("prompt_categories", [])

    if not categorization_prompt_template or not category_list:
        return "Uncategorized"

    meta_prompt = categorization_prompt_template.format(
        prompt_title=prompt_package.get("topic", ""),
        prompt_description=prompt_package.get("description", ""),
        prompt_template=prompt_package.get("template", ""),
        category_list="\n".join([f"- {c}" for c in category_list])
    )

    response = _generate_response(model, meta_prompt)
    if "error" in response:
        logger.error(f"Categorization agent failed: {response['error']}")
        return "Uncategorized"

    # The response should be just the category name, so we clean it up.
    # We find the closest match from the category list to avoid hallucinations.
    response_text = response.get("text", "").strip()
    
    # A simple way to find the best match
    best_match = "Uncategorized"
    highest_ratio = 0
    for category in category_list:
        # Simple substring check, can be improved with fuzzy matching later if needed
        if category.lower() in response_text.lower():
             best_match = category
             break # Take the first match

    logger.info(f"Agent 'categorize_prompt' completed. Assigned category: {best_match}")
    return best_match


def agent_analyze_trends(
    model: genai.GenerativeModel,
    prompts_config: Dict[str, Any],
    market_data: str
) -> List[Dict[str, Any]]:
    """
    Agent: Analyzes market data to predict trending prompt concepts.
    """
    logger.info("Agent 'analyze_trends' starting.")

    trend_prompt_template = prompts_config.get("trend_analysis_prompt")
    if not trend_prompt_template:
        return [{"error": "No 'trend_analysis_prompt' found in config."}]

    meta_prompt = trend_prompt_template.format(market_data=market_data)

    response = _generate_response(model, meta_prompt)
    if "error" in response:
        return [{"error": response["error"]}]

    parsed_json = _parse_json_from_response(response["text"])
    if "error" in parsed_json:
        return [{"error": parsed_json["error"]}]

    return parsed_json.get("trends", [])


def agent_extract_variables(
    model: genai.GenerativeModel,
    prompts_config: Dict[str, Any],
    text: str,
    variables: List[str]
) -> Dict[str, Any]:
    """
    Agent: Extracts specific variable values from a text string using LLM context.
    """
    logger.info(f"Agent 'extract_variables' starting for variables: {variables}")

    if not variables:
        return {}

    extraction_prompt = prompts_config.get("variable_extraction_prompt")
    if not extraction_prompt:
        logger.warning("No 'variable_extraction_prompt' found in config.")
        return {}

    meta_prompt = extraction_prompt.format(
        variables=", ".join(variables),
        text=text
    )

    response = _generate_response(model, meta_prompt)
    if "error" in response:
        logger.error(f"Extraction agent failed: {response['error']}")
        return {}

    parsed_json = _parse_json_from_response(response["text"])
    
    if "error" in parsed_json:
        logger.warning(f"Failed to parse extraction JSON: {parsed_json['error']}")
        return {}
        
    return parsed_json

