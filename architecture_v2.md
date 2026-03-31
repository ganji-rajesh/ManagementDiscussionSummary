# Architecture Overview: Financial Document Workspace (V2)

## 1. Executive Summary
This document outlines the architecture for version 2.0 of the Annual Report Analyzer. The project is pivoting from a single-purpose Management Discussion & Analysis (MD&A) summarizer into a generalized, interactive financial workspace heavily inspired by Google's NotebookLM. 

The new architecture enables users to extract, manage, and toggle multiple custom sections from an annual report (up to 10 distinct sources) and interact with them via a stateless Chat Interface powered by an abstracted LLM routing layer.

---

## 2. Core System Components

The system is divided into three primary layers to ensure modularity, scalability, and ease of testing:

1. **Presentation & State Layer (`app.py`)**: Streamlit UI, Session State management, and event handling.
2. **Document Processing Layer (`pdf_extraction_tools.py`)**: PyMuPDF wrapping, text extraction, PDF byte manipulation (splitting), and caching.
3. **Inference Abstraction Layer (`inference.py`)**: Abstract Base Class managing LLM connections, prompt construction, and stateful chat sessions.

### Architecture Diagram (Mermaid)

```mermaid
graph TD
    A[User via Browser] -->|Uploads PDF & Defines Ranges| B[Streamlit UI - app.py]
    B -->|State Management| C[(st.session_state)]
    
    B -->|Page Ranges| D[Document Processing Layer]
    D -->|@st.cache_data| E[Extracted Text]
    D -->|Sub-Document Bytes| F[Downloadable Split PDFs]
    
    C -->|Toggled Active Sources| G[Inference Layer - inference.py]
    
    G -->|BaseLLM Interface| H{Model Router}
    H -->|GeminiAPI| I[Google Gemini]
    H -->|OpenAI API| J[Other Providers...]
    
    G -->|Returns Chat / Summary| B
```
## 3. Proposed Directory Structure

To support this more robust Workspace architecture, the codebase should be reorganized from flat scripts into a modular structure (similar to professional SaaS applications):

```text
annual_report_workspace/
│
├── app.py                     # Streamlit UI entry point
│
├── core/
│   ├── __init__.py
│   ├── pdf_processing.py      # PyMuPDF extraction, PDF byte-splitting
│   ├── spatial_tools.py       # TOC heuristics and bounding box math
│   ├── llm_inference.py       # BaseLLM class and Gemini implementation
│   └── prompts.py             # Prompt templates (Summary, citations, chat)
│
├── utils/
│   ├── __init__.py
│   ├── state_manager.py       # Streamlit session state initialization & updates
│   └── validators.py          # Input validation (PDF format, API keys, page bounds)
│
├── config/
│   └── settings.py            # Constants, supported models, max sources (10)
│
├── tests/
│   ├── test_pdf_processing.py
│   ├── test_spatial_tools.py
│   └── test_inference.py
│
├── requirements.txt
└── README.md
---

## 3. Component Deep-Dive

### 3.1. Presentation & State Management (`app.py`)
Streamlit's stateless nature requires a robust session state configuration to mimic a complex workspace.

**Key Responsibilities:**
- **Left Panel (Source Management):** 
  - Manage inputs for `start_page` and `end_page` alongside an arbitrary source name (e.g., "Risk Factors").
  - Trigger PDF splitting and render a generated Download Button for the newly split PDF (`[ReportName]_[Start]_[End].pdf`).
  - Render up to 10 checkbox toggles representing `Active Context`.
- **Main Panel (Chat Interface):**
  - Render `st.chat_message` loops for conversation history.
  - Provide a `st.chat_input` for ad-hoc querying.
  - Surface a prominent **"Generate Overview"** button above the chat to quickly synthesize all toggled sources without typing a prompt.

**State Schema:**
```python
st.session_state.sources = [
    {
        "id": "uuid",
        "name": "Financial Highlights",
        "start": 10,
        "end": 15,
        "is_active": True,  # Controls if it's fed to LLM
        "text_content": "...",
        "pdf_bytes": <bytes>
    }
]
st.session_state.chat_history = []
st.session_state.llm_session = <LLMSessionObject>
```

### 3.2. Document Processing Layer
This layer handles all physical manipulation of the document.

**Key Upgrades:**
- **PDF Splitting Feature:** A new utility to slice the `pymupdf.Document` and save it to a byte stream for user download.
- **Aggressive Caching (`@st.cache_data`):** Heavy extraction and spatial analysis functions must be wrapped in Streamlit's cache decorators. This prevents the app from re-extracting text or re-running expensive spatial math if the user simply refreshes the page or changes visual themes.
- **TOC Heuristics (Optional but recommended):** Repurposing the previous MD&A spatial logic to parse the *entire* Table of Contents, offering users a clickable list to auto-create sources instead of typing numbers manually.

### 3.3. Inference Abstraction Layer (`inference.py`)
To future-proof the application against model deprecations and enable easy A/B testing, the LLM integration is decoupled from the UI.

**Implementation Strategy:**
- Create an Abstract Base Class (ABC) defining the contract for any LLM provider.
- Implement specific client wrappers (e.g., `GeminiClient`).

```python
from abc import ABC, abstractmethod

class BaseLLM(ABC):
    @abstractmethod
    def start_chat(self, system_instruction: str):
        pass
        
    @abstractmethod
    def send_message(self, prompt: str) -> str:
        pass

class GeminiClient(BaseLLM):
    # Implements Gemini-specific logic, manages robust context window,
    # and handles gemini's specific chat object.
```

When a user toggles sources or clicks the "Generate Overview" label, the UI layer extracts the `text_content` of all `is_active` sources, concatenates them into a highly structured Context String (with citations), and feeds them to the `BaseLLM` interface.

---

## 4. Workflows

### Scenario 1: Adding a Source
1. User inputs a name, start page, and end page in the sidebar.
2. `app.py` calls the Document Processing layer.
3. Extracted text and sub-document PDF bytes are saved to `st.session_state.sources`.
4. The sidebar updates, showing the new source with a checked toggle box and a download button.

### Scenario 2: The Chat Turn
1. User types a query in `st.chat_input`.
2. The system checks `st.session_state.sources` and gathers all text from sources where `is_active == True`.
3. The context string is assembled: `Source: [Name]\n[Text]\n\n...`
4. The Inference Layer sends the context and the user's query to the active LLM.
5. `st.session_state.chat_history` is appended with the user query and the LLM's response.
6. The Main Panel re-renders the chat.

---

## 5. Security & Performance Considerations
- **Memory Management:** Holding up to 10 split PDFs and their raw text strings in RAM (`st.session_state`) requires careful cleanup. PyMuPDF document objects should be explicitly closed.
- **Context Overload:** While modern models (Gemini 2.0) have massive context windows, sending 300 pages of text on every Streamlit rerun for a single chat turn is computationally expensive and slow. The Inference Layer should intelligently manage `chat_history` objects specific to the provider so context isn't needlessly resent if possible, or gracefully manage token limits.
