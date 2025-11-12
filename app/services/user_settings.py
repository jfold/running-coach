import json
import os
from typing import Dict, Optional


class UserSettingsService:
    """Service to manage user settings (temporary file-based storage)"""

    def __init__(self, data_dir: str = "app/data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def _get_user_file(self, user_id: str) -> str:
        return os.path.join(self.data_dir, f"user_{user_id}.json")

    def get_settings(self, user_id: str) -> Dict:
        """Get user settings"""
        file_path = self._get_user_file(user_id)

        if not os.path.exists(file_path):
            # Return default settings
            return self._default_settings()

        with open(file_path, 'r') as f:
            return json.load(f)

    def save_settings(self, user_id: str, settings: Dict) -> None:
        """Save user settings"""
        file_path = self._get_user_file(user_id)

        with open(file_path, 'w') as f:
            json.dump(settings, f, indent=2)

    def update_hr_zones(self, user_id: str, zones: Dict) -> Dict:
        """Update heart rate zones"""
        settings = self.get_settings(user_id)
        settings['hr_zones'] = zones
        self.save_settings(user_id, settings)
        return settings

    def update_hr_params(self, user_id: str, max_hr: Optional[int] = None,
                         fitness_age: Optional[int] = None, actual_age: Optional[int] = None) -> Dict:
        """Update HR parameters and recalculate zones"""
        settings = self.get_settings(user_id)

        if max_hr is not None:
            settings['max_hr'] = max_hr

        if fitness_age is not None:
            settings['fitness_age'] = fitness_age

        if actual_age is not None:
            settings['actual_age'] = actual_age

        # Recalculate zones based on max HR
        if 'max_hr' in settings:
            settings['hr_zones'] = self._calculate_zones(settings['max_hr'])

        self.save_settings(user_id, settings)
        return settings

    def _calculate_zones(self, max_hr: int) -> Dict:
        """Calculate heart rate zones based on max HR"""
        # Standard heart rate zones as percentage of max HR
        return {
            'zone1': {'min': int(max_hr * 0.50), 'max': int(max_hr * 0.60), 'name': 'Recovery'},
            'zone2': {'min': int(max_hr * 0.60), 'max': int(max_hr * 0.70), 'name': 'Aerobic'},
            'zone3': {'min': int(max_hr * 0.70), 'max': int(max_hr * 0.80), 'name': 'Tempo'},
            'zone4': {'min': int(max_hr * 0.80), 'max': int(max_hr * 0.90), 'name': 'Threshold'},
            'zone5': {'min': int(max_hr * 0.90), 'max': int(max_hr * 0.95), 'name': 'VO2 Max'},
            'zone6': {'min': int(max_hr * 0.95), 'max': max_hr, 'name': 'Anaerobic'}
        }

    def _default_settings(self) -> Dict:
        """Default user settings"""
        default_max_hr = 190  # Default max HR
        return {
            'max_hr': default_max_hr,
            'fitness_age': None,
            'actual_age': None,
            'hr_zones': self._calculate_zones(default_max_hr)
        }

    @staticmethod
    def calculate_max_hr_from_age(age: int) -> int:
        """Calculate max HR using age-based formula (220 - age)"""
        return 220 - age


# Singleton instance
user_settings_service = UserSettingsService()
