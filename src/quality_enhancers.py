"""
Quality Enhancers Module for Prompt Package Improvement.

This module implements counter-strategies identified from pattern analysis:
1. Title Fixer - Enforces [Descriptor] + [Subject] + [Type] pattern
2. Example Validator - Ensures 9-10 examples per package
3. Abstract Example Injector - Adds 2+ abstract/mood-based examples

Following @lint-agent guidelines:
- Type hints for all function signatures
- Docstrings for all public functions
- Use logging module instead of print()
- Error handling with fallback values
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

import google.generativeai as genai

logger = logging.getLogger(__name__)

# --- Constants ---

DESCRIPTORS = [
    "cinematic", "ethereal", "dramatic", "whimsical", "surreal", "vintage",
    "minimalist", "vibrant", "moody", "dreamy", "bold", "elegant", "rustic",
    "futuristic", "mystical", "playful", "serene", "dynamic", "abstract",
    "geometric", "organic", "retro", "neo", "hyper", "ultra", "epic"
]

FORMAT_TYPES = [
    "art", "illustration", "design", "photography", "portraits", "scenes",
    "landscapes", "mockups", "templates", "patterns", "icons", "logos",
    "poster", "wallpaper", "concept", "style", "aesthetic", "visuals",
    "renders", "compositions", "creations", "prints", "reveals", "tarot",
    "zines", "stickers", "graphics", "imagery", "artwork", "pieces",
    "shots", "images", "photos", "pictures", "views", "frames"
]

ABSTRACT_KEYWORDS = [
    "sense of", "feeling of", "essence of", "weight of", "spirit of",
    "melancholic", "ethereal", "transcendent", "ephemeral", "nostalgic",
    "forgotten", "oppressive", "liberating", "haunting", "evocative",
    "abstract", "conceptual", "mood", "atmosphere", "emotion"
]

MIN_TITLE_WORDS = 3
MAX_TITLE_WORDS = 6
MIN_EXAMPLES = 8
RECOMMENDED_EXAMPLES = 9
MIN_ABSTRACT_EXAMPLES = 2


# --- Title Validation & Fixing ---

def validate_title_pattern(title: str) -> Dict[str, Any]:
    """
    Validates a title against marketplace best practices.
    
    Args:
        title: The prompt package title to validate.
        
    Returns:
        dict: Validation result with keys:
            - is_valid: bool
            - issues: List of identified issues
            - word_count: int
            - has_descriptor: bool
            - has_format_type: bool
    """
    title_clean = title.strip().strip('"')
    words = title_clean.split()
    word_count = len(words)
    title_lower = title_clean.lower()
    
    issues = []
    
    # Check word count
    if word_count < MIN_TITLE_WORDS:
        issues.append("too_short")
    if word_count > MAX_TITLE_WORDS:
        issues.append("too_long")
    
    # Check for descriptor
    has_descriptor = any(desc in title_lower for desc in DESCRIPTORS)
    if not has_descriptor:
        issues.append("missing_descriptor")
    
    # Check for format type
    has_format_type = any(fmt in title_lower for fmt in FORMAT_TYPES)
    if not has_format_type:
        issues.append("missing_format_type")
    
    return {
        "is_valid": len(issues) == 0,
        "issues": issues,
        "word_count": word_count,
        "has_descriptor": has_descriptor,
        "has_format_type": has_format_type,
        "original_title": title
    }


def fix_title(
    model: genai.GenerativeModel,
    title: str,
    topic_context: Optional[str] = None
) -> Dict[str, Any]:
    """
    Uses AI to fix a title to match [Descriptor] + [Subject] + [Type] pattern.
    
    Args:
        model: Configured Gemini GenerativeModel instance.
        title: The original title to fix.
        topic_context: Optional additional context about the prompt.
        
    Returns:
        dict: Result with keys:
            - fixed_title: The improved title
            - original_title: The input title
            - was_changed: bool indicating if title was modified
    """
    validation = validate_title_pattern(title)
    
    if validation["is_valid"]:
        return {
            "fixed_title": title,
            "original_title": title,
            "was_changed": False,
            "validation": validation
        }
    
    prompt = f"""You are a marketplace title optimization expert.

Fix this title to match the pattern: [Emotional/Visual Descriptor] + [Subject] + [Format/Type]

ORIGINAL TITLE: "{title}"
ISSUES: {', '.join(validation['issues'])}
{f'CONTEXT: {topic_context}' if topic_context else ''}

REQUIREMENTS:
1. Must be 3-6 words total
2. Start with a descriptor: {', '.join(DESCRIPTORS[:10])}...
3. End with a format type: {', '.join(FORMAT_TYPES[:10])}...
4. Keep the core concept intact

EXAMPLES OF GOOD TITLES:
- "Cinematic Micro-Drone Product Reveals"
- "Surreal Edible Landscapes"
- "Neo-Victorian Cyberpunk Tarot"
- "Whimsical Watercolor Character Art"

Return ONLY a JSON object:
{{"fixed_title": "Your Fixed Title Here"}}
"""

    try:
        response = model.generate_content(prompt)
        response_text = response.text if hasattr(response, 'text') else str(response)
        
        # Parse JSON from response
        json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            fixed_title = result.get("fixed_title", title)
            
            return {
                "fixed_title": fixed_title,
                "original_title": title,
                "was_changed": fixed_title != title,
                "validation": validate_title_pattern(fixed_title)
            }
    except Exception as e:
        logger.error(f"Title fixing failed: {e}", exc_info=True)
    
    # Fallback: attempt simple fix
    return {
        "fixed_title": _simple_title_fix(title),
        "original_title": title,
        "was_changed": True,
        "validation": validation,
        "used_fallback": True
    }


def _simple_title_fix(title: str) -> str:
    """Fallback title fix without AI."""
    words = title.strip().strip('"').split()
    
    # Truncate if too long
    if len(words) > MAX_TITLE_WORDS:
        words = words[:MAX_TITLE_WORDS]
    
    # Add descriptor if missing
    title_lower = " ".join(words).lower()
    if not any(desc in title_lower for desc in DESCRIPTORS):
        words.insert(0, "Cinematic")
    
    # Add format type if missing
    if not any(fmt in title_lower for fmt in FORMAT_TYPES):
        words.append("Art")
    
    # Truncate again if needed
    if len(words) > MAX_TITLE_WORDS:
        words = words[:MAX_TITLE_WORDS]
    
    return " ".join(words)


# --- Example Validation ---

def validate_examples(package: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates that a package has sufficient examples.
    
    Args:
        package: The prompt package dictionary.
        
    Returns:
        dict: Validation result with keys:
            - is_valid: bool
            - current_count: int
            - required_count: int
            - deficit: int (negative means surplus)
    """
    examples = package.get("examples", [])
    
    # Handle both list of strings and list of dicts
    if examples and isinstance(examples[0], dict):
        count = len([e for e in examples if e.get("prompt") or e.get("variables")])
    else:
        count = len(examples)
    
    return {
        "is_valid": count >= MIN_EXAMPLES,
        "current_count": count,
        "required_count": MIN_EXAMPLES,
        "recommended_count": RECOMMENDED_EXAMPLES,
        "deficit": MIN_EXAMPLES - count
    }


# --- Abstract Example Detection & Injection ---

def check_abstract_examples(package: Dict[str, Any]) -> Dict[str, Any]:
    """
    Checks if package has abstract/conceptual examples.
    
    Args:
        package: The prompt package dictionary.
        
    Returns:
        dict: Check result with keys:
            - has_abstract: bool (True if >= 2 abstract examples)
            - abstract_count: int
            - abstract_indices: List of indices of abstract examples
    """
    examples = package.get("examples", [])
    abstract_indices = []
    
    for i, example in enumerate(examples):
        # Handle dict or string examples
        if isinstance(example, dict):
            text = example.get("prompt", "") or str(example.get("variables", ""))
        else:
            text = str(example)
        
        text_lower = text.lower()
        
        # Check for abstract keywords
        if any(keyword in text_lower for keyword in ABSTRACT_KEYWORDS):
            abstract_indices.append(i)
    
    return {
        "has_abstract": len(abstract_indices) >= MIN_ABSTRACT_EXAMPLES,
        "abstract_count": len(abstract_indices),
        "abstract_indices": abstract_indices,
        "required_count": MIN_ABSTRACT_EXAMPLES
    }


def inject_abstract_examples(
    model: genai.GenerativeModel,
    package: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Injects abstract/mood-based examples into a package.
    
    Args:
        model: Configured Gemini GenerativeModel instance.
        package: The prompt package to enhance.
        
    Returns:
        dict: Enhanced package with additional abstract examples.
    """
    check = check_abstract_examples(package)
    
    if check["has_abstract"]:
        package["_abstract_check"] = check
        return package
    
    template = package.get("template", "")
    topic = package.get("topic", "")
    
    prompt = f"""You are an expert prompt example creator.

Generate 2 ABSTRACT/CONCEPTUAL examples for this prompt template that focus on mood, emotion, or atmosphere rather than concrete subjects.

TEMPLATE: "{template}"
TOPIC: "{topic}"

REQUIREMENTS:
1. Must be abstract/conceptual (e.g., "A sense of forgotten history", "The oppressive weight of urban decay")
2. Must fit the template's variable structure
3. Must be usable as actual prompts

GOOD EXAMPLES:
- "A sense of forgotten history and melancholic beauty"
- "The ephemeral weight of passing time"
- "Transcendent moments of quiet contemplation"

Return ONLY a JSON object:
{{"abstract_examples": ["example1", "example2"]}}
"""

    try:
        response = model.generate_content(prompt)
        response_text = response.text if hasattr(response, 'text') else str(response)
        
        # Parse JSON
        json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            new_examples = result.get("abstract_examples", [])
            
            # Add to package
            existing = package.get("examples", [])
            if isinstance(existing, list):
                package["examples"] = existing + new_examples
            
            package["_abstract_injected"] = len(new_examples)
    except Exception as e:
        logger.error(f"Abstract example injection failed: {e}", exc_info=True)
        package["_abstract_error"] = str(e)
    
    return package


# --- Main Enhancement Pipeline ---

def enhance_package(
    package: Dict[str, Any],
    api_key: Optional[str] = None,
    model_name: str = "models/gemini-flash-latest"
) -> Dict[str, Any]:
    """
    Runs the full enhancement pipeline on a prompt package.
    
    Args:
        package: The prompt package to enhance.
        api_key: Optional Gemini API key (uses environment if not provided).
        model_name: The model to use for AI-powered fixes.
        
    Returns:
        dict: Enhanced package with enhancement_log.
    """
    enhancement_log = []
    
    # Configure API if key provided
    if api_key:
        genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel(model_name)
    
    # Step 1: Title validation and fixing
    title = package.get("topic", "")
    title_validation = validate_title_pattern(title)
    
    if not title_validation["is_valid"]:
        enhancement_log.append(f"Title issues: {title_validation['issues']}")
        title_result = fix_title(model, title)
        if title_result["was_changed"]:
            package["topic"] = title_result["fixed_title"]
            package["_original_topic"] = title
            enhancement_log.append(f"Title fixed: '{title}' -> '{title_result['fixed_title']}'")
    else:
        enhancement_log.append("Title validation passed")
    
    # Step 2: Example count validation
    example_validation = validate_examples(package)
    
    if not example_validation["is_valid"]:
        enhancement_log.append(
            f"Example count insufficient: {example_validation['current_count']}/{example_validation['required_count']}"
        )
        package["_needs_more_examples"] = example_validation["deficit"]
    else:
        enhancement_log.append(f"Example count OK: {example_validation['current_count']}")
    
    # Step 3: Abstract example check and injection
    abstract_check = check_abstract_examples(package)
    
    if not abstract_check["has_abstract"]:
        enhancement_log.append(
            f"Abstract examples insufficient: {abstract_check['abstract_count']}/{abstract_check['required_count']}"
        )
        package = inject_abstract_examples(model, package)
        if package.get("_abstract_injected"):
            enhancement_log.append(f"Injected {package['_abstract_injected']} abstract examples")
    else:
        enhancement_log.append(f"Abstract examples OK: {abstract_check['abstract_count']}")
    
    package["enhancement_log"] = enhancement_log
    
    return package


# --- Batch Processing ---

def enhance_all_packages(
    packages: List[Dict[str, Any]],
    api_key: str,
    model_name: str = "models/gemini-flash-latest"
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Enhances multiple packages with summary statistics.
    
    Args:
        packages: List of prompt packages to enhance.
        api_key: Gemini API key.
        model_name: The model to use.
        
    Returns:
        Tuple of (enhanced_packages, summary_stats).
    """
    enhanced = []
    stats = {
        "total": len(packages),
        "titles_fixed": 0,
        "examples_flagged": 0,
        "abstract_injected": 0
    }
    
    for package in packages:
        result = enhance_package(package, api_key, model_name)
        enhanced.append(result)
        
        if result.get("_original_topic"):
            stats["titles_fixed"] += 1
        if result.get("_needs_more_examples"):
            stats["examples_flagged"] += 1
        if result.get("_abstract_injected"):
            stats["abstract_injected"] += 1
    
    return enhanced, stats
