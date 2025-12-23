# PBT (PromptBase Tool)

A command-line tool to streamline the creation, testing, and packaging of generative AI prompts for PromptBase and other marketplaces.

## Features

- **Reverse Engineering**: Extract templates from images.
- **Batch Processing**: Process folders of images into variable-rich prompt templates.
- **Automated Packaging**: Generate submission-ready ZIP files with required metadata.
- **Previews**: Generate verification images using Flux/SDXL (via HuggingFace).
- **Smart Fix**: Optional LLM-based variable extraction for complex prompts.

## Quick Start

### Installation
```bash
pip install -r requirements.txt
```

### Configuration
1. Rename `.env.example` to `.env` (if applicable) or create one.
2. Add your keys:
   ```
   GEMINI_API_KEY=your_key_here
   HF_API_KEY=your_hf_key_here
   ```

## Usage

### 1. Reverse Engineer (Single Image)
Create a template from a single image.
```bash
python cli.py reverse --image "path/to/image.png"
```

### 2. Batch Processing
Process an entire folder of images.
```bash
python cli.py batch --folder "docs/images" --output "my_batch"
```

### 3. Generate Previews
Create test images to verify the template works.
```bash
python cli.py preview "path/to/file.json" --model flux --count 2
```
*Options:*
- `--model`: Choose between `flux` (default) or `sdxl`.
- `--count`: Number of previews to generate (default: 1).

### 4. Package for Submission
Create a ZIP file containing the JSON, `submission.txt`, previews, and source image.
```bash
python cli.py package "path/to/file.json"
```

### 5. Manual Creation
Draft a prompt from scratch based on a topic.
```bash
python cli.py create --topic "isometric city" --style "3d render" --platform Midjourney
```

## Structure
- `published/`: Default output for generated JSONs.
- `dist/`: Output for packaged ZIP files.
- `prompts.yaml`: Configuration for prompt generation logic.

## License
MIT
