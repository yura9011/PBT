# Agentic PromptBase Generator

**Generate high-quality, market-ready prompt templates aligned with PromptBase submission guidelines using Gemini AI.**

This Streamlit application is a powerful multi-agent system designed to help you research, ideate, and create professional prompt templates for top AI platforms. It leverages Google's Gemini models to automate the entire workflow, from trend analysis to final prompt generation.

## ✨ Key Features

*   **📈 Trend Engine:**
    *   **Market Analysis:** Paste text from articles, blogs, or competitor lists to analyze current market trends.
    *   **Automated Ideation:** The AI identifies "underserved niches" and suggests high-potential prompt concepts (Topic, Style, Use Case).
    *   **One-Click Creation:** Instantly turn a trend suggestion into a full prompt package with a single click.

*   **🚀 Advanced Template Generation:**
    *   **Multi-Platform Support:** Optimized for **Midjourney, DALL-E 3, Imagen 3 (Gemini), Gemini Nano, Sora, Stable Diffusion**, and more.
    *   **User-Friendly Variables:** Automatically enforces simple, high-level variables (e.g., `[Subject]`, `[Mood]`) while hiding technical complexity, ensuring a great end-user experience.
    *   **Dynamic Descriptions:** Generates unique, persuasive, and SEO-friendly product descriptions for your marketplace listings.

*   **📦 Comprehensive Output:**
    *   **Prompt Anatomy:** Produces a structured template with fixed technical specs and flexible user variables.
    *   **Diverse Examples:** Generates 4 distinct, "pleasant," and client-friendly examples to showcase the template's versatility.
    *   **Quality Evaluation:** Built-in "Reviewer Agent" scores your prompt against PromptBase guidelines and suggests improvements.

*   **📚 Local Library:**
    *   Save, organize, and manage your generated prompts in a local database.
    *   Export to JSON or Markdown for easy submission.

## 🛠️ Installation

1.  **Clone the repository.**
2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: Requires `streamlit`, `google-generativeai`, and standard libraries)*

3.  **Get a Gemini API Key:**
    *   Get your key from [Google AI Studio](https://aistudio.google.com/).

## ▶️ How to Run

1.  Navigate to the project directory.
2.  Run the application:
    ```bash
    streamlit run main.py
    ```
3.  Enter your **Gemini API Key** in the sidebar.

## 💡 Usage Guide

### 1. The Trend Engine (Recommended Start)
*   Go to the **"📈 Trend Engine"** tab.
*   Paste market data (e.g., "Top design trends for 2025") or upload a text file.
*   Click **"Analyze & Predict Trends"**.
*   Review the "Predicted Best-Sellers" and click **"✨ Create This"** on any idea you like.

### 2. The Idea Lab (Manual Creation)
*   Go to the **"🚀 Create"** tab.
*   Manually enter your **Topic**, **Content Type**, **Platform**, **Style**, and **Use Case**.
*   Click **"🚀 Generate Full Prompt Package"**.

### 3. Review & Export
*   Go to the **"📦 Results"** tab to see the generated content.
*   Check the **Compliance Score** and read the **Usage Tips**.
*   **Export:** Download as JSON/Markdown or copy the template to your clipboard.
*   **Save:** Click "💾 Save to Library" to store it locally.

### 4. Library
*   Go to the **"📚 Library"** tab to browse and manage your saved prompts.

## 💻 Developer Reference

### `run_agentic_workflow.py`
*   `run_workflow`: The main orchestrator that runs the multi-agent workflow, yielding status updates at each step.

### `api_handler.py` (Core Agents)
*   `agent_analyze_market`: Fetches and analyzes content from a URL to identify market trends.
*   `agent_generate_concepts`: Generates creative prompt concepts based on a theme and market analysis.
*   `agent_generate_initial_prompt`: Generates the initial prompt template package based on user input.
*   `agent_analyze_template`: Reverse engineers a prompt package from a raw template string.
*   `agent_reverse_engineer_from_image`: Reverse engineers a prompt template from an image using a Vision model.
*   `agent_evaluate_compliance`: Evaluates a prompt against PromptBase guidelines and scoring criteria.
*   `agent_refine_prompt`: Refines a prompt template based on evaluation feedback.
*   `agent_generate_examples`: Generates diverse examples for a given prompt template.
*   `agent_generate_test_guidance`: Creates a testing guide with quality checklists and troubleshooting tips.
*   `agent_generate_description`: Generates a commercially optimized marketplace description.
*   `agent_categorize_prompt`: Assigns a relevant category to the prompt package.
*   `agent_analyze_trends`: Analyzes aggregated market data to predict future trends.
*   `agent_normalize_data`: Normalizes unstructured text into structured JSON for the Knowledge Base.
*   `validate_prompt_title`: Validates the prompt title against patterns of success.

### `utils.py` (Data & Config)
*   `load_config`: Loads configuration from YAML files.
*   `initialize_database`: Sets up the SQLite database schema.
*   `save_prompt_to_db`: Saves a generated prompt package to the local database.
*   `get_all_prompts_from_db`: Retrieves all saved prompts from the database.
*   `save_market_data`: Saves market trend data to the Knowledge Base.
*   `get_all_market_data`: Fetches all market data entries.
