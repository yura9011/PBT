---
description: Reverse engineer a prompt template from an image
---

# Reverse Engineer from Image

## When to Use
When user has an image and wants to extract a reusable prompt template from it.

## Steps

1. Run the CLI command:
```bash
python cli.py reverse --image "path/to/image.png" --context "optional context"
```

2. Output is saved to `published/` folder automatically

3. Review the generated template in the JSON output

## Alternative: Using Streamlit UI

1. `streamlit run main.py`
2. Go to "🚀 Create" tab
3. Select "🖼️ Image to Prompt" sub-tab
4. Upload image and click "✨ Reverse Engineer from Image"
5. Review in "📦 Results" tab

## Key Files
- `src/api_handler.py`: function `agent_reverse_engineer_from_image()`
- `prompts.yaml`: key `reverse_engineer_image_prompt`
