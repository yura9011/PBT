# main.py

import streamlit as st
import logging
from api_handler import EnhancedPromptGenerator, QualityCheckLoop
from utils import initialize_database, load_config
from ui import create_enhanced_ui

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load configurations
config = load_config(["config.yaml", "prompts.yaml"])
DATABASE_NAME = config.get("database_name", "prompt_library.db")
DEFAULT_MODEL_NAME = config.get("default_model_name", 'gemini-2.0-flash-thinking-exp-01-21')
EVALUATOR_MODEL_NAME = config.get("evaluator_model_name", DEFAULT_MODEL_NAME)  # Can be the same or different
prompts_config = config  # All prompts are now in the main config

def main():
    # Set page config - MUST be the first Streamlit command
    st.set_page_config(
        page_title="Advanced PromptBase Template Generator",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize model variables with defaults
    generator_model = st.session_state.get("generator_model", DEFAULT_MODEL_NAME)
    evaluator_model = st.session_state.get("evaluator_model", EVALUATOR_MODEL_NAME)

    # Sidebar for API Key and Model Settings
    with st.sidebar:
        with st.expander("Configuration", expanded=True):
            gemini_api_key = st.text_input("Gemini API Key", type="password")
            st.session_state["gemini_api_key"] = gemini_api_key

            # Model settings
            st.subheader("Model Settings")

            # Update session state when model is selected
            generator_model = st.selectbox(
                "Generator Model",
                ["gemini-2.0-flash-thinking-exp-01-21", "gemini-2.0-pro", "gemini-1.5-pro"],
                index=0,
                key="generator_model"
            )

            evaluator_model = st.selectbox(
                "Evaluator Model",
                ["gemini-2.0-flash-thinking-exp-01-21", "gemini-2.0-pro", "gemini-1.5-pro"],
                index=0,
                key="evaluator_model"
            )

            if st.button("Clear Session State", key="main_clear_session"):
                for key in st.session_state.keys():
                    del st.session_state[key]
                st.rerun()

    # Initialize database
    initialize_database(DATABASE_NAME)

    # Initialize generator and quality loop if API key exists
    generator = None
    quality_loop = None
    if st.session_state.get("gemini_api_key"):
        generator = EnhancedPromptGenerator(
            st.session_state["gemini_api_key"],
            generator_model or DEFAULT_MODEL_NAME,
            prompts_config
        )

        quality_loop = QualityCheckLoop(
            api_key=st.session_state["gemini_api_key"],
            primary_model_name=generator_model or DEFAULT_MODEL_NAME,
            evaluator_model_name=evaluator_model or EVALUATOR_MODEL_NAME,
            prompts_config=prompts_config,
            max_iterations=3,  # Can be made configurable in UI
            quality_threshold=45.0  # Can be made configurable in UI
        )

        # Call the UI function with both generator and quality_loop
        create_enhanced_ui(DATABASE_NAME, generator_model or DEFAULT_MODEL_NAME,
                         prompts_config, generator, quality_loop)  # Pass both objects


if __name__ == "__main__":
    main()