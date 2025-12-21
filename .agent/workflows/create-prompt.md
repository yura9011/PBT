---
description: Create a new prompt template from an idea
---

# Create Prompt Template

## When to Use
When user has a topic/idea and wants to generate a full prompt package.

## Steps

1. Run the CLI command:
```bash
python cli.py create --topic "tema" --style "estilo" --platform "Midjourney"
```

Options:
- `--topic` / `-t`: Required. The main theme
- `--style` / `-s`: Optional. Style descriptors
- `--platform` / `-p`: Target platform (Midjourney, DALL-E 3, etc.)
- `--content-type` / `-c`: Image, Text, or Video
- `--use-case` / `-u`: Primary use case

2. Output is saved to `published/` folder

## Full Example
```bash
python cli.py create \
  --topic "Cozy autumn cabin scenes" \
  --style "warm, nostalgic, soft lighting" \
  --platform "Midjourney" \
  --use-case "wall art prints"
```

## Key Files
- `src/api_handler.py`: function `agent_generate_initial_prompt()`
- `src/run_agentic_workflow.py`: full pipeline
