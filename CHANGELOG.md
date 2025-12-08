# Changelog

All notable changes to this project will be documented in this file.

## [2025-12-06]

### Added
- **Reverse Engineering Mode**: Implemented a new feature that allows users to paste an existing prompt template. The AI automatically analyzes it, extracts metadata (topic, style), creates variable explanations, generates examples, and writes a sales description.
    - Added "Reverse Engineer" tab in the "Create" section.
    - Added `reverse_engineer_meta_prompt` configuration.
    - Added `agent_analyze_template` analytics agent.
- **Knowledge Base (Trend Engine)**:
    - Implemented a persistent "Knowledge Base" for market data.
    - Users can now **Save** uploaded files or manual text to the database.
    - Added "Manage Knowledge Base" section to view and delete stored data.
    - "Analyze Trends" now automatically combines **All Saved Knowledge** + **Current Input** for deeper analysis.
- **Veo 3.1 Support**:
    - Added "Veo 3.1" to the AI Platform dropdown.
    - Updated `prompts.yaml` with a specialized `video_meta_prompt` for Veo 3.1.
    - Implemented specific constraints: Max 5 variables, exactly 4 examples.
    - Added mandatory metadata generation (Duration: 8s, Aspect Ratio: 16:9/9:16, Audio: Yes).
- **PDF Support**:
    - Added `pypdf` dependency.
    - Updated Trend Engine to accept `.pdf` file uploads and automatically extract text for analysis.

### Fixed
- **Runtime Crash**: Fixed `TypeError: unhashable type: 'dict'` in `api_handler.py` (Agent 4: Example Generation).
- **Workflow Error**: Fixed `TypeError` in `run_agentic_workflow.py` caused by passing the new `input_mode` parameter to the legacy generation function.
- **Prompt Quality**: Enforced stricter variable limits (max 5) to comply with PromptBase rules, fixing an issue where 7+ variables were generated.
- **Video Examples**: Mandated that Veo 3.1 examples must include audio descriptions.
