import logging
import asyncio
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from debate_manager import DebateManager
from security_manager import SecurityManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ensure data directory exists
data_dir = os.path.dirname(os.getenv('DB_PATH', 'data/debates.db'))
os.makedirs(data_dir, exist_ok=True)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get predefined topics from environment or use defaults
PREDEFINED_TOPICS = os.getenv('PREDEFINED_TOPICS', 
    "Climate Change,AI Ethics,Universal Basic Income,Social Media Impact,Space Exploration"
).split(',')

class DebateBot:
    def __init__(self):
        self.debate_manager = DebateManager()
        self.security_manager = SecurityManager()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send a message when the command /start is issued."""
        if update.message is None:
            return
            
        welcome_message = (
            "Welcome to the AI Debate Partner Bot! 🎯\n\n"
            "I'm here to help you practice your debating skills. "
            "You can:\n"
            "- /topic [your topic] - Start a debate on a specific topic\n"
            "- /suggest - Get topic suggestions\n"
            "- /end - End the current debate\n\n"
            "To begin, use /topic followed by your chosen topic!"
        )
        await update.message.reply_text(welcome_message)
        logger.info(f"Start command received from user {update.message.from_user.id}")

    async def suggest_topics(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Suggest debate topics when /suggest is issued."""
        if update.message is None:
            return
            
        topics_message = "Here are some suggested topics for debate:\n\n" + \
                        "\n".join(f"• {topic}" for topic in PREDEFINED_TOPICS)
        await update.message.reply_text(topics_message)
        logger.info(f"Suggest command received from user {update.message.from_user.id}")

    async def handle_topic(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /topic command to start a debate."""
        if update.message is None:
            return
            
        if not context.args:
            await update.message.reply_text(
                "Please provide a topic after /topic command.\n"
                "Example: /topic Climate Change"
            )
            return

        topic = " ".join(context.args)
        await self.debate_manager.start_debate(update.message.chat_id, topic)
        await update.message.reply_text(
            f"Great! Let's debate about {topic}.\n"
            "Please provide your initial argument."
        )
        logger.info(f"Topic command received from user {update.message.from_user.id}: {topic}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user messages with security checks."""
        if update.message is None or update.message.from_user is None:
            return
            
        user_id = update.message.from_user.id
        chat_id = update.message.chat_id
        user_argument = update.message.text

        # Security checks
        if not self.security_manager.is_user_allowed(user_id):
            await update.message.reply_text("Sorry, you're not authorized to use this bot.")
            return

        if not self.security_manager.check_rate_limit(user_id):
            await update.message.reply_text(
                "You've been temporarily rate-limited. Please try again later."
            )
            return

        if not self.security_manager.check_message_length(user_argument):
            await update.message.reply_text(
                f"Message too long. Please keep it under {self.security_manager.max_message_length} characters."
            )
            return

        if not self.debate_manager.is_debate_active(chat_id):
            await update.message.reply_text(
                "No active debate. Use /topic to start a new debate!"
            )
            return

        try:
            logger.info(f"Processing argument from user {update.message.from_user.id}")
            response = await self.debate_manager.get_counter_argument(
                chat_id, user_argument
            )
            await update.message.reply_text(response)
            logger.info(f"Sent response to user {update.message.from_user.id}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await update.message.reply_text(
                "Sorry, I encountered an error. Please try again."
            )

    async def end_debate(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """End the current debate and provide a summary."""
        if update.message is None:
            return
            
        chat_id = update.message.chat_id
        summary = await self.debate_manager.end_debate(chat_id)
        await update.message.reply_text(summary)
        logger.info(f"End debate command received from user {update.message.from_user.id}")

    async def ban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin command to ban users."""
        if update.message is None or update.message.from_user is None:
            return

        if not self.security_manager.is_admin(update.message.from_user.id):
            await update.message.reply_text("You don't have permission to use this command.")
            return

        try:
            user_id = int(context.args[0])
            duration = int(context.args[1]) if len(context.args) > 1 else 60
            self.security_manager.ban_user(user_id, duration)
            await update.message.reply_text(f"User {user_id} has been banned for {duration} minutes.")
        except (ValueError, IndexError):
            await update.message.reply_text("Usage: /ban <user_id> [duration_minutes]")

async def start_bot():
    """Initialize and start the bot."""
    # Get telegram token from environment
    token = os.getenv('TELEGRAM_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_TOKEN not found in environment variables")

    # Initialize bot and database
    bot = DebateBot()
    await bot.debate_manager.initialize()
    logger.info("Database initialized")
    
    # Create the Application
    application = Application.builder().token(token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("suggest", bot.suggest_topics))
    application.add_handler(CommandHandler("topic", bot.handle_topic))
    application.add_handler(CommandHandler("end", bot.end_debate))
    application.add_handler(CommandHandler("ban", bot.ban_user))
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, 
        bot.handle_message
    ))
    
    logger.info("Starting bot...")
    
    # Start the application
    await application.initialize()
    await application.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )
    
    try:
        # Keep the bot running
        await application.start()
        await asyncio.Event().wait()  # run forever
    finally:
        # Properly shut down the application
        await application.stop()
        await application.shutdown()

if __name__ == '__main__':
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot stopped due to error: {e}") 