---
description: Full workflow to create a PromptBase-ready package
---

# Publish-Ready Workflow

## When to Use
When user wants a complete package ready to upload to PromptBase.

## Complete Steps

### 1. Generate the Template
```bash
python cli.py create --topic "tema" --style "estilo" --platform "Midjourney"
```

### 2. Review Output
- Open the JSON in `published/` folder
- Check:
  - `template`: Has `[VARIABLES]` in brackets
  - `examples`: Has 4-9 diverse examples
  - `commercial_description`: Has marketing copy
  - `variables`: Has 3-5 user-friendly variables

### 3. Generate Test Images
Use the template in Midjourney/DALL-E with example variables.

### 4. Export for PromptBase
Using Streamlit UI:
1. Open Library tab
2. Find your prompt
3. Click "📝 Download Markdown"

The Markdown file has the format PromptBase expects.

## Quality Checklist
- [ ] Template has 3-5 variables (not more)
- [ ] Variables use simple names: `[SUBJECT]`, `[STYLE]`, `[MOOD]`
- [ ] 9 diverse examples provided
- [ ] Description mentions use cases
- [ ] Title follows pattern: [Descriptor] + [Subject] + [Type]

## Files Generated
```
published/
└── prompt_package_{topic}_{timestamp}.json
```
