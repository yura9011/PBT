# main.py

import streamlit as st
import logging
from src.utils import initialize_database, load_config
from src.ui import create_ui

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Set page config
    st.set_page_config(
        page_title="Agentic PromptBase Generator",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # --- Load Configurations ---
    try:
        config = load_config(["config.yaml", "prompts.yaml"])
        DATABASE_NAME = config.get("database_name", "prompt_library.db")
        DEFAULT_MODEL_NAME = config.get("default_model", 'models/gemini-flash-latest') # Corrected key and user-suggested default
        EVALUATOR_MODEL_NAME = config.get("evaluator_model_name", 'models/gemini-flash-latest')
        prompts_config = config
    except FileNotFoundError as e:
        st.error(f"Configuration file not found: {e.filename}. Please make sure config.yaml and prompts.yaml are present.")
        st.stop()

    # --- Sidebar for Configuration ---
    with st.sidebar:
        st.header("Configuration")
        with st.expander("API and Model Settings", expanded=True):
            gemini_api_key = st.text_input("Gemini API Key", type="password", key="gemini_api_key")
            
            st.subheader("Model Selection")
            # Model mapping for cleaner UI
            model_mapping = {
                # Gemini 3.0 (newest)
                "gemini-3-flash-preview": "⚡ Gemini 3 Flash Preview",
                "gemini-3-pro-preview": "🧠 Gemini 3 Pro Preview",
                # Gemini 2.5
                "gemini-2.5-flash": "Gemini 2.5 Flash",
                "gemini-2.5-flash-lite": "Gemini 2.5 Flash-Lite",
                "gemini-2.5-pro": "Gemini 2.5 Pro",
                # Gemini 2.0
                "gemini-2.0-flash": "Gemini 2.0 Flash",
                "gemini-2.0-flash-lite": "Gemini 2.0 Flash-Lite",
                # Latest aliases
                "gemini-flash-latest": "Flash Latest (→ 2.5)",
                "gemini-flash-lite-latest": "Flash-Lite Latest (→ 2.5)",
            }
            
            # Ensure the default model from config is in our mapping or list
            if DEFAULT_MODEL_NAME not in model_mapping:
                 model_mapping[DEFAULT_MODEL_NAME] = DEFAULT_MODEL_NAME

            available_models = list(model_mapping.keys())
            
            generator_model = st.selectbox(
                "Generator Model",
                available_models,
                index=available_models.index(DEFAULT_MODEL_NAME) if DEFAULT_MODEL_NAME in available_models else 0,
                format_func=lambda x: model_mapping.get(x, x),
                key="generator_model",
                help="Select the model for generating prompts and examples."
            )

            evaluator_model = st.selectbox(
                "Evaluator Model",
                available_models,
                index=available_models.index(EVALUATOR_MODEL_NAME) if EVALUATOR_MODEL_NAME in available_models else 0,
                format_func=lambda x: model_mapping.get(x, x),
                key="evaluator_model",
                help="Select the model for evaluating prompt compliance."
            )

        if st.button("Clear Session State"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

    # --- Database Initialization ---
    try:
        initialize_database(DATABASE_NAME)
    except Exception as e:
        st.error(f"Failed to initialize the database: {e}")
        st.stop()

    # --- Render the main UI ---
    create_ui(DATABASE_NAME, prompts_config)

if __name__ == "__main__":
    main()
