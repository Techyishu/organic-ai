import os
from datetime import datetime
from typing import Dict, List, Optional
import time
from openai import OpenAI
from database_manager import DatabaseManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DebateManager:
    def __init__(self):
        self.active_debates: Dict[int, Dict] = {}
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
            
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1",
            default_headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )
        self.db = DatabaseManager(os.getenv('DB_PATH', 'debates.db'))

    async def initialize(self):
        """Initialize the database."""
        await self.db.initialize()

    def is_debate_active(self, chat_id: int) -> bool:
        """Check if there's an active debate for the given chat_id."""
        return chat_id in self.active_debates

    async def start_debate(self, chat_id: int, topic: str):
        """Initialize a new debate session."""
        self.active_debates[chat_id] = {
            'topic': topic,
            'context': [],
            'started_at': datetime.now()
        }
        await self.db.start_debate(chat_id, topic)

    async def get_counter_argument(self, chat_id: int, user_argument: str) -> str:
        """Generate a response that helps users vent their frustrations."""
        if chat_id not in self.active_debates:
            raise ValueError("No active debate found")

        debate = self.active_debates[chat_id]
        await self.db.add_message(chat_id, "user", user_argument)
        debate['context'].append({"role": "user", "content": user_argument})

        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                messages = [
                    {
                        "role": "system", 
                        "content": (
                            f"You are a debate partner specifically designed to help people vent about {debate['topic']}. "
                            "Your role is to engage with emotional and frustrating topics only.\n\n"
                            "Core rules:\n"
                            "1. Only respond to messages expressing frustration, anger, or complaints\n"
                            "2. If the user asks general questions or non-emotional topics, remind them this is a venting space\n"
                            "3. Keep responses very short (1-2 sentences)\n"
                            "4. Always validate their feelings first\n"
                            "5. Then gently challenge their perspective\n"
                            "6. Use phrases like 'I hear you', 'That sucks', 'I get why you're mad'\n"
                            "7. Talk like an empathetic friend\n"
                            "8. If user isn't venting, say: 'Hey, I'm here to help you vent! Tell me what's really bothering you about this.'"
                        )
                    },
                    # Example exchanges showing how to handle different types of messages
                    {
                        "role": "user",
                        "content": "What's the capital of France?"
                    },
                    {
                        "role": "assistant",
                        "content": "Hey, I'm here to help you vent! Tell me what's really bothering you instead."
                    },
                    {
                        "role": "user",
                        "content": "I'm so sick of my job, nobody appreciates my work!"
                    },
                    {
                        "role": "assistant",
                        "content": "That really sucks! Being undervalued is awful. Have you thought about showing them what'd happen if you stopped doing so much?"
                    },
                    # Add recent context
                    *debate['context'][-2:]
                ]

                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=messages,
                    temperature=0.9,
                    max_tokens=60,
                    stream=False,
                    presence_penalty=0.7,
                    frequency_penalty=0.7
                )

                counter_argument = response.choices[0].message.content
                
                # Keep responses very short
                if len(counter_argument.split()) > 30:
                    counter_argument = '. '.join(counter_argument.split('.')[:1]) + '.'

                await self.db.add_message(chat_id, "assistant", counter_argument)
                debate['context'].append(
                    {"role": "assistant", "content": counter_argument}
                )
                return counter_argument

            except Exception as e:
                retry_count += 1
                if retry_count == max_retries:
                    raise Exception(f"API error after {max_retries} retries: {str(e)}")
                time.sleep(1)
                continue

    async def end_debate(self, chat_id: int) -> str:
        """End the current debate and provide a summary."""
        if chat_id not in self.active_debates:
            return "No active debate to end."

        debate_summary = await self.db.end_debate(chat_id)
        if not debate_summary:
            return "Error retrieving debate summary."

        del self.active_debates[chat_id]
        return self._generate_summary(debate_summary)

    def _generate_summary(self, debate: Dict) -> str:
        """Generate a friendly summary of the venting session."""
        summary = [
            f"🎭 Venting Session About: {debate['topic']}\n",
            f"⏱️ Time Spent: {datetime.now() - debate['started_at']}\n",
            "\n💭 Highlights:"
        ]

        # Keep only key moments
        messages = debate['messages']
        if len(messages) > 4:  # If more than 4 messages
            messages = messages[:2] + messages[-2:]  # Keep first and last exchange

        for message in messages:
            role = "😤" if message["role"] == "user" else "🤔"
            summary.append(f"\n{role} {message['content']}")

        summary.append("\n\n🌟 Hope you're feeling better now!")
        return "\n".join(summary) 