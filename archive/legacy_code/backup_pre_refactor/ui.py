# ui.py

import streamlit as st
import json
import yaml
import logging
from api_handler import EnhancedPromptGenerator, QualityCheckLoop
from utils import save_prompt_to_db, get_all_prompts_from_db
from typing import List, Dict, Optional, Tuple


def create_enhanced_ui(database_name: str, default_model_name: str, prompts_config: Dict,
                      generator: EnhancedPromptGenerator = None,
                      quality_loop: QualityCheckLoop = None):
    st.markdown("""
    <style>
    .feedback-box {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .score-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 10px;
        font-weight: bold;
        margin-right: 5px;
    }
    .score-low {
        background-color: #ffcccc;
        color: #990000;
    }
    .score-medium {
        background-color: #fff2cc;
        color: #996600;
    }
    .score-high {
        background-color: #d9f2d9;
        color: #006600;
    }
    .streamlit-expanderHeader {
        font-weight: bold;
        color: #2c3e50;
    }
    .collapse-button {
        position: fixed;
        left: 0;
        top: 50%;
        background-color: #f0f2f6;
        z-index: 999;
        border-radius: 0 5px 5px 0;
    }
    </style>
    """, unsafe_allow_html=True)

    if 'current_prompt' not in st.session_state:
        st.session_state.current_prompt = None

    if 'show_feedback_panel' not in st.session_state:
        st.session_state.show_feedback_panel = False

    if 'improvement_history' not in st.session_state:
        st.session_state.improvement_history = []

    if 'current_iteration' not in st.session_state:
        st.session_state.current_iteration = 0

    if 'show_feedback_panel' not in st.session_state:
        st.session_state.show_feedback_panel = False

    if 'show_initial_prompt' not in st.session_state:
        st.session_state.show_initial_prompt = False

    if 'quality_check_started' not in st.session_state:
        st.session_state.quality_check_started = False

    if 'current_step' not in st.session_state:
        st.session_state.current_step = "input"  # Possible values: "input", "initial_prompt", "quality_loop"

    # Main title
    st.title("Professional PromptBase Template Generator")
    st.markdown("Generate high-quality, market-ready prompt templates aligned with PromptBase submission guidelines")

    # Main content in tabs
    tab1, tab2, tab3 = st.tabs(["Create Template", "Prompt Library", "Guidelines"])

    with tab1:
        st.header("Create New Prompt Template")

        # Determine column widths based on feedback panel visibility
        if st.session_state.show_feedback_panel:
            col1, col2 = st.columns([0.5, 0.5])
        else:
            col1, col2 = st.columns([0.4, 0.6])

        with col1:
            # Input Form
            topic = st.text_input("Prompt Topic", placeholder="e.g., Vintage Movie Posters")

            content_type = st.selectbox(
                "Content Type",
                ["Image", "Text", "Video"],
                index=0
            )

            model_platform = st.selectbox(
                "AI Platform",
                ["Midjourney", "DALL-E", "Stable Diffusion", "FLUX", "Sora", "ChatGPT", "Claude", "Llama", "Gemini"],
                index=0
            )

            # --- Style Selection with Custom Option ---
            if content_type == "Text":
                style_options = ["Custom..."] + [
                    "Academic", "Conversational", "Technical", "Journalistic",
                    "Persuasive", "Narrative", "Descriptive", "Analytical",
                    "Professional", "Informal", "Tutorial", "Blog Style",
                    "Business Formal", "Creative", "Poetic", "Documentary",
                    "Educational", "Marketing", "Scientific", "Editorial"
                ]
                use_case_options = ["Custom..."] + [
                    "Content Writing", "Technical Documentation", "Creative Writing",
                    "Business Communication", "Education", "Marketing Copy",
                    "Journalism", "Research", "Social Media", "Storytelling"
                ]
                style_help = "Select a predefined style or choose 'Custom...' to define your own."
                use_case_help = "Choose the main purpose or context for your text."

            elif content_type == "Image":
                style_options = ["Custom..."] + [
                    "Minimalist", "Photorealistic", "Vintage", "Cartoon", "Cyberpunk",
                    "Watercolor", "Pixel Art", "Abstract", "Surreal", "Gothic",
                    "Impressionist", "Pop Art", "Art Deco", "Sci-Fi", "Fantasy",
                    "Steampunk", "Retro", "Neon", "Vaporwave", "Cinematic", "Manga", "Anime"
                ]
                use_case_options = ["Custom..."] + [
                    "Marketing Materials", "Social Media Content", "Book/Album Covers",
                    "Product Photography", "Conceptual Art", "Advertising",
                    "Brand Identity", "Editorial", "E-commerce", "Personal Projects"
                ]
                style_help = "Select the visual style or choose 'Custom...' to define your own."
                use_case_help = "Choose the primary application or choose 'Custom...' to define your own."
            
            else:  # Video
                style_options = ["Custom..."] + [
                    "Cinematic", "Documentary", "Commercial", "Music Video",
                    "Tutorial", "Vlog", "Animation", "Experimental",
                    "Corporate", "Travel", "Sports", "Fashion",
                    "Product Showcase", "Event Coverage", "Storytelling",
                    "Aerial", "Time-lapse", "Slow Motion", "First Person", "Behind the Scenes"
                ]
                use_case_options = ["Custom..."] + [
                    "Product Demonstrations", "Social Media Content", "Advertisements",
                    "Educational Videos", "Corporate Communications", "Event Coverage",
                    "Documentary", "Entertainment", "Training Materials", "Brand Stories"
                ]
                style_help = "Choose the video style or choose 'Custom...' to define your own."
                use_case_help = "Select the main purpose or choose 'Custom...' to define your own."

            # Single style selection with help text
            style_preference = st.selectbox(
                "Style",
                style_options,
                help=style_help
            )

            if style_preference == "Custom...":
                custom_style = st.text_input("Enter Custom Style", placeholder="e.g., Biomechanical Surrealism")
                final_style = custom_style if custom_style else "user-defined style"
            else:
                final_style = style_preference

            # Single use case selection with help text
            use_case = st.selectbox(
                "Primary Use Case", 
                use_case_options,
                help=use_case_help
            )

            if use_case == "Custom...":
                custom_use_case = st.text_input("Enter Custom Use Case", placeholder="e.g., Generating abstract concepts")
                final_use_case = custom_use_case if custom_use_case else "user-defined use case"
            else:
                final_use_case = use_case
                
            # Quality loop settings
            st.subheader("Quality Improvement Settings")

            enable_quality_loop = st.checkbox("Enable Quality Improvement Loop", value=True)

            if enable_quality_loop:
                max_iterations = st.slider("Maximum Improvement Iterations", 1, 5, 3)
                quality_threshold = st.slider("Quality Score Threshold (Stop when reached)", 30, 50, 45)

        with col2:
            # Output Display or Feedback Panel
            if st.session_state.current_step == "quality_loop":
                st.subheader("Real-time Quality Improvement")

                if st.session_state.improvement_history:
                    # Create navigation for improvement iterations
                    iterations = len(st.session_state.improvement_history)

                    st.markdown("### Iterations")

                    # Create a horizontal layout using a single row
                    cols = st.columns(3)

                    with cols[0]:
                        # Previous button
                        if st.button("◀️ Previous", key="prev_iter",
                                    disabled=st.session_state.current_iteration <= 0):
                            st.session_state.current_iteration -= 1

                    with cols[1]:
                        # Current iteration display
                        st.markdown(f"**Version {st.session_state.current_iteration + 1}/{iterations}**")

                    with cols[2]:
                        # Next button
                        if st.button("Next ▶️", key="next_iter",
                                    disabled=st.session_state.current_iteration >= iterations - 1):
                            st.session_state.current_iteration += 1

                    # Best version button
                    if st.button("🌟 Show Best Version", key="best_iter"):
                        best_idx = max(range(iterations),
                                    key=lambda i: st.session_state.improvement_history[i].get("score", 0))
                        st.session_state.current_iteration = best_idx

                    # Display the selected iteration
                    current_iter = st.session_state.current_iteration
                    if current_iter < iterations:
                        iter_data = st.session_state.improvement_history[current_iter]

                        # Display metadata about this iteration
                        st.markdown(f"### Iteration {current_iter} "
                                   f"({'Original' if current_iter == 0 else 'Improved'})")

                        # Score display if available
                        if "evaluation" in iter_data and iter_data["evaluation"]:
                            eval_data = iter_data["evaluation"]
                            total_score = eval_data.get("total_score", 0)

                            # Score color class
                            score_class = "score-low"
                            if total_score >= 40:
                                score_class = "score-high"
                            elif total_score >= 30:
                                score_class = "score-medium"

                            st.markdown(f"""
                            <div class='feedback-box'>
                                <h4>Evaluation Scores</h4>
                                <div class='{score_class} score-badge'>Total: {total_score}/50</div>
                                <div class='score-badge'>Clarity: {eval_data.get('clarity', 0)}/10</div>
                                <div class='score-badge'>Flexibility: {eval_data.get('flexibility', 0)}/10</div>
                                <div class='score-badge'>Specificity: {eval_data.get('specificity', 0)}/10</div>
                                <div class='score-badge'>Creativity: {eval_data.get('creativity', 0)}/10</div>
                                <div class='score-badge'>Technical: {eval_data.get('technical_accuracy', 0)}/10</div>
                            </div>
                            """, unsafe_allow_html=True)

                        # Display the prompt template for this iteration
                        prompt_data = iter_data["prompt"]

                        st.subheader("Prompt Template")
                        st.code(prompt_data.get("template", ""), language="markdown")

                        # Show improvement changes if not the first iteration
                        if current_iter > 0 and "improvement_changes" in prompt_data:
                            with st.expander("Changes Made in This Iteration", expanded=True):
                                for change in prompt_data.get("improvement_changes", []):
                                    st.markdown(f"- {change}")

                            if "improvement_rationale" in prompt_data:
                                with st.expander("Improvement Rationale"):
                                    st.markdown(prompt_data["improvement_rationale"])

                        # Display suggestions for further improvement
                        if "evaluation" in iter_data and iter_data["evaluation"]:
                            suggestions = iter_data["evaluation"].get("priority_improvements", [])
                            if suggestions:
                                with st.expander("Suggestions for Further Improvement"):
                                    for suggestion in suggestions:
                                        st.markdown(f"- {suggestion}")
                else:
                    st.info("Generate a prompt to see real-time quality improvement feedback.")

            elif st.session_state.current_step == "initial_prompt":
                # Display the initial prompt
                prompt_data = st.session_state.current_prompt

                st.subheader("📝 Initial Prompt Template")
                st.code(prompt_data["template"], language="markdown")

                # Variables and Explanations
                with st.expander("📋 Variables and Explanations", expanded=True):
                    for var in prompt_data["variables"]:
                        explanation = prompt_data["variable_explanations"].get(var, "No explanation provided")
                        st.markdown(f"**{var}**: {explanation}")

                # Display Instructions
                with st.expander("📝 Instructions"):
                    st.markdown(prompt_data["instructions"])

                # Examples
                with st.expander("🔍 Example Prompts", expanded=True):
                    for i, example in enumerate(prompt_data["examples"], 1):
                        st.markdown(f"**Example {i}:** {example}")

                # Tips
                with st.expander("💡 Usage Tips"):
                    for tip in prompt_data["tips"]:
                        st.markdown(f"- {tip}")

                # Add evaluation results if available
                if "evaluation" in prompt_data:
                    with st.expander("🔎 Quality Evaluation"):
                        eval_data = prompt_data["evaluation"]
                        if eval_data:
                            total_score = eval_data.get("total_score", 0)

                            score_class = "score-low"
                            if total_score >= 40:
                                score_class = "score-high"
                            elif total_score >= 30:
                                score_class = "score-medium"

                            st.markdown(f"""
                            <div class='feedback-box'>
                                <h4>Evaluation Scores</h4>
                                <div class='{score_class} score-badge'>Total: {total_score}/50</div>
                                <div class='score-badge'>Clarity: {eval_data.get('clarity', 0)}/10</div>
                                <div class='score-badge'>Flexibility: {eval_data.get('flexibility', 0)}/10</div>
                                <div class='score-badge'>Specificity: {eval_data.get('specificity', 0)}/10</div>
                                <div class='score-badge'>Creativity: {eval_data.get('creativity', 0)}/10</div>
                                <div class='score-badge'>Technical: {eval_data.get('technical_accuracy', 0)}/10</div>
                            </div>
                            """, unsafe_allow_html=True)

                        suggestions = eval_data.get("priority_improvements", [])
                        if suggestions:
                            st.markdown("**Improvement Suggestions:**")
                            for suggestion in suggestions:
                                st.markdown(f"- {suggestion}")

                if enable_quality_loop and st.button("Start Quality Improvement Loop"):
                    st.session_state.current_step = "quality_loop"
                    with st.spinner("Running Quality Improvement Loop..."):
                        best_prompt, improvement_history = quality_loop.run_quality_loop(prompt_data)

                        # Update session state
                        st.session_state.current_prompt = best_prompt
                        st.session_state.improvement_history = improvement_history
                        st.session_state.current_iteration = len(improvement_history) - 1
                        st.session_state.show_feedback_panel = True
                        st.rerun()

            else:
                # Initial state: show a placeholder
                st.info("Click 'Generate Professional Prompt Template' to create a prompt.")

        # Generate button with quality loop implementation
        generate_col1, generate_col2 = st.columns([0.7, 0.3])

        with generate_col1:
            if st.button("Generate Professional Prompt Template", key="generate_btn"):
                if not st.session_state.get("gemini_api_key"):
                    st.error("Please enter a Gemini API Key in the sidebar.")
                elif not topic:
                    st.error("Please enter a prompt topic")
                elif generator and generator.is_initialized():
                    with st.spinner(f"Generating {content_type} prompt template..."):
                        initial_prompt_data = generator.generate_specialized_prompt(
                            topic=topic,
                            content_type=content_type,
                            style=final_style,
                            use_case=final_use_case,
                            model_platform=model_platform
                        )

                        if "error" in initial_prompt_data:
                            st.error(f"Initial generation failed: {initial_prompt_data['error']}")
                        else:
                            st.session_state.current_prompt = initial_prompt_data
                            st.session_state.current_step = "initial_prompt"  # Move to initial prompt display
                            st.rerun()

        with generate_col2:
            if st.button("Toggle Feedback Panel", key="toggle_feedback", disabled=True):
                # The toggle button is disabled now
                pass

        # Save button below all content
        if st.button("💾 Save to Library", key="save_library_button", disabled=(st.session_state.current_step != "quality_loop" and st.session_state.current_step != "initial_prompt")):
            if st.session_state.current_prompt is not None:
                save_prompt_to_db(database_name, st.session_state.current_prompt)
                st.success("✅ Prompt saved to library!")
            else:
                st.error("Please generate a prompt first before saving")


    with tab2:
        st.header("Prompt Library")
        prompts = get_all_prompts_from_db(database_name)

        if not prompts:
            st.info("Your prompt library is currently empty.")
        else:
            st.subheader("Saved Prompts")

            for prompt in prompts:
                # Use st.expander to make each prompt collapsible
                with st.expander(f"**{prompt['topic']}** ({prompt['content_type']} for {prompt['platform']}) - Saved on: {prompt['created_at']}", expanded=False):  # expanded=False for initial collapse
                    # All the prompt details content goes inside the expander:

                    st.markdown(f"**Style:** {prompt['style']} | **Use Case:** {prompt['use_case']}")  # Moved style and use_case up

                    # Template section
                    st.markdown("#### 📝 Prompt Template")
                    st.code(prompt["template"], language="markdown")

                    # Columns for Variables and Examples
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("#### 📋 Variables")
                        for var in prompt.get("variables", []):
                            explanation = prompt.get("variable_explanations", {}).get(var, "No explanation provided")
                            st.markdown(f"**{var}**: {explanation}")

                        st.markdown("#### 📖 Description")
                        if prompt.get("description"):
                            st.markdown(prompt["description"])
                        else:
                            st.info("No description provided")

                        st.markdown("#### 📝 Instructions")
                        if prompt.get("instructions"):
                            st.markdown(prompt["instructions"])
                        else:
                            st.info("No instructions provided")

                    with col2:
                        st.markdown("#### 🔍 Examples")
                        for i, example in enumerate(prompt.get("examples", []), 1):
                            st.markdown(f"**Example {i}:** {example}")

                        st.markdown("#### 💡 Tips")
                        for tip in prompt.get("tips", []):
                            st.markdown(f"- {tip}")

                    # Validation section
                    st.markdown("#### 🔎 Validation")
                    if prompt["validation"]["passed"]:
                        st.success("✅ Meets PromptBase guidelines")
                    else:
                        st.warning("⚠️ Needs improvements")

                    if prompt["validation"].get("issues"):
                        for issue in prompt["validation"]["issues"]:
                            st.markdown(f"- ⚠️ {issue}")

                    if prompt["validation"].get("suggestions"):
                        for suggestion in prompt["validation"]["suggestions"]:
                            st.markdown(f"- 💡 {suggestion}")

                    # Testing guidance
                    st.markdown("#### 🧪 Testing Guide")
                    if prompt.get("test_guidance") and "error" not in prompt["test_guidance"]:
                        col3, col4 = st.columns(2)
                        with col3:
                            st.markdown("**Test Instructions:**")
                            for instruction in prompt["test_guidance"]["test_instructions"]:
                                st.markdown(f"- {instruction}")

                            st.markdown("**Quality Checklist:**")
                            for check in prompt["test_guidance"]["quality_checklist"]:
                                st.markdown(f"- {check}")

                        with col4:
                            st.markdown("**Common Issues:**")
                            for issue in prompt["test_guidance"]["common_issues"]:
                                st.markdown(f"- {issue}")

                    st.markdown("---")
    with tab3:
        st.header("PromptBase Submission Guidelines")

        st.markdown("""
        ### Key Guidelines for Successful PromptBase Submissions

        #### 1. Prompt Templates
        - Use [VARIABLES] in square brackets to make prompts adaptable
        - Make sure your prompt can generate various outputs in the same style
        - Each variable should control a meaningful aspect of the output

        #### 2. High Use-Case Factor
        - Prompts with practical applications sell better
        - Examples: logo designs, product photography, marketing content
        - Consider how others might use your prompt in their work

        #### 3. Unique Styles
        - Develop prompts that achieve distinctive visual or writing styles
        - Push the boundaries of what AI models can create
        - Create styles that would be difficult to achieve manually

        #### 4. Common Reasons for Rejection
        - Too specific or overly niche prompts
        - Inconsistent style across outputs
        - Low quality or distorted outputs
        - Example outputs too similar
        - Prompt too simple or easily guessable

        #### 5. Testing Your Prompts
        - Generate multiple examples with different variables
        - Ensure consistent style across all outputs
        - Verify that changing variables produces meaningful differences
        - Check for technical issues or artifacts
        """)

    # Add a button to clear the session state
    if st.sidebar.button("Clear Session State", key="ui_clear_session"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.sidebar.success("Session state cleared!")