# Changelog

All notable changes to this project will be documented in this file.

## [2025-12-12]

### Added
- **Quality Enhancement Module** (`quality_enhancers.py`): New post-processing pipeline based on pattern analysis of 31 generated packages:
    - `validate_title_pattern()` / `fix_title()`: Enforces [Descriptor] + [Subject] + [Type] title pattern (78% of packages were failing).
    - `validate_examples()`: Validates 8-10 examples are present.
    - `check_abstract_examples()` / `inject_abstract_examples()`: Ensures 2+ abstract/mood-based examples are included.
- **Test Infrastructure**: Added `tests/` directory with `pytest` configuration:
    - `test_quality_enhancers.py`: 12 test cases covering title validation, example counting, and abstract example injection.
    - Uses mocking per `@test-agent` guidelines to avoid real API calls.
- **Pattern Analysis Tool** (`analyze_patterns.py`): Script to analyze prompt packages and identify recurring issues.

### Changed
- **Workflow Enhancement**: `run_agentic_workflow.py` now includes Step 8: Quality Enhancement between categorization and save.
- **Updated Data Flow**: Quality Enhancers now process packages before database save.


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
