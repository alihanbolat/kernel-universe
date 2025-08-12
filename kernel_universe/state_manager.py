"""
Redis-based state manager for Kernel Universe.
"""

import json
import redis
from typing import Dict, Any, Optional

from . import config


class StateManager:
    """Manages simulation state persistence using Redis."""
    
    def __init__(self, redis_url: str = None):
        """Initialize the state manager."""
        self.redis_url = redis_url or config.REDIS_URL
        self.redis_client = redis.Redis.from_url(self.redis_url)
        self.state_key = config.REDIS_STATE_KEY
    
    def save_state(self, state: Dict[str, Any]) -> bool:
        """Save the simulation state to Redis."""
        try:
            # Convert to JSON string
            state_json = json.dumps(state)
            
            # Store in Redis
            self.redis_client.set(self.state_key, state_json)
            return True
        except Exception as e:
            print(f"Error saving state: {e}")
            return False
    
    def load_state(self) -> Optional[Dict[str, Any]]:
        """Load the simulation state from Redis."""
        try:
            # Get from Redis
            state_json = self.redis_client.get(self.state_key)
            
            if state_json:
                # Parse JSON
                return json.loads(state_json)
            return None
        except Exception as e:
            print(f"Error loading state: {e}")
            return None
    
    def clear_state(self) -> bool:
        """Clear the stored state."""
        try:
            self.redis_client.delete(self.state_key)
            return True
        except Exception as e:
            print(f"Error clearing state: {e}")
            return False