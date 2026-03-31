"""
llm_inference.py

Inference Layer Abstraction.
Decouples the core UI and application logic from specific Language Model providers.
Implements a standardized BaseLLM interface and concrete Google Gemini client.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Generator

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# Configure module-level logging
logger = logging.getLogger(__name__)

class BaseLLM(ABC):
    """
    Abstract Base Class defining the contract for Language Model APIs.
    """
    
    @abstractmethod
    def start_chat(self, system_instruction: str) -> None:
        """Initializes a stateful chat session."""
        pass
        
    @abstractmethod
    def send_message(self, prompt: str) -> str:
        """Sends a synchronous prompt to the active session."""
        pass

    @abstractmethod
    def send_message_stream(self, prompt: str) -> Generator[str, None, None]:
        """Sends a prompt to the active session and streams the response."""
        pass

    @abstractmethod
    def get_history(self) -> List[Dict[str, str]]:
        """Retrieves the normalized chat history in a provider-agnostic format."""
        pass

class GeminiClient(BaseLLM):
    """
    Concrete Implementation for Google's Gemini Models.
    """
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        if genai is None:
            raise ImportError("The `google-generativeai` SDK is missing.")
            
        if not api_key:
            raise ValueError("A valid Google API Key is required.")
            
        genai.configure(api_key=api_key)
        self.model_name = model_name
        self.model = None
        self.chat_session = None
        self.system_instruction = ""
        self.last_usage = None
        
    def start_chat(self, system_instruction: str = "") -> None:
        try:
            self.system_instruction = system_instruction
            generation_config = genai.GenerationConfig(temperature=0.2, top_p=0.95, top_k=40)
            
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_instruction if self.system_instruction else None,
                generation_config=generation_config
            )
            
            self.chat_session = self.model.start_chat(history=[])
            logger.info(f"Initialized Gemini chat session using {self.model_name}")
            
        except Exception as e:
            logger.error(f"Initialization failure: {e}", exc_info=True)
            raise RuntimeError(f"Failed to initialize Gemini Client: {e}")

    def send_message(self, prompt: str) -> str:
        if not self.chat_session:
            raise RuntimeError("Chat context is not active.")
            
        try:
            response = self.chat_session.send_message(prompt)
            if not response.parts:
                return "Model response blocked, potentially due to safety triggers."
            try:
                meta = response.usage_metadata
                if meta:
                    self.last_usage = {
                        "prompt_tokens": meta.prompt_token_count,
                        "completion_tokens": meta.candidates_token_count,
                        "total_tokens": meta.total_token_count
                    }
            except Exception:
                pass
            return response.text
        except Exception as e:
            if "complete iteration" in str(e) or "resolve" in str(e):
                # Recover from a locked session by cloning the clean history
                logger.warning("Recovering from locked Gemini ChatSession.")
                safe_history = list(self.chat_session.history)
                self.chat_session = self.model.start_chat(history=safe_history)
                retry_response = self.chat_session.send_message(prompt)
                return retry_response.text
            raise RuntimeError(f"Gemini Inference Error: {e}")

    def send_message_stream(self, prompt: str) -> Generator[str, None, None]:
        if not self.chat_session:
            raise RuntimeError("Chat context is not active.")
            
        response = None
        try:
            response = self.chat_session.send_message(prompt, stream=True)
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            if "complete iteration" in str(e) or "resolve" in str(e):
                logger.warning("Recovering from locked Gemini ChatSession (Stream).")
                safe_history = list(self.chat_session.history)
                self.chat_session = self.model.start_chat(history=safe_history)
                
                # Retry
                response = self.chat_session.send_message(prompt, stream=True)
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
                return
            raise RuntimeError(f"Gemini Streaming Error: {e}")
        finally:
            if response is not None:
                try:
                    response.resolve()
                except Exception:
                    pass
                try:
                    meta = response.usage_metadata
                    if meta:
                        self.last_usage = {
                            "prompt_tokens": meta.prompt_token_count,
                            "completion_tokens": meta.candidates_token_count,
                            "total_tokens": meta.total_token_count
                        }
                except Exception:
                    pass

    def get_history(self) -> List[Dict[str, str]]:
        if not self.chat_session:
            return []
            
        normalized_history = []
        for item in self.chat_session.history:
            role = "assistant" if item.role == "model" else "user"
            content_text = " ".join([p.text for p in getattr(item, 'parts', []) if hasattr(p, "text") and p.text])
            normalized_history.append({"role": role, "content": content_text})
            
        return normalized_history
