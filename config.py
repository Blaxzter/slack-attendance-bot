import json
import os
from typing import Dict, List, Any
import pytz

class ConfigurationError(Exception):
    pass

class Config:
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.settings = self._load_default_config()
        if config_path and os.path.exists(config_path):
            self._load_custom_config()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load the default configuration from default_config.json"""
        default_config_path = os.path.join(os.path.dirname(__file__), 'default_config.json')
        try:
            with open(default_config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            raise ConfigurationError(f"Failed to load default configuration: {str(e)}")

    def _load_custom_config(self) -> None:
        """Load and merge custom configuration with defaults"""
        try:
            with open(self.config_path, 'r') as f:
                custom_config = json.load(f)
            self._merge_config(custom_config)
        except Exception as e:
            raise ConfigurationError(f"Failed to load custom configuration: {str(e)}")

    def _merge_config(self, custom_config: Dict[str, Any]) -> None:
        """Merge custom configuration with defaults"""
        for key, value in custom_config.items():
            if key in self.settings:
                if isinstance(value, dict) and isinstance(self.settings[key], dict):
                    self.settings[key].update(value)
                else:
                    self.settings[key] = value

    def validate(self) -> None:
        """Validate the configuration settings"""
        self._validate_schedule()
        self._validate_workdays()
        self._validate_response_options()
        self._validate_templates()

    def _validate_schedule(self) -> None:
        """Validate schedule settings"""
        schedule = self.settings.get('poll_schedule', {})
        
        # Validate hour
        hour = schedule.get('hour')
        if not isinstance(hour, int) or hour < 0 or hour > 23:
            raise ConfigurationError("Schedule hour must be an integer between 0 and 23")

        # Validate minute
        minute = schedule.get('minute')
        if not isinstance(minute, int) or minute < 0 or minute > 59:
            raise ConfigurationError("Schedule minute must be an integer between 0 and 59")

        # Validate timezone
        timezone = schedule.get('timezone')
        if timezone not in pytz.all_timezones:
            raise ConfigurationError(f"Invalid timezone: {timezone}")

    def _validate_workdays(self) -> None:
        """Validate workday settings"""
        workdays = self.settings.get('workdays', {})
        required_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        for day in required_days:
            if day not in workdays:
                raise ConfigurationError(f"Missing workday configuration for {day}")
            if not isinstance(workdays[day], bool):
                raise ConfigurationError(f"Workday value for {day} must be a boolean")

    def _validate_response_options(self) -> None:
        """Validate response options"""
        options = self.settings.get('response_options', [])
        if not isinstance(options, list) or len(options) == 0:
            raise ConfigurationError("Response options must be a non-empty list")

        for option in options:
            if not isinstance(option, dict):
                raise ConfigurationError("Each response option must be a dictionary")
            required_keys = ['text', 'value', 'action_id']
            for key in required_keys:
                if key not in option:
                    raise ConfigurationError(f"Response option missing required key: {key}")

    def _validate_templates(self) -> None:
        """Validate message templates"""
        required_templates = ['message_template', 'summary_template']
        for template_name in required_templates:
            template = self.settings.get(template_name)
            if not isinstance(template, str) or not template:
                raise ConfigurationError(f"{template_name} must be a non-empty string")

    def get_schedule(self) -> Dict[str, Any]:
        return self.settings['poll_schedule']

    def get_workdays(self) -> Dict[str, bool]:
        return self.settings['workdays']

    def get_response_options(self) -> List[Dict[str, str]]:
        return self.settings['response_options']

    def get_message_template(self) -> str:
        return self.settings['message_template']

    def get_summary_template(self) -> str:
        return self.settings['summary_template']

    def save_custom_config(self, config_path: str = None) -> None:
        """Save current configuration to a file"""
        save_path = config_path or self.config_path
        if not save_path:
            raise ConfigurationError("No configuration path specified")

        try:
            with open(save_path, 'w') as f:
                json.dump(self.settings, f, indent=4)
        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {str(e)}") 