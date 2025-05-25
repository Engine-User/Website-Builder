# app.py - React Website Builder (CDN Preview) with Sidebar Chat, Tabs, and New Window Link
import streamlit as st
import os
from pathlib import Path
import json
import time
from dotenv import load_dotenv
import re  # For regex used in CSS injection
import urllib.parse  # For URL encoding
import requests  # For requests library

# --- Configuration ---
st.set_page_config(layout="wide", page_title="AI Web Builder (React CDN)")
load_dotenv()  # Load environment variables from .env file FIRST

# --- Constants ---
WORKSPACE_DIR = Path("workspace")  # Directory for generated web files
WORKSPACE_DIR.mkdir(exist_ok=True)
CSS_FILENAME = "style.css"  # Conventional CSS filename for injection

# --- Groq API Configuration ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("🔴 Groq API Key not found. Please ensure GROQ_API_KEY is set in your .env file.")
    st.stop()

model_name = "llama-3.3-70b-versatile"
st.sidebar.caption(f"Using Model (via requests): `{model_name}`")  # Updated caption

# --- Session State Initialization ---
if "messages" not in st.session_state: st.session_state.messages = []
if "selected_file" not in st.session_state: st.session_state.selected_file = None
if "file_content" not in st.session_state: st.session_state.file_content = ""
if "rendered_html" not in st.session_state: st.session_state.rendered_html = ""
if "last_prompt" not in st.session_state: st.session_state.last_prompt = ""
if "workspace_reset_needed" not in st.session_state: st.session_state.workspace_reset_needed = False
# rendered_for_{filename} marker is added/removed dynamically

# --- Helper Functions ---
def get_workspace_files():
    try: return sorted([f.name for f in WORKSPACE_DIR.iterdir() if f.is_file()])
    except Exception as e: st.error(f"Error listing workspace files: {e}"); return []

def read_file_content(filename):
    if not filename: return None
    if ".." in filename or filename.startswith(("/", "\\")): return None
    filepath = WORKSPACE_DIR / filename
    try:
        with open(filepath, "r", encoding="utf-8") as f: return f.read()
    except FileNotFoundError: return None
    except Exception as e: st.error(f"Error reading file '{filename}': {e}"); return None

def save_file_content(filename, content):
    if not filename: return False
    if ".." in filename or filename.startswith(("/", "\\")): return False
    filepath = WORKSPACE_DIR / filename
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f: f.write(content); return True
    except Exception as e: st.error(f"Error saving file '{filename}': {e}"); return False

def delete_file(filename):
    if not filename: return False
    if ".." in filename or filename.startswith(("/", "\\")): return False
    filepath = WORKSPACE_DIR / filename
    try:
        os.remove(filepath)
        if st.session_state.selected_file == filename:  # Clear state if selected file is deleted
            st.session_state.selected_file = None
            st.session_state.file_content = ""
            st.session_state.rendered_html = ""
            st.session_state.pop(f"rendered_for_{filename}", None)
        return True
    except FileNotFoundError: st.warning(f"File '{filename}' not found for deletion."); return False
    except Exception as e: st.error(f"Error deleting file '{filename}': {e}"); return False

def clear_workspace():
    """Clear all files in the workspace directory."""
    try:
        for file_path in WORKSPACE_DIR.iterdir():
            if file_path.is_file():
                os.remove(file_path)
        # Reset session state related to files
        st.session_state.selected_file = None
        st.session_state.file_content = ""
        st.session_state.rendered_html = ""
        # Clear any rendered_for markers
        keys_to_remove = [key for key in st.session_state.keys() if key.startswith("rendered_for_")]
        for key in keys_to_remove:
            st.session_state.pop(key, None)
        return True
    except Exception as e:
        st.error(f"Error clearing workspace: {e}")
        return False

# --- AI Interaction & File Ops ---
def parse_and_execute_commands(ai_response_text):
    parsed_commands = []
    try:
        # Clean up the response text
        response_text_cleaned = ai_response_text.strip()
        
        # Handle various code block formats
        if response_text_cleaned.startswith("```json") and response_text_cleaned.endswith("```"):
            response_text_cleaned = response_text_cleaned[7:-3].strip()
        elif response_text_cleaned.startswith("```") and response_text_cleaned.endswith("```"):
            response_text_cleaned = response_text_cleaned[3:-3].strip()
        
        # Fix common JSON escaping issues
        # This helps with quotes inside HTML/CSS content that might not be properly escaped
        try:
            # First attempt to parse as is
            commands = json.loads(response_text_cleaned)
        except json.JSONDecodeError as e:
            # If that fails, try to fix common issues with quotes in HTML/CSS
            # Look for unescaped quotes in content fields
            fixed_json = re.sub(r'("content": ")(.+?)(")', 
                               lambda m: m.group(1) + m.group(2).replace('"', '\\"') + m.group(3), 
                               response_text_cleaned, 
                               flags=re.DOTALL)
            
            # Try again with the fixed JSON
            try:
                commands = json.loads(fixed_json)
            except json.JSONDecodeError:
                # If still failing, try a more aggressive approach for HTML attributes with quotes
                # This regex looks for HTML attributes with unescaped quotes
                fixed_json = re.sub(r'(content=".+?)(\s+\w+=")(.*?)(")', 
                                   lambda m: m.group(1) + m.group(2) + m.group(3).replace('"', '\\"') + m.group(4), 
                                   fixed_json, 
                                   flags=re.DOTALL)
                commands = json.loads(fixed_json)
        
        if not isinstance(commands, list): 
            return [{"action": "chat", "content": f"AI (Non-list JSON): {ai_response_text}"}]
        
        # If workspace reset is needed, clear all files before processing new commands
        if st.session_state.workspace_reset_needed:
            clear_workspace()
            st.session_state.workspace_reset_needed = False
            
        for command in commands:
            if not isinstance(command, dict): 
                parsed_commands.append({"action": "chat", "content": f"Skipped: {command}"}); 
                continue
                
            action=command.get("action")
            filename=command.get("filename")
            content=command.get("content")
            
            parsed_commands.append(command)
            
            if action=="create_update":
                if filename and content is not None:
                    if not save_file_content(filename, content): 
                        st.warning(f"Failed save '{filename}'.")
                else: 
                    st.warning(f"⚠️ Invalid 'create_update': {command}")
            elif action=="delete":
                if filename: 
                    delete_file(filename)
                else: 
                    st.warning(f"⚠️ Invalid 'delete': {command}")
            elif action=="chat": 
                pass
            else: 
                st.warning(f"⚠️ Unknown action '{action}': {command}")
                
        return parsed_commands
    except json.JSONDecodeError as e:
        st.error(f"🔴 Invalid JSON: {e}\nTxt:\n'{ai_response_text[:500]}...'")
        # Try to salvage what we can by manually extracting and saving files
        try:
            # Look for patterns that might indicate file content
            html_match = re.search(r'"filename":\s*"(index\.html)".*?"content":\s*"(<!DOCTYPE.*?)</html>"', 
                                  ai_response_text, re.DOTALL)
            css_match = re.search(r'"filename":\s*"(style\.css)".*?"content":\s*"(/\*.*?\*/.*?)"', 
                                 ai_response_text, re.DOTALL)
            js_match = re.search(r'"filename":\s*"(script\.js)".*?"content":\s*"(.*?)"', 
                                ai_response_text, re.DOTALL)
            
            salvaged = False
            if html_match:
                html_content = html_match.group(2).replace('\\n', '\n').replace('\\"', '"')
                save_file_content("index.html", html_content)
                salvaged = True
                
            if css_match:
                css_content = css_match.group(2).replace('\\n', '\n').replace('\\"', '"')
                save_file_content("style.css", css_content)
                salvaged = True
                
            if js_match:
                js_content = js_match.group(2).replace('\\n', '\n').replace('\\"', '"')
                save_file_content("script.js", js_content)
                salvaged = True
                
            if salvaged:
                return [{"action": "chat", "content": f"Recovered files from invalid JSON. Please check the workspace for extracted files."}]
        except Exception as salvage_error:
            st.error(f"Failed to salvage content: {salvage_error}")
            
        return [{"action": "chat", "content": f"AI(Invalid JSON): {ai_response_text}"}]
    except Exception as e:
        st.error(f"🔴 Error processing commands: {e}")
        return [{"action": "chat", "content": f"Error processing commands: {e}"}]

# --- Updated call_groq Function for Groq API ---
def call_groq(history):
    # Convert history to Groq format
    groq_messages = []
    for msg in history:
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            # Groq API expects "user" and "assistant" roles
            role = msg["role"]  # Groq uses "assistant" role directly
            content = str(msg["content"])
            groq_messages.append({"role": role, "content": content})

    instruction = """
    You are an AI assistant that helps users create web pages and simple web applications.
    Your goal is to generate HTML, CSS, JavaScript code, or self-contained React preview files.
    Based on the user's request, you MUST respond ONLY with a valid JSON array containing file operation objects.

    **JSON FORMATTING RULES (VERY IMPORTANT):**
    1.  The entire response MUST be a single JSON array starting with '[' and ending with ']'.
    2.  All keys (like "action", "filename", "content") MUST be enclosed in **double quotes** (").
    3.  All string values (like filenames and the large code content) MUST be enclosed in **double quotes** ("). Single quotes (') or backticks (`) are NOT ALLOWED for keys or string values in the JSON structure.
    4.  Special characters within the "content" string (like newlines, double quotes inside the code) MUST be properly escaped (e.g., use '\\n' for newlines, '\\"' for double quotes).

    **EXAMPLE of Correct JSON action object:**
    {
        "action": "create_update",
        "filename": "example.html",
        "content": "<!DOCTYPE html>\\n<html>\\n<head>\\n  <title>Example</title>\\n</head>\\n<body>\\n  <h1>Hello World!</h1>\\n  <p>This contains a \\"quote\\" example.</p>\\n</body>\\n</html>"
    }

    Possible action objects in the JSON array:
    - {"action": "create_update", "filename": "path/to/file.ext", "content": "file content string here..."}
    - {"action": "delete", "filename": "path/to/file.ext"}
    - {"action": "chat", "content": "Your helpful answer string here..."}

    **VERY IMPORTANT - UPDATING FILES:**
    If the user asks you to modify an existing file (e.g., "add a footer to index.html", "change the button color in style.css"), you MUST provide the **ENTIRE**, complete, updated file content within the 'content' field of the 'create_update' action object, following all JSON formatting rules. Do NOT provide only the changed lines or a diff.

    **REACT PREVIEWS:**
    If the user asks for a simple React component/app to preview, generate a SINGLE self-contained HTML file (e.g., 'react_preview.html') using 'create_update'. This file MUST use CDN links for React/ReactDOM/Babel, have a <div id="root">, include JSX in a <script type="text/babel"> tag, render to the root, and include CSS in <style> tags within the <head>. (Ensure valid JSON).

    **GENERAL:**
    Use standard filenames ('index.html', 'style.css', 'script.js'). The standard CSS file for injection is 'style.css'. If unsure, ask the user. Respond ONLY with the JSON array. Use 'chat' action for questions or explanations.
    
    **ESCAPING QUOTES:**
    When including HTML or CSS with attributes that contain quotes, you MUST properly escape all double quotes within the content. For example:
    - HTML: <div class="container"> should be written as <div class=\\"container\\">
    - CSS: font-family: "Times New Roman" should be written as font-family: \\"Times New Roman\\"
    """
    current_files = get_workspace_files()
    file_list_prompt = f"Current files in workspace: {', '.join(current_files) if current_files else 'None'}"
    
    # Add system message at the beginning
    system_message = {
        "role": "system", 
        "content": instruction
    }
    
    # Prepare messages for Groq API
    messages = [system_message]
    
    # Add a confirmation message from assistant to acknowledge the instructions
    messages.append({
        "role": "assistant", 
        "content": "[{\"action\": \"chat\", \"content\": \"Okay, I understand the strict JSON formatting rules (double quotes, escaping) and the need to provide full file content on updates. I will respond only with the valid JSON array. Ready.\"}]"
    })
    
    # Add user history
    for msg in groq_messages:
        messages.append(msg)
    
    try:
        # Groq API endpoint
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.5,
            "max_tokens": 8000  # Increased token limit to handle larger responses
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code != 200:
            if response.status_code == 429:
                st.error("🔴 Groq API Rate Limit Exceeded.")
            elif response.status_code == 401 or response.status_code == 403:
                st.error("🔴 Groq API call failed: Invalid API Key or Permissions Issue.")
            else:
                st.error(f"🔴 Groq API call failed with status {response.status_code}: {response.text}")
            error_content = f"Error calling AI: {response.text}".replace('"',"'")
            return json.dumps([{"action": "chat", "content": error_content}])
        
        response_json = response.json()
        
        # Check if the response contains the expected structure
        if 'choices' in response_json and len(response_json['choices']) > 0:
            if 'message' in response_json['choices'][0] and 'content' in response_json['choices'][0]['message']:
                # Extracting the response text from Groq API structure
                response_text = response_json['choices'][0]['message']['content']
                
                # Pre-process the response to fix common JSON issues
                # Replace unescaped quotes in HTML attributes
                response_text = re.sub(r'(<[^>]*?)="([^"]*?)"', 
                                      lambda m: m.group(1) + '=\\"' + m.group(2) + '\\"', 
                                      response_text)
                
                return response_text
            else:
                st.error("🔴 Unexpected Groq API response structure.")
                return json.dumps([{"action": "chat", "content": "Error: Unexpected API response structure"}])
        else:
            st.error("🔴 Empty or invalid Groq API response.")
            return json.dumps([{"action": "chat", "content": "Error: Empty or invalid API response"}])
    except requests.exceptions.RequestException as e:
        st.error(f"🔴 Groq API call failed: {e}")
        error_content = f"Error calling AI: {str(e)}".replace('"',"'")
        return json.dumps([{"action": "chat", "content": error_content}])
    except Exception as e:
        st.error(f"🔴 An unexpected error occurred during Groq API call: {e}")
        error_content = f"Error calling AI: {str(e)}".replace('"',"'")
        return json.dumps([{"action": "chat", "content": error_content}])

# --- Streamlit UI Layout ---

# --- Sidebar: Chat Interface ---
with st.sidebar:
    st.header("💬 Chat with AI")
    st.markdown("Ask the AI to create or modify web files (HTML, CSS, JS, React CDN Previews).")
    st.caption(f"Using Model: `{model_name}`")  # Display model name
    chat_container = st.container(height=500)
    with chat_container:
        if st.session_state.messages:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    if isinstance(message.get("content"), list) and message.get("role") == "assistant":
                        display_text = ""; chat_messages = []
                        for command in message["content"]:
                            if not isinstance(command, dict): continue
                            action = command.get("action"); filename = command.get("filename")
                            if action == "create_update": display_text += f"📝 Create/Update: `{filename}`\n"
                            elif action == "delete": display_text += f"🗑️ Delete: `{filename}`\n"
                            elif action == "chat": chat_messages.append(command.get('content', '...'))
                            else: display_text += f"⚠️ {command.get('content', f'Unknown action: {action}')}\n"
                        final_display = (display_text + "\n".join(chat_messages)).strip()
                        if not final_display: final_display = "(No action)"
                        st.markdown(final_display)
                    else: st.write(str(message.get("content", "")))
        else: st.info("Chat history empty.")
    if prompt := st.chat_input("e.g., Create index.html with a title"):
        # Set workspace_reset_needed flag to true when a new prompt is received
        # This will trigger workspace clearing before processing new commands
        if prompt != st.session_state.last_prompt:
            st.session_state.workspace_reset_needed = True
            st.session_state.last_prompt = prompt
            
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("🧠 AI Thinking..."):
            ai_response_text = call_groq(st.session_state.messages)
            executed_commands = parse_and_execute_commands(ai_response_text)
            st.session_state.messages.append({"role": "assistant", "content": executed_commands})
            st.rerun()

# --- Main Area: Tabs ---
st.title("🤖 AI Web Builder (React CDN Preview)")
tab1, tab2 = st.tabs([" 📂 Workspace ", " 👀 Preview "])

with tab1:  # --- Workspace Tab ---
    st.header("Workspace & Editor")
    st.markdown("---")
    st.subheader("Files")
    available_files = get_workspace_files()
    if not available_files: st.info(f"Workspace '{WORKSPACE_DIR.name}' empty.")
    current_selection_index = 0; options = [None] + available_files
    if st.session_state.selected_file in options:
        try: current_selection_index = options.index(st.session_state.selected_file)
        except ValueError: st.session_state.selected_file = None
    selected_file_option = st.selectbox("Select file:", options=options, format_func=lambda x: "--- Select ---" if x is None else x, key="ws_file_select", index=current_selection_index)
    st.subheader("Edit Code")
    editor_key = f"editor_{st.session_state.selected_file or 'none'}"
    if selected_file_option != st.session_state.selected_file:
        st.session_state.selected_file = selected_file_option
        st.session_state.file_content = read_file_content(st.session_state.selected_file) or "" if st.session_state.selected_file else ""
        st.session_state.rendered_html = ""; st.session_state.pop(f"rendered_for_{st.session_state.selected_file}", None)
        st.rerun()
    if st.session_state.selected_file:
        st.caption(f"Editing: `{st.session_state.selected_file}`")
        file_ext = Path(st.session_state.selected_file).suffix.lower()
        lang_map = {".html": "html", ".css": "css", ".js": "javascript", ".py":"python", ".md": "markdown", ".json": "json", ".jsx":"javascript", ".vue":"vue", ".svelte":"svelte", ".txt":"text"}
        language = lang_map.get(file_ext)
        edited_content = st.text_area("Code Editor", value=st.session_state.file_content, height=400, key=editor_key, label_visibility="collapsed", args=(language,))
        if edited_content != st.session_state.file_content:
             if st.button("💾 Save Manual Changes"):
                if save_file_content(st.session_state.selected_file, edited_content):
                    st.session_state.file_content = edited_content; st.success(f"Saved: `{st.session_state.selected_file}`")
                    st.session_state.rendered_html = ""; st.session_state.pop(f"rendered_for_{st.session_state.selected_file}", None)
                    time.sleep(0.5); st.rerun()
                else: st.error("Failed to save.")
    else:
        st.info("Select a file to edit.")
        st.text_area("Code Editor", value="Select a file...", height=400, key="editor_placeholder", disabled=True, label_visibility="collapsed")

with tab2:  # --- Preview Tab ---
    st.header("👀 Live Preview")
    st.markdown("---")
    css_applied_info = ""  # Initialize to prevent NameError

    if st.session_state.selected_file:
        if st.session_state.selected_file.lower().endswith(('.html', '.htm')):
            current_file_content_for_preview = read_file_content(st.session_state.selected_file)
            rendered_marker_key = f"rendered_for_{st.session_state.selected_file}"
            needs_render_update = False
            if current_file_content_for_preview is not None:
                needs_render_update = (not st.session_state.rendered_html or 
                                      rendered_marker_key not in st.session_state or 
                                      st.session_state[rendered_marker_key] != current_file_content_for_preview)
                if needs_render_update:
                    # Check for CSS file and inject if found
                    css_content = read_file_content(CSS_FILENAME)
                    if css_content:
                        # Simple CSS injection - find </head> and insert style before it
                        if "</head>" in current_file_content_for_preview:
                            current_file_content_for_preview = current_file_content_for_preview.replace(
                                "</head>", f"<style>\n{css_content}\n</style>\n</head>")
                            css_applied_info = f"✅ CSS from `{CSS_FILENAME}` injected."
                    st.session_state.rendered_html = current_file_content_for_preview
                    st.session_state[rendered_marker_key] = current_file_content_for_preview
            
            # Display the preview
            if st.session_state.rendered_html:
                st.components.v1.html(st.session_state.rendered_html, height=600, scrolling=True)
                if css_applied_info: st.caption(css_applied_info)
                
                # Open in new window option
                encoded_html = urllib.parse.quote(st.session_state.rendered_html)
                new_window_url = f"data:text/html,{encoded_html}"
                st.markdown(f'<a href="{new_window_url}" target="_blank">🔗 Open in New Window</a>', unsafe_allow_html=True)
            else:
                st.warning("Preview failed to render.")
        else:
            st.info(f"Select an HTML file to preview. Current file: `{st.session_state.selected_file}`")
    else:
        st.info("Select a file to preview.")

# Add a button to manually clear workspace if needed
with st.sidebar:
    st.markdown("---")
    if st.button("🗑️ Clear Workspace"):
        if clear_workspace():
            st.success("Workspace cleared successfully!")
            st.session_state.workspace_reset_needed = False
            time.sleep(0.5)
            st.rerun()
        else:
            st.error("Failed to clear workspace.")
