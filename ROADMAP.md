# 🗺️ Project Roadmap & Tech Debt

## 🚦 Immediate TODOs
- [ ] **Unit Tests:** Add pytest coverage for `cli.py` (currently 0%).
- [ ] **GUI Integration:** Port `batch` and `package` commands to Streamlit UI.
- [ ] **Database:** Migrate from JSON files to SQLite for tracking "processed" status more reliably.
- [ ] **Error Handling:** Improve `hf_handler.py` retries for specific HTTP codes (429 vs 500).

## 🔮 Future Features
- **Multi-Model Previews:** Support DALL-E 3 and Midjourney (via external API) for preview generation.
- **Analytics Dashboard:** Visualization of trending topics from the gathered data.
- **Direct Upload:** API integration with PromptBase (if they offer one day).
- **Auto-Tagging:** AI agent to generate SEO tags for PromptBase submission.

## 🧹 Maintenance
- **Refactor:** `api_handler.py` is getting large (800+ lines). Split into `agents/` module.
- **Config:** Move hardcoded lists in prompts to `config.yaml`.
