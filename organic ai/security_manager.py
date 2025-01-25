import time
from typing import Dict, Set
from dataclasses import dataclass
import os
from datetime import datetime, timedelta

@dataclass
class UserActivity:
    message_count: int = 0
    last_reset: datetime = datetime.now()
    is_banned: bool = False
    ban_until: datetime = datetime.min

class SecurityManager:
    def __init__(self):
        # Load admin users from env
        admin_users_str = os.getenv('ADMIN_USERS', '')
        self.admin_users: Set[int] = set(
            int(uid.strip()) for uid in admin_users_str.split(',') if uid.strip()
        ) if admin_users_str else set()
        
        # Rate limiting settings
        self.max_messages_per_minute = int(os.getenv('MAX_MESSAGES_PER_MINUTE', 30))
        self.max_message_length = int(os.getenv('MAX_MESSAGE_LENGTH', 500))
        
        # Track user activity
        self.user_activity: Dict[int, UserActivity] = {}

    def is_user_allowed(self, user_id: int) -> bool:
        """Check if user is allowed to use the bot."""
        return True  # Allow all users

    def is_admin(self, user_id: int) -> bool:
        """Check if user is an admin."""
        return user_id in self.admin_users

    def check_rate_limit(self, user_id: int) -> bool:
        """Check if user has exceeded rate limits."""
        now = datetime.now()
        
        # Initialize user activity if not exists
        if user_id not in self.user_activity:
            self.user_activity[user_id] = UserActivity()
        
        activity = self.user_activity[user_id]
        
        # Check if user is banned
        if activity.is_banned:
            if now < activity.ban_until:
                return False
            activity.is_banned = False
        
        # Reset counter if minute has passed
        if now - activity.last_reset > timedelta(minutes=1):
            activity.message_count = 0
            activity.last_reset = now
        
        # Increment and check counter
        activity.message_count += 1
        if activity.message_count > self.max_messages_per_minute:
            activity.is_banned = True
            activity.ban_until = now + timedelta(minutes=5)
            return False
        
        return True

    def check_message_length(self, message: str) -> bool:
        """Check if message length is within limits."""
        return len(message) <= self.max_message_length

    def ban_user(self, user_id: int, duration_minutes: int = 60):
        """Ban a user for specified duration."""
        if user_id not in self.user_activity:
            self.user_activity[user_id] = UserActivity()
        
        activity = self.user_activity[user_id]
        activity.is_banned = True
        activity.ban_until = datetime.now() + timedelta(minutes=duration_minutes)

    def unban_user(self, user_id: int):
        """Unban a user."""
        if user_id in self.user_activity:
            activity = self.user_activity[user_id]
            activity.is_banned = False
            activity.ban_until = datetime.min 