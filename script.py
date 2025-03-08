import streamlit as st
import google.generativeai as genai
from typing import List, Dict, Optional, Tuple
import json
import re
import sqlite3

DATABASE_NAME = "prompt_library.db"  

def initialize_database():
    """Initializes the database and creates the prompts table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            content_type TEXT NOT NULL,
            platform TEXT NOT NULL,
            style TEXT NOT NULL,
            use_case TEXT NOT NULL,
            template TEXT NOT NULL,
            variables TEXT,  -- JSON stringified list
            variable_explanations TEXT, -- JSON stringified dict
            examples TEXT, -- JSON stringified list
            tips TEXT, -- JSON stringified list
            validation TEXT, -- JSON stringified dict
            test_guidance TEXT, -- JSON stringified dict
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_prompt_to_db(prompt_data: Dict[str, any]):
    """
    Saves prompt data to the SQLite database.

    Args:
        prompt_data (Dict[str, any]): A dictionary containing the prompt details to be saved.
    """
    print("DEBUG: save_prompt_to_db() - Function called")  # Keep for monitoring
    prompt_data_with_defaults = {
        "topic": prompt_data.get("topic", ""),
        "content_type": prompt_data.get("content_type", ""),
        "platform": prompt_data.get("platform", ""),
        "style": prompt_data.get("style", ""),
        "use_case": prompt_data.get("use_case", ""),
        "template": prompt_data.get("template", ""),
        "variables": prompt_data.get("variables", []),
        "variable_explanations": prompt_data.get("variable_explanations", {}),
        "examples": prompt_data.get("examples", []),
        "tips": prompt_data.get("tips", []),
        "validation": prompt_data.get("validation", {
            "passed": True,
            "issues": [],
            "suggestions": []
        }),
        "test_guidance": prompt_data.get("test_guidance", {
            "test_instructions": [],
            "quality_checklist": [],
            "common_issues": []
        })
    }

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO prompts (
                topic, content_type, platform, style, use_case, template,
                variables, variable_explanations, examples, tips, validation, test_guidance
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prompt_data_with_defaults["topic"],
            prompt_data_with_defaults["content_type"],
            prompt_data_with_defaults["platform"],
            prompt_data_with_defaults["style"],
            prompt_data_with_defaults["use_case"],
            prompt_data_with_defaults["template"],
            json.dumps(prompt_data_with_defaults["variables"]),
            json.dumps(prompt_data_with_defaults["variable_explanations"]),
            json.dumps(prompt_data_with_defaults["examples"]),
            json.dumps(prompt_data_with_defaults["tips"]),
            json.dumps(prompt_data_with_defaults["validation"]),
            json.dumps(prompt_data_with_defaults["test_guidance"])
        ))
        conn.commit()
        print("DEBUG: save_prompt_to_db() - Prompt saved successfully")
    except sqlite3.Error as e:
        print(f"DEBUG: save_prompt_to_db() - Database Error: {e}") 
        raise
    finally:
        conn.close()
        print("DEBUG: save_prompt_to_db() - Database connection closed") 

def get_all_prompts_from_db() -> List[Dict[str, any]]:
    """
    Fetches all prompts from the SQLite database and deserializes JSON fields.

    Returns:
        List[Dict[str, any]]: A list of dictionaries, where each dictionary represents a saved prompt.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    print("DEBUG: get_all_prompts_from_db() - Database connected") # DEBUG
    try:
        cursor.execute("SELECT * FROM prompts ORDER BY created_at DESC") # Order by newest first
        rows = cursor.fetchall()
        print(f"DEBUG: get_all_prompts_from_db() - Rows fetched: {rows}") # DEBUG
        prompts = []
        for row in rows:
            print(f"DEBUG: get_all_prompts_from_db() - Processing row: {row}") # DEBUG
            prompt_dict = {
                "id": row[0],
                "topic": row[1],
                "content_type": row[2],
                "platform": row[3],
                "style": row[4],
                "use_case": row[5],
                "template": row[6],
                "variables": json.loads(row[7]) if row[7] else [], # Deserialize JSON strings back to Python objects
                "variable_explanations": json.loads(row[8]) if row[8] else {},
                "examples": json.loads(row[9]) if row[9] else [],
                "tips": json.loads(row[10]) if row[10] else [],
                "validation": json.loads(row[11]) if row[11] else {},
                "test_guidance": json.loads(row[12]) if row[12] else {},
                "created_at": row[13]
            }
            prompts.append(prompt_dict)
        print(f"DEBUG: get_all_prompts_from_db() - Prompts list: {prompts}") # DEBUG
        return prompts
    except sqlite3.Error as e:
        st.error(f"Error fetching prompts from database: {e}")
        print(f"DEBUG: get_all_prompts_from_db() - Database Error: {e}") # DEBUG
        return []
    finally:
        conn.close()
        print("DEBUG: get_all_prompts_from_db() - Database connection closed") # DEBUG

initialize_database()

class EnhancedPromptGenerator:
    """
    A class for generating enhanced prompt templates using the Gemini API.

    It supports generating templates for images, text, and videos, tailored for different AI platforms.
    """
    def __init__(self, api_key: str):
        """
        Initializes the EnhancedPromptGenerator with a Gemini API key.

        Handles API initialization and sets up the Gemini GenerativeModel.

        Args:
            api_key (str): The API key for accessing the Gemini API.
        """
        try:
            genai.configure(api_key=api_key)
            # Use the most recent stable Gemini model
            self.model = genai.GenerativeModel('gemini-2.0-flash-thinking-exp-01-21')
            self.initialization_error = None
        except Exception as e:
            self.initialization_error = f"API Initialization Error: {e}"
            st.error(self.initialization_error)
    
    def is_initialized(self) -> bool:
        """
        Checks if the EnhancedPromptGenerator was successfully initialized.

        Returns:
            bool: True if initialized successfully, False otherwise.
        """
        return self.initialization_error is None
    
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
            st.error(f"Prompt Generation Error: {e}")
            return {"error": str(e)}
    
    def _generate_image_prompt(self, topic: str, style: str, use_case: str, model_platform: str) -> Dict[str, any]:
        """Generate a specialized image prompt template with enhanced quality"""
        
        # Get platform-specific guidelines
        platform_guidelines = self._get_platform_guidelines(model_platform)
        
        # Get reference examples
        reference_examples = self._get_reference_examples("image", model_platform)
        
        # Construct an improved meta-prompt with more specific anti-patterns
        meta_prompt = f"""
        You are an expert prompt engineer specializing in image generation prompts for {model_platform}, with deep knowledge of visual arts, photography, and design.
        
        TASK: Create a professional-quality prompt template for generating images of {topic} in {style} style for {use_case}.
        
        {reference_examples}
        
        OUTPUT REQUIREMENTS:
        1. Create a prompt template that uses technical terminology that artists, photographers, and designers actually use
        2. Use [VARIABLES] for elements that truly impact the image generation (avoid generic variables), Max Variables 5
        3. Variables should control: subject specifics, composition elements, technical aspects, stylistic elements, and mood/atmosphere
        4. Each example must be substantively different while maintaining the core {style} aesthetic
        5. Include specific visual techniques relevant to {style} (not general terms like "beautiful" or "high quality")
        6. Use language that a professional {style} artist would use to describe their work
        
        ANTI-PATTERNS TO AVOID:
        1. DO NOT use AI-sounding language like:
        - "in the style of..." (use more specific descriptors instead)
        - "high-quality", "detailed", "intricate", "photorealistic", "4k", "8k", "HD"
        - "beautifully rendered", "stunning", "amazing", "incredible", "gorgeous"
        - "masterpiece", "award-winning", "breathtaking", "professional"
        2. DO NOT use meaningless adjectives that don't actually guide the image generation
        3. DO NOT create examples by just swapping similar words
        4. DO NOT list technical specifications without explaining their visual impact
        5. DO NOT use cliché phrases from prompt marketplaces
        
        INSTEAD, USE:
        1. Specific technical terms: "split lighting", "low-key portrait", "Dutch angle", "telephoto compression"
        2. Actual artistic/photographic techniques: "chiaroscuro", "contre-jour", "rack focus", "selective color"
        3. Real material descriptions: "corten steel", "brushed aluminum", "gesso on canvas"
        4. Specific color theory language: "analogous palette", "monochromatic with accent color", "split complementary"
        
        FORMAT YOUR RESPONSE LIKE THIS:
        
        # {topic} - {style} Style Template for {model_platform}
        
        ## Prompt Template:
        [Full template with [VARIABLES] in square brackets]
        
        #DESCRIPTION OF PROMPT
        - [DESCRIPTION]
        
        ## Variables Explanation:
        - [VARIABLE_1]: Brief explanation of what this variable controls and why it matters visually
        - [VARIABLE_2]: Brief explanation of what this variable controls and why it matters visually
        (and so on for all variables)
        
        ## Example Prompts:
        1. [First complete example with all variables filled in - must be a truly distinct visual concept]
        2. [Second complete example with different variables - must create a substantially different image]
        (and so on for 5-9 examples)
       
        
        ## Technical Tips:
        - 3-5 specific tips relating to {model_platform}'s specific capabilities and limitations with {style} style
        - Include why these tips matter technically
        
        
        ## Instructions:
        - [INSTRUCTIONS]
        
        """
        
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
            "image"
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
        
        # Construct the meta-prompt for generating a text prompt template
        meta_prompt = f"""
        You are an expert prompt engineer specializing in AI writing prompts for {model_platform}.
        
        TASK: Create a professional-quality prompt template for generating written content about {topic} in {style} style for {use_case}.
        
        OUTPUT REQUIREMENTS:
        1. The prompt template must follow PromptBase's guidelines:
           - Must be a template with editable variables in [SQUARE_BRACKETS]
           - Must have a consistent output style across different inputs
           - Must be specific enough to generate high-quality, useful text
           - Must not be too specific or niche
        
        2. Include 4 clearly marked editable variables that allow users to customize key aspects
        
        3. Create 9 diverse example prompts that show the template's versatility
        
        4. Include format specifications (length, structure, tone)
        
        5. Include context-setting elements that help the AI understand the background
        
        FORMAT YOUR RESPONSE LIKE THIS:
        
        # {topic} - {style} Style Writing Template for {model_platform}
        
        ## Prompt Template:
        [Full template with [VARIABLES] in square brackets]
        
        ## Variables Explanation:
        - [VARIABLE_1]: Brief explanation of what this variable controls
        - [VARIABLE_2]: Brief explanation of what this variable controls
        (and so on for all variables)
        
        ## Example Prompts:
        1. [First complete example with all variables filled in]
        2. [Second complete example with different variables]
        (and so on for 9 examples)
        
        ## Writing Strategy:
        - 3-5 specific tips for getting the best results with this prompt
        
        ## DESCRIPTION:
        - [DESCRIPTION]
        
        ## Instructions:
        - [INSTRUCTIONS]
        
        """
        
        # Generate the prompt template
        response = self._generate_response(meta_prompt)
        if "error" in response:
            return response
        
        # Parse the response
        parsed_template = self._parse_prompt_response(response["text"]) 
        
        # Add metadata
        parsed_template["content_type"] = "text"
        parsed_template["platform"] = model_platform
        parsed_template["topic"] = topic
        parsed_template["style"] = style
        parsed_template["use_case"] = use_case
        parsed_template["raw_response"] = response["text"]
        parsed_template["instructions"] = response["text"].split("INSTRUCTIONS:")[1].strip()
        parsed_template["description"] = response["text"].split("DESCRIPTION:")[1].split("##")[0].strip()

        # Extract instructions and description if present
        try:
            parsed_template["instructions"] = response["text"].split("## Instructions:")[1].split("##")[0].strip()
        except IndexError:
            parsed_template["instructions"] = ""
            
        try:
            parsed_template["description"] = response["text"].split("## DESCRIPTION:")[1].split("##")[0].strip()
        except IndexError:
            parsed_template["description"] = ""
        
        return parsed_template
    
    def _generate_video_prompt(self, topic: str, style: str, use_case: str, model_platform: str) -> Dict[str, any]:
        """Generate a specialized video prompt template"""
        
        # Construct the meta-prompt for generating a video prompt template
        meta_prompt = f"""
        You are an expert prompt engineer specializing in AI video generation prompts for {model_platform}.
        
        TASK: Create a professional-quality prompt template for generating videos of {topic} in {style} style for {use_case}.
        
        OUTPUT REQUIREMENTS:
        1. The prompt template must follow PromptBase's guidelines:
           - Must be a template with editable variables in [SQUARE_BRACKETS]
           - Must have a consistent style across different inputs
           - Must be specific enough to generate high-quality videos
           - Must include temporal elements (movement, transitions, etc.)
        
        2. Include 5-7 clearly marked editable variables that allow users to customize key aspects
        
        3. Create 9 diverse example prompts that show the template's versatility
        
        4. Include technical specifications (camera movement, lighting, pacing)
        
        FORMAT YOUR RESPONSE LIKE THIS:
        
        # {topic} - {style} Style Video Template for {model_platform}
        
        ## Prompt Template:
        [Full template with [VARIABLES] in square brackets]
        
        ## Variables Explanation:
        - [VARIABLE_1]: Brief explanation of what this variable controls
        - [VARIABLE_2]: Brief explanation of what this variable controls
        (and so on for all variables)
        
        ## Example Prompts:
        1. [First complete example with all variables filled in]
        2. [Second complete example with different variables]
        (and so on for 9 examples)
        
        ## Video Techniques:
        - 3-5 specific tips for getting the best results with this prompt
        """
        
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
            generation_config = genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=4096,
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
            return {"error": f"Generation Error: {str(e)}"}

    def _get_reference_examples(self, content_type: str, model_platform: str) -> str:
        """Return reference examples for the given content type and platform"""
        platform = model_platform.lower()
        content_type = content_type.lower()
        
        if content_type == "image":
            if "midjourney" in platform:
                return """
                REFERENCE EXAMPLES:
                
                Good Example 1: "Ancient Egyptian temple, low angle view, sandstone architecture, hieroglyphics on pillars, [TIME_OF_DAY] light filtering through columns, [MOOD] atmosphere, detailed carved reliefs, desert landscape visible through entrance, architectural photography, 32mm lens"
                
                Good Example 2: "Retrofuturistic control room, [ERA] technology aesthetic, curved console displays, analog meters and switches, [COLOR_SCHEME] color palette, atmospheric lighting, mid-century modern furniture details, wide-angle composition, technical illustration style"
                
                Bad Example: "Beautiful hyperrealistic 8K image of a stunning portrait, high quality, best quality, masterpiece, trending on artstation" (Generic terms that don't guide generation)
                """
            elif "dalle" in platform or "dall-e" in platform:
                return """
                REFERENCE EXAMPLES:
                
                Good Example 1: "Botanical illustration of [PLANT_SPECIES] in the style of 19th century scientific journals, detailed pen and ink technique, labeled anatomical features, delicate watercolor wash in [COLOR_SCHEME], composition on aged parchment, scientifically accurate"
                
                Good Example 2: "Isometric cityscape of [CITY_TYPE] with distinct architectural styles, 45-degree viewing angle, selective focus on [FOCAL_POINT], morning mist effect, modular building arrangement, detailed infrastructure elements, muted palette with [ACCENT_COLOR] highlights"
                
                Bad Example: "Stunning 4K ultra detailed cityscape, photorealistic, breathtaking view, high quality, trending" (Lacks specific visual direction)
                """
            else:
                return """
                REFERENCE EXAMPLES:
                
                Good Example 1: "Stylized character design of [CHARACTER_TYPE], three-quarter view, [ART_STYLE] influence, distinctive silhouette, [COLOR_PALETTE] scheme, subtle texturing on clothing, dynamic pose suggesting personality, clean linework, neutral background with rim lighting"
                
                Good Example 2: "Atmospheric landscape featuring [LANDSCAPE_ELEMENT], [WEATHER_CONDITION] effects, foreground detail of [FOREGROUND_ELEMENT], receding planes of depth, complimentary color harmony based around [PRIMARY_COLOR], photographic composition with rule of thirds, diffused lighting"
                
                Bad Example: "Amazing 8K artwork, extremely detailed, beautiful masterpiece, award-winning, trending on artstation" (Generic superlatives without specific direction)
                """
        
        elif content_type == "text":
            return """
            REFERENCE EXAMPLES:
            
            Good Example 1: "Create a comprehensive guide about [TOPIC] that includes: historical context, key principles, practical applications for [USER_TYPE], common misconceptions, and future developments. Use [TONE] language suitable for [AUDIENCE_EXPERTISE] level readers, with clear subheadings, practical examples, and actionable takeaways."
            
            Good Example 2: "Write a persuasive [DOCUMENT_TYPE] about [SUBJECT] targeting [SPECIFIC_AUDIENCE]. Structure it with: an attention-grabbing opening using [HOOK_TYPE], three compelling arguments supported by [EVIDENCE_TYPE], anticipation and refutation of [COUNTERARGUMENT], and a call to action that emphasizes [BENEFIT]. Maintain a [TONE] voice throughout."
            
            Bad Example: "Write a good article about business that is interesting and informative" (Too vague, lacks specific structure and style guidance)
            """
            
        elif content_type == "video":
            if "sora" in platform:
                return """
                REFERENCE EXAMPLES:
                
                Good Example 1: "A [DURATION] video of [SUBJECT] with [CAMERA_MOVEMENT] revealing the [SETTING]. [LIGHTING_CONDITION] creates dynamic shadows as the camera [TRANSITION_TYPE] to show [SECONDARY_ELEMENT]. The atmosphere is [MOOD] with [COLOR_GRADE] color treatment. [WEATHER_ELEMENT] adds environmental depth. Camera uses [LENS_TYPE] perspective."
                
                Good Example 2: "A [TIME_PERIOD] inspired sequence beginning with [OPENING_SHOT] of [LOCATION], transitioning through [TRANSITION_TECHNIQUE] to reveal [SUBJECT] engaged in [ACTION]. Camera [MOVEMENT_TYPE] at [SPEED] while [LIGHTING_CHANGE] occurs. [ATMOSPHERIC_ELEMENT] provides depth as the scene develops toward [CLIMAX_ELEMENT]."
                
                Bad Example: "Beautiful cinematic video of a city with amazing details and perfect lighting, 8K, hyperrealistic" (Lacks temporal elements and specific visual direction)
                """
            else:
                return """
                REFERENCE EXAMPLES:
                
                Good Example 1: "A [DURATION] video showing [SUBJECT] with [CAMERA_TECHNIQUE] from [STARTING_PERSPECTIVE] to [ENDING_PERSPECTIVE]. Scene transitions from [OPENING_CONDITION] to [CLOSING_CONDITION] with [LIGHTING_STYLE] creating mood. [MOVEMENT_TYPE] of the subject contrasts with [BACKGROUND_ELEMENT]."
                
                Good Example 2: "A sequence depicting [EVENT] in [SETTING], beginning with [ESTABLISHING_SHOT] and progressing through [SHOT_SEQUENCE]. [TECHNICAL_EFFECT] emphasizes the [FOCAL_POINT] while [ENVIRONMENTAL_CONDITION] evolves throughout. Camera uses [LENS_CHARACTERISTIC] to achieve [VISUAL_GOAL]."
                
                Bad Example: "Amazing 4K video with beautiful cinematic quality showing stunning scenery" (Generic terms without specific visual direction or temporal elements)
                """
                
        else:
            return """
            REFERENCE EXAMPLES:
            
            Good Example 1: "Create a specialized template with clear variables controlling specific elements, demonstrated through diverse examples showing substantially different outputs."
            
            Good Example 2: "Design a versatile template that uses technical terminology specific to the field, with variables that modify meaningful aspects of the output."
            
            Bad Example: "Make a good template that creates amazing high-quality outputs" (Too vague and uses generic terms)
            """
    
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
        """Parse the structured response into a usable dictionary"""
        result = {
            "template": "",
            "variables": [],
            "variable_explanations": {},
            "examples": [],
            "tips": [],
            "description": "",
            "instructions": ""
        }
        
        # Extract Prompt Template 
        template_match = re.search(r'## Prompt Template:\s*\n(.*?)(?=\n## Description:|## DESCRIPTION:|## Variables Explanation:|## Variables explanation:|## Example Prompts:|## Example prompts:|\Z)', response_text, re.DOTALL | re.IGNORECASE)
        if template_match:
            result["template"] = template_match.group(1).strip()

            # Extract variables from the template
            variables = re.findall(r'\[(.*?)\]', result["template"])
            result["variables"] = list(set(variables))  # Remove duplicates

        # Extract Description 
        description_match = re.search(r'## (DESCRIPTION|Description):\s*\n(.*?)(?=\n## Variables Explanation:|## Variables explanation:|## Example Prompts:|## Example prompts:|## Usage Tips:|## Writing Strategy:|## Video Techniques:|\Z)', response_text, re.DOTALL | re.IGNORECASE)
        if description_match:
            result["description"] = description_match.group(2).strip()


        # Extract Variable Explanations
        var_explanations_section = re.search(r'## (VARIABLES EXPLANATION|Variables Explanation):\s*\n(.*?)(?=## Example Prompts:|## Example prompts:|## Usage Tips:|## Writing Strategy:|## Video Techniques:|\Z)', response_text, re.DOTALL | re.IGNORECASE)
        if var_explanations_section:
            var_lines = var_explanations_section.group(2).strip().split('\n')
            for line in var_lines:
                if line.strip().startswith('-'):
                    parts = line.strip('- ').split(':', 1)
                    if len(parts) == 2:
                        var_name = parts[0].strip()
                        var_explanation = parts[1].strip()
                        result["variable_explanations"][var_name] = var_explanation

        # Extract Example Prompts
        examples_section = re.search(r'## (EXAMPLE PROMPTS|Example Prompts):\s*\n(.*?)(?=## (USAGE TIPS|Usage Tips|Writing Strategy|Video Techniques):|\Z)', response_text, re.DOTALL | re.IGNORECASE)
        if examples_section:
            example_lines = examples_section.group(2).strip().split('\n')
            current_example = ""
            for line in example_lines:
                if re.match(r'^\d+\.', line.strip()):
                    if current_example:
                        result["examples"].append(current_example.strip())
                    current_example = line.strip()[line.find('.')+1:].strip()
                else:
                    current_example += " " + line.strip()
            if current_example:
                result["examples"].append(current_example.strip())

        # Extract Tips
        tips_section = re.search(r'## (USAGE TIPS|Usage Tips|WRITING STRATEGY|Writing Strategy|VIDEO TECHNIQUES|Video Techniques):\s*\n(.*?)(?=## DESCRIPTION:|## Description:|## Instructions:|\Z)', response_text, re.DOTALL | re.IGNORECASE)
        if tips_section:
            tip_lines = tips_section.group(2).strip().split('\n')
            for line in tip_lines:
                if line.strip().startswith('-'):
                    result["tips"].append(line.strip('- ').strip())

        # Extract Instructions
        instructions_section = re.search(r'## Instructions:\s*\n(.*?)(?=##|\Z)', response_text, re.DOTALL | re.IGNORECASE)
        if instructions_section:
            result["instructions"] = instructions_section.group(1).strip()


        # Additional post-processing to improve example quality
        processed_examples = self._process_examples(result["examples"], result["variables"])
        result["examples"] = processed_examples

        return result
    
    def _get_platform_guidelines(self, platform: str) -> str:
        """Return platform-specific guidelines for prompt engineering"""
        platform = platform.lower()
            
        if "midjourney" in platform:
            return """
            For Midjourney:
            - Place subject descriptions at the beginning, followed by style, then technical parameters
            - Use "--ar 16:9" for cinema, "--ar 1:1" for square compositions, "--ar 3:4" for portrait
            - Specific styles work better with specific values: "--stylize 100" for photorealism, "--stylize 750" for artistic
            - Use "--chaos 25" for more variability in compositions
            - Implement "--no" for negative prompts: "--no text, watermarks, blurry elements, distortion"
            - For lighting, specify: "rim lighting," "golden hour," "split lighting," or "Rembrandt lighting"
            - Use real photography/art terminology like "shallow depth of field," "Dutch angle," or "impasto technique"
            """
        elif "dalle" in platform or "dall-e" in platform:
            return """
            For DALL-E:
            - Be specific about artistic style and medium
            - Describe the subject and composition clearly
            - Include details about lighting, colors, and mood
            - Keep prompts concise but descriptive (under 400 characters works best)
            - Include a time period or art movement for stylistic clarity
            """
        elif "stable diffusion" in platform:
            return """
            For Stable Diffusion:
            - Use weights like (term:1.5) to emphasize certain elements
            - Include negative prompts with --no parameter
            - Specify camera details: lens type, distance, angle
            - Include lighting details and specific render styles
            - Reference specific artists or art styles for better results
            """
        elif "flux" in platform:
            return """
            For FLUX:
            - Specify resolution or aspect ratio in the prompt
            - Use detailed composition description
            - Include specific art styles or artist references
            - Specify camera angle, focal length, and lighting setup
            - Include mood descriptors for consistent results
            """
        elif "sora" in platform:
            return """
            For Sora:
            - Include camera movement descriptions (pan, zoom, tracking)
            - Specify the duration and pacing of the video
            - Include scene transitions if applicable
            - Describe lighting changes and environmental effects
            - Specify sound/audio elements if they affect visual components
            """
        elif "gpt" in platform or "claude" in platform or "llama" in platform or "gemini" in platform:
            return """
            For Language Models:
            - Provide clear context and background information
            - Specify the desired tone, style, and format
            - Define the target audience clearly
            - Include structural elements (headings, sections, etc.)
            - Specify the desired level of detail and technical complexity
            """
        else:
            return """
            General Guidelines:
            - Be specific about artistic style and medium
            - Include detailed descriptions of the subject matter
            - Specify composition, lighting, and color palette
            - Include references to specific techniques or artists if needed
            - Balance between detail and brevity
            """
    
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
            return {"error": f"Failed to generate test guidance: {str(e)}"}

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
def create_enhanced_ui():
    st.set_page_config(page_title="Advanced PromptBase Template Generator", layout="wide")
    
    if 'current_prompt' not in st.session_state:
        st.session_state.current_prompt = None    
        
    st.title("Professional PromptBase Template Generator")
    st.markdown("Generate high-quality, market-ready prompt templates aligned with PromptBase submission guidelines")
    
    # Sidebar for API Key
    st.sidebar.header("Configuration")
    gemini_api_key = st.sidebar.text_input("Gemini API Key", type="password")
    
    # Initialize generator if API key exists
    generator = None
    if gemini_api_key:
        generator = EnhancedPromptGenerator(gemini_api_key)
    
    # Main content in tabs
    tab1, tab2, tab3 = st.tabs(["Create Template", "Prompt Library", "Guidelines"])
    
    with tab1:
        st.header("Create New Prompt Template")

        col1, col2 = st.columns(2)

        with col1:
            # Basic parameters
            topic = st.text_input("Prompt Topic", placeholder="e.g., Vintage Movie Posters")

            content_type = st.selectbox(
                "Content Type",
                ["Image", "Text", "Video"],
                index=0
            )

            model_platform = st.selectbox(
                "AI Platform",
                ["Midjourney", "DALL-E", "Stable Diffusion", "FLUX", "Sora", "ChatGPT", "Claude", "Llama", "Gemini"],
                index=0
            )

        with col2:
            # Style options - adapt based on content type
            if content_type == "Image" or content_type == "Video":
                style_options = [
                    "Minimalist", "Photorealistic", "Vintage", "Cartoon", "Cyberpunk",
                    "Watercolor", "Pixel Art", "Abstract", "Surreal", "Gothic",
                    "Impressionist", "Pop Art", "Art Deco", "Sci-Fi", "Fantasy",
                    "Steampunk", "Retro", "Neon", "Vaporwave", "Cinematic"
                ]
            else:  # Text
                style_options = [
                    "Professional", "Conversational", "Academic", "Journalistic",
                    "Technical", "Creative", "Persuasive", "Instructional",
                    "Narrative", "Analytical", "Humorous", "Inspirational"
                ]

            style_preference = st.selectbox("Style", style_options)

            # Use case selection
            use_case_options = [
                "Marketing Materials", "Social Media Content", "Book/Album Covers",
                "Product Design", "Conceptual Art", "Advertising", "Personal Projects",
                "Educational Content", "Technical Documentation", "Entertainment"
            ]
            use_case = st.selectbox("Primary Use Case", use_case_options)

        # Generate button
        if st.button("Generate Professional Prompt Template"):
            if not gemini_api_key:
                st.error("Please enter a Gemini API Key")
            elif not topic:
                st.error("Please enter a prompt topic")
            elif generator and generator.is_initialized():
                with st.spinner(f"Generating {content_type} prompt template..."):
                    # Generate the prompt
                    prompt_data = generator.generate_specialized_prompt(
                        topic=topic,
                        content_type=content_type,
                        style=style_preference,
                        use_case=use_case,
                        model_platform=model_platform
                    )

                    if "error" in prompt_data:
                        st.error(f"Generation failed: {prompt_data['error']}")
                    else:
                        # Display results in expandable sections
                        st.success(f"✅ Generated {content_type} prompt template for {topic}")

                        # Validation check
                        validation = generator.validate_prompt_against_guidelines(prompt_data)

                        # Display the template
                        st.subheader("📝 Prompt Template")
                        st.code(prompt_data["template"], language="markdown")

                        # Variables and Explanations
                        with st.expander("📋 Variables and Explanations", expanded=True):
                            for var in prompt_data["variables"]:
                                explanation = prompt_data["variable_explanations"].get(var, "No explanation provided")
                                st.markdown(f"**{var}**: {explanation}")

                        #Display Description
                        #with st.expander("📖 Description"):
                        #    st.markdown(prompt_data["description"])

                        # Display Instructions
                        with st.expander("📝 Instructions"):
                            st.markdown(prompt_data["instructions"])

                        # Examples
                        with st.expander("🔍 Example Prompts", expanded=True):
                            for i, example in enumerate(prompt_data["examples"], 1):
                                st.markdown(f"**Example {i}:** {example}")

                        # Tips
                        with st.expander("💡 Usage Tips"):
                            for tip in prompt_data["tips"]:
                                st.markdown(f"- {tip}")

                        # Validation results
                        with st.expander("🔎 Prompt Quality Check"):
                            if validation["passed"]:
                                st.success("✅ This prompt meets all PromptBase guidelines")
                            else:
                                st.warning("⚠️ This prompt needs improvements to meet guidelines")

                            if validation["issues"]:
                                st.markdown("**Issues detected:**")
                                for issue in validation["issues"]:
                                    st.markdown(f"- {issue}")

                            if validation["suggestions"]:
                                st.markdown("**Improvement suggestions:**")
                                for suggestion in validation["suggestions"]:
                                    st.markdown(f"- {suggestion}")

                        # Testing guidance
                        with st.expander("🧪 Testing Instructions"):
                            test_guidance = generator.generate_test_outputs(
                                prompt_data, content_type, model_platform
                            )

                            if "error" in test_guidance:
                                st.error(test_guidance["error"])
                            else:
                                st.markdown("**How to test your prompt:**")
                                for instruction in test_guidance["test_instructions"]:
                                    st.markdown(f"- {instruction}")

                                st.markdown("**Quality checklist:**")
                                for check in test_guidance["quality_checklist"]:
                                    st.markdown(f"- {check}")

                                st.markdown("**Watch out for these common issues:**")
                                for issue in test_guidance["common_issues"]:
                                    st.markdown(f"- {issue}")

                        # Create export_data from prompt_data and store in session state
                        export_data = prompt_data.copy()
                        export_data["validation"] = validation  
                        export_data["test_guidance"] = test_guidance  
                        st.session_state.current_prompt = export_data

                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                label="📥 Download Prompt Package",
                                data=json.dumps(export_data, indent=2),
                                file_name=f"{topic.replace(' ', '_')}_{content_type.lower()}_prompt.json",
                                mime="application/json"
                            )
        
        # Move the save button outside of all conditional blocks
        if st.button("💾 Save to Library", key="save_library_button"): # <-- ADDED key="save_library_button"
            if st.session_state.current_prompt is not None:
                save_prompt_to_db(st.session_state.current_prompt)
                st.success("✅ Prompt saved to library!")
                # Optional: Clear the state after saving
                st.session_state.current_prompt = None
            else:
                st.error("Please generate a prompt first before saving")              
    with tab2:
            st.header("Prompt Library")
            prompts = get_all_prompts_from_db()

            if not prompts:
                st.info("Your prompt library is currently empty.")
            else:
                st.subheader("Saved Prompts")
                
                for prompt in prompts:
                    # Use st.expander to make each prompt collapsible
                    with st.expander(f"**{prompt['topic']}** ({prompt['content_type']} for {prompt['platform']}) - Saved on: {prompt['created_at']}", expanded=False): # expanded=False for initial collapse
                        # All the prompt details content goes inside the expander:

                        st.markdown(f"**Style:** {prompt['style']} | **Use Case:** {prompt['use_case']}") # Moved style and use_case up

                        # Template section
                        st.markdown("#### 📝 Prompt Template")
                        st.code(prompt["template"], language="markdown")
                        
                        # Columns for Variables and Examples
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("#### 📋 Variables")
                            for var in prompt.get("variables", []):
                                explanation = prompt.get("variable_explanations", {}).get(var, "No explanation provided")
                                st.markdown(f"**{var}**: {explanation}")
                            
                            st.markdown("#### 📖 Description")
                            if prompt.get("description"):
                                st.markdown(prompt["description"])
                            else:
                                st.info("No description provided")
                            
                            st.markdown("#### 📝 Instructions")
                            if prompt.get("instructions"):
                                st.markdown(prompt["instructions"])
                            else:
                                st.info("No instructions provided")
                        
                        with col2:
                            st.markdown("#### 🔍 Examples")
                            for i, example in enumerate(prompt.get("examples", []), 1):
                                st.markdown(f"**Example {i}:** {example}")
                            
                            st.markdown("#### 💡 Tips")
                            for tip in prompt.get("tips", []):
                                st.markdown(f"- {tip}")
                        
                        # Validation section
                        st.markdown("#### 🔎 Validation")
                        if prompt["validation"]["passed"]:
                            st.success("✅ Meets PromptBase guidelines")
                        else:
                            st.warning("⚠️ Needs improvements")
                        
                        if prompt["validation"].get("issues"):
                            for issue in prompt["validation"]["issues"]:
                                st.markdown(f"- ⚠️ {issue}")
                        
                        if prompt["validation"].get("suggestions"):
                            for suggestion in prompt["validation"]["suggestions"]:
                                st.markdown(f"- 💡 {suggestion}")
                        
                        # Testing guidance
                        st.markdown("#### 🧪 Testing Guide")
                        if prompt.get("test_guidance") and "error" not in prompt["test_guidance"]:
                            col3, col4 = st.columns(2)
                            with col3:
                                st.markdown("**Test Instructions:**")
                                for instruction in prompt["test_guidance"]["test_instructions"]:
                                    st.markdown(f"- {instruction}")
                                
                                st.markdown("**Quality Checklist:**")
                                for check in prompt["test_guidance"]["quality_checklist"]:
                                    st.markdown(f"- {check}")
                            
                            with col4:
                                st.markdown("**Common Issues:**")
                                for issue in prompt["test_guidance"]["common_issues"]:
                                    st.markdown(f"- {issue}")
                        
                        st.markdown("---")
    with tab3:
        st.header("PromptBase Submission Guidelines")
        
        st.markdown("""
        ### Key Guidelines for Successful PromptBase Submissions
        
        #### 1. Prompt Templates
        - Use [VARIABLES] in square brackets to make prompts adaptable
        - Make sure your prompt can generate various outputs in the same style
        - Each variable should control a meaningful aspect of the output
        
        #### 2. High Use-Case Factor
        - Prompts with practical applications sell better
        - Examples: logo designs, product photography, marketing content
        - Consider how others might use your prompt in their work
        
        #### 3. Unique Styles
        - Develop prompts that achieve distinctive visual or writing styles
        - Push the boundaries of what AI models can create
        - Create styles that would be difficult to achieve manually
        
        #### 4. Common Reasons for Rejection
        - Too specific or overly niche prompts
        - Inconsistent style across outputs
        - Low quality or distorted outputs
        - Example outputs too similar
        - Prompt too simple or easily guessable
        
        #### 5. Testing Your Prompts
        - Generate multiple examples with different variables
        - Ensure consistent style across all outputs
        - Verify that changing variables produces meaningful differences
        - Check for technical issues or artifacts
        """)

def main():
    create_enhanced_ui()

if __name__ == "__main__":
    main()