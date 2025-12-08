# ui.py

import streamlit as st
import json
import random
from typing import Dict, Any, Callable
import google.generativeai as genai
from pypdf import PdfReader
from PIL import Image

from utils import save_prompt_to_db, get_all_prompts_from_db, save_output_to_json, update_prompt_in_db, save_market_data, get_all_market_data, delete_market_data, parse_csv_to_text, parse_json_to_text
from run_agentic_workflow import run_workflow
from api_handler import agent_analyze_market, agent_generate_concepts, agent_manage_examples, agent_analyze_trends, agent_normalize_data


def initialize_session_state():
    """Initializes all required session state variables."""
    state_defaults = {
        "prompt_package": None,
        "workflow_running": False,
        "market_analysis": None,
        "analysis_running": False,
        "concepts": None,
        "concepts_running": False,
        "gemini_api_key": None,
        "generator_model": "models/gemini-flash-latest",
        "evaluator_model": "models/gemini-flash-latest",
        "updating_examples_prompt_id": None, # To track which prompt is being updated
        "normalized_data": None,
    }

    for key, value in state_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def create_ui(database_name: str, prompts_config: Dict[str, Any]):
    """Creates the main user interface for the agentic prompt generator."""
    initialize_session_state()

    st.markdown("""
    <style>
    .stButton>button { width: 100%; }
    .stExpander { border: 1px solid #dfe4ea !important; border-radius: 10px !important; }
    .score-badge { display: inline-block; padding: 4px 12px; border-radius: 15px; font-weight: bold; margin: 2px; }
    .score-low { background-color: #ffcccc; color: #990000; }
    .score-medium { background-color: #fff2cc; color: #996600; }
    .score-high { background-color: #d9f2d9; color: #006600; }
    </style>
    """, unsafe_allow_html=True)

    st.title("✨ Agentic PromptBase Generator")
    st.markdown("A multi-agent system to research, ideate, and create market-ready prompt templates.")

    # Reordered and renamed tabs for a more logical workflow
    tab_create, tab_trends, tab_results, tab_library, tab_guides = st.tabs([
        "🚀 Create", "📈 Trend Engine", "📦 Results", "📚 Library", "📄 Guidelines"
    ])

    # "Create" tab is the new starting point, containing the enhanced Idea Lab
    with tab_create:
        render_idea_lab(prompts_config)

    with tab_trends:
        render_trend_engine(prompts_config, database_name)

    # "Results" tab now exclusively shows the output from the workflow
    with tab_results:
        render_output_area(st.session_state.get("user_inputs", {}), prompts_config, database_name)

    with tab_library:
        render_prompt_library(database_name, prompts_config)

    with tab_guides:
        render_guidelines()

def handle_concept_selection(concept: Dict[str, Any]):
    st.session_state.topic = concept.get("topic", "")
    st.session_state.content_type = concept.get("content_type", "Image")
    # Join lists into strings for text inputs, handling the new data structure
    st.session_state.style = ", ".join(concept.get("style_descriptors", []))
    st.session_state.use_case = ", ".join(concept.get("use_cases", []))

    st.success(f"✅ Concept '{concept.get('topic')}' loaded! Navigate to the '🚀 Create Template' tab to continue.")

def load_trend_into_state(trend: Dict[str, Any]):
    """Callback to load trend data into session state widgets."""
    st.session_state["topic_idea"] = trend.get("topic")
    st.session_state["style_idea"] = trend.get("style")
    st.session_state["use_case_idea"] = trend.get("use_case")
    # We can also set a flag to show a success message on the next run if needed
    st.session_state["trend_loaded"] = True

def render_idea_lab(prompts_config: Dict[str, Any]):
    st.header("💡 Idea Lab")
    st.markdown("Define your prompt concept. Our AI agents will research the market, analyze trends, and generate a complete marketplace-ready template.")

    if not st.session_state.get("gemini_api_key"):
        st.warning("Please enter your Gemini API Key in the sidebar to use the Idea Lab.")
        return

    # Simplified input form with Tabs for Mode Selection
    mode_tab1, mode_tab2, mode_tab3 = st.tabs(["✨ Generation Mode", "🛠️ Reverse Engineer", "🖼️ Image to Prompt"])

    with mode_tab1:
        content_type = st.selectbox("Content Type", ["Image", "Text", "Video"], key="content_type_idea")
        platform = st.selectbox("AI Platform", ["Veo 3.1", "Midjourney", "DALL-E 3", "Imagen 3 (Gemini)", "Gemini Nano", "Sora", "Stable Diffusion", "ChatGPT-4o", "Claude 3"], key="platform_idea")
        
        topic = st.text_input("Topic / Theme", placeholder="e.g., watercolor flowers, cyberpunk portraits", key="topic_idea")
        style = st.text_input("Style Direction (Optional)", key="style_idea")
        use_case = st.text_input("Primary Use Case", key="use_case_idea")

        if st.button("🚀 Generate Full Prompt Package", type="primary", use_container_width=True):
            if not topic:
                st.error("⚠️ Please enter a topic to continue")
            else:
                user_inputs = {
                    "input_mode": "Generation",
                    "topic": topic,
                    "content_type": content_type,
                    "model_platform": platform,
                    "style": style,
                    "use_case": use_case
                }
                st.session_state.workflow_running = True
                st.session_state.prompt_package = None
                st.session_state.user_inputs = user_inputs
                st.success("Starting workflow... check the '🚀 Create Template' tab for progress.")
                st.rerun()

    with mode_tab2:
        st.info("Paste your **Final Prompt Template** below. Our AI will analyze it, extract variables, and generate a complete sales package for you.")
        reverse_content_type = st.selectbox("Prompt Type", ["Image", "Text", "Video"], key="reverse_content_type")
        reverse_platform = st.selectbox("Target Platform", ["Veo 3.1", "Midjourney", "DALL-E 3", "Imagen 3 (Gemini)", "Sora", "Stable Diffusion", "ChatGPT-4o", "Claude 3"], key="reverse_platform")
        template_input = st.text_area("Paste your Prompt Template here", height=150, placeholder="e.g., A cinematic shot of a [SUBJECT] in the style of [STYLE]...")
        
        if st.button("🛠️ Reverse Engineer Package", type="primary", use_container_width=True):
            if not template_input:
                st.error("⚠️ Please paste a template provided.")
            else:
                 user_inputs = {
                    "input_mode": "Reverse",
                    "template": template_input,
                    "content_type": reverse_content_type,
                    "platform": reverse_platform
                }
                 st.session_state.workflow_running = True
                 st.session_state.prompt_package = None
                 st.session_state.user_inputs = user_inputs
                 st.session_state.topic = "Reverse Engineering..." 
                 st.success("Analyzing template... Check the '📦 Results' tab.")
                 st.rerun()

    with mode_tab3:
        st.info("Upload an **Image** to reverse-engineer its style into a reusable prompt template.")
        uploaded_image = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg", "webp"], key="reverse_image_upload")
        
        if st.button("✨ Reverse Engineer from Image", type="primary", use_container_width=True):
            if not uploaded_image:
                st.error("⚠️ Please upload an image first.")
            else:
                try:
                    image_data = Image.open(uploaded_image)
                    user_inputs = {
                        "input_mode": "ReverseImage",
                        "image_data": image_data
                    }
                    st.session_state.workflow_running = True
                    st.session_state.prompt_package = None
                    st.session_state.user_inputs = user_inputs
                    # Model selection is handled in render_output_area based on input_mode 
                    st.session_state.topic = "Image Reverse Engineering..."
                    st.success("Analyzing image... Check the '📦 Results' tab.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error processing image: {e}")


def render_trend_engine(prompts_config: Dict[str, Any], database_name: str):
    st.header("📈 Trend Engine & Knowledge Base")
    st.markdown("Accumulate market intelligence to generate data-driven prompt ideas. Saved data acts as 'long-term memory' for the trend analyzer.")

    if not st.session_state.get("gemini_api_key"):
        st.warning("Please enter your Gemini API Key in the sidebar to use the Trend Engine.")
        return

    # --- Section: Knowledge Base Status ---
    stored_data = get_all_market_data(database_name)
    with st.expander(f"📚 Manage Knowledge Base ({len(stored_data)} items saved)", expanded=False):
        if not stored_data:
            st.info("Knowledge Base is empty. Upload data or paste text below to save.")
        else:
            for item in stored_data:
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(f"{item['created_at'][:10]} | Source: {item.get('source', 'Unknown')} | {item['content'][:60]}...")
                with col2:
                    if st.button("🗑️", key=f"del_{item['id']}"):
                        delete_market_data(database_name, item['id'])
                        st.rerun()

    # --- Tool: Data Helper ---
    with st.expander("🛠️ Data Helper (Unstructured -> Structured JSON)", expanded=False):
        st.markdown("Paste unstructured text (articles, lists) to convert it into clean JSON.")
        raw_input = st.text_area("Raw Text Input", height=150, key="raw_data_helper")
        if st.button("🔄 Normalize Data", key="btn_normalize"):
            if not raw_input:
                st.error("Please provide text.")
            else:
                with st.spinner("Normalizing data..."):
                    model = genai.GenerativeModel(st.session_state.generator_model)
                    normalized_items = agent_normalize_data(model, prompts_config, raw_input)
                    if normalized_items and isinstance(normalized_items, list) and "error" in normalized_items[0]:
                        st.error(normalized_items[0]['error'])
                    else:
                        st.session_state.normalized_data = normalized_items
                        st.success(f"Extracted {len(normalized_items)} items!")
        
        if st.session_state.get("normalized_data"):
            st.json(st.session_state.normalized_data)
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                # Save directly to KB
                if st.button("💾 Save All to Knowledge Base", key="save_norm_kb"):
                    count = 0 
                    for item in st.session_state.normalized_data:
                        # Convert item back to string format for storage 'content'
                        content_str = f"Item: {item.get('content')} | Tags: {item.get('tags')}"
                        save_market_data(database_name, content_str, source=item.get('source', 'Data Helper'))
                        count += 1
                    st.success(f"Saved {count} items to Knowledge Base!")
                    st.session_state.normalized_data = None # Clear after save
                    st.rerun()
            with col_d2:
                 st.download_button(
                    label="⬇️ Download JSON",
                    data=json.dumps(st.session_state.normalized_data, indent=2),
                    file_name="normalized_market_data.json",
                    mime="application/json"
                )

    # --- Section: Input / Upload ---
    st.subheader("Add Market Data")

    market_data_input = st.text_area("Paste Market Data / Trends Text", height=150, placeholder="Paste text here...", key="market_input")
    uploaded_file = st.file_uploader("Or upload file (TXT, MD, PDF, CSV, JSON)", type=["txt", "md", "pdf", "csv", "json"], key="market_file")

    current_text = market_data_input
    source_name = "Manual Input"

    if uploaded_file:
        source_name = uploaded_file.name
        try:
            if uploaded_file.type == "application/pdf":
                reader = PdfReader(uploaded_file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                current_text = text
            elif uploaded_file.type == "text/csv" or uploaded_file.name.endswith('.csv'):
                content = uploaded_file.read().decode("utf-8")
                current_text = parse_csv_to_text(content)
            elif uploaded_file.type == "application/json" or uploaded_file.name.endswith('.json'):
                content = uploaded_file.read().decode("utf-8")
                current_text = parse_json_to_text(content)
            else:
                # Fallback for txt/md
                current_text = uploaded_file.read().decode("utf-8")
        except Exception as e:
            st.error(f"Error reading file: {e}")
            current_text = ""

    col_save, col_analyze = st.columns(2)

    with col_save:
        if st.button("💾 Save to Knowledge Base", use_container_width=True):
            if not current_text:
                st.error("No content to save.")
            else:
                save_market_data(database_name, current_text, source=source_name)
                st.success("✅ Saved to Knowledge Base!")
                st.rerun()

    with col_analyze:
        analyze_btn = st.button("🔮 Analyze Trends", type="primary", use_container_width=True)

    if analyze_btn:
        with st.spinner("Analyzing market trends from Knowledge Base + Input..."):
            
            # Combine KB data + Current Input
            combined_context = ""
            
            # 1. Add stored data
            if stored_data:
                combined_context += "--- HISTORICAL MARKET DATA (FROM KNOWLEDGE BASE) ---\n"
                for item in stored_data:
                    combined_context += f"Source: {item.get('source', 'Unknown')} ({item['created_at']})\nContent: {item['content']}\n\n"
            
            # 2. Add current input (if different or new)
            if current_text:
                 combined_context += "--- NEW / CURRENT INPUT DATA ---\n"
                 combined_context += f"Source: {source_name}\nContent: {current_text}\n"

            if not combined_context:
                st.error("Please provide some market data (stored or new) to analyze.")
            else:
                model = genai.GenerativeModel(st.session_state.generator_model)
                trends = agent_analyze_trends(model, prompts_config, combined_context)
                
                if trends and isinstance(trends, list) and "error" in trends[0]:
                    st.error(f"Analysis failed: {trends[0]['error']}")
                else:
                    st.session_state.trends_results = trends
                    st.success("Analysis complete! See suggestions below.")

    if st.session_state.get("trends_results"):
        st.subheader("🔥 Predicted Best-Sellers")
        for i, trend in enumerate(st.session_state.trends_results):
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{trend.get('topic')}**")
                    st.caption(f"Style: {trend.get('style')} | Use Case: {trend.get('use_case')}")
                    st.markdown(f"*{trend.get('reasoning')}*")
                with col2:
                    st.button(
                        "✨ Create This", 
                        key=f"create_trend_{i}",
                        on_click=load_trend_into_state,
                        args=(trend,)
                    )
    
    if st.session_state.get("trend_loaded"):
        st.success("Concept loaded! Go to '🚀 Create' tab to generate.")
        # Reset the flag so it doesn't persist forever
        st.session_state["trend_loaded"] = False

def render_input_form() -> Dict[str, Any]:
    with st.container(border=True):
        st.subheader("1. Define Your Prompt Concept")
        content_type = st.selectbox("Content Type", ["Image", "Text", "Video"], key="content_type")
        user_inputs = {
            "topic": st.text_input("Topic", placeholder="e.g., Vintage Movie Posters", key="topic"),
            "content_type": content_type,
            "model_platform": st.selectbox("AI Platform", ["Midjourney", "DALL-E 3", "Imagen 3 (Gemini)", "Gemini Nano", "Sora", "Stable Diffusion", "ChatGPT-4o", "Claude 3"], key="model_platform"),
            "style": st.text_input("Style", key="style"),
            "use_case": st.text_input("Primary Use Case", key="use_case")
        }
        st.subheader("2. Start the Workflow")
        if st.button("🤖 Generate with AI Agents", type="primary", disabled=st.session_state.workflow_running):
            if not st.session_state.get("gemini_api_key"):
                st.error("Please enter your Gemini API Key in the sidebar.")
            elif not user_inputs["topic"]:
                st.warning("Please enter a topic for your prompt.")
            else:
                st.session_state.workflow_running = True
                st.session_state.prompt_package = None
                st.session_state.user_inputs = user_inputs
                st.rerun()
        return user_inputs

def render_output_area(user_inputs: Dict[str, Any], prompts_config: Dict[str, Any], database_name: str):
    if not st.session_state.workflow_running and not st.session_state.prompt_package:
        st.info("Fill in the details on the left and click the button to start the agent workflow, or use the Idea Lab to brainstorm first.")
        return

    if st.session_state.workflow_running:
        status_placeholder = st.empty()

        # Determine which model to use.
        # For ReverseImage, we force a vision-capable model if one isn't selected,
        # but here we'll just hardcode a known good vision model or keep the user's choice if it supports vision.
        # For simplicity, let's override for ReverseImage as intended in the original code.
        generator_model_name = st.session_state.generator_model
        if st.session_state.user_inputs.get("input_mode") == "ReverseImage":
             generator_model_name = "models/gemini-flash-latest" # User requested 'flash_last' which maps to this

        workflow_generator = run_workflow(
            api_key=st.session_state.gemini_api_key,
            generator_model_name=generator_model_name,
            evaluator_model_name=st.session_state.evaluator_model,
            prompts_config=prompts_config,
            user_inputs=st.session_state.user_inputs
        )
        for result in workflow_generator:
            status_placeholder.info(f"**Agent:** {result.get('step', 'System')}  \n**Status:** {result.get('output', 'An unknown error occurred.')}")
            if result.get("prompt_package"):
                st.session_state.prompt_package = result["prompt_package"]
            if result["status"] == "error":
                st.error(f"An error occurred: {result['output']}")
                st.session_state.workflow_running = False
                break
            if result["status"] == "completed":
                st.session_state.workflow_running = False
                status_placeholder.success(f"✅ {result.get('output')}")
                st.rerun()

    if st.session_state.prompt_package:
        render_prompt_package(st.session_state.prompt_package, database_name, show_save_button=True)

def render_prompt_package(prompt: Dict[str, Any], database_name: str, show_save_button: bool = False, is_in_library: bool = False, prompts_config: Dict = None):
    # Main Title and Commercial Description
    st.header(f"{prompt.get('topic', 'Untitled Prompt')}")
    if prompt.get("commercial_description"):
        st.markdown(f"> {prompt.get('commercial_description')}")
    elif prompt.get("description"):
        st.markdown(f"> {prompt.get('description')}")
    st.divider()

    # --- Evaluation Score ---
    if "evaluation" in prompt and prompt["evaluation"]:
        with st.container(border=True):
            eval_data = prompt["evaluation"]
            total_score = eval_data.get("total_score", 0)
            score_class = "score-low" if total_score < 60 else "score-medium" if total_score < 85 else "score-high"
            st.markdown(f'**Compliance Score:** <div class="score-badge {score_class}">{total_score}/100</div>', unsafe_allow_html=True)
            with st.expander("View Detailed Evaluation"):
                st.markdown("**Priority Improvements:**")
                for suggestion in eval_data.get("priority_improvements", ["None."]):
                    st.markdown(f"- {suggestion}")
                st.divider()
                st.json(eval_data.get("scores", eval_data))

    # --- Core Prompt Details ---
    with st.container(border=True):
        st.subheader("📝 Prompt Template")
        st.code(prompt.get("template", "No template found."), language="markdown")

        col1, col2 = st.columns(2)
        with col1:
            with st.expander("📋 Variables & Explanations"):
                variables = prompt.get("variables", [])
                explanations = prompt.get("variable_explanations", {})
                if variables:
                    # Create a normalized (lowercase) map of explanations for robust lookup
                    normalized_explanations = {k.lower(): v for k, v in explanations.items()}
                    
                    for var in variables:
                        # Try exact match, then case-insensitive match
                        explanation = explanations.get(var) or normalized_explanations.get(var.lower(), 'No explanation provided.')
                        st.markdown(f"**`{var}`**: {explanation}")
                else:
                    st.info("This prompt has no variables.")
        with col2:
            with st.expander("💡 Usage Tips"):
                tips = prompt.get("tips", [])
                if tips:
                    for tip in tips:
                        st.markdown(f"- {tip}")
                else:
                    st.info("No usage tips provided.")

    # --- Examples Section ---
    st.subheader("🔍 Examples")
    examples = prompt.get("examples", [])
    if examples and isinstance(examples[0], dict):
        for i, example_obj in enumerate(examples):
            with st.container(border=True):
                st.markdown(f"**Example {i+1}**")
                if example_obj.get("variables"):
                    st.markdown("Variables Used:")
                if example_obj.get("variables"):
                    st.markdown("Variables Used:")
                    # st.code(json.dumps(example_obj["variables"], indent=2), language="json")
                    # User requested individual copy buttons. 
                    # Using columns to show "Name: [Value (Copyable)]"
                    for var_name, var_value in example_obj["variables"].items():
                        c1, c2 = st.columns([1, 3])
                        with c1:
                            st.markdown(f"**{var_name}:**")
                        with c2:
                            st.code(var_value, language="text")
                
                st.markdown("Resulting Prompt:")
                st.text_area(
                    label=f"Prompt_example_{i+1}", 
                    value=example_obj.get("prompt", ""), 
                    height=100, 
                    key=f"example_{prompt.get('id', 0)}_{i}",
                    label_visibility="collapsed"
                )
    elif examples: # Fallback for old data format
        for i, example_str in enumerate(examples):
            st.text_area(f"Example {i+1}", example_str, height=100, key=f"example_{prompt.get('id', 0)}_{i}")
    else:
        st.info("No examples were generated for this prompt.")

    # --- Final Action Buttons ---
    if show_save_button:
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save to Library", key="save_button", type="primary", use_container_width=True):
                try:
                    save_prompt_to_db(database_name, prompt)
                    st.success("✅ Prompt saved successfully to the library!")
                except Exception as e:
                    st.error(f"Failed to save prompt: {e}")
        with col2:
            # Placeholder for another main action
            pass

    # --- Export Section ---
    st.subheader("💾 Export Options")
    export_col1, export_col2, export_col3 = st.columns(3)
    package = prompt # Use the passed prompt data

    with export_col1:
        # JSON export
        json_data = json.dumps(package, indent=2)
        st.download_button(
            label="📄 Download JSON",
            data=json_data,
            file_name=f"{package.get('topic', 'prompt').replace(' ', '_')}.json",
            mime="application/json",
            use_container_width=True,
            key=f"download_json_{package.get('id', 'new')}_{random.randint(0, 10000)}"
        )
    
    with export_col2:
        # Markdown export for PromptBase
        markdown_content = f"""# {package.get('topic', 'Untitled')}

## Description
{package.get('commercial_description', package.get('description', ''))}

## Template
```
{package.get('template', '')}
```

## Example Prompts
"""
        # Safely access nested example prompts
        examples = package.get('examples', [])
        if examples and isinstance(examples[0], dict):
            for i, ex_obj in enumerate(examples[:9], 1):
                markdown_content += f"{i}. `{ex_obj.get('prompt', '')}`\n"
        
        st.download_button(
            label="📝 Download Markdown",
            data=markdown_content,
            file_name=f"{package.get('topic', 'prompt').replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True,
            key=f"download_md_{package.get('id', 'new')}_{random.randint(0, 10000)}"
        )
    
    with export_col3:
        # Copy to clipboard
        if st.button("📋 Copy Template", use_container_width=True, key=f"copy_btn_{package.get('id')}"):
            st.code(package.get('template', ''), language='text')
            st.success("Template copied to clipboard!")

def render_prompt_library(database_name: str, prompts_config: Dict[str, Any]):
    st.header("📚 My Prompt Library")
    prompts = get_all_prompts_from_db(database_name)
    if not prompts:
        st.info("Your library is empty. Save a generated prompt to see it here.")
        return

    # Handle the update logic if a prompt update was triggered
    if st.session_state.get("updating_examples_prompt_id"):
        prompt_id_to_update = st.session_state.updating_examples_prompt_id
        action, detail = st.session_state.update_action
        prompt_to_update = next((p for p in prompts if p['id'] == prompt_id_to_update), None)

        if prompt_to_update:
            with st.spinner(f"Performing action '{action}' on examples..."):
                model = genai.GenerativeModel(st.session_state.generator_model)
                
                if action == "regenerate_one":
                    example_index = detail
                    example_to_regenerate = prompt_to_update["examples"][example_index]
                    new_examples = agent_manage_examples(model, prompt_to_update, action="regenerate_one", example_index=example_index, example_to_regenerate=example_to_regenerate)
                elif action == "complete":
                    target_total = detail
                    new_examples = agent_manage_examples(model, prompt_to_update, action="complete", target_total=target_total)
                
                if isinstance(new_examples, list):
                    update_prompt_in_db(database_name, prompt_id_to_update, {"examples": new_examples})
                    st.success("Examples updated successfully!")
                else:
                    st.error(f"Failed to update examples: {new_examples.get('error', 'Unknown error')}")
                
                # Clear state and rerun to show updated library
                st.session_state.updating_examples_prompt_id = None
                st.session_state.update_action = None
                st.rerun()

    search_query = st.text_input("Search library by topic...", "")
    filtered_prompts = [p for p in prompts if search_query.lower() in p.get('topic', '').lower()]
    st.markdown(f"Showing **{len(filtered_prompts)}** of **{len(prompts)}** prompts.")

    for prompt in filtered_prompts:
        with st.expander(f"**{prompt['topic']}** ({prompt['content_type']} for {prompt['platform']})"):
            render_prompt_package(prompt, database_name, is_in_library=True, prompts_config=prompts_config)

def render_guidelines():
    st.header("📄 PromptBase Submission Guidelines")
    st.markdown("""
    ### Key Guidelines for Success
    1.  **Be a Template:** Use `[VARIABLES]` to let users adapt your prompt. A good template is flexible.
    2.  **Have a High Use-Case:** Create prompts for real-world needs (e.g., logos, marketing, t-shirt designs).
    3.  **Develop a Unique Style:** Make prompts that produce a distinctive, hard-to-replicate style. This is your signature.
    4.  **Provide Diverse Examples:** Show off the prompt's flexibility with varied examples. Don't just change one word.
    5.  **Avoid Common Pitfalls:** Don't be too niche, too simple, or have inconsistent outputs. Avoid generic terms like "4K, 8K, high quality".
    """)