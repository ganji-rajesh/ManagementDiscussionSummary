
"""
state_manager.py

Streamlit session state management.
Centralizes the initialization and updates of the application's state variables.
"""

import streamlit as st
import uuid
from typing import List, Dict, Any, Optional

def initialize_session_state() -> None:
    """
    Initializes the required session state variables if they don't exist.
    """
    if "sources" not in st.session_state:
        # Schema: [{"id": str, "name": str, "start": int, "end": int, "is_active": bool, "text_content": str, "pdf_bytes": bytes}]
        st.session_state.sources = []
        
    if "chat_history" not in st.session_state:
        # Schema: [{"role": "user"|"assistant", "content": str}]
        st.session_state.chat_history = []
        
    if "llm_session" not in st.session_state:
        # Holds the Inference abstraction object
        st.session_state.llm_session = None
        
    if "document_info" not in st.session_state:
        # Context about the uploaded PDF (total pages, name, etc.)
        st.session_state.document_info = None

def add_source(name: str, start_page: int, end_page: int, text_content: str, pdf_bytes: bytes) -> str:
    """
    Adds a new extracted source to the session state.
    Returns the generated source ID.
    """
    source_id = str(uuid.uuid4())
    new_source = {
        "id": source_id,
        "name": name,
        "start": start_page,
        "end": end_page,
        "is_active": True,
        "text_content": text_content,
        "pdf_bytes": pdf_bytes
    }
    st.session_state.sources.append(new_source)
    return source_id

def remove_source(source_id: str) -> bool:
    """
    Removes a source by its ID.
    Returns True if removed, False if not found.
    """
    initial_length = len(st.session_state.sources)
    st.session_state.sources = [s for s in st.session_state.sources if s.get("id") != source_id]
    return len(st.session_state.sources) < initial_length

def toggle_source(source_id: str, is_active: bool) -> None:
    """
    Updates the active status of a specific source.
    """
    for source in st.session_state.sources:
        if source.get("id") == source_id:
            source["is_active"] = is_active
            break

def get_active_context() -> str:
    """
    Compiles the text content of all active sources into a single context string.
    """
    active_sources = [s for s in st.session_state.sources if s.get("is_active", False)]
    
    if not active_sources:
        return ""
        
    context_parts = []
    for source in active_sources:
        context_parts.append(f"--- SOURCE: {source.get('name')} (Pages {source.get('start')}-{source.get('end')}) ---")
        context_parts.append(source.get('text_content', ''))
        context_parts.append("\n")
        
    return "\n".join(context_parts)

def append_chat_message(role: str, content: str, tokens: Optional[Dict[str, int]] = None) -> None:
    """
    Appends a new message to the chat history.
    """
    if role not in ["user", "assistant"]:
        raise ValueError("Role must be 'user' or 'assistant'.")
        
    msg: Dict[str, Any] = {"role": role, "content": content}
    if tokens:
        msg["tokens"] = tokens
        
    st.session_state.chat_history.append(msg)

def clear_chat_history() -> None:
    """
    Clears the current chat history.
    """
    st.session_state.chat_history = []
