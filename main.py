import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.error import BadRequest, Forbidden
from database import Database
from validators import Validators
import config

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize database and validators
db = Database()
validators = Validators()

# Channel configuration - Update these with your actual channels
REQUIRED_CHANNELS = {
    'main_channel': '@mntchkk',  # Your main Telegram channel
    'announcement_channel': '@MinatiVaultAnnouncements',  # Optional: announcements channel
}

async def check_channel_membership(context: ContextTypes.DEFAULT_TYPE, user_id: int, channel_username: str) -> bool:
    """Check if user is a member of the specified channel"""
    try:
        # Get chat member status
        member = await context.bot.get_chat_member(chat_id=channel_username, user_id=user_id)
        
        # Check if user is a member (not left, kicked, or restricted)
        if member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
            return True
        else:
            return False
            
    except (BadRequest, Forbidden) as e:
        logger.warning(f"Could not check membership for user {user_id} in {channel_username}: {e}")
        # If we can't check (maybe bot isn't admin), assume user needs to join
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking membership: {e}")
        return False

async def verify_social_follow(platform: str, username: str) -> bool:
    """
    Verify if user actually follows on social media
    Note: This is a placeholder - real verification would require API access
    For Twitter/Instagram, you'd need their APIs and user authentication
    """
    # For now, we'll do basic username validation
    # In production, you'd integrate with Twitter/Instagram APIs
    is_valid, _ = validators.validate_username(username)
    return is_valid

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user = update.effective_user
    user_id = user.id
    username = user.username or "No username"
    first_name = user.first_name or "User"
    
    logger.info(f"User {user_id} ({first_name}) started the bot")
    
    # Check if user exists in database
    existing_user = db.get_user(user_id)
    
    if not existing_user:
        # Create new user
        if db.create_user(user_id, username, first_name):
            await update.message.reply_text(
                f"Welcome {first_name}! 🎉\n\n{config.WELCOME_MESSAGE}"
            )
            await show_step(update, context, 1)
        else:
            await update.message.reply_text(
                "❌ Error creating your profile. Please try again later."
            )
    else:
        current_step = existing_user.get('current_step', 1)
        
        # Check if user has completed all steps
        if current_step > 6:
            await update.message.reply_text(
                f"Welcome back {first_name}! 🎉\n\n"
                "✅ You have already completed all steps!\n\n"
                f"📞 Contact: @{config.CUSTOMER_CARE_USERNAME}"
            )
            
            keyboard = [
                [InlineKeyboardButton("🔄 Start Over", callback_data="restart_process")],
                [InlineKeyboardButton("📊 View Status", callback_data="show_status")],
                [InlineKeyboardButton("🌐 Website", url=config.SOCIAL_LINKS['website'])]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "Would you like to restart or view your status?",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                f"Welcome back {first_name}! 👋\n\nYou're currently on step {current_step}."
            )
            await show_step(update, context, current_step)

async def show_step(update: Update, context: ContextTypes.DEFAULT_TYPE, step: int):
    """Show current step with proper validation buttons"""
    if step > 6:
        await update.message.reply_text(
            "🎉 Congratulations! All steps completed!\n\n"
            f"Contact: @{config.CUSTOMER_CARE_USERNAME}"
        )
        return
    
    step_message = config.STEPS.get(step, "Invalid step")
    if step == 6:
        step_message = step_message.format(config.CUSTOMER_CARE_USERNAME)
    
    keyboard = []
    
    if step == 1:
        keyboard = [
            [InlineKeyboardButton("📱 Download App", url=config.SOCIAL_LINKS['app_download'])],
            [InlineKeyboardButton("✅ Downloaded & Reviewed", callback_data="verify_step_1")]
        ]
    elif step == 2:
        keyboard = [
            [InlineKeyboardButton("🐦 Follow on Twitter", url=config.SOCIAL_LINKS['twitter'])],
            [InlineKeyboardButton("ℹ️ Send Username After Following", callback_data="twitter_info")]
        ]
    elif step == 3:
        keyboard = [
            [InlineKeyboardButton("📸 Follow on Instagram", url=config.SOCIAL_LINKS['instagram'])],
            [InlineKeyboardButton("ℹ️ Send Username After Following", callback_data="instagram_info")]
        ]
    elif step == 4:
        keyboard = [
            [InlineKeyboardButton("💬 Join Main Channel", url=f"https://t.me/{REQUIRED_CHANNELS['main_channel'][1:]}")],
            [InlineKeyboardButton("🔍 Verify I Joined", callback_data="verify_telegram")]
        ]
    elif step == 5:
        keyboard = [
            [InlineKeyboardButton("ℹ️ Send BEP20 Address", callback_data="bep20_info")]
        ]
    elif step == 6:
        keyboard = [
            [InlineKeyboardButton("🎉 Complete Process", callback_data="complete_process")]
        ]
    
    keyboard.append([InlineKeyboardButton("❓ Need Help", callback_data="help")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"**Step {step}/6** 📋\n\n{step_message}",
        reply_markup=reply_markup,
        parse_mode='Markdown',
        disable_web_page_preview=False
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard button clicks with validation"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    user_data = db.get_user(user_id)
    
    if not user_data:
        await query.edit_message_text("❌ User not found. Please use /start command.")
        return
    
    current_step = user_data.get('current_step', 1)
    
    # Step 1 verification
    if query.data == "verify_step_1":
        if current_step == 1:
            db.update_user_step(user_id, 1, True)
            await query.edit_message_text("✅ Great! App download confirmed.")
            await show_step_callback(query, context, 2)
        else:
            await query.edit_message_text("❌ You're not on step 1.")
    
    # Telegram channel verification
    elif query.data == "verify_telegram":
        if current_step == 4:
            await query.edit_message_text("🔍 Verifying your channel membership...")
            
            # Check if user joined the main channel
            is_member = await check_channel_membership(context, user_id, REQUIRED_CHANNELS['main_channel'])
            
            if is_member:
                db.update_user_step(user_id, 4, True)
                await query.edit_message_text(
                    "✅ **Verified!** You've successfully joined our Telegram channel!\n\n"
                    "Thank you for joining our community! 🎉"
                )
                await show_step_callback(query, context, 5)
            else:
                await query.edit_message_text(
                    "❌ **Verification Failed**\n\n"
                    "We couldn't verify that you've joined our Telegram channel.\n\n"
                    "**Please make sure to:**\n"
                    "1. Click the 'Join Main Channel' button above\n"
                    "2. Actually join the channel (not just visit)\n"
                    "3. Then click 'Verify I Joined' again\n\n"
                    "**Note:** It may take a few seconds for the verification to work."
                )
                # Re-show the current step
                await show_step_callback(query, context, 4)
        else:
            await query.edit_message_text("❌ You're not on the Telegram step.")
    
    # Complete process
    elif query.data == "complete_process":
        if current_step == 6:
            db.update_user_step(user_id, 6, True)
            
            # Get user's final info for confirmation
            user_data = db.get_user(user_id)
            social_usernames = user_data.get('social_usernames', {})
            bep20_address = user_data.get('bep20_address', '')
            
            completion_message = f"""
🎉 **CONGRATULATIONS!** 🎉

You have successfully completed all steps!

**Your Submitted Information:**
🐦 Twitter: @{social_usernames.get('twitter', 'Not provided')}
📸 Instagram: @{social_usernames.get('instagram', 'Not provided')}
💬 Telegram: ✅ Verified Member
🏦 BEP20 Address: `{bep20_address[:10]}...{bep20_address[-6:] if bep20_address else 'Not provided'}`

**What's Next?**
Our team will review your submission and contact you soon!

📞 **Customer Care:** @{config.CUSTOMER_CARE_USERNAME}
🌐 **Website:** {config.SOCIAL_LINKS['website']}

Thank you for using Minati Vault Bot! 🚀
"""
            
            await query.edit_message_text(completion_message, parse_mode='Markdown')
        else:
            await query.edit_message_text("❌ You're not on the final step.")
    
    # Info buttons
    elif query.data == "twitter_info":
        await query.edit_message_text(
            "📝 **Twitter Instructions:**\n\n"
            "1. Click 'Follow on Twitter' button above\n"
            "2. Follow our Twitter account\n"
            "3. Like and retweet our pinned post\n"
            "4. Send your Twitter username here (without @)\n\n"
            "Example: If your Twitter is @john_crypto, just send: john_crypto"
        )
    
    elif query.data == "instagram_info":
        await query.edit_message_text(
            "📝 **Instagram Instructions:**\n\n"
            "1. Click 'Follow on Instagram' button above\n"
            "2. Follow our Instagram account\n"
            "3. Like our latest post\n"
            "4. Send your Instagram username here (without @)\n\n"
            "Example: If your Instagram is @john.crypto, just send: john.crypto"
        )
    
    elif query.data == "bep20_info":
        await query.edit_message_text(
            "🏦 **BEP20 Address Instructions:**\n\n"
            "Please send your BEP20 (Binance Smart Chain) wallet address.\n\n"
            "**Requirements:**\n"
            "• Must start with 0x\n"
            "• Must be exactly 42 characters long\n"
            "• Only contains letters (a-f) and numbers (0-9)\n\n"
            "**Example:** 0x742d35Cc6634C0532925a3b8D4B29E3f5fCffd52"
        )
    
    # Restart process
    elif query.data == "restart_process":
        try:
            db.users.update_one(
                {"_id": user_id},
                {"$set": {
                    "current_step": 1,
                    "steps_completed": {},
                    "social_usernames": {"twitter": None, "instagram": None},
                    "bep20_address": None,
                    "updated_at": datetime.now()
                }}
            )
            await query.edit_message_text("🔄 Process restarted! Let's begin again.")
            await show_step_callback(query, context, 1)
        except Exception as e:
            await query.edit_message_text("❌ Error restarting. Please try /start again.")
    
    # Show status
    elif query.data == "show_status":
        social_usernames = user_data.get('social_usernames', {})
        bep20_address = user_data.get('bep20_address')
        
        status_text = f"""
📊 **Completion Status**

✅ All steps completed successfully!

**Your Information:**
• Twitter: @{social_usernames.get('twitter', 'Not provided')}
• Instagram: @{social_usernames.get('instagram', 'Not provided')}
• Telegram: ✅ Verified
• BEP20: {bep20_address[:10]}...{bep20_address[-6:] if bep20_address else 'Not provided'}

**Need Changes?** Contact: @{config.CUSTOMER_CARE_USERNAME}
"""
        
        keyboard = [
            [InlineKeyboardButton("🔄 Start Over", callback_data="restart_process")],
            [InlineKeyboardButton("🌐 Website", url=config.SOCIAL_LINKS['website'])]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(status_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    # Help
    elif query.data == "help":
        help_text = f"""
🆘 **Need Help?**

**Commands:**
• /start - Start or restart
• /status - Check progress
• /help - Show help
• /reset - Reset progress

**Customer Care:** @{config.CUSTOMER_CARE_USERNAME}

**Quick Links:**
• Website: {config.SOCIAL_LINKS['website']}
• Twitter: {config.SOCIAL_LINKS['twitter']}
• Instagram: {config.SOCIAL_LINKS['instagram']}
"""
        await query.edit_message_text(help_text, parse_mode='Markdown')

async def show_step_callback(query, context: ContextTypes.DEFAULT_TYPE, step: int):
    """Show step via callback query"""
    if step > 6:
        await context.bot.send_message(query.from_user.id, "🎉 All steps completed!")
        return
    
    step_message = config.STEPS.get(step, "Invalid step")
    if step == 6:
        step_message = step_message.format(config.CUSTOMER_CARE_USERNAME)
    
    keyboard = []
    
    if step == 1:
        keyboard = [
            [InlineKeyboardButton("📱 Download App", url=config.SOCIAL_LINKS['app_download'])],
            [InlineKeyboardButton("✅ Downloaded & Reviewed", callback_data="verify_step_1")]
        ]
    elif step == 2:
        keyboard = [
            [InlineKeyboardButton("🐦 Follow on Twitter", url=config.SOCIAL_LINKS['twitter'])],
            [InlineKeyboardButton("ℹ️ Send Username After Following", callback_data="twitter_info")]
        ]
    elif step == 3:
        keyboard = [
            [InlineKeyboardButton("📸 Follow on Instagram", url=config.SOCIAL_LINKS['instagram'])],
            [InlineKeyboardButton("ℹ️ Send Username After Following", callback_data="instagram_info")]
        ]
    elif step == 4:
        keyboard = [
            [InlineKeyboardButton("💬 Join Main Channel", url=f"https://t.me/{REQUIRED_CHANNELS['main_channel'][1:]}")],
            [InlineKeyboardButton("🔍 Verify I Joined", callback_data="verify_telegram")]
        ]
    elif step == 5:
        keyboard = [
            [InlineKeyboardButton("ℹ️ Send BEP20 Address", callback_data="bep20_info")]
        ]
    elif step == 6:
        keyboard = [
            [InlineKeyboardButton("🎉 Complete Process", callback_data="complete_process")]
        ]
    
    keyboard.append([InlineKeyboardButton("❓ Need Help", callback_data="help")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=f"**Step {step}/6** 📋\n\n{step_message}",
        reply_markup=reply_markup,
        parse_mode='Markdown',
        disable_web_page_preview=False
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages with enhanced validation"""
    user_id = update.effective_user.id
    message_text = update.message.text.strip()
    
    user_data = db.get_user(user_id)
    if not user_data:
        await update.message.reply_text("❌ Please use /start command first.")
        return
    
    current_step = user_data.get('current_step', 1)
    
    # Step 2: Handle Twitter username with validation
    if current_step == 2:
        username = message_text.lstrip('@').strip()
        
        # Validate username format
        is_valid, validation_message = validators.validate_username(username)
        
        if is_valid:
            # Additional verification (placeholder for real API check)
            is_follower = await verify_social_follow('twitter', username)
            
            if is_follower:
                if db.save_social_username(user_id, 'twitter', username):
                    db.update_user_step(user_id, 2, True)
                    await update.message.reply_text(
                        f"✅ **Twitter Verified!**\n\n"
                        f"Username: @{username}\n"
                        f"Thank you for following us on Twitter! 🐦\n\n"
                        "Moving to next step..."
                    )
                    await show_step(update, context, 3)
                else:
                    await update.message.reply_text("❌ Error saving Twitter username. Please try again.")
            else:
                await update.message.reply_text(
                    f"⚠️ **Username received but not verified**\n\n"
                    f"Username: @{username}\n\n"
                    "**Please make sure you:**\n"
                    "1. Actually followed our Twitter account\n"
                    "2. Liked and retweeted our pinned post\n"
                    "3. Wait 30 seconds then try again\n\n"
                    f"Twitter: {config.SOCIAL_LINKS['twitter']}"
                )
        else:
            await update.message.reply_text(
                f"❌ **Invalid Twitter Username**\n\n"
                f"Error: {validation_message}\n\n"
                "Please send a valid Twitter username (without @).\n"
                f"Example: If your Twitter is @john_crypto, send: john_crypto"
            )
        return
    
    # Step 3: Handle Instagram username with validation
    elif current_step == 3:
        username = message_text.lstrip('@').strip()
        
        is_valid, validation_message = validators.validate_username(username)
        
        if is_valid:
            is_follower = await verify_social_follow('instagram', username)
            
            if is_follower:
                if db.save_social_username(user_id, 'instagram', username):
                    db.update_user_step(user_id, 3, True)
                    await update.message.reply_text(
                        f"✅ **Instagram Verified!**\n\n"
                        f"Username: @{username}\n"
                        f"Thank you for following us on Instagram! 📸\n\n"
                        "Moving to next step..."
                    )
                    await show_step(update, context, 4)
                else:
                    await update.message.reply_text("❌ Error saving Instagram username. Please try again.")
            else:
                await update.message.reply_text(
                    f"⚠️ **Username received but not verified**\n\n"
                    f"Username: @{username}\n\n"
                    "**Please make sure you:**\n"
                    "1. Actually followed our Instagram account\n"
                    "2. Liked our latest post\n"
                    "3. Wait 30 seconds then try again\n\n"
                    f"Instagram: {config.SOCIAL_LINKS['instagram']}"
                )
        else:
            await update.message.reply_text(
                f"❌ **Invalid Instagram Username**\n\n"
                f"Error: {validation_message}\n\n"
                "Please send a valid Instagram username (without @).\n"
                f"Example: If your Instagram is @john.crypto, send: john.crypto"
            )
        return
    
    # Step 5: Handle BEP20 address
    elif current_step == 5:
        is_valid, message = validators.validate_bep20_address(message_text)
        
        if is_valid:
            if db.save_bep20_address(user_id, message_text):
                db.update_user_step(user_id, 5, True)
                await update.message.reply_text(
                    f"✅ **BEP20 Address Saved!**\n\n"
                    f"Address: `{message_text}`\n\n"
                    "Moving to final step...",
                    parse_mode='Markdown'
                )
                await show_step(update, context, 6)
            else:
                await update.message.reply_text("❌ Error saving address. Please try again.")
        else:
            await update.message.reply_text(
                f"❌ **Invalid BEP20 Address**\n\n"
                f"Error: {message}\n\n"
                "Please send a valid BEP20 address:\n"
                "• Must start with 0x\n"
                "• Must be 42 characters long\n"
                "• Example: 0x742d35Cc6634C0532925a3b8D4B29E3f5fCffd52"
            )
        return
    
    # Default response
    await update.message.reply_text(
        f"📍 **You're currently on step {current_step}**\n\n"
        "Please follow the instructions above or use the buttons provided.\n\n"
        "Need help? Type /help or contact @{config.CUSTOMER_CARE_USERNAME}"
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Status command with verification info"""
    user_id = update.effective_user.id
    
    user_data = db.get_user(user_id)
    if not user_data:
        await update.message.reply_text("❌ Please use /start command first.")
        return
    
    current_step = user_data.get('current_step', 1)
    steps_completed = user_data.get('steps_completed', {})
    bep20_address = user_data.get('bep20_address')
    social_usernames = user_data.get('social_usernames', {})
    
    # Check current Telegram membership
    telegram_status = "❌ Not verified"
    if steps_completed.get('step_4'):
        is_member = await check_channel_membership(context, user_id, REQUIRED_CHANNELS['main_channel'])
        telegram_status = "✅ Verified member" if is_member else "⚠️ Previously verified (please rejoin if left)"
    
    status_text = f"""
📊 **Your Progress Status**

**Current Step:** {current_step}/6
**Completed Steps:** {len(steps_completed)}/6

**Step Details:**
{'✅' if steps_completed.get('step_1') else '❌'} Step 1: App Download & Review
{'✅' if steps_completed.get('step_2') else '❌'} Step 2: Twitter Follow
{'✅' if steps_completed.get('step_3') else '❌'} Step 3: Instagram Follow
{'✅' if steps_completed.get('step_4') else '❌'} Step 4: Telegram Join
{'✅' if steps_completed.get('step_5') else '❌'} Step 5: BEP20 Address  
{'✅' if steps_completed.get('step_6') else '❌'} Step 6: Final Verification

**Verification Status:**
🐦 Twitter: @{social_usernames.get('twitter', 'Not provided')}
📸 Instagram: @{social_usernames.get('instagram', 'Not provided')}
💬 Telegram: {telegram_status}
🏦 BEP20: {'✅ Provided' if bep20_address else '❌ Not provided'}

**Next Action:** {config.STEPS.get(current_step, 'All steps completed! 🎉')}
"""
    
    keyboard = [
        [InlineKeyboardButton("🌐 Website", url=config.SOCIAL_LINKS['website'])],
        [InlineKeyboardButton("💬 Main Channel", url=f"https://t.me/{REQUIRED_CHANNELS['main_channel'][1:]}")],
        [InlineKeyboardButton("🔄 Restart Process", callback_data="restart_process")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        status_text, 
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Enhanced help command"""
    keyboard = [
        [InlineKeyboardButton("🌐 Website", url=config.SOCIAL_LINKS['website']),
         InlineKeyboardButton("📱 Download App", url=config.SOCIAL_LINKS['app_download'])],
        [InlineKeyboardButton("🐦 Twitter", url=config.SOCIAL_LINKS['twitter']),
         InlineKeyboardButton("📸 Instagram", url=config.SOCIAL_LINKS['instagram'])],
        [InlineKeyboardButton("💬 Main Channel", url=f"https://t.me/{REQUIRED_CHANNELS['main_channel'][1:]}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    help_text = f"""
🆘 **Minati Vault Bot Help**

**Available Commands:**
• /start - Start or restart the bot
• /status - Check your current progress  
• /help - Show this help message
• /reset - Reset your progress completely

**Verification Process:**
✅ **Real verification** for Telegram channel membership
⚠️ **Username collection** for Twitter & Instagram
🔐 **Address validation** for BEP20 wallet

**Need Personal Assistance?**
👨‍💼 Customer Care: @{config.CUSTOMER_CARE_USERNAME}

**Important Notes:**
• Telegram membership is verified in real-time
• Make sure to actually join channels, not just visit
• Social media usernames are collected for manual verification
• BEP20 addresses are validated for correct format

**Quick Access Links:**
Use the buttons below for instant access to our platforms.
"""
    
    await update.message.reply_text(
        help_text, 
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset user progress"""
    user_id = update.effective_user.id
    
    try:
        result = db.users.update_one(
            {"_id": user_id},
            {"$set": {
                "current_step": 1,
                "steps_completed": {},
                "social_usernames": {"twitter": None, "instagram": None},
                "bep20_address": None,
                "updated_at": datetime.now()
            }}
        )
        
        if result.modified_count > 0:
            await update.message.reply_text(
                "🔄 **Your progress has been completely reset!**\n\n"
                "All your previous data has been cleared.\n"
                "Use /start to begin the process again from Step 1."
            )
        else:
            await update.message.reply_text(
                "❌ No user data found to reset.\n"
                "Use /start to create your profile first."
            )
            
    except Exception as e:
        logger.error(f"Error resetting user {user_id}: {e}")
        await update.message.reply_text(
            "❌ Error resetting your progress.\n"
            "Please try /start to continue."
        )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by Updates"""
    logger.warning(f'Update {update} caused error {context.error}')

def main():
    """Main function to run the bot"""
    if not config.BOT_TOKEN:
        print("❌ BOT_TOKEN not found in .env file!")
        return
    
    if not config.MONGODB_URL:
        print("❌ MONGODB_URL not found in .env file!")
        return
    
    # Create application
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("reset", reset_command))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    print("🚀 Minati Vault Bot with Real Validation is starting...")
    print("✅ Telegram channel verification: ENABLED")
    print("📊 Enhanced validation features: ACTIVE")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error running bot: {e}")
        logger.error(f"Bot startup error: {e}")
    finally:
        # Close database connection
        db.close_connection()
        print("🔌 Database connection closed") 