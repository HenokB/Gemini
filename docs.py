import json
import asyncio
import os
import google.generativeai as genai

from telegram import Update, ForceReply
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, Application

from dotenv import load_dotenv
load_dotenv()

# Configure the Generative AI model with API key from the environment variable
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

def log_interaction(user_id, message):
    """Logs interactions between the bot and the user to a file.
    
    Args:
        user_id (int): Telegram user ID.
        message (str): Message sent by the user or the bot.
    """
    data = {"user_id": user_id, "message": message}
    with open("user_interactions.json", "a") as file:
        json.dump(data, file)
        file.write('\n')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the '/start' command sent by the user.
    
    Args:
        update (Update): Telegram update object.
        context (ContextTypes): The context of the bot.
    """
    user = update.effective_user
    await update.message.reply_html(rf"Hi {user.mention_html()}!, I'm Gemini.")
    log_interaction(user.id, '/start')
    

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the '/help' command sent by the user.
    
    Args:
        update (Update): Telegram update object.
        context (ContextTypes): The context of the bot.
    """
    await update.message.reply_text("Start asking any textual questions you want, I'm here to help!")
    user = update.effective_user
    log_interaction(user.id, '/help')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles regular text messages sent by the user.
    
    Args:
        update (Update): Telegram update object.
        context (ContextTypes): The context of the bot.
    """
    text = update.message.text
    user = update.effective_user
    log_interaction(user.id, f"User : {text}")

    init_msg = await update.message.reply_text(text="Generating...", reply_to_message_id=update.message.message_id)
    inited = True
    full_bot_response = ""  # Accumulate the bot's response
    response = model.generate_content(text, stream=True)
    
    for chunk in response:
        try:
            if chunk.text:
                message = chunk.text
                full_bot_response += message

                if inited:
                    inited = False
                    await init_msg.edit_text(text=message)
                else:
                    await init_msg.edit_text(text=init_msg.text + message)
        except Exception as e:
            print(e)
            if chunk.text:
                await update.message.reply_text(text=chunk.text, reply_to_message_id=init_msg.message_id)
                full_bot_response += chunk.text
        await asyncio.sleep(0.1)

    if full_bot_response:
        log_interaction(user.id, f"Gemini replied: {full_bot_response}")

def main() -> None:
    """Main function to set up and run the Telegram bot."""
    print("Bot is running...")  # Console message indicating that the bot is running
    application = Application.builder().token(os.getenv("BOT_TOKEN")).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
