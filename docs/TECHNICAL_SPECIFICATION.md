# Technical Specification: Agentic PromptBase Generator

**Version:** 1.2
**Date:** 2025-12-07

## 1. Core Purpose

The **Agentic PromptBase Generator** is a specialized, multi-agent AI system designed to automate the research, engineering, and packaging of high-quality AI prompts for commercial marketplaces (specifically PromptBase). 

The application solves the problem of manual prompt engineering by providing a streamlined workflow that:
1.  **Ideates:** Uses market trends to suggest high-value concepts.
2.  **Engineers:** Creates technically robust templates optimized for specific platforms (Midjourney, DALL-E, Veo, etc.).
3.  **Validates:** Automatically scores and refines prompts against commercial standards.
4.  **Packages:** Generates all necessary sales assets (titles, descriptions, examples, technical tips).

The primary user experience transforms a vague 2-3 word idea (e.g., "watercolor flowers") or a raw trend report into a fully sellable digital product.

---

## 2. Main Features

### A. Core Workflow Features
*   **Multi-Agent Generation:** A sequential chain of AI agents responsible for distinct tasks:
    *   **Generator Agent:** Creates the initial template architecture.
    *   **Compliance Agent:** Evaluates the prompt against strict quality criteria (scoring 0-100).
    *   **Refinement Agent:** Iteratively improves the template if compliance scores are low.
    *   **Example Agent:** Generates diverse, high-quality output examples to demonstrate versatility.
    *   **Technical Agent:** Writes usage guides and technical tips.
    *   **Sales Agent:** Drafts SEO-optimized commercial descriptions.
*   **Trend Engine & Knowledge Base:**
    *   **Market Analysis:** Analyzes raw text or PDF documents to identify selling trends.
    *   **Knowledge Base (SQLite):** Persistent storage of market data acting as a "long-term memory" for the analyzer.
    *   **Contextual Prediction:** Combines historical knowledge with new inputs to suggest "Best-Seller" concepts.
*   **Reverse Engineering Mode:**
    *   Allows users to input an existing "Final Prompt Template".
    *   Automatically deconstructs the template to generate a full sales package (Variables, Explanations, Metadata, Description).

### B. Platform-Specific Support
*   **Universal Support:** Midjourney, DALL-E 3, Stable Diffusion, text models (GPT/Claude).
*   **Veo 3.1 Specialization:**
    *   Enforces strict variable limits (Max 5).
    *   Generates mandatory metadata (Duration, Aspect Ratio, Audio settings).
    *   Produces exactly 4 unique video examples with required audio descriptions.

### C. Data Management
*   **Prompt Library:** A local SQLite database (`prompts.db`) storing all generated packages.
*   **Example Management:** Functionality to regenerate specific examples or auto-complete the example set to meet marketplace quotas.
*   **Export Options:** One-click export to JSON or Markdown (formatted for PromptBase upload).

---

## 3. Functional Behavior

### Input Methods
1.  **Idea Lab:** User selects Content Type, Platform, Topic, Style, and Use Case.
2.  **Reverse Engineer:** User pastes a raw prompt template string.
3.  **Trend Engine:** User pastes text or uploads files (TXT, MD, PDF).

### Processing Flow
1.  **Orchestration (`run_agentic_workflow.py`):** The central controller receives user input.
2.  **Routing:**
    *   If **Reverse Mode**: Skips generation, calls `agent_analyze_template` to deconstruct the input.
    *   If **Generation Mode**: Calls `agent_generate_initial_prompt` using platform-specific meta-prompts.
3.  **Validation Loop:**
    *   The **Evaluator Agent** scores the prompt.
    *   **Decision Logic:** If Score < Threshold (default 35), the **Refiner Agent** attempts to fix identified issues.
4.  **Asset Generation:**
    *   The system generates examples (checking constraints like "Exact 4 for Veo").
    *   Generates commercial descriptions and technical guides.
    *   Auto-categorizes the prompt.
5.  **Output:** Returns a comprehensive dictionary ("Prompt Package").

### Error Handling
*   Input sanitization prevents `TypeError` when switching modes.
*   Agent failures (e.g., API timeouts) are caught, logged, and surfaced to the UI without crashing the app.
*   Fallback values are used if specific metadata cannot be generated.

---

## 4. Architecture Overview

### System Structure
The application follows a modular, functional architecture built on **Streamlit** (Frontend) and **Google Gemini 1.5** (Intelligence Layer).

### Key Modules
1.  **`ui.py` (Presentation):** Handles all user interactions, state management, and renders the specific tabs (Create, Trends, Results, Library).
2.  **`run_agentic_workflow.py` (Controller):** Implements the logic flow, connecting the UI inputs to the specific sequence of agent calls. Now includes Step 8: Quality Enhancement.
3.  **`api_handler.py` (Intelligence):** Contains the definitions for all AI agents. It interfaces directly with the `google.generativeai` SDK and handles JSON parsing.
4.  **`utils.py` (Persistence):** Manages the SQLite database connections. Handles CRUD operations for Prompts and Market Data.
5.  **`prompts.yaml` (Configuration):** Stores the "Meta-Prompts" (the instructions for the AI agents). This isolates the AI behavior from the application code.
6.  **`quality_enhancers.py` (Quality Assurance):** Implements counter-strategies identified from pattern analysis:
    - `validate_title_pattern()` / `fix_title()`: Enforces [Descriptor] + [Subject] + [Type] title pattern.
    - `validate_examples()`: Ensures packages have 8-10 examples.
    - `check_abstract_examples()` / `inject_abstract_examples()`: Adds 2+ abstract/mood-based examples.

### Data Flow
`User Input (UI)` -> `Workflow Controller` -> `AI Agents (API Handler)` -> `Gemini API` -> `Structured JSON` -> `Quality Enhancers` -> `Database (Utils)` -> `UI Display`

---

## 5. User Interaction Model

### Workflow
1.  **Research (Optional):** User uploads a PDF market report to the **Trend Engine**. They save it to the Knowledge Base and click "Analyze" to get ideas.
2.  **Selection:** User clicks "Create This" on a trend trend result, or manually enters a topic in the **Create** tab.
3.  **Generation:** User clicks "Generate". The app displays a real-time progress log (e.g., "Agent: Compliance Evaluation...").
4.  **Review:** The **Results** tab displays the created package. The user can view the template, compliance score, and examples.
5.  **Refinement (Optional):** User can manually edit the result or regenerate examples in the **Library**.
6.  **Export:** User downloads the `.md` file for upload to the marketplace.

---

## 6. Internal Rules & Constraints

### Marketplace Compliance (Enforced by Logic/Prompts)
1.  **Variable Format:** MUST use `[SQUARE_BRACKETS]`.
2.  **Variable Limits:**
    *   **General:** 1-9 variables.
    *   **Veo 3.1:** STRICT limit of 3-5 variables.
3.  **Example Counts:**
    *   **General:** 9 diverse examples.
    *   **Veo 3.1:** EXACTLY 4 examples (Platform Requirement).
4.  **Content Safety:**
    *   Strict adherence to Gemini's safety filters (Harassment, Hate Speech, Sexually Explicit, Dangerous Content).

### System Constraints
*   **Dependencies:** Requires active Internet connection and valid Google Gemini API Key.
*   **File Uploads:** PDF parsing is text-only (images in PDFs are ignored). max 200MB limit (Streamlit default).

---

## 7. Known Issues or Limitations

1.  **Prompt Hallucinations:** Rarely, the model may generate a variable name in the examples that does not match the template (e.g., `[Time]` vs `[TimeOfDay]`).
2.  **PDF Formatting:** Complex PDF layouts (tables, multi-column) may result in disjointed text extraction, potentially confusing the Trend Analyzer.
3.  **Refinement Loop:** The Refinement Agent runs only once. If the prompt is still poor after one refinement, it is returned as-is to prevent infinite loops and API waste.
4.  **State Persistence:** Streamlit session state is volatile; a browser refresh clears unsaved "Working" data (though the Library/Database is persistent).

---

## 8. Suggested Next Updates

### High Impact
1.  **Batch Processing:** Allow the Trend Engine to automatically generate prompt packages for *all* identified trends in a single click.
2.  **Advanced PDF Parsing:** Integrate a more robust parser (e.g., LlamaParse or Gemini 1.5 Pro's native document understanding) to handle charts and complex layouts.
3.  **Direct API Integration:** (Future) Logic to attempt direct upload to marketplace APIs if available.

### UX Improvements
1.  **In-App Editor:** A "wysiwyg" editor in the Results tab to manually tweak the JSON structure before saving to the library.
2.  **Image-to-Prompt (Reverse Engineering):** Allow users to upload an *image* and have the Vision model reverse-engineer the prompt template.
