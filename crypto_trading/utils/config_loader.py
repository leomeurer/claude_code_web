"""
Configuration loader for the trading system.
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


class ConfigLoader:
    """Load and manage configuration from YAML and environment variables."""

    def __init__(self, config_file: str = "config/config.yaml"):
        """
        Initialize the config loader.

        Args:
            config_file: Path to the YAML configuration file
        """
        self.config_file = config_file
        self.config = {}
        self._load_env()
        self._load_yaml()

    def _load_env(self):
        """Load environment variables from .env file."""
        load_dotenv()

    def _load_yaml(self):
        """Load configuration from YAML file."""
        config_path = Path(self.config_file)

        if config_path.exists():
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f) or {}
        else:
            self.config = {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: Configuration key (supports nested keys with dot notation)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        # Try environment variable first
        env_value = os.getenv(key.upper().replace('.', '_'))
        if env_value is not None:
            return env_value

        # Try YAML config with nested key support
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def get_all(self) -> Dict[str, Any]:
        """
        Get all configuration.

        Returns:
            Dictionary with all configuration
        """
        return self.config

    def set(self, key: str, value: Any):
        """
        Set a configuration value.

        Args:
            key: Configuration key (supports nested keys with dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self, output_file: str = None):
        """
        Save configuration to YAML file.

        Args:
            output_file: Output file path (uses config_file if not provided)
        """
        output_path = Path(output_file or self.config_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
