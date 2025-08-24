from pymongo import MongoClient
from datetime import datetime
from typing import Optional, Dict, Any
import config

class Database:
    
    def __init__(self):
        self.client = MongoClient(config.MONGODB_URL)
        self.db = self.client[config.DATABASE_NAME]
        self.users = self.db.users
        
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user data from database"""
        return self.users.find_one({"_id": user_id})
    
    def create_user(self, user_id: int, username: str, first_name: str) -> bool:
        """Create new user in database"""
        try:
            user_data = {
                "_id": user_id,
                "username": username,
                "first_name": first_name,
                "current_step": 1,
                "steps_completed": {},
                "bep20_address": None,
                "social_usernames": {
                    "twitter": None,
                    "instagram": None
                },
                "screenshots": [],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            self.users.insert_one(user_data)
            return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    def update_user_step(self, user_id: int, step: int, completed: bool = True) -> bool:
        """Update user's current step and completion status"""
        try:
            update_data = {
                "current_step": step + 1 if completed else step,
                f"steps_completed.step_{step}": completed,
                "updated_at": datetime.now()
            }
            
            result = self.users.update_one(
                {"_id": user_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error updating user step: {e}")
            return False
    
    def save_social_username(self, user_id: int, platform: str, username: str) -> bool:
        """Save user's social media username"""
        try:
            result = self.users.update_one(
                {"_id": user_id},
                {"$set": {
                    f"social_usernames.{platform}": username,
                    "updated_at": datetime.now()
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error saving {platform} username: {e}")
            return False
    
    def save_bep20_address(self, user_id: int, address: str) -> bool:
        """Save user's BEP20 address"""
        try:
            result = self.users.update_one(
                {"_id": user_id},
                {"$set": {
                    "bep20_address": address,
                    "updated_at": datetime.now()
                }}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error saving BEP20 address: {e}")
            return False
    
    def add_screenshot(self, user_id: int, file_id: str, file_name: str) -> bool:
        """Add screenshot to user's record"""
        try:
            screenshot_data = {
                "file_id": file_id,
                "file_name": file_name,
                "uploaded_at": datetime.now()
            }
            
            result = self.users.update_one(
                {"_id": user_id},
                {"$push": {"screenshots": screenshot_data},
                 "$set": {"updated_at": datetime.now()}}
            )
            return result.modified_count > 0
        except Exception as e:
            print(f"Error adding screenshot: {e}")
            return False
    
    def get_user_stats(self) -> Dict:
        """Get overall bot statistics"""
        try:
            total_users = self.users.count_documents({})
            completed_users = self.users.count_documents({"current_step": {"$gte": 7}})
            
            return {
                "total_users": total_users,
                "completed_users": completed_users,
                "completion_rate": (completed_users / total_users * 100) if total_users > 0 else 0
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {"total_users": 0, "completed_users": 0, "completion_rate": 0}
    
    def close_connection(self):
        """Close database connection"""
        self.client.close()