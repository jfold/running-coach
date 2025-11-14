"""Service to calculate personal records from Strava activities"""
from typing import Dict, List, Optional


class PersonalRecordsService:
    """Calculate personal records from activities"""

    # Standard distances in meters
    DISTANCES = {
        "1km": 1000,
        "5km": 5000,
        "10km": 10000,
        "half_marathon": 21097.5,
        "marathon": 42195
    }

    # Tolerance for distance matching (2% for more accurate matching)
    DISTANCE_TOLERANCE = 0.02

    # Standard distances - map Strava best effort names to our keys
    DISTANCE_MAPPING = {
        "1k": "1km",
        "5k": "5km",
        "10k": "10km",
        "Half-Marathon": "half_marathon",
        "Marathon": "marathon"
    }

    def calculate_personal_records(self, activities: List[Dict]) -> Dict:
        """
        Calculate personal records from activity list using simple distance matching

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

    def calculate_personal_records_from_best_efforts(self, best_efforts_by_activity: List[List[Dict]]) -> Dict:
        """
        Calculate personal records from best efforts across all activities

        Args:
            best_efforts_by_activity: List of best_efforts arrays from each activity

        Returns:
            Dictionary of personal records by distance
        """
        personal_records = {}

        # Initialize records for our target distances
        for distance_key in self.DISTANCE_MAPPING.values():
            personal_records[distance_key] = None

        # Flatten all best efforts from all activities
        all_best_efforts = []
        for best_efforts in best_efforts_by_activity:
            if best_efforts:
                all_best_efforts.extend(best_efforts)

        # Group by distance and find fastest time for each
        for effort in all_best_efforts:
            effort_name = effort.get('name', '')

            # Map Strava's effort name to our distance key
            distance_key = self.DISTANCE_MAPPING.get(effort_name)

            if distance_key:
                moving_time = effort.get('moving_time', 0)

                if moving_time > 0:
                    current_best = personal_records[distance_key]

                    # Update if this is faster than current best (or first entry)
                    if current_best is None or moving_time < current_best['time_seconds']:
                        personal_records[distance_key] = {
                            "time_seconds": moving_time,
                            "time_formatted": self._format_time(moving_time),
                            "pace": self._calculate_pace(moving_time, effort.get('distance', 0)),
                            "date": effort.get('start_date_local', '').split('T')[0] if effort.get('start_date_local') else '',
                            "activity_id": effort.get('activity_id'),
                            "effort_name": effort_name
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
