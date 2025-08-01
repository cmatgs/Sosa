"""
Konfigurationsmodul: Enthält DEFAULT_CONFIG und ConfigManager.
"""
from .constants import DEFAULT_CONFIG, ConfigSchema
from .config_manager import ConfigManager

__all__ = ["DEFAULT_CONFIG", "ConfigSchema", "ConfigManager"]