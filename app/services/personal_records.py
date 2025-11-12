"""Service to calculate personal records from Strava activities"""
from typing import Dict, List, Optional


class PersonalRecordsService:
    """Calculate personal records from activities"""

    # Standard distances in meters
    DISTANCES = {
        "1km": 1000,
        "5km": 5000,
        "10km": 10000,
        "half_marathon": 21097.5,  # 21.0975 km
        "marathon": 42195  # 42.195 km
    }

    # Tolerance for distance matching (5%)
    DISTANCE_TOLERANCE = 0.05

    def calculate_personal_records(self, activities: List[Dict]) -> Dict:
        """
        Calculate personal records from a list of activities

        Args:
            activities: List of activity dictionaries from Strava API

        Returns:
            Dictionary of personal records by distance
        """
        personal_records = {}

        # Initialize records
        for distance_name in self.DISTANCES.keys():
            personal_records[distance_name] = None

        # Filter only running activities
        run_activities = [a for a in activities if a.get('type') == 'Run']

        for distance_name, target_distance in self.DISTANCES.items():
            best_time = None
            best_activity = None

            for activity in run_activities:
                activity_distance = activity.get('distance', 0)
                moving_time = activity.get('moving_time', 0)

                # Check if activity distance matches target (within tolerance)
                distance_diff = abs(activity_distance - target_distance)
                max_diff = target_distance * self.DISTANCE_TOLERANCE

                if distance_diff <= max_diff and moving_time > 0:
                    # This activity is close to our target distance
                    if best_time is None or moving_time < best_time:
                        best_time = moving_time
                        best_activity = activity

            if best_activity:
                personal_records[distance_name] = {
                    "time_seconds": best_time,
                    "time_formatted": self._format_time(best_time),
                    "pace": self._calculate_pace(best_time, best_activity['distance']),
                    "date": best_activity.get('start_date_local', '').split('T')[0],
                    "activity_id": best_activity.get('id'),
                    "activity_name": best_activity.get('name')
                }

        return personal_records

    def _format_time(self, seconds: int) -> str:
        """Format seconds to HH:MM:SS or MM:SS"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"

    def _calculate_pace(self, time_seconds: int, distance_meters: float) -> str:
        """Calculate pace in min/km"""
        if distance_meters == 0:
            return "N/A"

        pace_seconds = (time_seconds / distance_meters) * 1000
        pace_minutes = int(pace_seconds // 60)
        pace_secs = int(pace_seconds % 60)

        return f"{pace_minutes}:{pace_secs:02d}/km"


# Singleton instance
personal_records_service = PersonalRecordsService()
