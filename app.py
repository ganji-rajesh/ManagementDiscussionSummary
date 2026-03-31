"""
app.py

Main entry point for the Annual Report Workspace (V2).
Orchestrates the Streamlit UI, user input events, and bridges the 
backend core/utils layers together.
"""

import streamlit as st
import hashlib
import io

# Local Module Imports
from config import SETTINGS
from utils import (
    initialize_session_state,
    add_source,
    remove_source,
    toggle_source,
    get_active_context,
    append_chat_message,
    validate_pdf_format,
    validate_api_key,
    validate_page_bounds,
    validate_source_name
)
from core.pdf_processing import extract_text_from_pdf, split_pdf_to_bytes, get_pdf_page_count
from core.llm_inference import GeminiClient
from core.prompts import SYSTEM_ANALYST_INSTRUCTION, OVERVIEW_PROMPT, build_contextual_prompt

def init_ui():
    """Configures the main page and ensures required states exist."""
    st.set_page_config(
        page_title=SETTINGS.APP_NAME,
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    initialize_session_state()

def render_sidebar():
    """Renders the left panel for document management and API configuration."""
    with st.sidebar:
        st.title(f"📚 {SETTINGS.APP_NAME}")
        st.caption(f"Version {SETTINGS.APP_VERSION}")
        
        # --- 1. Document Upload ---
        st.header("1. Upload Report")
        uploaded_file = st.file_uploader("Upload Annual Report (PDF)", type=["pdf"])
        
        if uploaded_file:
            is_valid, msg = validate_pdf_format(
                uploaded_file.name, 
                uploaded_file.size, 
                SETTINGS.MAX_FILE_SIZE_MB
            )
            if not is_valid:
                st.error(msg)
            else:
                bytes_data = uploaded_file.getvalue()
                # Check for new document to clear UI out
                info_cache = st.session_state.document_info
                if info_cache is None or info_cache.get("name") != uploaded_file.name:
                    total_pages = get_pdf_page_count(bytes_data)
                    st.session_state.document_info = {
                        "name": uploaded_file.name,
                        "bytes": bytes_data,
                        "total_pages": total_pages
                    }
                    st.success(f"{uploaded_file.name} loaded ({total_pages} pages).")
                    
        # --- 2. Source Extraction ---
        if st.session_state.document_info:
            st.header("2. Extract Source")
            
            with st.form("extraction_form"):
                source_name = st.text_input("Source Name (e.g., 'Risk Factors')")
                col1, col2 = st.columns(2)
                with col1:
                    start_page = st.number_input("Start Page", min_value=1, value=1)
                with col2:
                    end_page = st.number_input("End Page", min_value=1, value=1)
                
                submit_extract = st.form_submit_button("Extract Sub-Document")
                
                if submit_extract:
                    existing_names = [s.get("name") for s in st.session_state.sources]
                    is_valid_name, name_msg = validate_source_name(source_name, existing_names)
                    total_pages = st.session_state.document_info.get("total_pages", 0)
                    is_valid_bounds, bounds_msg = validate_page_bounds(start_page, end_page, total_pages)
                    
                    if not is_valid_name:
                        st.error(name_msg)
                    elif not is_valid_bounds:
                        st.error(bounds_msg)
                    elif len(st.session_state.sources) >= SETTINGS.MAX_SOURCES:
                        st.error(f"Limit of {SETTINGS.MAX_SOURCES} sources reached.")
                    else:
                        with st.spinner(f"Extracting {source_name}..."):
                            try:
                                pdf_bytes = st.session_state.document_info["bytes"]
                                # Hits PyMuPDF core utilities
                                text = extract_text_from_pdf(pdf_bytes, start_page, end_page)
                                sub_pdf = split_pdf_to_bytes(pdf_bytes, start_page, end_page)
                                
                                # Appends to Streamlit native session lists
                                add_source(source_name, start_page, end_page, text, sub_pdf)
                                st.success(f"Source '{source_name}' active.")
                                st.rerun() 
                            except Exception as e:
                                st.error(f"Extraction failed: {str(e)}")
                                
        # --- 3. Context Management ---
        if st.session_state.sources:
            st.header("3. Active Context")
            st.caption("Toggle checkboxes to include specific sections in LLM limits.")
            
            # Track which source text panel is open
            if "viewing_text_id" not in st.session_state:
                st.session_state.viewing_text_id = None
            
            for source in list(st.session_state.sources):
                colA, colB, colC, colD = st.columns([0.55, 0.15, 0.15, 0.15])
                
                with colA:
                    is_checked = st.checkbox(
                        f"{source['name']} ({source['start']}-{source['end']})", 
                        value=source['is_active'], 
                        key=f"chk_{source['id']}"
                    )
                    if is_checked != source['is_active']:
                        toggle_source(source['id'], is_checked)
                
                with colB:
                    # Toggle the text viewer for this source
                    is_viewing = st.session_state.viewing_text_id == source['id']
                    view_label = "🔍" if not is_viewing else "✖️"
                    view_help = "View extracted text" if not is_viewing else "Close text viewer"
                    if st.button(view_label, key=f"view_{source['id']}", help=view_help):
                        if is_viewing:
                            st.session_state.viewing_text_id = None
                        else:
                            st.session_state.viewing_text_id = source['id']
                        st.rerun()
                        
                with colC:
                    st.download_button(
                        label="📄",
                        data=source['pdf_bytes'],
                        file_name=f"{source['name'].replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        key=f"dl_{source['id']}",
                        help="Download this extracted PDF"
                    )
                    
                with colD:
                    if st.button("🗑️", key=f"del_{source['id']}", help="Delete from Workspace"):
                        remove_source(source['id'])
                        st.rerun()
                
                # Show extracted text panel below the row if this source is selected
                if st.session_state.viewing_text_id == source['id']:
                    text_content = source.get('text_content', '')
                    token_count = len(text_content) // 4 if text_content else 0
                    
                    with st.expander(f"📝 Extracted Text — {source['name']} (pages {source['start']}–{source['end']}) | ~{token_count:,} tokens", expanded=True):
                        st.text_area(
                            label="Extracted Content",
                            value=text_content if text_content else '(No text available)',
                            height=300,
                            disabled=True,
                            key=f"txt_{source['id']}",
                            label_visibility="collapsed"
                        )

        # --- 4. API Configuration ---
        st.header("4. Configuration")
        api_key = st.text_input("Gemini API Key", type="password")
        
        AVAILABLE_MODELS = [
            "gemini-2.5-flash",
            "gemini-2.0-flash", 
            "gemini-2.0-flash-lite", 
            "gemini-1.5-pro", 
            "gemini-1.5-flash"
        ]
        selected_model = st.selectbox("Select Model", AVAILABLE_MODELS, index=1)
        
        if api_key:
            is_valid, msg = validate_api_key(api_key, provider="gemini")
            if not is_valid:
                st.error(msg)
            else:
                # Detect if the API key has changed since last initialization.
                # Uses a hash so the raw key is never stored in session state.
                key_fingerprint = hashlib.sha256(api_key.encode()).hexdigest()
                key_changed = (key_fingerprint != st.session_state.get("api_key_fingerprint"))
                model_changed = (selected_model != st.session_state.get("selected_model"))
                
                if not st.session_state.llm_session or key_changed or model_changed:
                    with st.spinner(f"Connecting to Google Gemini API ({selected_model})..."):
                        try:
                            client = GeminiClient(api_key=api_key, model_name=selected_model)
                            client.start_chat(system_instruction=SYSTEM_ANALYST_INSTRUCTION)
                            st.session_state.llm_session = client
                            st.session_state.api_key_fingerprint = key_fingerprint
                            st.session_state.selected_model = selected_model
                            st.success(f"Connected to {selected_model} successfully!")
                        except Exception as e:
                            st.error(f"Failed to connect: {str(e)}")
        else:
            # Key was cleared — tear down the existing session
            if st.session_state.get("llm_session"):
                st.session_state.llm_session = None
                st.session_state.api_key_fingerprint = None
            st.warning("Please enter your API Key to enable chat functions.")

def render_main():
    """Renders the main Chat Interface where AI interaction happens."""
    
    st.header("Annual Report Analyzer")
    
    with st.expander("How to use this app"):
        st.markdown("""
        1. Enter your Gemini API Key in the left Configuration panel.
        2. Upload an Annual Report PDF in the left panel.
        3. Extract a section (like 'MD&A') using the page numbers.
        4. Start querying the active context in the chat, or click 'Generate Executive Overview' for an automated summary.
        """)
    
    # Pre-requisite Checks
    if not st.session_state.llm_session:
        st.info("👈 Please enter a valid API Key in the sidebar to activate the LLM.")
        return
        
    if not st.session_state.sources:
        st.markdown("👈 Please upload a PDF and extract a logical fragment (like *MD&A* or *Risk Factors*) to begin.")
        return

    active_context = get_active_context()
    if not active_context.strip():
        st.warning("⚠️ No sources are currently 'Active'. Please check a box on the left panel to provide context.")

    st.divider()

    # Re-render Visual History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "tokens" in msg:
                t = msg["tokens"]
                st.caption(f"Tokens: Input **{t['input']}** | Output **{t['output']}** | Total **{t['total']}**")

    # High-level Automation action positioned just above the chat box
    # Place Download functionality to right of Overview button
    col_btn1, col_btn2 = st.columns([0.7, 0.3])
    
    with col_btn1:
        generate_overview = st.button("📊 Generate Executive Overview", type="primary", use_container_width=True)
        
    with col_btn2:
        pdf_bytes = None
        if st.session_state.chat_history:
            try:
                import textwrap
                from fpdf import FPDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("helvetica", size=11)
                for hm in st.session_state.chat_history:
                    role_str = "User" if hm["role"] == "user" else "Assistant"
                    # Safe encoding without crashing on special characters
                    safe_txt = hm["content"].encode('latin-1', 'replace').decode('latin-1')
                    
                    # Force word splitting for unusually long unbroken strings (URLs, markdown dividers)
                    # This prevents FPDF2's 'Not enough horizontal space' error.
                    wrapped_lines = []
                    for line in safe_txt.split('\n'):
                        wrapped_lines.append('\n'.join(textwrap.wrap(line, width=80, break_long_words=True)))
                    wrapped_txt = '\n'.join(wrapped_lines)

                    pdf.set_font("helvetica", style="B", size=12)
                    pdf.multi_cell(0, 10, f"{role_str}:")
                    pdf.set_font("helvetica", size=11)
                    pdf.multi_cell(0, 8, wrapped_txt)
                    pdf.ln(5)
                pdf_bytes = bytes(pdf.output())
            except Exception as e:
                st.error(f"Cannot generate PDF: {e}")
        
        if pdf_bytes:
            st.download_button(
                label="📥 Download PDF",
                data=pdf_bytes,
                file_name="chat_history.pdf",
                mime="application/pdf",
                use_container_width=True
            )

    if generate_overview:
        if not active_context.strip():
            st.error("Cannot generate an overview without active source context.")
        else:
            with st.chat_message("user"):
                st.write("Generate Overview")
            append_chat_message("user", "Generate Overview")
            
            # Construct the secure prompt wrapping the rules
            prompt = build_contextual_prompt(OVERVIEW_PROMPT, active_context)
            
            with st.chat_message("assistant"):
                try:
                    # Execute stream
                    stream = st.session_state.llm_session.send_message_stream(prompt)
                    response_text = st.write_stream(stream)
                    
                    usage = getattr(st.session_state.llm_session, "last_usage", None)
                    tokens_dict = None
                    if usage:
                        tokens_dict = {
                            "input": usage["prompt_tokens"],
                            "output": usage["completion_tokens"],
                            "total": usage["total_tokens"]
                        }
                    append_chat_message("assistant", response_text, tokens=tokens_dict)
                    
                    if tokens_dict:
                        st.caption(f"Tokens: Input **{tokens_dict['input']}** | Output **{tokens_dict['output']}** | Total **{tokens_dict['total']}**")
                    st.rerun() # Refresh to update PDF download bytes
                except Exception as e:
                    st.error(f"Inference process failed: {e}")

    # Wait for Ad-Hoc queries
    if user_input := st.chat_input("Ask a question about the active sources..."):
        # Display the user input natively
        with st.chat_message("user"):
            st.markdown(user_input)
            
        append_chat_message("user", user_input)
        
        # Merge input with context blocks
        full_wrapped_prompt = build_contextual_prompt(user_input, active_context)
        
        # Display backend generating
        with st.chat_message("assistant"):
            try:
                stream = st.session_state.llm_session.send_message_stream(full_wrapped_prompt)
                response_text = st.write_stream(stream)
                
                usage = getattr(st.session_state.llm_session, "last_usage", None)
                tokens_dict = None
                if usage:
                    tokens_dict = {
                        "input": usage["prompt_tokens"],
                        "output": usage["completion_tokens"],
                        "total": usage["total_tokens"]
                    }
                append_chat_message("assistant", response_text, tokens=tokens_dict)
                
                if tokens_dict:
                    st.caption(f"Tokens: Input **{tokens_dict['input']}** | Output **{tokens_dict['output']}** | Total **{tokens_dict['total']}**")
                st.rerun() # Refresh to update PDF download bytes
            except Exception as e:
                st.error(f"LLM API Error: {str(e)}")

def main():
    init_ui()
    render_sidebar()
    render_main()

if __name__ == "__main__":
    main()
