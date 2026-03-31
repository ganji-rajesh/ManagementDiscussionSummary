"""
settings.py

Configuration settings and constants for the Annual Report Workspace.
Centrally manages app-wide parameters, supported models, and limits.
"""

import os
from dataclasses import dataclass

@dataclass
class AppSettings:
    # Application Info
    APP_NAME: str = "Annual Report Workspace"
    APP_VERSION: str = "2.0.0"

    # Limitations
    MAX_SOURCES: int = 10
    MAX_FILE_SIZE_MB: int = 100
    
    # Supported LLM Models
    # Focusing on Gemini as per the V2 architecture document
    SUPPORTED_MODELS: tuple = (
        "gemini-2.5-pro",
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    )
    DEFAULT_MODEL: str = "gemini-2.0-flash"

    # Prompts & Context
    SYSTEM_INSTRUCTION: str = (
        "You are an expert financial analyst assistant. Your task is to analyze "
        "and answer questions based ONLY on the provided annual report excerpts. "
        "Always cite your sources using the [Source Name] format when providing information."
    )

    # UI Settings
    THEME_COLOR: str = "#2b5c8f"

# Global settings instance
SETTINGS = AppSettings()
