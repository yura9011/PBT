import google.generativeai as genai
from google.generativeai import types as genai_types  # Import for GenerationConfig
from typing import List, Dict, Optional, Tuple
import re
import yaml
import logging
import json

logger = logging.getLogger(__name__)

class QualityCheckLoop:
    """Handles the quality improvement loop for prompts"""
    
    def __init__(self, api_key: str, 
                 primary_model_name: str,
                 evaluator_model_name: str,
                 prompts_config: Dict = None,
                 max_iterations: int = 3,
                 quality_threshold: float = 45.0):
        """Initialize the quality improvement loop
        
        Args:
            api_key: Gemini API key
            primary_model_name: Model for generating improvements
            evaluator_model_name: Model for evaluating prompts
            prompts_config: Configuration dictionary containing prompts
            max_iterations: Maximum improvement iterations
            quality_threshold: Score threshold to stop improvements
        """
        self.api_key = api_key
        self.primary_model_name = primary_model_name
        self.evaluator_model_name = evaluator_model_name
        self.prompts_config = prompts_config or {}
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.improvement_history = []
        
        # Initialize Gemini models
        genai.configure(api_key=api_key)
        self.generator = genai.GenerativeModel(primary_model_name)
        self.evaluator = genai.GenerativeModel(evaluator_model_name)
        
        # Add logging
        logger.info(f"QualityCheckLoop initialized with models: {primary_model_name} (generator) and {evaluator_model_name} (evaluator)")

        
    def evaluate_prompt(self, prompt_data: Dict[str, any]) -> Dict[str, any]:
        """
        Evaluates a generated prompt and provides detailed quality assessment.
        
        Args:
            prompt_data: Dictionary containing the generated prompt template
            
        Returns:
            Dictionary with scores and improvement suggestions
        """
        evaluation_prompt = f"""
        You are a professional prompt engineer evaluator. 
        Evaluate this prompt template for {prompt_data.get('content_type', 'image')} generation based on:
        
        1. Clarity (1-10): Is the prompt clear and unambiguous?
        2. Flexibility (1-10): Do the variables provide meaningful control?
        3. Specificity (1-10): Does it contain enough details for consistent results?
        4. Creativity (1-10): Does it encourage unique, high-quality outputs?
        5. Technical accuracy (1-10): Does it follow platform-specific best practices?
        6. Aproach (1-10): Is the prompt real useful or its getting a wrong aproach? 
        7. Efficay (1-10): Is the prompt following the topic the user mentioned at first?
        
        PROMPT TEMPLATE:
        {prompt_data.get('template', '')}
        
        VARIABLES:
        {', '.join(prompt_data.get('variables', []))}
        
        EXAMPLES:
        {json.dumps(prompt_data.get('examples', []), indent=2)}
        
        Provide your evaluation as a JSON object with scores and specific improvement suggestions.
        Include a "total_score" field (sum of all scores) and "priority_improvements" list.
        Be specific and actionable in your improvement suggestions. Do not comment other things than your instructions.
        """
        
        try:
            response = self.evaluator.generate_content(evaluation_prompt)
            evaluation_text = response.text
            
            # Extract JSON from response
            json_pattern = r'```json\s*([\s\S]*?)\s*```'
            match = re.search(json_pattern, evaluation_text)
            if match:
                evaluation_json = json.loads(match.group(1))
            else:
                # Try to find JSON without code blocks
                json_start = evaluation_text.find('{')
                json_end = evaluation_text.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    evaluation_json = json.loads(evaluation_text[json_start:json_end])
                else:
                    raise ValueError("Could not extract JSON from evaluation response")
            
            return evaluation_json
            
        except Exception as e:
            logging.error(f"Evaluation error: {str(e)}")
            return {
                "error": str(e),
                "total_score": 0,
                "clarity": 0,
                "flexibility": 0,
                "specificity": 0,
                "creativity": 0,
                "technical_accuracy": 0,
                "priority_improvements": ["Evaluation failed"]
            }
    
    def improve_prompt(self, prompt_data: Dict[str, any], evaluation: Dict[str, any]) -> Dict[str, any]:
        """Takes a prompt and its evaluation, then generates an improved version"""
        # Get original variables for reference
        original_vars = prompt_data.get('variables', [])
        
        improvement_prompt = f"""
        You are an expert prompt engineer. Review and improve this prompt template.

        CURRENT PROMPT:
        {prompt_data.get('template', '')}

        CURRENT VARIABLES ({len(original_vars)}):
        {', '.join(original_vars)}

        EVALUATION SCORES:
        - Clarity: {evaluation.get('clarity', 0)}/10
        - Flexibility: {evaluation.get('flexibility', 0)}/10
        - Specificity: {evaluation.get('specificity', 0)}/10
        - Creativity: {evaluation.get('creativity', 0)}/10
        - Technical: {evaluation.get('technical_accuracy', 0)}/10
        - Aproach: {evaluation.get('aproach', 0)}/10
        - Efficay: {evaluation.get('efficay', 0)}/10

        YOUR TASK:
        1. Improve the prompt template while keeping EXACTLY the same {len(original_vars)} variables:
        {', '.join(original_vars)}

        2. Generate EXACTLY 9 examples using these variables. Each example must:
        - Use ALL variables in a unique way
        - Show a completely different use case
        - Be realistic and practical
        - Follow a clear pattern: [VARIABLE_1] + [VARIABLE_2] + ... (use all variables)

        REQUIRED OUTPUT FORMAT (JSON):
        {{
            "improved_template": "Your improved template using only these variables: {', '.join(original_vars)}",
            "variables": {json.dumps(original_vars)},
            "examples": [
                "Complete example 1 using all variables",
                "Complete example 2 using all variables",
                ... (exactly 9 examples)
            ],
            "changes_made": ["List specific improvements"],
            "rationale": "Why these changes improve the prompt"
        }}

        REQUIREMENTS:
        - Keep EXACTLY {len(original_vars)} variables
        - Generate EXACTLY 9 examples
        - Each example must use ALL variables
        - Do not add or remove variables
        - Make examples substantially different from each other
        """

        try:
            response = self.generator.generate_content(improvement_prompt)
            improvement_text = response.text

            # Extract JSON from response
            json_match = re.search(r'{[\s\S]*}', improvement_text)
            if json_match:
                improvement_data = json.loads(json_match.group())
                
                # Verify correct number of variables and examples
                if len(improvement_data.get("variables", [])) != len(original_vars):
                    logger.warning("Wrong number of variables - reverting to original")
                    improvement_data["variables"] = original_vars
                
                if len(improvement_data.get("examples", [])) != 9:
                    logger.warning("Wrong number of examples - generating additional examples")
                    current_examples = improvement_data.get("examples", [])
                    additional_needed = 9 - len(current_examples)
                    if additional_needed > 0:
                        additional_examples = self._generate_additional_examples(
                            improvement_data["improved_template"],
                            original_vars,
                            additional_needed
                        )
                        improvement_data["examples"] = current_examples + additional_examples[:additional_needed]
                
                # Update prompt with improvements
                improved_prompt = prompt_data.copy()
                improved_prompt.update({
                    "template": improvement_data["improved_template"],
                    "variables": original_vars,  # Keep original variables
                    "examples": improvement_data["examples"][:9],
                    "improvement_changes": improvement_data["changes_made"],
                    "improvement_rationale": improvement_data["rationale"]
                })
                
                return improved_prompt
                
        except Exception as e:
            logger.error(f"Improvement error: {str(e)}")
            return prompt_data

    def _generate_additional_examples(self, template: str, variables: List[str], num_needed: int) -> List[str]:
        """Generate additional examples if we don't have enough"""
        additional_prompt = f"""
        Using this prompt template:
        {template}
        
        With these variables:
        {', '.join(variables)}
        
        Generate {num_needed} more unique examples that:
        1. Use all variables in different ways
        2. Show different possible use cases
        3. Demonstrate the template's flexibility
        4. Are substantially different from each other
        
        Return only the list of examples, one per line.
        """
        
        try:
            response = self.generator.generate_content(additional_prompt)
            additional_examples = [ex.strip() for ex in response.text.split('\n') if ex.strip()]
            return additional_examples[:num_needed]
        except Exception as e:
            logger.error(f"Error generating additional examples: {str(e)}")
            return []
     
    def run_quality_loop(self, prompt_data: Dict[str, any]) -> Tuple[Dict[str, any], List[Dict[str, any]]]:
        """
        Runs the full quality improvement loop with evaluation and improvement steps.
        
        Args:
            prompt_data: Original prompt data to improve
            
        Returns:
            Tuple of (final improved prompt, list of improvement iterations)
        """
        current_prompt = prompt_data.copy()
        self.improvement_history = [{
            "iteration": 0,
            "prompt": current_prompt,
            "evaluation": None,
            "score": 0
        }]
        
        # Add quality threshold check
        quality_threshold = 75  # Can be made configurable
        max_iterations = self.max_iterations
        
        for i in range(1, max_iterations + 1):
            # Evaluate current prompt
            evaluation = self.evaluate_prompt(current_prompt)
            
            # Update previous iteration's evaluation
            self.improvement_history[-1]["evaluation"] = evaluation
            self.improvement_history[-1]["score"] = evaluation.get("total_score", 0)
            
            # Check if quality threshold is met
            if evaluation.get("total_score", 0) >= quality_threshold:
                logging.info(f"Quality threshold met at iteration {i}")
                break
                
            # Break if no improvement in last 2 iterations
            if i > 2:
                last_scores = [h["score"] for h in self.improvement_history[-2:]]
                if len(set(last_scores)) == 1:  # If last 2 scores are identical
                    logging.info("No improvement in last 2 iterations, stopping")
                    break
                    
            # Improve prompt based on evaluation
            improved_prompt = self.improve_prompt(current_prompt, evaluation)
            
            # Add to history
            self.improvement_history.append({
                "iteration": i,
                "prompt": improved_prompt,
                "evaluation": None,
                "score": 0
            })
            
            # Update current prompt for next iteration
            current_prompt = improved_prompt
            
        # Final evaluation of the last prompt
        if self.improvement_history[-1]["evaluation"] is None:
            final_evaluation = self.evaluate_prompt(self.improvement_history[-1]["prompt"])
            self.improvement_history[-1]["evaluation"] = final_evaluation
            self.improvement_history[-1]["score"] = final_evaluation.get("total_score", 0)
        
        # Return the best prompt version based on score
        best_iteration = max(self.improvement_history, key=lambda x: x["score"])
        return best_iteration["prompt"], self.improvement_history


class EnhancedPromptGenerator:
    """
    A class for generating enhanced prompt templates using the Gemini API.
    """
    def __init__(self, api_key: str, model_name: str = None, prompts_config: Dict = None):
        """
        Initializes the EnhancedPromptGenerator with a Gemini API key.

        Handles API initialization and sets up the Gemini GenerativeModel.

        Args:
            api_key: The API key for accessing the Gemini API.
            model_name: The name of the Gemini model to use.
            prompts_config: The configuration for prompts from prompts.yaml
        """
        try:
            genai.configure(api_key=api_key)
            # Use the specified Gemini model or a default if none is provided
            self.model = genai.GenerativeModel(model_name or 'gemini-2.0-flash-thinking-exp-01-21')
            self.initialization_error = None
            self.prompts_config = prompts_config or {}  # Load prompts configuration
        except Exception as e:
            self.initialization_error = f"API Initialization Error: {e}"
            logger.error(self.initialization_error, exc_info=True)

    def is_initialized(self) -> bool:
        """
        Checks if the EnhancedPromptGenerator was successfully initialized.

        Returns:
            bool: True if initialized successfully, False otherwise.
        """
        return self.initialization_error is None

    def _evaluate_prompt_quality(self, prompt_data: Dict[str, any]) -> float:
        """
        Evaluate the quality of a prompt based on simple heuristics.

        Args:
            prompt_data: Dictionary containing the prompt template and related information.

        Returns:
            A score representing the quality of the prompt. Higher is better.
        """
        template = prompt_data.get("template", "")
        variables = prompt_data.get("variables", [])

        score = 0

        # Basic checks
        if template:
            score += 0.3  # Template exists
        if variables:
            score += 0.2  # Variables exist

        # Heuristics
        score += min(0.2, len(template.split()) / 100)  # Length (up to 200 words)
        score += min(0.3, len(variables) / 5)  # Number of variables (up to 5)

        return score

    def generate_specialized_prompt(self,
                                   topic: str,
                                   content_type: str,
                                   style: str,
                                   use_case: str,
                                   model_platform: str) -> Dict[str, any]:
        """
        Generate a specialized prompt based on content type and platform

        Args:
            topic: The main subject of the prompt
            content_type: "image", "text", "video", etc.
            style: Visual or writing style preference
            use_case: The intended application of the output
            model_platform: The AI model platform (Midjourney, DALLE, etc.)

        Returns:
            Dictionary containing the prompt template and related information
        """
        if not self.is_initialized():
            return {"error": self.initialization_error}

        try:
            # Select the appropriate template structure based on content type
            if content_type.lower() == "image":
                return self._generate_image_prompt(topic, style, use_case, model_platform)
            elif content_type.lower() == "text":
                return self._generate_text_prompt(topic, style, use_case, model_platform)
            elif content_type.lower() == "video":
                return self._generate_video_prompt(topic, style, use_case, model_platform)
            else:
                return {"error": f"Unsupported content type: {content_type}"}

        except Exception as e:
            error_message = f"Prompt Generation Error: {e}"
            logger.error(error_message, exc_info=True)
            return {"error": str(e)}

    def _generate_image_prompt(self, topic: str, style: str, use_case: str, model_platform: str) -> Dict[str, any]:
        """Generate a specialized image prompt template with enhanced quality"""

        # Get platform-specific guidelines
        platform_guidelines = self._get_platform_guidelines(model_platform)

        # Get reference examples
        reference_examples = self._get_reference_examples("image", model_platform)

        # Construct an improved meta-prompt with more specific anti-patterns
        meta_prompt = self.prompts_config.get("image_meta_prompt", "").format(
            model_platform=model_platform,
            topic=topic,
            style=style,
            use_case=use_case,
            reference_examples=reference_examples
        )

        # Generate the prompt template with enhanced parameters
        response = self._generate_response(meta_prompt)
        if "error" in response:
            return response

        # Parse the response
        parsed_template = self._parse_prompt_response(response["text"])

        # Validate examples for quality and diversity
        example_validation = self._validate_examples(
            parsed_template["examples"],
            parsed_template["variables"],
            "image" # content_type
        )

        # Add metadata
        parsed_template["content_type"] = "image"
        parsed_template["platform"] = model_platform
        parsed_template["topic"] = topic
        parsed_template["style"] = style
        parsed_template["use_case"] = use_case
        parsed_template["raw_response"] = response["text"]
        parsed_template["example_validation"] = example_validation

        return parsed_template

    def _generate_text_prompt(self, topic: str, style: str, use_case: str, model_platform: str) -> Dict[str, any]:
        """Generate a specialized text prompt template"""
        try:
            # Construct the meta-prompt for generating a text prompt template
            meta_prompt = self.prompts_config.get("text_meta_prompt", "").format(
                model_platform=model_platform,
                topic=topic,
                style=style,
                use_case=use_case
            )

            # Generate the prompt template
            response = self._generate_response(meta_prompt)
            if "error" in response:
                return response

            # Parse the response
            parsed_template = self._parse_prompt_response(response["text"])

            # Add metadata
            parsed_template.update({
                "content_type": "text",
                "platform": model_platform,
                "topic": topic,
                "style": style,
                "use_case": use_case,
                "raw_response": response["text"]
            })

            # Safely extract instructions and description
            try:
                instructions_section = response["text"].split("## Instructions:")
                if len(instructions_section) > 1:
                    parsed_template["instructions"] = instructions_section[1].strip().split("##")[0].strip()
                else:
                    parsed_template["instructions"] = "No specific instructions provided."

                description_section = response["text"].split("## DESCRIPTION:")
                if len(description_section) > 1:
                    parsed_template["description"] = description_section[1].strip().split("##")[0].strip()
                else:
                    parsed_template["description"] = "No specific description provided."
            except Exception as e:
                logger.warning(f"Error extracting sections: {str(e)}")
                parsed_template["instructions"] = "Error extracting instructions."
                parsed_template["description"] = "Error extracting description."

            return parsed_template

        except Exception as e:
            logger.error(f"Text prompt generation error: {str(e)}", exc_info=True)
            return {
                "error": f"Failed to generate text prompt: {str(e)}",
                "template": "",
                "variables": [],
                "examples": [],
                "instructions": "Generation failed",
                "description": "Generation failed"
            }

    def _generate_video_prompt(self, topic: str, style: str, use_case: str, model_platform: str) -> Dict[str, any]:
        """Generate a specialized video prompt template"""

        # Construct the meta-prompt for generating a video prompt template
        meta_prompt = self.prompts_config.get("video_meta_prompt", "").format(
            model_platform=model_platform,
            topic=topic,
            style=style,
            use_case=use_case
        )

        # Generate the prompt template
        response = self._generate_response(meta_prompt)
        if "error" in response:
            return response

        # Parse the response
        parsed_template = self._parse_prompt_response(response["text"])
        parsed_template["content_type"] = "video"
        parsed_template["platform"] = model_platform
        parsed_template["topic"] = topic
        parsed_template["style"] = style
        parsed_template["use_case"] = use_case
        parsed_template["raw_response"] = response["text"]

        return parsed_template

    def _generate_response(self, prompt: str) -> Dict[str, any]:
        """Generate a response using the Gemini model with enhanced configurations"""
        try:
            # Configure generation parameters
            generation_config = genai_types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=8191,
                top_p=0.95,
                top_k=40
            )

            # Generate the response
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )

            return {"text": response.text}

        except Exception as e:
            error_message = f"Generation Error: {str(e)}"
            logger.error(error_message, exc_info=True)
            return {"error": error_message, "exception": e}

    def _get_reference_examples(self, content_type: str, model_platform: str) -> str:
        """Return reference examples for the given content type and platform"""
        platform = model_platform.lower()
        content_type = content_type.lower()

        if content_type == "image":
            if "midjourney" in platform:
                return self.prompts_config.get("midjourney_image_examples", "")
            elif "dalle" in platform or "dall-e" in platform:
                return self.prompts_config.get("dalle_image_examples", "")
            else:
                return self.prompts_config.get("generic_image_examples", "")

        elif content_type == "text":
            return self.prompts_config.get("text_examples", "")

        elif content_type == "video":
            if "sora" in platform:
                return self.prompts_config.get("sora_video_examples", "")
            else:
                return self.prompts_config.get("generic_video_examples", "")

        else:
            return self.prompts_config.get("generic_examples", "")

    def _process_examples(self, examples: List[str], variables: List[str]) -> List[str]:
        """Process and validate example prompts"""
        processed_examples = []

        for example in examples:
            # Skip empty examples
            if not example.strip():
                continue

            # Remove any leftover variable placeholders
            processed = example
            for var in variables:
                if f"[{var}]" in processed:
                    processed = processed.replace(f"[{var}]", f"{var.lower()}")

            # Basic cleaning
            processed = processed.strip()
            processed = processed.replace("\n", " ")
            processed = " ".join(processed.split())  # Remove extra spaces

            # Remove common formatting artifacts
            processed = processed.strip('"').strip("'")

            # Only add non-empty, non-duplicate examples
            if processed and processed not in processed_examples:
                processed_examples.append(processed)

        return processed_examples

    def _parse_prompt_response(self, response_text: str) -> Dict[str, any]:
        """
        Parse the structured JSON response from the model into a usable dictionary.
        This version is more robust and can handle missing code block fences.
        """
        try:
            # First, try to find the content within ```json ... ```
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', response_text)
            if json_match:
                json_string = json_match.group(1)
            else:
                # If no ```json``` block is found, try to find the first '{' and last '}'
                # This handles cases where the AI forgets the code block but still returns JSON.
                start_index = response_text.find('{')
                end_index = response_text.rfind('}')
                if start_index != -1 and end_index != -1 and end_index > start_index:
                    json_string = response_text[start_index : end_index + 1]
                else:
                    # If we can't find any JSON structure, we can't proceed.
                    raise ValueError("Could not find a valid JSON structure in the response.")

            # Convert the extracted JSON string into a Python dictionary
            parsed_json = json.loads(json_string)

            # Safely get the values from the parsed JSON.
            template = parsed_json.get("template", "")
            variables = list(set(re.findall(r'\[(.*?)\]', template)))

            # Map the parsed JSON to your final result dictionary.
            result = {
                "template": template,
                "variables": variables,
                "variable_explanations": parsed_json.get("variables_explanation", {}),
                "examples": self._process_examples(parsed_json.get("example_prompts", []), variables),
                "tips": parsed_json.get("technical_tips", []) or parsed_json.get("writing_strategy", []) or parsed_json.get("video_techniques", []),
                "description": parsed_json.get("description", ""),
                "instructions": parsed_json.get("instructions", "")
            }
            return result

        except (json.JSONDecodeError, ValueError, Exception) as e:
            logger.error(f"Failed to parse response: {e}\nRaw Response:\n{response_text}")
            return {
                "error": "The AI model returned a response that could not be understood. Please try again.",
                "template": "", "variables": [], "variable_explanations": {}, "examples": [],
                "tips": [], "description": "", "instructions": ""
            }
        
    def _get_platform_guidelines(self, platform: str) -> str:
        """Return platform-specific guidelines for prompt engineering"""
        platform = platform.lower()

        if "midjourney" in platform:
            return self.prompts_config.get("midjourney_guidelines", "")
        elif "dalle" in platform or "dall-e" in platform:
            return self.prompts_config.get("dalle_guidelines", "")
        elif "stable diffusion" in platform:
            return self.prompts_config.get("stable_diffusion_guidelines", "")
        elif "flux" in platform:
            return self.prompts_config.get("flux_guidelines", "")
        elif "sora" in platform:
            return self.prompts_config.get("sora_guidelines", "")
        elif "gpt" in platform or "claude" in platform or "llama" in platform or "gemini" in platform:
            return self.prompts_config.get("language_model_guidelines", "")
        else:
            return self.prompts_config.get("general_guidelines", "")

    def validate_prompt_against_guidelines(self, prompt_data: Dict[str, any]) -> Dict[str, any]:
        """
        Validate the generated prompt against PromptBase guidelines

        Returns a dictionary with validation results and improvement suggestions
        """
        validation_results = {
            "passed": True,
            "issues": [],
            "suggestions": []
        }

        template = prompt_data.get("template", "")
        variables = prompt_data.get("variables", [])
        examples = prompt_data.get("examples", [])

        # Check if template exists
        if not template:
            validation_results["passed"] = False
            validation_results["issues"].append("Missing prompt template")

        # Check for variables in square brackets
        if not variables:
            validation_results["passed"] = False
            validation_results["issues"].append("No editable variables found in square brackets")
            validation_results["suggestions"].append("Add editable variables in [SQUARE_BRACKETS] to make the prompt more versatile")

        # Check if there are too many variables (potentially making it complex)
        if len(variables) > 10:
            validation_results["passed"] = False
            validation_results["issues"].append(f"Too many variables ({len(variables)})")
            validation_results["suggestions"].append("Reduce the number of variables to 5 key elements")

        # Check for example diversity
        if len(examples) < 3:
            validation_results["passed"] = False
            validation_results["issues"].append("Not enough example prompts")
            validation_results["suggestions"].append("Include at least 5 diverse examples")

        # Check template length
        if len(template.split()) < 10:
            validation_results["passed"] = False
            validation_results["issues"].append("Prompt template too short/simple")
            validation_results["suggestions"].append("Expand the template with more specific styling instructions")
        elif len(template.split()) > 150:
            validation_results["issues"].append("Prompt template very long, may be unwieldy")
            validation_results["suggestions"].append("Consider simplifying the template while maintaining specificity")

        return validation_results

    def generate_test_outputs(self, prompt_data: Dict[str, any],
                              content_type: str,
                              model_platform: str) -> Dict[str, any]:
        """
        Generate a prompt with testing guidance to help the user validate outputs

        Returns instructions for testing the generated prompt effectively
        """
        if not prompt_data.get("template"):
            return {"error": "No prompt template available to generate test outputs"}

        try:
            test_guidance = {
                "test_instructions": [],
                "quality_checklist": [],
                "common_issues": []
            }

        # General test instructions
            test_guidance["test_instructions"] = [
                f"Fill in each variable with different values to test versatility",
                f"Try using the first example prompt exactly as written as your baseline",
                f"Test at least 5 different variations to ensure consistent style",
                f"Save all outputs generated during testing for comparison"
            ]

            # Content type specific checks
            if content_type.lower() == "image":
                test_guidance["quality_checklist"] = [
                    "Check that the style remains consistent across different subjects",
                    "Verify that the composition matches your expectations",
                    "Ensure the visual quality is high (no distortions, artifacts)",
                    "Confirm that changing variables produces meaningful differences",
                    "Verify that objects/subjects are properly formed and proportional"
                ]

                test_guidance["common_issues"] = [
                    "Subject distortion or anatomical issues",
                    "Inconsistent style between generations",
                    "Text rendering problems if text is included",
                    "Composition issues when changing aspect ratio",
                    f"Platform-specific limitations of {model_platform}"
                ]

            elif content_type.lower() == "text":
                test_guidance["quality_checklist"] = [
                    "Verify that the tone and style remain consistent",
                    "Check that the structure follows your specifications",
                    "Ensure factual accuracy and logical coherence",
                    "Confirm proper adaptation to different variables",
                    "Verify appropriate length and detail level"
                ]

                test_guidance["common_issues"] = [
                    "Inconsistent tone or style",
                    "Repetitive phrasing or content",
                    "Lack of specific detail when needed",
                    "Factual inconsistencies or logical errors",
                    "Format not following specifications"
                ]

            elif content_type.lower() == "video":
                test_guidance["quality_checklist"] = [
                    "Check that motion and transitions are smooth",
                    "Verify that the visual style is consistent throughout",
                    "Ensure temporal coherence (logical sequence of events)",
                    "Confirm that changing variables produces meaningful differences",
                    "Verify appropriate pacing and timing"
                ]

                test_guidance["common_issues"] = [
                    "Temporal inconsistencies or jumps",
                    "Motion artifacts or distortions",
                    "Subject transformation or 'melting' issues",
                    "Inconsistent style between frames",
                    "Camera movement issues"
                ]

            # Add platform-specific testing advice
            if "midjourney" in model_platform.lower():
                test_guidance["test_instructions"].append("Try adding --stylize 250 to increase Midjourney's artistic input")
                test_guidance["test_instructions"].append("Experiment with different aspect ratios using --ar parameter")

            elif "dalle" in model_platform.lower():
                test_guidance["test_instructions"].append("Try modifying the prompt order to prioritize different elements")
                test_guidance["test_instructions"].append("Test both square and rectangular aspect ratios")


            return test_guidance

        except Exception as e:
            error_message = f"Failed to generate test guidance: {str(e)}"
            logger.error(error_message, exc_info=True)
            return {"error": error_message}

    def _validate_examples(self, examples: List[str], variables: List[str], content_type: str) -> List[Dict[str, any]]:
        """Validate generated examples for quality and diversity with more sophisticated checks"""
        validation_results = []

        # Expanded list of generic AI terms to check for
        generic_ai_terms = [
            "beautiful", "stunning", "amazing", "high quality", "high-quality",
            "detailed", "intricate", "professional", "perfect", "exquisite",
            "4k", "8k", "ultra hd", "ultra-detailed", "masterpiece",
            "trending on artstation", "award winning", "breathtaking",
            "photorealistic", "hyperrealistic", "cinematic"
        ]

        # Track key elements across examples to check for real diversity
        key_elements = []

        for i, example in enumerate(examples):
            result = {
                "example": example,
                "issues": [],
                "score": 10  # Start with perfect score
            }

            # Extract key elements from this example (simple implementation)
            words = set(example.lower().split())
            key_elements.append(words)

            # Check for generic AI language
            ai_term_count = 0
            for term in generic_ai_terms:
                if term in example.lower():
                    result["issues"].append(f"Contains generic AI term: {term}")
                    ai_term_count += 1

            # Penalize based on number of AI terms
            if ai_term_count > 0:
                result["score"] -= min(5, ai_term_count)  # Cap at -5 points

            # Check for variable usage
            for var in variables:
                if f"[{var}]" in example:
                    result["issues"].append(f"Contains unfilled variable: {var}")
                    result["score"] -= 2

            # Check for adequate length/complexity
            if len(example.split()) < 10:
                result["issues"].append("Example too short")
                result["score"] -= 2
            elif len(example.split()) > 100:
                result["issues"].append("Example excessively long")
                result["score"] -= 1

            # More sophisticated similarity check using Jaccard similarity
            for j, other_words in enumerate(key_elements[:i]):  # Only check against previous examples
                # Calculate Jaccard similarity (set intersection over union)
                intersection = len(words.intersection(other_words))
                union = len(words.union(other_words))
                similarity = intersection / union if union > 0 else 0

                if similarity > 0.6:  # More than 60% similar
                    result["issues"].append(f"Too similar to example #{j+1} (similarity: {similarity:.2f})")
                    result["score"] -= min(4, int(similarity * 6))  # Higher penalty for higher similarity

            # Penalize keyword repetition within the same example
            word_counts = {}
            for word in example.lower().split():
                if len(word) > 3:  # Only count significant words
                    word_counts[word] = word_counts.get(word, 0) + 1

            repetitive_words = [word for word, count in word_counts.items() if count > 2]
            if repetitive_words:
                result["issues"].append(f"Repetitive words: {', '.join(repetitive_words)}")
                result["score"] -= min(3, len(repetitive_words))

            validation_results.append(result)

        return validation_results