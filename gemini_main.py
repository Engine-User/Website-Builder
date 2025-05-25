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
import base64  # For image encoding
import zipfile  # For creating zip files
import io  # For in-memory file operations
# OpenRouter API will be used instead of Gemini API

# --- Configuration ---
st.set_page_config(layout="wide", page_title="AI Web Builder", initial_sidebar_state="expanded")
load_dotenv()  # Load environment variables from .env file FIRST

# --- Constants ---
WORKSPACE_DIR = Path("workspace")  # Directory for generated web files
WORKSPACE_DIR.mkdir(exist_ok=True)
CSS_FILENAME = "style.css"  # Conventional CSS filename for injection

# --- Custom CSS for enhanced UI ---
def get_custom_css():
    return """
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&family=Fira+Code:wght@400;500&display=swap');
    
    :root {
        --primary-color: #0a192f;
        --secondary-color: #112240;
        --accent-color: #64ffda;
        --text-color: #e6f1ff;
        --highlight-color: #ffd700;
        --gradient-light: linear-gradient(135deg, #112240, #233554);
        --gradient-dark: linear-gradient(135deg, #0a192f, #112240);
        --code-green: #64ffda;
        --code-glow: 0 0 5px rgba(100, 255, 218, 0.5);
        --gold: #ffd700;
        --silver: #c0c0c0;
    }
    
    /* Global Styles */
    .stApp {
        background-color: var(--primary-color);
        color: var(--text-color);
        font-family: 'Poppins', sans-serif;
    }
    
    /* Main Title Styling */
    .main-title {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        background: linear-gradient(90deg, var(--accent-color), var(--gold));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 4rem;
        margin-bottom: 1.5rem;
        text-align: center;
        text-shadow: 0 0 15px rgba(100, 255, 218, 0.3);
        letter-spacing: 2px;
        position: relative;
        padding: 10px;
    }
    
    .main-title::after {
        content: "";
        position: absolute;
        bottom: 0;
        left: 25%;
        width: 50%;
        height: 3px;
        background: linear-gradient(90deg, transparent, var(--accent-color), var(--gold), transparent);
    }
    
    /* Subtitle Styling */
    .subtitle {
        font-family: 'Poppins', sans-serif;
        font-weight: 300;
        color: var(--text-color);
        font-size: 1.2rem;
        text-align: center;
        margin-bottom: 2rem;
        opacity: 0.8;
    }
    
    /* 3D Input Box */
    .stTextInput > div > div > input {
        background-color: #112240 !important;
        color: var(--code-green) !important;
        font-family: 'Fira Code', monospace !important;
        font-size: 1.1rem !important;
        border: 2px solid #233554 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3), inset 0 1px 2px rgba(255, 255, 255, 0.05) !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--accent-color) !important;
        box-shadow: 0 4px 12px rgba(100, 255, 218, 0.2), inset 0 1px 2px rgba(255, 255, 255, 0.05), 0 0 5px rgba(100, 255, 218, 0.3) !important;
    }
    
    /* Chat Input Box */
    .stChatInputContainer {
        background-color: #112240 !important;
        border: 2px solid #233554 !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3), inset 0 1px 2px rgba(255, 255, 255, 0.05) !important;
    }
    
    .stChatInputContainer:focus-within {
        border-color: var(--accent-color) !important;
        box-shadow: 0 4px 12px rgba(100, 255, 218, 0.2), inset 0 1px 2px rgba(255, 255, 255, 0.05), 0 0 5px rgba(100, 255, 218, 0.3) !important;
    }
    
    .stChatInputContainer textarea {
        color: var(--code-green) !important;
        font-family: 'Fira Code', monospace !important;
        font-size: 1.1rem !important;
    }
    
    /* Button Styling */
    .stButton > button {
        background: var(--gradient-light) !important;
        color: var(--text-color) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.5rem 1.5rem !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 500 !important;
        letter-spacing: 1px !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.3s ease !important;
        text-transform: uppercase !important;
        border-left: 3px solid var(--accent-color) !important;
    }
    
    .stButton > button:hover {
        background: var(--gradient-dark) !important;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.4) !important;
        transform: translateY(-2px) !important;
        border-left: 3px solid var(--gold) !important;
    }
    
    .stButton > button:active {
        transform: translateY(1px) !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* 3D Download Button */
    .download-btn {
        display: inline-block;
        background: var(--gradient-light);
        color: var(--accent-color);
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 1rem;
        letter-spacing: 1px;
        text-transform: uppercase;
        padding: 0.8rem 1.5rem;
        border-radius: 8px;
        border: none;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3), 
                    inset 1px 1px 1px rgba(255, 255, 255, 0.05),
                    inset -1px -1px 1px rgba(0, 0, 0, 0.2);
        transition: all 0.2s ease;
        cursor: pointer;
        text-decoration: none;
        position: relative;
        overflow: hidden;
        z-index: 1;
        border-left: 3px solid var(--accent-color);
    }
    
    .download-btn:before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
        transition: all 0.5s ease;
        z-index: -1;
    }
    
    .download-btn:hover:before {
        left: 100%;
    }
    
    .download-btn:hover {
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.4),
                    inset 1px 1px 1px rgba(255, 255, 255, 0.05),
                    inset -1px -1px 1px rgba(0, 0, 0, 0.2);
        transform: translateY(-2px);
        color: var(--gold);
        text-shadow: 0 0 5px rgba(255, 215, 0, 0.3);
        border-left: 3px solid var(--gold);
    }
    
    .download-btn:active {
        transform: translateY(1px);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3),
                    inset 1px 1px 1px rgba(0, 0, 0, 0.2),
                    inset -1px -1px 1px rgba(255, 255, 255, 0.05);
    }
    
    .download-btn i {
        margin-right: 8px;
    }
    
    /* Tabs Styling */
    .stTabs {
        background: var(--secondary-color) !important;
        border-radius: 10px !important;
        padding: 0.5rem !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
        margin-bottom: 1.5rem !important;
        border: 1px solid rgba(100, 255, 218, 0.1) !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px !important;
        background-color: transparent !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: var(--gradient-dark) !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 500 !important;
        color: var(--text-color) !important;
        border: none !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.3s ease !important;
        border-bottom: 2px solid transparent !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--gradient-light) !important;
        color: var(--accent-color) !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3) !important;
        border-bottom: 2px solid var(--accent-color) !important;
    }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: var(--secondary-color) !important;
        border-right: 1px solid rgba(100, 255, 218, 0.1) !important;
        padding: 1.5rem 1rem !important;
    }
    
    /* Sidebar Brand Logo */
    .sidebar-brand {
        text-align: center;
        margin-bottom: 20px;
        padding-bottom: 15px;
        border-bottom: 1px solid rgba(100, 255, 218, 0.1);
        position: relative;
    }
    
    .sidebar-brand h1 {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        font-size: 2.2rem;
        letter-spacing: 2px;
        margin: 0;
        background: linear-gradient(90deg, var(--accent-color), var(--gold));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 0 0 10px rgba(100, 255, 218, 0.2);
    }
    
    .sidebar-brand::after {
        content: "";
        position: absolute;
        bottom: -1px;
        left: 25%;
        width: 50%;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--accent-color), var(--gold), transparent);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
        color: var(--accent-color) !important;
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: 1px !important;
    }
    
    /* Chat Message Styling */
    [data-testid="stChatMessage"] {
        background: var(--gradient-dark) !important;
        border-radius: 10px !important;
        padding: 1rem !important;
        margin-bottom: 1rem !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
        border-left: 3px solid var(--accent-color) !important;
    }
    
    /* Code Editor Styling */
    .stTextArea textarea {
        background-color: #112240 !important;
        color: #e6f1ff !important;
        font-family: 'Fira Code', monospace !important;
        border: 2px solid #233554 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    
    /* Select Box Styling */
    .stSelectbox [data-baseweb="select"] {
        background-color: var(--secondary-color) !important;
        border: 2px solid #233554 !important;
        border-radius: 8px !important;
    }
    
    .stSelectbox [data-baseweb="select"] [data-baseweb="tag"] {
        background-color: var(--accent-color) !important;
    }
    
    /* Spinner Animation */
    .stSpinner > div {
        border-color: var(--accent-color) transparent transparent !important;
    }
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--primary-color);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--accent-color);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--gold);
    }
    
    /* Loading Animation */
    @keyframes pulse {
        0% { opacity: 0.6; }
        50% { opacity: 1; }
        100% { opacity: 0.6; }
    }
    
    .loading-text {
        font-family: 'Space Grotesk', sans-serif;
        color: var(--accent-color);
        animation: pulse 1.5s infinite;
        text-align: center;
        margin: 1rem 0;
        font-size: 1.2rem;
        letter-spacing: 1px;
    }
    
    /* Section Headers */
    .section-header {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        color: var(--accent-color);
        font-size: 1.8rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid var(--accent-color);
    }
    
    /* Info Box */
    .info-box {
        background: var(--gradient-dark);
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 3px solid var(--accent-color);
    }
    
    /* New Window Link */
    .new-window-link {
        display: inline-block;
        background: var(--gradient-dark);
        color: var(--text-color);
        text-decoration: none;
        padding: 0.7rem 1.2rem;
        border-radius: 8px;
        font-family: 'Space Grotesk', sans-serif;
        margin-top: 1rem;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
        border-left: 3px solid var(--accent-color);
    }
    
    .new-window-link:hover {
        background: var(--gradient-light);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.4);
        transform: translateY(-2px);
        color: var(--accent-color);
        border-left: 3px solid var(--gold);
    }
    
    .new-window-link:active {
        transform: translateY(1px);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2.5rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 0.5rem 1rem !important;
        }
        
        .sidebar-brand h1 {
            font-size: 1.8rem;
        }
    }
    
    /* Input Container Styling */
    .input-container {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 20px;
    }
    
    .input-container > div:first-child {
        flex-grow: 1;
    }
    
    /* Haptic Feedback Animation */
    @keyframes haptic-feedback {
        0% { transform: scale(1); }
        50% { transform: scale(0.98); }
        100% { transform: scale(1); }
    }
    
    .haptic-feedback {
        animation: haptic-feedback 0.15s ease;
    }
    
    /* OpenRouter Badge */
    .openrouter-badge {
        display: inline-block;
        background: linear-gradient(135deg, #0a84ff, #00c3ff);
        color: white;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
        font-size: 0.8rem;
        padding: 0.3rem 0.6rem;
        border-radius: 4px;
        margin-left: 8px;
        vertical-align: middle;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    """

# Apply custom CSS
st.markdown(f'<style>{get_custom_css()}</style>', unsafe_allow_html=True)

# --- OpenRouter API Configuration ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    st.error("🔴 OpenRouter API Key not found. Please ensure OPENROUTER_API_KEY is set in your .env file.")
    st.stop()

# OpenRouter API settings
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_CHAT_URL = f"{OPENROUTER_BASE_URL}/chat/completions"
model_name = "anthropic/claude-3-opus"

# Site information for OpenRouter rankings (optional)
SITE_URL = os.getenv("SITE_URL", "https://example.com")
SITE_NAME = os.getenv("SITE_NAME", "AI Web Builder")

# --- Session State Initialization ---
if "messages" not in st.session_state: st.session_state.messages = []
if "selected_file" not in st.session_state: st.session_state.selected_file = None
if "file_content" not in st.session_state: st.session_state.file_content = ""
if "rendered_html" not in st.session_state: st.session_state.rendered_html = ""
if "last_prompt" not in st.session_state: st.session_state.last_prompt = ""
if "workspace_reset_needed" not in st.session_state: st.session_state.workspace_reset_needed = False
if "active_tab" not in st.session_state: st.session_state.active_tab = "about"
if "haptic_feedback" not in st.session_state: st.session_state.haptic_feedback = False
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

def create_download_zip():
    """Create a zip file containing all files in the workspace directory."""
    try:
        # Create a BytesIO object
        zip_buffer = io.BytesIO()
        
        # Create a zip file
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for file_path in WORKSPACE_DIR.iterdir():
                if file_path.is_file():
                    # Add file to zip
                    zip_file.write(file_path, arcname=file_path.name)
        
        # Reset buffer position
        zip_buffer.seek(0)
        return zip_buffer
    except Exception as e:
        st.error(f"Error creating zip file: {e}")
        return None

def get_download_link(buffer, filename="project.zip", text="Download Project"):
    """Generate a download link for a file."""
    b64 = base64.b64encode(buffer.getvalue()).decode()
    href = f'<a href="data:application/zip;base64,{b64}" download="{filename}" class="download-btn" onclick="this.classList.add(\'haptic-feedback\'); setTimeout(() => this.classList.remove(\'haptic-feedback\'), 150);"><i class="fas fa-download"></i> {text}</a>'
    return href

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

# --- Updated call_gemini Function for OpenRouter API ---
def call_gemini(instruction, history=[]):
    # Convert history to OpenRouter format
    openrouter_messages = []
    
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
    
    try:
        # Prepare messages for OpenRouter API
        messages = [
            {"role": "system", "content": instruction},
            {"role": "assistant", "content": "I understand the strict JSON formatting rules (double quotes, escaping) and the need to provide full file content on updates. I will respond only with the valid JSON array. Ready."},
            {"role": "user", "content": file_list_prompt}
        ]
        
        # Add user history
        for msg in history:
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                if msg["role"] == "user":
                    messages.append({"role": "user", "content": str(msg["content"])})
                # We don't need to send assistant messages back to the model
        
        # Add final instruction
        messages.append({"role": "user", "content": "Based on the above conversation, generate the appropriate JSON response following all the formatting rules."})
        
        # Make the API request to OpenRouter
        response = requests.post(
            url=OPENROUTER_CHAT_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": SITE_URL,
                "X-Title": SITE_NAME
            },
            data=json.dumps({
                "model": model_name,
                "messages": messages
            })
        )
        
        # Check if the request was successful
        if response.status_code == 200:
            response_json = response.json()
            if "choices" in response_json and len(response_json["choices"]) > 0:
                response_text = response_json["choices"][0]["message"]["content"]
                
                # Pre-process the response to fix common JSON issues
                # Replace unescaped quotes in HTML attributes
                response_text = re.sub(r'(<[^>]*?)="([^"]*?)"', 
                                      lambda m: m.group(1) + '=\\"' + m.group(2) + '\\"', 
                                      response_text)
                
                return response_text
            else:
                st.error("🔴 Invalid response structure from OpenRouter API.")
                return json.dumps([{"action": "chat", "content": "Error: Invalid response structure"}])
        else:
            st.error(f"🔴 OpenRouter API call failed with status {response.status_code}: {response.text}")
            error_content = f"Error calling AI: {response.text}".replace('"',"'")
            return json.dumps([{"action": "chat", "content": error_content}])
            
    except Exception as e:
        st.error(f"🔴 An error occurred during OpenRouter API call: {e}")
        error_content = f"Error calling AI: {str(e)}".replace('"',"'")
        return json.dumps([{"action": "chat", "content": error_content}])

# --- Sidebar: Extended with About and How to Use sections ---
with st.sidebar:
    # Logo or Brand
    st.markdown('<div class="sidebar-brand"><h1>AI WEB BUILDER <span class="openrouter-badge">OpenRouter</span></h1></div>', unsafe_allow_html=True)
    
    # Sidebar Tabs
    sidebar_tabs = ["about", "how_to_use", "chat"]
    tab_icons = {
        "about": "ℹ️ About",
        "how_to_use": "📚 How to Use",
        "chat": "💬 Chat with AI"
    }
    
    selected_tab = st.radio("Navigation", options=sidebar_tabs, format_func=lambda x: tab_icons.get(x, x), key="sidebar_tabs", label_visibility="visible")
    st.session_state.active_tab = selected_tab
    
    st.markdown("---")
    
    # Display content based on selected tab
    if st.session_state.active_tab == "about":
        st.markdown('<h2 style="font-family: \'Space Grotesk\', sans-serif; color: var(--accent-color);">About</h2>', unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
            <p><strong>Made by:</strong> Engineer</p>
            <p><strong>Email:</strong> ggengineerco@gmail.com</p>
            <p><strong>Version:</strong> 1.0.0</p>
            <p><strong>Model:</strong> gemini-1.5-pro</p>
        </div>
        
        <p>AI Web Builder is a powerful tool that helps you create websites and landing pages with just a text description. Simply describe what you want, and the AI will generate the HTML, CSS, and JavaScript code for you.</p>
        
        <p>This tool is perfect for:</p>
        <ul>
            <li>Quickly prototyping website ideas</li>
            <li>Creating landing pages without coding</li>
            <li>Learning web development through AI-generated examples</li>
            <li>Testing different design concepts rapidly</li>
        </ul>
        """, unsafe_allow_html=True)
        
    elif st.session_state.active_tab == "how_to_use":
        st.markdown('<h2 style="font-family: \'Space Grotesk\', sans-serif; color: var(--accent-color);">How to Use</h2>', unsafe_allow_html=True)
        st.markdown("""
        <div class="info-box">
            <p>Follow these steps to create your website:</p>
        </div>
        
        <ol>
            <li><strong>Describe your website</strong> in the input box at the top of the page. Be as detailed as possible about layout, colors, content, and functionality.</li>
            <li><strong>Wait for the AI</strong> to generate your website files. This usually takes a few seconds.</li>
            <li><strong>View the generated files</strong> in the Workspace tab. You can select and edit any file.</li>
            <li><strong>Preview your website</strong> in the Preview tab to see how it looks.</li>
            <li><strong>Make adjustments</strong> by chatting with the AI. You can ask it to modify specific aspects of your website.</li>
            <li><strong>Save your work</strong> by downloading the files or deploying to a hosting service.</li>
        </ol>
        
        <h3>Best Practices:</h3>
        <ul>
            <li>Be specific about design elements like colors, fonts, and layout</li>
            <li>Mention responsive design if you want mobile compatibility</li>
            <li>Specify any interactive elements or animations you want</li>
            <li>For complex websites, build section by section</li>
            <li>Use the Clear Workspace button when starting a completely new project</li>
        </ul>
        """, unsafe_allow_html=True)
        
    elif st.session_state.active_tab == "chat":
        st.markdown('<h2 style="font-family: \'Space Grotesk\', sans-serif; color: var(--accent-color);">Chat with AI</h2>', unsafe_allow_html=True)
        st.caption(f"Using Model: `{model_name}`")
        
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
            else: 
                st.info("Chat history empty. Start by describing your website in the input box above.")
        
        # Clear Workspace Button
        if st.button("🗑️ Clear Workspace", key="clear_workspace_btn", help="Clear all files in the workspace", type="primary"):
            if clear_workspace():
                st.success("Workspace cleared successfully!")
                st.session_state.workspace_reset_needed = False
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("Failed to clear workspace.")

# --- Main Area: Modern UI with 3D effects ---
# Main Title with modern styling
st.markdown('<h1 class="main-title">Describe your website</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Turn your ideas into reality with AI-powered web development</p>', unsafe_allow_html=True)

# Input container with 3D Input Box and Download Button
st.markdown('<div class="input-container">', unsafe_allow_html=True)

# 3D Input Box for website description
col1, col2 = st.columns([4, 1])
with col1:
    prompt = st.chat_input("Describe your website idea in detail...", key="website_description")

with col2:
    # Only show download button if there are files in the workspace
    available_files = get_workspace_files()
    if available_files:
        # Create zip file
        zip_buffer = create_download_zip()
        if zip_buffer:
            # Create download link
            download_link = get_download_link(zip_buffer, "website_project.zip", "Download")
            st.markdown(download_link, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Process the prompt if provided
if prompt:
    # Set workspace_reset_needed flag to true when a new prompt is received
    if prompt != st.session_state.last_prompt:
        st.session_state.workspace_reset_needed = True
        st.session_state.last_prompt = prompt
        
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Loading animation
    with st.spinner():
        st.markdown('<div class="loading-text">Your thoughts are coming alive...</div>', unsafe_allow_html=True)
        ai_response_text = call_gemini(st.session_state.messages)
        executed_commands = parse_and_execute_commands(ai_response_text)
        st.session_state.messages.append({"role": "assistant", "content": executed_commands})
        st.rerun()

# --- Main Area: Tabs with metallic finish ---
tab1, tab2 = st.tabs([" 📂 Workspace ", " 👀 Preview "])

with tab1:  # --- Workspace Tab ---
    st.markdown('<h2 class="section-header">Workspace & Editor</h2>', unsafe_allow_html=True)
    st.markdown("---")
    st.subheader("Files")
    available_files = get_workspace_files()
    if not available_files: st.info(f"Workspace '{WORKSPACE_DIR.name}' empty.")
    current_selection_index = 0; options = [None] + available_files
    if st.session_state.selected_file in options:
        try: current_selection_index = options.index(st.session_state.selected_file)
        except ValueError: st.session_state.selected_file = None
    selected_file_option = st.selectbox("Select file:", options=options, format_func=lambda x: "--- Select ---" if x is None else x, key="ws_file_select", index=current_selection_index, label_visibility="visible")
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
        edited_content = st.text_area("Code Editor", value=st.session_state.file_content, height=400, key=editor_key, label_visibility="visible")
        if edited_content != st.session_state.file_content:
             if st.button("💾 Save Manual Changes", key="save_changes_btn", help="Save changes to the file", type="primary"):
                if save_file_content(st.session_state.selected_file, edited_content):
                    st.session_state.file_content = edited_content; st.success(f"Saved: `{st.session_state.selected_file}`")
                    st.session_state.rendered_html = ""; st.session_state.pop(f"rendered_for_{st.session_state.selected_file}", None)
                    time.sleep(0.5); st.rerun()
                else: st.error("Failed to save.")
    else:
        st.info("Select a file to edit.")
        st.text_area("Editor Placeholder", value="Select a file...", height=400, key="editor_placeholder", disabled=True, label_visibility="visible")

with tab2:  # --- Preview Tab ---
    st.markdown('<h2 class="section-header">Live Preview</h2>', unsafe_allow_html=True)
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
                # Preview container with styling
                st.markdown('<div style="background: #112240; border-radius: 10px; padding: 1rem; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3); border: 1px solid rgba(100, 255, 218, 0.1);">', unsafe_allow_html=True)
                st.components.v1.html(st.session_state.rendered_html, height=600, scrolling=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                if css_applied_info: st.caption(css_applied_info)
                
                # Create a proper HTML file for the new window
                html_content = st.session_state.rendered_html
                
                # Create a JavaScript function to open a new window with the HTML content
                js_open_window = f"""
                <script>
                function openInNewWindow() {{
                    const newWindow = window.open('', '_blank');
                    if (newWindow) {{
                        newWindow.document.write(`{html_content}`);
                        newWindow.document.close();
                    }} else {{
                        alert('Pop-up blocked! Please allow pop-ups for this site.');
                    }}
                }}
                </script>
                <a href="javascript:void(0);" onclick="openInNewWindow();" class="new-window-link">🔗 Open in New Window</a>
                """
                
                # Display the link
                st.markdown(js_open_window, unsafe_allow_html=True)
            else:
                st.warning("Preview failed to render.")
        else:
            st.info(f"Select an HTML file to preview. Current file: `{st.session_state.selected_file}`")
    else:
        st.info("Select a file to preview.")

# Add Font Awesome for icons
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
""", unsafe_allow_html=True)
