import aiosqlite
import os
from typing import Dict, List, Optional
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path: str = "debates.db"):
        self.db_path = db_path
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

    async def initialize(self):
        """Initialize the database with required tables."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS debates (
                        chat_id INTEGER,
                        topic TEXT,
                        started_at TIMESTAMP,
                        ended_at TIMESTAMP NULL,
                        PRIMARY KEY (chat_id, started_at)
                    )
                """)
                
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER,
                        debate_started_at TIMESTAMP,
                        role TEXT,
                        content TEXT,
                        timestamp TIMESTAMP,
                        FOREIGN KEY (chat_id, debate_started_at) 
                        REFERENCES debates (chat_id, started_at)
                    )
                """)
                await db.commit()
        except Exception as e:
            raise Exception(f"Database initialization failed: {str(e)}")

    async def start_debate(self, chat_id: int, topic: str) -> None:
        """Start a new debate session."""
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.now()
            await db.execute(
                "INSERT INTO debates (chat_id, topic, started_at) VALUES (?, ?, ?)",
                (chat_id, topic, now)
            )
            await db.commit()

    async def add_message(self, chat_id: int, role: str, content: str) -> None:
        """Add a message to the current debate."""
        async with aiosqlite.connect(self.db_path) as db:
            # Get the current debate's started_at
            cursor = await db.execute(
                """
                SELECT started_at FROM debates 
                WHERE chat_id = ? AND ended_at IS NULL
                ORDER BY started_at DESC LIMIT 1
                """,
                (chat_id,)
            )
            debate = await cursor.fetchone()
            if debate:
                await db.execute(
                    """
                    INSERT INTO messages 
                    (chat_id, debate_started_at, role, content, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (chat_id, debate[0], role, content, datetime.now())
                )
                await db.commit()

    async def end_debate(self, chat_id: int) -> Optional[Dict]:
        """End the current debate and return its summary."""
        async with aiosqlite.connect(self.db_path) as db:
            # Mark debate as ended
            now = datetime.now()
            await db.execute(
                """
                UPDATE debates SET ended_at = ?
                WHERE chat_id = ? AND ended_at IS NULL
                """,
                (now, chat_id)
            )
            await db.commit()

            # Get debate summary
            cursor = await db.execute(
                """
                SELECT d.topic, d.started_at, m.role, m.content
                FROM debates d
                JOIN messages m ON d.chat_id = m.chat_id 
                    AND d.started_at = m.debate_started_at
                WHERE d.chat_id = ? AND d.ended_at = ?
                ORDER BY m.timestamp
                """,
                (chat_id, now)
            )
            messages = await cursor.fetchall()
            
            if not messages:
                return None

            return {
                'topic': messages[0][0],
                'started_at': datetime.fromisoformat(messages[0][1]),
                'messages': [
                    {'role': msg[2], 'content': msg[3]}
                    for msg in messages
                ]
            } 