#!/usr/bin/env python
"""
PBT CLI - Command Line Interface for Agentic PromptBase Generator

Usage:
    python cli.py reverse --image "path/to/image.png"
    python cli.py create --topic "tema" --style "estilo" --platform "midjourney"
    python cli.py list
"""

import click
import json
import os
import sys
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass  # python-dotenv not installed, skip

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import google.generativeai as genai
from PIL import Image

from src.api_handler import (
    agent_reverse_engineer_from_image,
    agent_generate_initial_prompt,
    agent_analyze_template,
    agent_extract_variables
)
from src.utils import load_config, save_output_to_json
import re


def post_process_for_quick_copy(result: dict, model=None, config=None, use_smart=False) -> dict:
    """
    Post-process result to add quick_copy_examples with extracted variable values.
    Supports 'smart' mode using LLM extraction if model/config provided.
    """
    if not result.get("examples") or not result.get("variables"):
        return result
    
    template = result.get("template", "")
    variables = result.get("variables", [])
    examples = result.get("examples", [])
    
    # Build quick copy examples
    quick_copy = []
    
    for example in examples:
        if isinstance(example, str):
            extracted = {}
            
            # --- SMART MODE (LLM) ---
            if use_smart and model and config:
                try:
                    extracted = agent_extract_variables(model, config, example, variables)
                    if extracted:
                        click.echo(f"  🧠 Smart extracted: {extracted}")
                except Exception as e:
                    click.echo(f"  ⚠️ Smart extraction failed: {e}", err=True)
            
            # --- REGEX MODE (Fallback) ---
            if not extracted:
                # For each variable, try to find what replaced it in this example
                for var in variables:
                    var_bracket = f"[{var}]"
                    if var_bracket in template:
                        # Find text before and after the variable in template to locate it in example
                        parts = template.split(var_bracket)
                        if len(parts) >= 2:
                            before = parts[0][-30:] if len(parts[0]) > 30 else parts[0]
                            after = parts[1][:30] if len(parts[1]) > 30 else parts[1]
                            
                            # Try to extract the value between these markers
                            pattern = re.escape(before.strip()) + r"(.+?)" + re.escape(after.strip()[:15])
                            match = re.search(pattern, example, re.IGNORECASE)
                            if match:
                                value = match.group(1).strip()
                                # Remove extra quotes that might have been in the example
                                value = value.strip("'\"")
                                extracted[var] = value
            
            if extracted:
                quick_copy.append(extracted)
    
    # Validation Warning
    if len(variables) < 4:
        click.echo(f"⚠️ Warning: Generated template has only {len(variables)} variables. PromptBase requires minimum 4.", err=True)

    result["quick_copy_examples"] = quick_copy
    
    # Also add ready-to-paste format for PromptBase
    result["promptbase_ready"] = {
        "title": result.get("topic", ""),
        "description": result.get("description", ""),
        "template": result.get("template", ""),
        "example_prompts": examples[:9]  # PromptBase wants max 9
    }
    
    return result


def get_api_key():
    """Get API key from environment or prompt user."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        key = click.prompt("Enter your Gemini API Key", hide_input=True)
    return key


@click.group()
@click.pass_context
def cli(ctx):
    """PBT - Agentic PromptBase Generator CLI"""
    ctx.ensure_object(dict)
    

@cli.command()
@click.option("--image", "-i", required=True, type=click.Path(exists=True), 
              help="Path to image file to reverse engineer")
@click.option("--context", "-c", default="", help="Additional context for the analysis")
@click.option("--output", "-o", default=None, help="Output file path (default: auto-generated)")
def reverse(image, context, output):
    """Reverse engineer a prompt template from an image."""
    click.echo(f"🔍 Analyzing image: {image}")
    
    api_key = get_api_key()
    genai.configure(api_key=api_key)
    
    # Load config
    try:
        config = load_config(["config.yaml", "prompts.yaml"])
    except FileNotFoundError:
        click.echo("❌ Error: config.yaml or prompts.yaml not found", err=True)
        return
    
    # Load image
    try:
        image_data = Image.open(image)
    except Exception as e:
        click.echo(f"❌ Error loading image: {e}", err=True)
        return
    
    # Get model
    model_name = config.get("default_model", "models/gemini-flash-latest")
    model = genai.GenerativeModel(model_name)
    
    click.echo(f"🤖 Using model: {model_name}")
    click.echo("⏳ Processing...")
    
    # Run reverse engineering
    result = agent_reverse_engineer_from_image(
        model=model,
        prompts_config=config,
        image_data=image_data,
        additional_context=context
    )
    
    if "error" in result:
        click.echo(f"❌ Error: {result['error']}", err=True)
        return
    
    # Post-process for quick copy
    click.echo("✨ Post-processing for quick copy...")
    result = post_process_for_quick_copy(result)
    
    # Save output
    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        click.echo(f"✅ Saved to: {output}")
    else:
        output_path = save_output_to_json(result, f"reverse_{Path(image).stem}")
        click.echo(f"✅ Saved to: {output_path}")
    
    # Print summary
    click.echo("\n📝 Template Generated:")
    click.echo("-" * 50)
    click.echo(result.get("template", "No template generated"))
    click.echo("-" * 50)
    click.echo(f"\n📋 Variables: {result.get('variables', [])}")


@cli.command()
@click.option("--topic", "-t", required=True, help="Topic/theme for the prompt")
@click.option("--style", "-s", default="", help="Style direction")
@click.option("--platform", "-p", default="Midjourney", 
              type=click.Choice(["Midjourney", "DALL-E 3", "Imagen 3", "Veo 3.1", "Stable Diffusion"]),
              help="Target AI platform")
@click.option("--content-type", "-c", default="Image",
              type=click.Choice(["Image", "Text", "Video"]),
              help="Content type")
@click.option("--use-case", "-u", default="", help="Primary use case")
@click.option("--output", "-o", default=None, help="Output file path")
def create(topic, style, platform, content_type, use_case, output):
    """Create a new prompt template from scratch."""
    click.echo(f"🚀 Creating template for: {topic}")
    
    api_key = get_api_key()
    genai.configure(api_key=api_key)
    
    # Load config
    try:
        config = load_config(["config.yaml", "prompts.yaml"])
    except FileNotFoundError:
        click.echo("❌ Error: config.yaml or prompts.yaml not found", err=True)
        return
    
    model_name = config.get("default_model", "models/gemini-flash-latest")
    model = genai.GenerativeModel(model_name)
    
    click.echo(f"🤖 Using model: {model_name}")
    click.echo("⏳ Generating...")
    
    result = agent_generate_initial_prompt(
        model=model,
        prompts_config=config,
        topic=topic,
        content_type=content_type,
        style=style,
        use_case=use_case,
        model_platform=platform
    )
    
    if "error" in result:
        click.echo(f"❌ Error: {result['error']}", err=True)
        return
    
    # Post-process for quick copy
    click.echo("✨ Post-processing for quick copy...")
    result = post_process_for_quick_copy(result)
    
    # Save output
    if output:
        with open(output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        click.echo(f"✅ Saved to: {output}")
    else:
        safe_topic = "".join(c for c in topic if c.isalnum() or c in " _-")[:30]
        output_path = save_output_to_json(result, f"prompt_{safe_topic}")
    click.echo(f"✅ Saved to: {output_path}")
    
    click.echo("\n📝 Template Generated:")
    click.echo("-" * 50)
    click.echo(result.get("template", "No template generated"))
    click.echo("-" * 50)


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--overwrite", is_flag=True, help="Overwrite the existing file.")
@click.option("--smart", is_flag=True, help="Use LLM for smarter extraction (costs quota).")
def enhance(path, overwrite, smart):
    """
    Enhance an existing JSON file with quick_copy and promptbase_ready sections.
    """
    model = None
    config = None
    
    if smart:
        click.echo("🧠 Initializing Smart Mode...")
        try:
            api_key = get_api_key()
            if not api_key:
                click.echo("❌ Error: Smart mode requires GEMINI_API_KEY set.", err=True)
                return
            
            genai.configure(api_key=api_key)
            # Load config
            try:
                config = load_config(["config.yaml", "prompts.yaml"])
            except:
                click.echo("⚠️ Config not found, smart mode might list fewer prompts", err=True)
                config = {}
                
            model_name = config.get("default_model", "gemini-2.5-flash-lite")
            model = genai.GenerativeModel(model_name)
            click.echo(f"🤖 Connected to {model_name}")
            
        except Exception as e:
             click.echo(f"❌ Error initializing Smart Mode: {e}", err=True)
             return

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        click.echo(f"🔍 Enhancing {path}...")
        
        # Apply post-processing
        enhanced_data = post_process_for_quick_copy(data, model=model, config=config, use_smart=smart)
        
        # Determine output path
        output_path = path if overwrite else path.replace(".json", "_enhanced.json")
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
            
        click.echo(f"✅ Saved enhanced file to: {output_path}")
        
    except Exception as e:
        click.echo(f"❌ Error enhancing file: {e}", err=True)


@cli.command()
@click.argument("json_path", type=click.Path(exists=True))
@click.option("--count", default=1, help="Number of previews to generate")
def preview(json_path, count):
    """
    Generate preview images for a prompt package using HuggingFace.
    """
    from src.hf_handler import generate_preview_image
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        template = data.get("template", "")
        examples = data.get("examples", [])
        
        if not template:
            click.echo("❌ No template found in JSON")
            return
            
        # Use first example or fill template with defaults if needed
        # ideally we use the examples generated
        prompts_to_run = []
        if examples:
             prompts_to_run = examples[:count]
        else:
             click.echo("⚠️ No examples found, using raw template (might fail if variables exist)")
             prompts_to_run = [template]
             
        click.echo(f"🎨 Generating {len(prompts_to_run)} preview(s)...")
        
        base_name = Path(json_path).stem
        parent_dir = Path(json_path).parent
        
        for i, prompt in enumerate(prompts_to_run):
            if isinstance(prompt, dict): # Handle if example is structured (rare but possible)
                prompt = json.dumps(prompt)
                
            output_path = parent_dir / f"{base_name}_preview_{i+1}.png"
            click.echo(f"  • Generating preview {i+1}...")
            
            result = generate_preview_image(str(prompt), str(output_path))
            
            if result.get("success"):
                click.echo(f"    ✅ Saved to: {output_path}")
            else:
                click.echo(f"    ❌ Failed: {result.get('error')}")
                
    except Exception as e:
         click.echo(f"❌ Error: {e}", err=True)


@cli.command()
@click.option("--folder", required=True, type=click.Path(exists=True), help="Input folder containing images.")
@click.option("--output", default=None, help="Output folder for JSONs. Defaults to 'published/' inside input folder.")
@click.option("--delay", default=5, help="Delay in seconds between requests to avoid rate limits.")
@click.option("--smart", is_flag=True, help="Use Smart Mode (LLM) for extraction.")
def batch(folder, output, delay, smart):
    """
    Reverse engineer all images in a folder (Batch Mode).
    """
    import time
    
    input_path = Path(folder)
    # Output to published/ inside project or sibling, user preference?
    # Default behavior: project root 'published' if not specific, or relative?
    # Let's stick to project root 'published' as default for consistency, or 'processed' inside folder
    # User usually wants centralized output.
    # Let's verify utils.output_dir logic.
    # We'll use the CLI provided output or default to 'batch_output' inside input folder to keep it separate?
    # User said: "siempre y cuando esas 50 vayan a parar a una nueva lista"
    
    if output:
        out_dir = Path(output)
    else:
        out_dir = input_path / "processed"
        
    if not out_dir.exists():
        out_dir.mkdir(parents=True)
        
    # Valid extensions
    extensions = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
    images = [f for f in input_path.iterdir() if f.suffix.lower() in extensions]
    
    if not images:
        click.echo(f"⚠️ No images found in {folder}")
        return
        
    click.echo(f"🏭 Starting Batch Factory: {len(images)} images found.")
    click.echo(f"📂 Output: {out_dir}")
    click.echo(f"🧠 Smart Mode: {'ON' if smart else 'OFF'}")
    click.echo(f"⏱️ Delay: {delay}s")
    click.echo("-" * 50)
    
    # Init API
    api_key = get_api_key()
    if not api_key:
         click.echo("❌ Error: GEMINI_API_KEY required.")
         return
    genai.configure(api_key=api_key)
    config = load_config(["config.yaml", "prompts.yaml"])
    model_name = config.get("default_model", "gemini-2.5-flash-lite")
    model = genai.GenerativeModel(model_name)
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    report_file = out_dir / f"batch_report_{int(time.time())}.md"
    
    with open(report_file, "w", encoding="utf-8") as report:
        report.write(f"# Batch Process Report\nDate: {time.ctime()}\nFolder: {folder}\n\n| Image | Status | Output | Notes |\n|---|---|---|---|\n")

    for i, img_path in enumerate(images):
        # Resume Check: if output JSON already exists, skip
        json_filename = f"reverse_{img_path.stem}.json" 
        # Note: existing logic might name it with date.
        # Ideally we stick to consistent naming. agent_reverse_engineer returns result, we manually save.
        target_json = out_dir / json_filename
        
        # We need a robust check. If any file starts with reverse_{img_path.stem} in out_dir?
        # Let's just check exact match for now or use glob
        existing = list(out_dir.glob(f"reverse_{img_path.stem}*.json"))
        
        if existing:
            click.echo(f"⏩ Skipping {img_path.name} (already exists: {existing[0].name})")
            skip_count += 1
            continue

        click.echo(f"[{i+1}/{len(images)}] Processing {img_path.name}...")
        
        try:
            # CALL AGENT
            # We reuse agent_reverse_engineer_from_image, but we need to pass model directly or let it re-init?
            # The agent function takes 'model' as arg? Let's check api_handler signature (Line 30 in cli imports).
            # agent_reverse_engineer_from_image(model, prompts_config, image_path, ...)
            
            result = agent_reverse_engineer_from_image(
                model=model,
                prompts_config=config,
                image_path=str(img_path)
            )
            
            if "error" in result:
                click.echo(f"  ❌ Error: {result['error']}")
                fail_count += 1
                with open(report_file, "a", encoding="utf-8") as report:
                    report.write(f"| {img_path.name} | ❌ Failed | - | {result['error']} |\n")
            else:
                # Post-process
                result = post_process_for_quick_copy(result, model, config, use_smart=smart)
                
                # Save
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                final_filename = f"reverse_{img_path.stem}_{timestamp}.json"
                final_path = out_dir / final_filename
                
                with open(final_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                    
                click.echo(f"  ✅ Done")
                success_count += 1
                
                # Report
                vars_count = len(result.get("variables", []))
                note = "Smart Extracted" if smart else "Regex Extracted"
                if vars_count < 4:
                    note += f" | ⚠️ Low vars: {vars_count}"
                
                with open(report_file, "a", encoding="utf-8") as report:
                    report.write(f"| {img_path.name} | ✅ Success | {final_filename} | {note} |\n")
                    
                # Rate limit sleep
                time.sleep(delay)
                
        except Exception as e:
            click.echo(f"  ❌ Exception: {e}")
            fail_count += 1
            with open(report_file, "a", encoding="utf-8") as report:
                 report.write(f"| {img_path.name} | ❌ Crash | - | {str(e)} |\n")
                 
    click.echo("-" * 50)
    click.echo(f"🏭 Batch Complete.\n✅ Success: {success_count}\n⏩ Skipped: {skip_count}\n❌ Failed: {fail_count}")
    click.echo(f"📄 Report saved to: {report_file}")
    
@cli.command()
@click.option("--folder", required=True, type=click.Path(exists=True), help="Input folder containing images.")
@click.option("--output", default=None, help="Output folder for JSONs. Defaults to 'processed/' inside input folder.")
@click.option("--delay", default=2, help="Delay in seconds between requests to avoid rate limits.")
@click.option("--smart", is_flag=True, help="Use Smart Mode (LLM) for extraction (slower, costs quota).")
def batch(folder, output, delay, smart):
    """
    Reverse engineer all images in a folder (Batch Mode).
    """
    import time
    
    input_path = Path(folder)
    
    if output:
        out_dir = Path(output)
    else:
        out_dir = input_path / "processed"
        
    if not out_dir.exists():
        out_dir.mkdir(parents=True)
        
    # Valid extensions
    extensions = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
    images = [f for f in input_path.iterdir() if f.suffix.lower() in extensions]
    
    if not images:
        click.echo(f"⚠️ No images found in {folder}")
        return
        
    click.echo(f"🏭 Starting Batch Factory: {len(images)} images found.")
    click.echo(f"📂 Output: {out_dir}")
    click.echo(f"🧠 Smart Mode: {'ON' if smart else 'OFF'}")
    click.echo(f"⏱️ Delay: {delay}s")
    click.echo("-" * 50)
    
    # Init API
    try:
        api_key = get_api_key()
        if not api_key:
             click.echo("❌ Error: GEMINI_API_KEY required.")
             return
        genai.configure(api_key=api_key)
        config = load_config(["config.yaml", "prompts.yaml"])
        model_name = config.get("default_model", "gemini-2.5-flash-lite")
        model = genai.GenerativeModel(model_name)
    except Exception as e:
        click.echo(f"❌ Error initializing API: {e}", err=True)
        return
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    report_file = out_dir / f"batch_report_{int(time.time())}.md"
    
    with open(report_file, "w", encoding="utf-8") as report:
        report.write(f"# Batch Process Report\nDate: {time.ctime()}\nFolder: {folder}\n\n| Image | Status | Output | Notes |\n|---|---|---|---|\n")

    for i, img_path in enumerate(images):
        # Resume Check: if output JSON already exists, skip
        # We need to match the naming convention used by save_output_to_json usually
        # But here we control the saving name.
        json_filename = f"reverse_{img_path.stem}.json"
        
        # Check if file exists with this name or similar patterns in out_dir
        # Standardize strictly here for batch to allow Resume.
        final_path = out_dir / json_filename
        
        # Also check for timestamped versions if user ran it before?
        # Let's check strict first.
        existing = list(out_dir.glob(f"reverse_{img_path.stem}*.json"))
        
        if existing:
            click.echo(f"⏩ [{i+1}/{len(images)}] Skipping {img_path.name} (exists)")
            skip_count += 1
            continue

        click.echo(f"🔄 [{i+1}/{len(images)}] Processing {img_path.name}...")
        
        try:
            # Load Image
            try:
                image_data = Image.open(img_path)
            except Exception as e:
                click.echo(f"  ❌ Error loading image: {e}")
                fail_count += 1
                with open(report_file, "a", encoding="utf-8") as report:
                    report.write(f"| {img_path.name} | ❌ Read Fail | - | {str(e)} |\n")
                continue

            result = agent_reverse_engineer_from_image(
                model=model,
                prompts_config=config,
                image_data=image_data
            )
            
            if "error" in result:
                click.echo(f"  ❌ Error: {result['error']}")
                fail_count += 1
                with open(report_file, "a", encoding="utf-8") as report:
                    report.write(f"| {img_path.name} | ❌ Failed | - | {result['error']} |\n")
            else:
                # Post-process
                result = post_process_for_quick_copy(result, model, config, use_smart=smart)
                
                # Save
                with open(final_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                    
                click.echo(f"  ✅ Done -> {json_filename}")
                success_count += 1
                
                # Report
                vars_count = len(result.get("variables", []))
                note = "Smart Extracted" if smart else "Regex Extracted"
                if vars_count < 4:
                    note += f" | ⚠️ Low vars: {vars_count}"
                
                with open(report_file, "a", encoding="utf-8") as report:
                    report.write(f"| {img_path.name} | ✅ Success | {json_filename} | {note} |\n")
                    
                # Rate limit sleep
                time.sleep(delay)
                
        except Exception as e:
            click.echo(f"  ❌ Exception: {e}")
            fail_count += 1
            with open(report_file, "a", encoding="utf-8") as report:
                 report.write(f"| {img_path.name} | ❌ Crash | - | {str(e)} |\n")
                 
    click.echo("-" * 50)
    click.echo(f"🏭 Batch Complete.\n✅ Success: {success_count}\n⏩ Skipped: {skip_count}\n❌ Failed: {fail_count}")
    click.echo(f"📄 Report saved to: {report_file}")
    
    click.echo(f"📄 Report saved to: {report_file}")


@cli.command()
@click.argument("json_path", type=click.Path(exists=True))
@click.option("--output", default="dist", help="Output directory for packages")
def package(json_path, output):
    """
    Package a processed JSON into a submission-ready ZIP file.
    """
    try:
        import shutil
        import zipfile
        import time
        
        json_file = Path(json_path)
        out_root = Path(output)
        
        if not out_root.exists():
            out_root.mkdir(parents=True)
            
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Project Name
        topic = data.get("topic", "Unknown").replace(" ", "_")
        project_name = f"{topic}_{int(time.time())}"
        package_dir = out_root / project_name
        package_dir.mkdir(exist_ok=True)
        
        click.echo(f"📦 Packaging {topic}...")
        
        # 1. Copy JSON
        shutil.copy(json_path, package_dir / "data.json")
        
        # 2. Copy Source Image (if available in metadata)
        source_path = data.get("source_image_path")
        if source_path and Path(source_path).exists():
             shutil.copy(source_path, package_dir / f"source_image{Path(source_path).suffix}")
             click.echo("  📸 Included source image")
        else:
             click.echo("  ⚠️ Source image not found in metadata or disk")

        # 3. Copy/Generate Preview (Look for sibling files)
        # Naming convention: {json_stem}_preview_1.png
        parent_dir = json_file.parent
        previews = list(parent_dir.glob(f"{json_file.stem}*_preview_*.png"))
        
        if previews:
            preview_dir = package_dir / "previews"
            preview_dir.mkdir()
            for p in previews:
                shutil.copy(p, preview_dir / p.name)
            click.echo(f"  🎨 Included {len(previews)} preview(s)")
        else:
            click.echo("  ⚠️ No previews found to include")
            
        # 4. Generate submission.txt (PromptBase Ready)
        pb_data = data.get("promptbase_ready", {})
        if not pb_data:
             # Fallback if enhance wasn't run
             pb_data = {
                 "title": data.get("topic"),
                 "description": data.get("description"),
                 "template": data.get("template"),
                 "example_prompts": data.get("examples")
             }
        
        submission_text = f"""
================================================================
TITLE
================================================================
{pb_data.get('title')}

================================================================
DESCRIPTION
================================================================
{pb_data.get('description')}

================================================================
PROMPT
================================================================
{pb_data.get('template')}

================================================================
TESTING PROMPTS
================================================================
"""
        examples = pb_data.get("example_prompts", [])
        for ex in examples:
            submission_text += f"{ex}\n\n"
            
        submission_text += f"""
================================================================
INSTRUCTIONS
================================================================
{data.get('instructions', 'Copy and paste the prompt...')}

================================================================
TIPS
================================================================
"""
        for tip in data.get("tips", []):
             submission_text += f"- {tip}\n"
             
        # Add Smart Examples if available
        qc = data.get("quick_copy_examples", [])
        if qc:
             submission_text += "\n================================================================\n"
             submission_text += "VARIABLE EXAMPLES (For Buyer README)\n"
             submission_text += "================================================================\n"
             submission_text += json.dumps(qc, indent=2)

        with open(package_dir / "submission.txt", "w", encoding="utf-8") as f:
            f.write(submission_text)
        click.echo("  📝 Generated submission.txt")
        
        # 5. Create ZIP
        zip_path = out_root / f"{project_name}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file in package_dir.rglob("*"):
                if file.is_file():
                    zf.write(file, file.relative_to(package_dir.parent))
                    
        click.echo(f"  🤐 Zipped to: {zip_path}")
        click.echo(f"✅ Package Complete!")
        
    except Exception as e:
        click.echo(f"❌ Packaging failed: {e}", err=True)

@cli.command("list")
def list_published():
    """List all published prompts."""
    published_dir = Path(__file__).parent / "published"
    
    if not published_dir.exists():
        click.echo("📁 No published directory found")
        return
    
    files = list(published_dir.glob("*.json"))
    click.echo(f"\n📚 Found {len(files)} published prompts:\n")
    
    for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:20]:
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                topic = data.get("topic", "Unknown")
                click.echo(f"  • {topic} ({f.name})")
        except:
            click.echo(f"  • [Error reading] {f.name}")
    
    if len(files) > 20:
        click.echo(f"\n  ... and {len(files) - 20} more")


if __name__ == "__main__":
    cli()
