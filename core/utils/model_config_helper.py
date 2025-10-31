"""
core/utils/model_config_helper.py

This module provides utility functions for working with model configurations,
including functions to identify and display model configuration names.
"""

import inspect
from typing import Dict, Any, Union
from config.agents import MODEL_CONFIG
import core.types.models as models_module

def get_model_config_name(config_entry):
    """
    Find the variable name for a model configuration in models.py or agents.py
    
    Args:
        config_entry: A ModelConfig object or dict with model configuration info
        
    Returns:
        str: The configuration name (like "GPT4_1_CREATIVE" or "CLAUDE_WITH_REASONING")
    """
    # First check if it's one of the predefined phase configs
    for phase, config in MODEL_CONFIG.items():
        if isinstance(config_entry, dict):
            if (config.provider == config_entry.get("provider") and 
                config.model_name == config_entry.get("model_name") and
                config.reasoning == config_entry.get("reasoning") and
                config.temperature == config_entry.get("temperature")):
                # Instead of returning the phase name, continue looking for the actual config name
                pass
        elif config is config_entry:
            # Direct object identity match (for when passing MODEL_CONFIG['phase1'] directly)
            # First check in models_module to find predefined configs
            for name, value in inspect.getmembers(models_module):
                if name.isupper() and value is config:
                    return name
            
            # If not found, check in agents_module (backwards compatibility)
            import config.agents as agents_module
            for name, value in inspect.getmembers(agents_module):
                if name.isupper() and value is config:
                    return name
    
    # Check all variables in the core.types.models module
    for name, value in inspect.getmembers(models_module):
        if name.isupper() and value is not None and hasattr(value, "provider") and hasattr(value, "model_name"):
            if isinstance(config_entry, dict):
                if (value.provider == config_entry.get("provider") and 
                    value.model_name == config_entry.get("model_name") and
                    value.reasoning == config_entry.get("reasoning") and
                    value.temperature == config_entry.get("temperature")):
                    return name
            elif (value.provider == getattr(config_entry, "provider", None) and 
                  value.model_name == getattr(config_entry, "model_name", None) and
                  value.reasoning == getattr(config_entry, "reasoning", None) and
                  value.temperature == getattr(config_entry, "temperature", None)):
                return name
    
    # If not found in models_module, check in agents_module (backwards compatibility)
    import config.agents as agents_module
    for name, value in inspect.getmembers(agents_module):
        if name.isupper() and hasattr(value, "provider") and hasattr(value, "model_name"):
            if isinstance(config_entry, dict):
                if (value.provider == config_entry.get("provider") and 
                    value.model_name == config_entry.get("model_name") and
                    value.reasoning == config_entry.get("reasoning") and
                    value.temperature == config_entry.get("temperature")):
                    return name
            elif (value.provider == getattr(config_entry, "provider", None) and 
                  value.model_name == getattr(config_entry, "model_name", None) and
                  value.reasoning == getattr(config_entry, "reasoning", None) and
                  value.temperature == getattr(config_entry, "temperature", None)):
                return name
                
    # Return the model name if no match is found
    if isinstance(config_entry, dict):
        provider = config_entry.get("provider", "unknown")
        model_name = config_entry.get("model_name", "unknown")
        provider_name = provider.name if hasattr(provider, "name") else provider
        return f"{provider_name}_{model_name}"
    else:
        provider_name = config_entry.provider.name if hasattr(config_entry, "provider") else "unknown"
        model_name = getattr(config_entry, "model_name", "unknown")
        return f"{provider_name}_{model_name}" 