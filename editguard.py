import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode, ChatMemberStatus
from pyrogram.errors import MessageDeleteForbidden, ChatAdminRequired
import logging
from config import API_ID, API_HASH, BOT_TOKEN

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the bot client
app = Client("edit_delete_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Dictionary to store original messages
original_messages = {}

async def is_admin(chat_id: int, user_id: int) -> bool:
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

@app.on_message(filters.group)
async def store_original_message(client: Client, message: Message):
    """Store original messages to track edits"""
    try:
        # Store the original message content
        original_messages[message.id] = {
            "text": message.text or message.caption,
            "user_id": message.from_user.id,
            "chat_id": message.chat.id,
            "message_id": message.id
        }
        
        # Clean up old messages (keep only last 1000 to save memory)
        if len(original_messages) > 1000:
            # Remove oldest entries
            oldest_keys = list(original_messages.keys())[:100]
            for key in oldest_keys:
                del original_messages[key]
                
    except Exception as e:
        logger.error(f"Error storing message: {e}")

@app.on_edited_message(filters.group)
async def handle_edited_message(client: Client, message: Message):
    """Handle edited messages - delete them and send notification (skip admins)"""
    try:
        # Check if we have the original message stored
        if message.id in original_messages:
            original_data = original_messages[message.id]
            
            # Check if the user is an admin - if yes, skip deletion
            if await is_admin(message.chat.id, message.from_user.id):
                logger.info(f"Skipping deletion - {message.from_user.first_name} is an admin")
                # Remove from storage but don't delete the message
                del original_messages[message.id]
                return
            
            # Delete the edited message (only for non-admins)
            try:
                await message.delete()
                logger.info(f"Deleted edited message from {message.from_user.first_name}")
            except MessageDeleteForbidden:
                logger.warning("Bot doesn't have permission to delete messages")
                return
            except ChatAdminRequired:
                logger.warning("Bot needs admin rights to delete messages")
                return
            
            # Create inline keyboard with "Add me to your group" button
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ", 
                    url=f"https://t.me/{(await client.get_me()).username}?startgroup=true"
                )]
            ])
            
            # Send notification message
            notification_text = f"<b>{message.from_user.first_name} ᴊᴜsᴛ ᴇᴅɪᴛᴇᴅ ᴛʜᴇɪʀ ᴍᴇssᴀɢᴇ, ᴀɴᴅ ɪ ʜᴀᴠᴇ ᴅᴇʟᴇᴛᴇᴅ ɪᴛ.</b>"
            
            await client.send_message(
                chat_id=message.chat.id,
                text=notification_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            
            # Remove the message from our storage
            del original_messages[message.id]
            
    except Exception as e:
        logger.error(f"Error handling edited message: {e}")

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    """Handle /start command"""
    try:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ", 
                url=f"https://t.me/{(await client.get_me()).username}?startgroup=true"
            )],
            [
            InlineKeyboardButton("👤 ᴏᴡɴᴇʀ", user_id=6878311635),
            InlineKeyboardButton("🤝 Sᴜᴘᴘᴏʀᴛ", url="https://t.me/FearlessCheats")
           ]
        ])
        
        bot_info = await client.get_me()
        user_mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"
        bot_mention = f"<a href='tg://user?id={bot_info.id}'>{bot_info.first_name}</a>"
        
        welcome_text = f"""
<b>ʜᴇʏ, {user_mention}

ɪ ᴀᴍ {bot_mention} ♡ 

<u>ꜰᴇᴀᴛᴜʀᴇꜱ:</u>
• ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ ᴅᴇʟᴇᴛᴇ ᴇᴅɪᴛᴇᴅ ᴍᴇꜱꜱᴀɢᴇꜱ (ᴇxᴄᴇᴘᴛ ꜰʀᴏᴍ ᴀᴅᴍɪɴꜱ)
• ɴᴏᴛɪꜰʏ ɢʀᴏᴜᴘ ᴡʜᴇɴ ᴀ ᴍᴇꜱꜱᴀɢᴇ ɪꜱ ᴇᴅɪᴛᴇᴅ
• ᴇᴀꜱʏ ᴛᴏ ᴀᴅᴅ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘꜱ
• ᴀᴅᴍɪɴꜱ ᴄᴀɴ ᴇᴅɪᴛ ᴍᴇꜱꜱᴀɢᴇꜱ ᴡɪᴛʜᴏᴜᴛ ᴅᴇʟᴇᴛɪᴏɴ

<u>ꜱᴇᴛᴜᴘ:</u>
1. ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ
2. ᴍᴀᴋᴇ ᴍᴇ ᴀɴ ᴀᴅᴍɪɴ ᴡɪᴛʜ ᴅᴇʟᴇᴛᴇ ᴍᴇꜱꜱᴀɢᴇꜱ ᴘᴇʀᴍɪꜱꜱɪᴏɴ
3. ɪ'ʟʟ ꜱᴛᴀʀᴛ ᴍᴏɴɪᴛᴏʀɪɴɢ ᴀᴜᴛᴏᴍᴀᴛɪᴄᴀʟʟʏ!

<u>ɴᴏᴛᴇ:</u> ɪ ɴᴇᴇᴅ ᴀᴅᴍɪɴ ʀɪɢʜᴛꜱ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴍᴇꜱꜱᴀɢᴇꜱ. ᴀᴅᴍɪɴ ᴍᴇꜱꜱᴀɢᴇꜱ ᴡᴏɴ'ᴛ ʙᴇ ᴅᴇʟᴇᴛᴇᴅ ᴡʜᴇɴ ᴇᴅɪᴛᴇᴅ.</b>
        """
        
        await message.reply_text(
            welcome_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")

@app.on_message(filters.command("help"))
async def help_command(client: Client, message: Message):
    """Handle /help command"""
    try:
        help_text = """
🆘 **Help - Edit Delete Bot**

**Commands:**
• `/start` - Show welcome message
• `/help` - Show this help message
• `/status` - Check bot status in group

**How it works:**
1. I monitor all messages in the group
2. When someone edits their message, I delete it (except for admins)
3. I send a notification with the person's name
4. The notification includes a button to add me to other groups
5. Admins can edit their messages freely without deletion

**Required Permissions:**
• Delete messages
• Send messages

**Need support?** Contact the bot developer.
        """
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ", 
                url=f"https://t.me/{(await client.get_me()).username}?startgroup=true"
            )]
        ])
        
        await message.reply_text(
            help_text,
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error in help command: {e}")

@app.on_message(filters.command("status") & filters.group)
async def status_command(client: Client, message: Message):
    """Check bot status in group"""
    try:
        bot_member = await client.get_chat_member(message.chat.id, (await client.get_me()).id)
        
        if bot_member.privileges and bot_member.privileges.can_delete_messages:
            status_text = "✅ Bot is working properly! I have permission to delete messages.\n\n📝 Note: Admin messages won't be deleted when edited."
        else:
            status_text = "⚠️ Bot needs admin rights with 'Delete Messages' permission to work properly."
            
        await message.reply_text(status_text)
        
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        await message.reply_text("❌ Error checking bot status.")

@app.on_message(filters.new_chat_members)
async def welcome_new_member(client: Client, message: Message):
    """Welcome message when bot is added to a group"""
    try:
        bot_user = await client.get_me()
        
        # Check if bot was added
        for new_member in message.new_chat_members:
            if new_member.id == bot_user.id:
                welcome_text = f"""
🎉 **Thanks for adding me to {message.chat.title}!**

I'm now monitoring this group for edited messages. 

**Important:** Please make me an admin with "Delete Messages" permission so I can work properly.

**Note:** I won't delete edited messages from group admins.

Use /status to check if I'm configured correctly.
                """
                
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton(
                        "ADD ME TO OTHER GROUPS", 
                        url=f"https://t.me/{bot_user.username}?startgroup=true"
                    )]
                ])
                
                await message.reply_text(
                    welcome_text,
                    reply_markup=keyboard
                )
                break
                
    except Exception as e:
        logger.error(f"Error in welcome message: {e}")

# Error handler
@app.on_message(filters.all, group=-300)
async def error_handler(client: Client, message: Message):
    """Global error handler"""
    pass  # Just to catch any unhandled errors

if __name__ == "__main__":
    print("🤖 Starting Edit Delete Bot...")
    print("📝 Make sure to:")
    print("   1. Replace API_ID, API_HASH, and BOT_TOKEN with your actual values")
    print("   2. Install pyrogram: pip install pyrogram")
    print("   3. Make the bot admin in groups with delete messages permission")
    print("   4. Admins can edit messages without deletion")
    print("🚀 Bot is running...")
    
    app.run()
