"""Configuration management for Aeon Core."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    yaml = None


class Config:
    """Configuration manager for Aeon Core."""

    DEFAULT_CONFIG = {
        "llm": {
            "type": "llama-cpp",
            "api_url": "http://localhost:8000/v1/chat/completions",
            "model": "llama-cpp-model",
            "api_key": None,
        },
        "orchestrator": {
            "ttl": 10,
        },
        "logging": {
            "enabled": False,
            "file": None,
        },
    }

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """
        Initialize configuration.

        Args:
            config_path: Path to config file (optional). If not provided, looks for:
                - .aeon.yaml in current directory
                - .aeon.yaml in home directory
                - ~/.config/aeon/config.yaml
        """
        self.config_path = config_path or self._find_config_file()
        self.config = self._load_config()

    def _find_config_file(self) -> Optional[Path]:
        """Find config file in standard locations."""
        # Check current directory
        current_dir = Path.cwd()
        config_file = current_dir / ".aeon.yaml"
        if config_file.exists():
            return config_file

        # Check home directory
        home_dir = Path.home()
        config_file = home_dir / ".aeon.yaml"
        if config_file.exists():
            return config_file

        # Check XDG config directory
        xdg_config = os.getenv("XDG_CONFIG_HOME", home_dir / ".config")
        config_file = Path(xdg_config) / "aeon" / "config.yaml"
        if config_file.exists():
            return config_file

        return None

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file and environment variables."""
        config = self.DEFAULT_CONFIG.copy()

        # Load from file if it exists
        if self.config_path and self.config_path.exists():
            if yaml is None:
                raise ImportError(
                    "PyYAML is required for config file support. "
                    "Install with: pip install pyyaml"
                )
            with open(self.config_path, "r") as f:
                file_config = yaml.safe_load(f) or {}
                # Deep merge with defaults
                config = self._deep_merge(config, file_config)

        # Override with environment variables
        config = self._apply_env_overrides(config)

        return config

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides."""
        # LLM type
        if os.getenv("AEON_LLM_TYPE"):
            config["llm"]["type"] = os.getenv("AEON_LLM_TYPE")

        # LLM API URL
        if os.getenv("AEON_LLM_URL"):
            config["llm"]["api_url"] = os.getenv("AEON_LLM_URL")

        # LLM model
        if os.getenv("AEON_LLM_MODEL"):
            config["llm"]["model"] = os.getenv("AEON_LLM_MODEL")

        # LLM API key
        if os.getenv("AEON_LLM_API_KEY"):
            config["llm"]["api_key"] = os.getenv("AEON_LLM_API_KEY")

        # TTL
        if os.getenv("AEON_TTL"):
            try:
                config["orchestrator"]["ttl"] = int(os.getenv("AEON_TTL"))
            except ValueError:
                pass

        # Log file
        if os.getenv("AEON_LOG_FILE"):
            config["logging"]["file"] = os.getenv("AEON_LOG_FILE")
            config["logging"]["enabled"] = True

        return config

    def get_llm_type(self) -> str:
        """Get LLM adapter type."""
        return self.config["llm"]["type"]

    def get_llm_url(self) -> Optional[str]:
        """Get LLM API URL."""
        return self.config["llm"]["api_url"]

    def get_llm_model(self) -> str:
        """Get LLM model identifier."""
        return self.config["llm"]["model"]

    def get_llm_api_key(self) -> Optional[str]:
        """Get LLM API key."""
        return self.config["llm"]["api_key"]

    def get_ttl(self) -> int:
        """Get TTL value."""
        return self.config["orchestrator"]["ttl"]

    def get_log_file(self) -> Optional[str]:
        """Get log file path."""
        if self.config["logging"]["enabled"]:
            return self.config["logging"]["file"]
        return None


def create_default_config_file(path: Path) -> None:
    """Create a default config file at the specified path."""
    if yaml is None:
        raise ImportError(
            "PyYAML is required for config file support. "
            "Install with: pip install pyyaml"
        )

    # Ensure parent directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    default_config = {
        "llm": {
            "type": "llama-cpp",
            "api_url": "http://localhost:8000/v1/chat/completions",
            "model": "llama-cpp-model",
            "api_key": None,  # Set to your API key if needed
        },
        "orchestrator": {
            "ttl": 10,
        },
        "logging": {
            "enabled": False,
            "file": "aeon.log",
        },
    }

    with open(path, "w") as f:
        yaml.dump(default_config, f, default_flow_style=False, sort_keys=False)

