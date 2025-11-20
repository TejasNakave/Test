import logging
import logging.handlers
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ..config import settings
from ..schemas import LogEntry, SubscriptionTier
import json
import sqlite3
import aiosqlite

logger = logging.getLogger(__name__)

class LoggerService:
    """Service for logging interactions and managing usage statistics"""
    
    def __init__(self):
        self.db_path = "logs/chatbot_logs.db"
        self.ensure_db_directory()
        self._init_database()
    
    def ensure_db_directory(self):
        """Ensure the logs directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _init_database(self):
        """Initialize the SQLite database with required tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create interactions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        question TEXT NOT NULL,
                        answer TEXT NOT NULL,
                        subscription_tier TEXT NOT NULL,
                        response_time_ms INTEGER NOT NULL,
                        tokens_used INTEGER DEFAULT 0,
                        sources_count INTEGER DEFAULT 0,
                        conversation_id TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create usage_stats table for tracking quotas
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS usage_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        subscription_tier TEXT NOT NULL,
                        questions_count INTEGER DEFAULT 0,
                        last_reset_date DATE DEFAULT CURRENT_DATE,
                        last_activity DATETIME,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id)
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_interactions_user_id ON interactions(user_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_interactions_conversation_id ON interactions(conversation_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON interactions(timestamp)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_usage_stats_user_id ON usage_stats(user_id)")
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise
    
    async def log_interaction(
        self,
        user_id: str,
        question: str,
        answer: str,
        subscription_tier: str,
        response_time_ms: int,
        tokens_used: int = 0,
        sources_count: int = 0,
        conversation_id: Optional[str] = None
    ):
        """Log a user interaction to the database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Insert interaction log
                await db.execute("""
                    INSERT INTO interactions 
                    (user_id, question, answer, subscription_tier, response_time_ms, 
                     tokens_used, sources_count, conversation_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, question, answer, subscription_tier, response_time_ms,
                    tokens_used, sources_count, conversation_id
                ))
                
                # Update or create usage stats
                await db.execute("""
                    INSERT INTO usage_stats (user_id, subscription_tier, questions_count, last_activity)
                    VALUES (?, ?, 1, ?)
                    ON CONFLICT(user_id) DO UPDATE SET
                        questions_count = CASE
                            WHEN date(last_reset_date) < date('now', 'start of month')
                            THEN 1
                            ELSE questions_count + 1
                        END,
                        last_reset_date = CASE
                            WHEN date(last_reset_date) < date('now', 'start of month')
                            THEN date('now', 'start of month')
                            ELSE last_reset_date
                        END,
                        subscription_tier = ?,
                        last_activity = ?,
                        updated_at = CURRENT_TIMESTAMP
                """, (user_id, subscription_tier, datetime.now(), subscription_tier, datetime.now()))
                
                await db.commit()
                
            logger.info(f"Logged interaction for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to log interaction: {str(e)}")
    
    async def get_user_usage_stats(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get usage statistics for a specific user"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get current usage stats
                async with db.execute("""
                    SELECT questions_count, subscription_tier, last_activity, last_reset_date
                    FROM usage_stats 
                    WHERE user_id = ?
                """, (user_id,)) as cursor:
                    row = await cursor.fetchone()
                
                if row:
                    questions_count, tier, last_activity, last_reset_date = row
                    return {
                        "questions_count": questions_count,
                        "subscription_tier": tier,
                        "last_activity": datetime.fromisoformat(last_activity) if last_activity else None,
                        "last_reset_date": last_reset_date
                    }
                else:
                    # User not found, return default stats
                    return {
                        "questions_count": 0,
                        "subscription_tier": "tier_1",
                        "last_activity": None,
                        "last_reset_date": None
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get usage stats for user {user_id}: {str(e)}")
            return {"questions_count": 0, "subscription_tier": "tier_1", "last_activity": None}
    
    async def get_user_usage_history(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get detailed usage history for a user"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT DATE(timestamp) as date, COUNT(*) as questions_count,
                           AVG(response_time_ms) as avg_response_time,
                           SUM(tokens_used) as total_tokens
                    FROM interactions
                    WHERE user_id = ? AND timestamp BETWEEN ? AND ?
                    GROUP BY DATE(timestamp)
                    ORDER BY date DESC
                """, (user_id, start_date, end_date)) as cursor:
                    rows = await cursor.fetchall()
                
                history = []
                for row in rows:
                    date_str, count, avg_time, total_tokens = row
                    history.append({
                        "date": date_str,
                        "questions_count": count,
                        "avg_response_time_ms": int(avg_time) if avg_time else 0,
                        "total_tokens_used": total_tokens or 0
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Failed to get usage history for user {user_id}: {str(e)}")
            return []
    
    async def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a specific conversation"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT user_id, question, answer, timestamp, response_time_ms, tokens_used
                    FROM interactions
                    WHERE conversation_id = ?
                    ORDER BY timestamp ASC
                """, (conversation_id,)) as cursor:
                    rows = await cursor.fetchall()
                
                history = []
                for row in rows:
                    user_id, question, answer, timestamp, response_time, tokens = row
                    history.append({
                        "user_id": user_id,
                        "question": question,
                        "answer": answer,
                        "timestamp": timestamp,
                        "response_time_ms": response_time,
                        "tokens_used": tokens
                    })
                
                return history
                
        except Exception as e:
            logger.error(f"Failed to get conversation history: {str(e)}")
            return []
    
    async def reset_user_usage(self, user_id: str):
        """Reset usage statistics for a user (admin function)"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE usage_stats 
                    SET questions_count = 0, 
                        last_reset_date = date('now'),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (user_id,))
                await db.commit()
                
            logger.info(f"Reset usage for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to reset usage for user {user_id}: {str(e)}")
            raise
    
    async def get_global_usage_summary(self) -> Dict[str, Any]:
        """Get global usage summary across all users"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get total interactions
                async with db.execute("SELECT COUNT(*) FROM interactions") as cursor:
                    total_interactions = (await cursor.fetchone())[0]
                
                # Get active users (last 30 days)
                thirty_days_ago = datetime.now() - timedelta(days=30)
                async with db.execute("""
                    SELECT COUNT(DISTINCT user_id) FROM interactions 
                    WHERE timestamp > ?
                """, (thirty_days_ago,)) as cursor:
                    active_users = (await cursor.fetchone())[0]
                
                # Get subscription tier distribution
                async with db.execute("""
                    SELECT subscription_tier, COUNT(*) as count
                    FROM usage_stats
                    GROUP BY subscription_tier
                """) as cursor:
                    tier_rows = await cursor.fetchall()
                
                tier_distribution = {tier: count for tier, count in tier_rows}
                
                # Get average response time
                async with db.execute("""
                    SELECT AVG(response_time_ms) FROM interactions
                    WHERE timestamp > ?
                """, (thirty_days_ago,)) as cursor:
                    avg_response_time = (await cursor.fetchone())[0] or 0
                
                return {
                    "total_interactions": total_interactions,
                    "active_users_30d": active_users,
                    "subscription_tier_distribution": tier_distribution,
                    "avg_response_time_ms": int(avg_response_time),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Failed to get global usage summary: {str(e)}")
            return {}
    
    async def get_user_recent_interactions(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recent interactions for a user"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT question, answer, timestamp, response_time_ms, sources_count
                    FROM interactions 
                    WHERE user_id = ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (user_id, limit)) as cursor:
                    rows = await cursor.fetchall()
                    
                    interactions = []
                    for row in rows:
                        interactions.append({
                            "question": row[0],
                            "answer": row[1],
                            "timestamp": row[2],
                            "response_time_ms": row[3],
                            "sources_count": row[4]
                        })
                    
                    return interactions
                    
        except Exception as e:
            logger.error(f"Failed to get recent interactions for user {user_id}: {str(e)}")
            return []
    
    async def log_proactive_feedback(
        self,
        user_id: str,
        suggestion_id: str,
        feedback_type: str
    ):
        """Log feedback on proactive suggestions for learning purposes"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Create proactive_feedback table if it doesn't exist
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS proactive_feedback (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        suggestion_id TEXT NOT NULL,
                        feedback_type TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert feedback
                await db.execute("""
                    INSERT INTO proactive_feedback (user_id, suggestion_id, feedback_type)
                    VALUES (?, ?, ?)
                """, (user_id, suggestion_id, feedback_type))
                
                await db.commit()
                
            logger.info(f"Logged proactive feedback for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to log proactive feedback: {str(e)}")

def setup_logging():
    """Setup logging configuration for the application"""
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.handlers.RotatingFileHandler(
                settings.LOG_FILE,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)