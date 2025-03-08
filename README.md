PromptBase Template Generator
Generate high-quality, market-ready prompt templates aligned with PromptBase submission guidelines using Gemini AI.

This Streamlit application is designed to help you create professional prompt templates for various AI platforms like Midjourney, DALL-E, Stable Diffusion, and more. It leverages the power of the Gemini AI model to generate structured prompt templates tailored for different content types (image, text, video), styles, and use cases. The application also includes a local prompt library to save and manage your generated templates.

Features
Prompt Template Generation: Create specialized prompt templates for images, text, and videos using the Gemini AI API.
Platform Specificity: Generate templates optimized for different AI platforms (Midjourney, DALL-E, Stable Diffusion, etc.).
Style and Use Case Customization: Tailor prompts by specifying content style and intended use case.
Prompt Validation: Includes a built-in quality check to validate generated prompts against PromptBase submission guidelines.
Example Generation: Provides diverse example prompts based on the generated template.
Usage Tips & Testing Guidance: Offers helpful tips and testing instructions to ensure high-quality outputs from your prompts.
Local Prompt Library: Save and manage your generated prompt templates in a local SQLite database. Browse, view, and organize your prompts within the application.
Downloadable Prompt Packages: Export your generated prompts as JSON files to easily share or submit to platforms like PromptBase.
PromptBase Guidelines: Integrated tab to view PromptBase submission guidelines directly within the application.
Installation
Clone the repository (if applicable) or download the script.py file.

Install Python Dependencies: Ensure you have Python 3.7 or higher installed. Then, install the required Python libraries using pip:

pip install streamlit google-generativeai
You might also need to install pysqlite3 explicitly if sqlite3 is not readily available in your Python environment:

pip install pysqlite3
Get a Gemini API Key:

You need an API key to use the Gemini AI model.
Set the Gemini API Key:

Option 1: Streamlit Sidebar Input (For local testing ): You can enter your Gemini API key in the sidebar input field within the Streamlit application itself when you run it.
How to Run the Application
Navigate to the project directory in your terminal where you saved script.py.

Run the Streamlit application using the command:

streamlit run script.py
Usage
The application has three main tabs:

Create Template:

Configuration Sidebar: Enter your Gemini API key in the sidebar.
Prompt Parameters: Fill in the input fields for:
Prompt Topic: The subject of your prompt template (e.g., "Cyberpunk Cityscapes").
Content Type: Select the type of content (Image, Text, Video).
AI Platform: Choose the target AI platform (Midjourney, DALL-E, etc.).
Style: Select a style preference (e.g., "Photorealistic", "Minimalist", "Academic").
Primary Use Case: Choose the intended application (e.g., "Marketing Materials", "Social Media Content").
Generate Button: Click "Generate Professional Prompt Template" to generate the prompt template.
Results Display: The generated prompt template, variables, examples, tips, validation results, and testing guidance will be displayed in expandable sections.
Download Button: "📥 Download Prompt Package" to download the prompt data as a JSON file.
Save to Library Button: "💾 Save to Library" to save the generated prompt to your local prompt library.
Prompt Library:

Browse Saved Prompts: View a list of your saved prompt templates. Each prompt is initially collapsed for easy browsing.
Expand Prompts: Click on a prompt header to expand and view its full details, including the template, variables, examples, tips, validation, and testing guidance.
Guidelines:

PromptBase Submission Guidelines: Displays key guidelines for creating successful prompt templates for platforms like PromptBase. Review these guidelines to optimize your prompt templates for marketability.
