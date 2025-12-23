import os
import requests
from huggingface_hub import InferenceClient
from PIL import Image
import io

import re

# Models
FLUX_SCHNELL = "black-forest-labs/FLUX.1-schnell"
SDXL_BASE = "stabilityai/stable-diffusion-xl-base-1.0"

def clean_prompt(prompt: str) -> str:
    """
    Remove Midjourney parameters (--ar, --v, etc.) to avoid artifacts in HF models.
    """
    # Remove parameters like --ar 16:9, --v 6.0, --stylize 100
    cleaned = re.sub(r'--[a-zA-Z0-9]+(\s+[a-zA-Z0-9:.]+)?', '', prompt)
    return cleaned.strip()

def generate_preview_image(prompt: str, output_path: str, api_key: str = None, model: str = FLUX_SCHNELL):
    """
    Generate a preview image using HuggingFace Inference API.
    """
    if not api_key:
        api_key = os.environ.get("HF_API_KEY")
        
    if not api_key:
        return {"error": "No HF_API_KEY found. Please set it in .env or pass it as an argument."}

    # Clean prompt for HF
    clean_p = clean_prompt(prompt)
    print(f"🎨 Generating preview with {model}...")
    print(f"   Prompt: {clean_p[:50]}...")
    
    try:
        client = InferenceClient(model=model, token=api_key)
        
        # Generate image
        image = client.text_to_image(clean_p)
        
        # Save image
        image.save(output_path)
        return {"success": True, "path": output_path}
        
    except Exception as e:
        # Fallback to requests if client fails or for specific errors
        print(f"⚠️ InferenceClient error: {e}. Trying raw API request...")
        return _generate_via_requests(prompt, output_path, api_key, model)

def _generate_via_requests(prompt, output_path, api_key, model):
    headers = {"Authorization": f"Bearer {api_key}"}
    api_url = f"https://router.huggingface.co/models/{model}"
    
    try:
        response = requests.post(api_url, headers=headers, json={"inputs": prompt})
        
        if response.status_code != 200:
            return {"error": f"API Error {response.status_code}: {response.text}"}
            
        image_bytes = response.content
        image = Image.open(io.BytesIO(image_bytes))
        image.save(output_path)
        return {"success": True, "path": output_path}
        
    except Exception as e:
        return {"error": str(e)}
