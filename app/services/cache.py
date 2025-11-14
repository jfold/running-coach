"""Simple file-based cache for API data"""
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Any
from pathlib import Path


class CacheService:
    """Simple file-based cache with expiration"""

    def __init__(self, cache_dir: str = "app/data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """Get the file path for a cache key"""
        return self.cache_dir / f"{key}.json"

    def get(self, key: str, max_age_hours: int = 24) -> Optional[Any]:
        """
        Get cached data if it exists and is not expired

        Args:
            key: Cache key
            max_age_hours: Maximum age of cache in hours

        Returns:
            Cached data or None if expired/missing
        """
        cache_path = self._get_cache_path(key)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)

            # Check if expired
            cached_at = datetime.fromisoformat(cache_data['cached_at'])
            expires_at = cached_at + timedelta(hours=max_age_hours)

            if datetime.now() > expires_at:
                # Expired, delete the cache file
                cache_path.unlink()
                return None

            return cache_data['data']

        except (json.JSONDecodeError, KeyError, ValueError):
            # Corrupted cache, delete it
            cache_path.unlink()
            return None

    def set(self, key: str, data: Any) -> None:
        """
        Store data in cache

        Args:
            key: Cache key
            data: Data to cache (must be JSON serializable)
        """
        cache_path = self._get_cache_path(key)

        cache_data = {
            'cached_at': datetime.now().isoformat(),
            'data': data
        }

        with open(cache_path, 'w') as f:
            json.dump(cache_data, f, indent=2)

    def delete(self, key: str) -> None:
        """Delete cached data"""
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()

    def clear_all(self) -> None:
        """Clear all cache files"""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()


# Singleton instance
cache_service = CacheService()
