import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ParseMode, ChatMemberStatus, MessageMediaType
from pyrogram.errors import MessageDeleteForbidden, ChatAdminRequired
import logging
from datetime import datetime, timedelta
import motor.motor_asyncio
from config import API_ID, API_HASH, BOT_TOKEN, MONGODB_URI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the bot client
app = Client("edit_delete_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# MongoDB setup
client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client.editguard_bot
messages_collection = db.messages

class MessageStorage:
    """MongoDB-based message storage"""
    
    @staticmethod
    async def store_message(message_id: int, text: str, user_id: int, chat_id: int, media_type: str = None, has_media: bool = False):
        """Store original message in MongoDB"""
        try:
            document = {
                "_id": message_id,
                "text": text,
                "user_id": user_id,
                "chat_id": chat_id,
                "media_type": media_type,
                "has_media": has_media,
                "timestamp": datetime.utcnow()
            }
            
            await messages_collection.replace_one(
                {"_id": message_id}, 
                document, 
                upsert=True
            )
            logger.debug(f"Stored message {message_id} in database")
            
        except Exception as e:
            logger.error(f"Error storing message in database: {e}")
    
    @staticmethod
    async def get_message(message_id: int):
        """Retrieve original message from MongoDB"""
        try:
            document = await messages_collection.find_one({"_id": message_id})
            return document
        except Exception as e:
            logger.error(f"Error retrieving message from database: {e}")
            return None
    
    @staticmethod
    async def delete_message(message_id: int):
        """Delete message from MongoDB"""
        try:
            await messages_collection.delete_one({"_id": message_id})
            logger.debug(f"Deleted message {message_id} from database")
        except Exception as e:
            logger.error(f"Error deleting message from database: {e}")
    
    @staticmethod
    async def cleanup_old_messages():
        """Clean up messages older than 7 days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            result = await messages_collection.delete_many({
                "timestamp": {"$lt": cutoff_date}
            })
            logger.info(f"Cleaned up {result.deleted_count} old messages from database")
        except Exception as e:
            logger.error(f"Error cleaning up old messages: {e}")

async def is_admin(chat_id: int, user_id: int) -> bool:
    """Check if user is admin in the chat"""
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]
    except Exception as e:
        logger.error(f"Error checking admin status: {e}")
        return False

def get_message_content_info(message: Message) -> tuple:
    """Get comprehensive message content information for comparison"""
    text_content = message.text or message.caption or ""
    
    # Check media type
    media_type = None
    has_media = False
    
    if message.media:
        has_media = True
        if message.photo:
            media_type = "photo"
        elif message.video:
            media_type = "video"
        elif message.audio:
            media_type = "audio"
        elif message.voice:
            media_type = "voice"
        elif message.video_note:
            media_type = "video_note"
        elif message.document:
            media_type = "document"
        elif message.sticker:
            media_type = "sticker"
        elif message.animation:
            media_type = "animation"
        elif message.location:
            media_type = "location"
        elif message.venue:
            media_type = "venue"
        elif message.contact:
            media_type = "contact"
        elif message.poll:
            media_type = "poll"
        else:
            media_type = "other"
    
    return text_content, media_type, has_media

def is_content_edited(original_data: dict, current_message: Message) -> bool:
    """Check if the actual message content was edited (not just reactions)"""
    current_text, current_media_type, current_has_media = get_message_content_info(current_message)
    
    # Compare text content
    text_changed = original_data["text"] != current_text
    
    # Compare media information
    media_changed = (
        original_data.get("media_type") != current_media_type or
        original_data.get("has_media", False) != current_has_media
    )
    
    # Return True if either text or media content changed
    return text_changed or media_changed

@app.on_message(filters.group)
async def store_original_message(client: Client, message: Message):
    """Store original messages to track edits"""
    try:
        # Store messages that have text, caption, or media
        if message.text or message.caption or message.media:
            text_content, media_type, has_media = get_message_content_info(message)
            
            await MessageStorage.store_message(
                message_id=message.id,
                text=text_content,
                user_id=message.from_user.id,
                chat_id=message.chat.id,
                media_type=media_type,
                has_media=has_media
            )
                
    except Exception as e:
        logger.error(f"Error storing message: {e}")

@app.on_edited_message(filters.group)
async def handle_edited_message(client: Client, message: Message):
    """Handle edited messages - delete them and send notification (skip admins and reactions)"""
    try:
        # Get the original message from database
        original_data = await MessageStorage.get_message(message.id)
        
        if original_data:
            # Check if this is just a reaction update (content hasn't changed)
            if not is_content_edited(original_data, message):
                logger.debug(f"Skipping deletion - message {message.id} only has reaction changes")
                return
            
            # Check if the user is an admin - if yes, skip deletion
            if await is_admin(message.chat.id, message.from_user.id):
                logger.info(f"Skipping deletion - {message.from_user.first_name} is an admin")
                # Update the stored message with new content but don't delete
                current_text, current_media_type, current_has_media = get_message_content_info(message)
                await MessageStorage.store_message(
                    message_id=message.id,
                    text=current_text,
                    user_id=message.from_user.id,
                    chat_id=message.chat.id,
                    media_type=current_media_type,
                    has_media=current_has_media
                )
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
            
            # Remove the message from database
            await MessageStorage.delete_message(message.id)
            
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
👋 𝐇𝐞𝐲, {user_mention}

𝐈 𝐚𝐦 {bot_mention} ♡ 

<u>⚡ 𝐅𝐞𝐚𝐭𝐮𝐫𝐞𝐬:</u>
✅ 𝐀𝐮𝐭𝐨𝐦𝐚𝐭𝐢𝐜𝐚𝐥𝐥𝐲 𝐝𝐞𝐥𝐞𝐭𝐞 𝐞𝐝𝐢𝐭𝐞𝐝 𝐦𝐞𝐬𝐬𝐚𝐠𝐞𝐬 (𝐄𝐱𝐜𝐞𝐩𝐭 𝐟𝐫𝐨𝐦 𝐚𝐝𝐦𝐢𝐧𝐬).
✅ 𝐍𝐨𝐭𝐢𝐟𝐲 𝐰𝐡𝐞𝐧 𝐚 𝐦𝐞𝐬𝐬𝐚𝐠𝐞 𝐢𝐬 𝐞𝐝𝐢𝐭𝐞𝐝.
✅ 𝐄𝐚𝐬𝐲 𝐭𝐨 𝐚𝐝𝐝 𝐭𝐨 𝐲𝐨𝐮𝐫 𝐠𝐫𝐨𝐮𝐩𝐬.
✅ 𝐏𝐞𝐫𝐬𝐢𝐬𝐭𝐞𝐧𝐭 𝐬𝐭𝐨𝐫𝐚𝐠𝐞 𝐰𝐢𝐭𝐡 𝐌𝐨𝐧𝐠𝐨𝐃𝐁.

<u>⚙️ 𝐒𝐞𝐭𝐮𝐩:</u>
⦿ 𝐀𝐝𝐝 𝐦𝐞 𝐭𝐨 𝐲𝐨𝐮𝐫 𝐠𝐫𝐨𝐮𝐩
⦿ 𝐌𝐚𝐤𝐞 𝐦𝐞 𝐚𝐧 𝐚𝐝𝐦𝐢𝐧 𝐰𝐢𝐭𝐡 𝐝𝐞𝐥𝐞𝐭𝐞 𝐦𝐞𝐬𝐬𝐚𝐠𝐞 𝐩𝐞𝐫𝐦𝐢𝐬𝐬𝐢𝐨𝐧
⦿ 𝐈'𝐥𝐥 𝐬𝐭𝐚𝐫𝐭 𝐦𝐨𝐧𝐢𝐭𝐨𝐫𝐢𝐧𝐠 𝐚𝐮𝐭𝐨𝐦𝐚𝐭𝐢𝐜𝐚𝐥𝐥𝐲!

<u>⚠️ 𝐍𝐨𝐭𝐞:</u> 𝐈 𝐧𝐞𝐞𝐝 𝐚𝐝𝐦𝐢𝐧 𝐫𝐢𝐠𝐡𝐭𝐬 𝐭𝐨 𝐝𝐞𝐥𝐞𝐭𝐞 𝐦𝐞𝐬𝐬𝐚𝐠𝐞𝐬. 𝐀𝐝𝐦𝐢𝐧 𝐌𝐞𝐬𝐬𝐚𝐠𝐞𝐬 𝐰𝐨𝐧'𝐭 𝐛𝐞 𝐝𝐞𝐥𝐞𝐭𝐞𝐝 𝐰𝐡𝐞𝐧 𝐞𝐝𝐢𝐭𝐞𝐝.
        """
        
        await message.reply_text(
            welcome_text,
            reply_markup=keyboard,
            disable_web_page_preview=True,
            parse_mode=ParseMode.HTML
        )
        
    except Exception as e:
        logger.error(f"Error in start command: {e}")

@app.on_message(filters.command("status") & filters.group)
async def status_command(client: Client, message: Message):
    """Check bot status in group"""
    try:
        bot_member = await client.get_chat_member(message.chat.id, (await client.get_me()).id)
        
        # Check database connection
        try:
            await client.admin.command('ping')
            db_status = "✅ Connected"
        except:
            db_status = "❌ Disconnected"
        
        # Get message count in database for this chat
        message_count = await messages_collection.count_documents({"chat_id": message.chat.id})
        
        if bot_member.privileges and bot_member.privileges.can_delete_messages:
            status_text = f"""✅ **Bot is working properly!**

🔧 **Permissions:** Delete messages ✅
🗄️ **Database:** {db_status}
📊 **Stored messages:** {message_count}

📝 **Note:** Admin messages won't be deleted when edited."""
        else:
            status_text = f"""⚠️ **Bot needs admin rights!**

🔧 **Required:** Delete Messages permission
🗄️ **Database:** {db_status}
📊 **Stored messages:** {message_count}

Please make me admin with delete messages permission."""
            
        await message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        logger.error(f"Error checking status: {e}")
        await message.reply_text("❌ Error checking bot status.")

@app.on_message(filters.command("cleanup") & filters.private)
async def cleanup_command(client: Client, message: Message):
    """Manual cleanup command (owner only)"""
    try:
        # Check if user is the owner (replace with your user ID)
        if message.from_user.id != 6878311635:
            await message.reply_text("❌ This command is only for the bot owner.")
            return
        
        await MessageStorage.cleanup_old_messages()
        
        # Get total message count
        total_messages = await messages_collection.count_documents({})
        
        await message.reply_text(
            f"🧹 **Database cleanup completed!**\n\n"
            f"📊 **Total messages in database:** {total_messages}",
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in cleanup command: {e}")
        await message.reply_text("❌ Error during cleanup.")

@app.on_message(filters.command("stats") & filters.private)
async def stats_command(client: Client, message: Message):
    """Database statistics (owner only)"""
    try:
        # Check if user is the owner
        if message.from_user.id != 6878311635:
            await message.reply_text("❌ This command is only for the bot owner.")
            return
        
        # Get statistics
        total_messages = await messages_collection.count_documents({})
        
        # Get top 5 most active chats
        pipeline = [
            {"$group": {"_id": "$chat_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        
        top_chats = await messages_collection.aggregate(pipeline).to_list(5)
        
        stats_text = f"""📊 **Database Statistics**

📈 **Total stored messages:** {total_messages}

🏆 **Top 5 most active chats:**
"""
        
        for i, chat in enumerate(top_chats, 1):
            try:
                chat_info = await client.get_chat(chat["_id"])
                chat_name = chat_info.title or f"Chat {chat['_id']}"
            except:
                chat_name = f"Chat {chat['_id']}"
            
            stats_text += f"{i}. {chat_name}: {chat['count']} messages\n"
        
        await message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
        
    except Exception as e:
        logger.error(f"Error in stats command: {e}")
        await message.reply_text("❌ Error retrieving statistics.")

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

I'm now monitoring this group for edited messages with persistent MongoDB storage.

**Important:** Please make me an admin with "Delete Messages" permission so I can work properly.

**Note:** I won't delete edited messages from group admins.

**Features:**
✅ Persistent storage - data survives restarts
✅ Automatic cleanup of old messages (7 days)
✅ Real-time edit monitoring
✅ Ignores reaction-only changes

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

# Periodic cleanup task
async def periodic_cleanup():
    """Run cleanup every 24 hours"""
    while True:
        try:
            await asyncio.sleep(86400)  # 24 hours
            await MessageStorage.cleanup_old_messages()
            logger.info("Periodic cleanup completed")
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")

# Error handler
@app.on_message(filters.all, group=-300)
async def error_handler(client: Client, message: Message):
    """Global error handler"""
    pass  # Just to catch any unhandled errors

async def startup():
    """Startup tasks"""
    try:
        # Test database connection
        await client.admin.command('ping')
        logger.info("✅ MongoDB connection successful")
        
        # Create index for better performance
        await messages_collection.create_index([("timestamp", 1)])
        await messages_collection.create_index([("chat_id", 1)])
        
        # Start periodic cleanup task
        asyncio.create_task(periodic_cleanup())
        
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        print("❌ Failed to connect to MongoDB. Please check your MONGODB_URI.")

if __name__ == "__main__":
    print("🤖 Starting Edit Delete Bot with MongoDB...")
    print("📝 Make sure to:")
    print("   1. Replace API_ID, API_HASH, BOT_TOKEN, and MONGODB_URI in config.py")
    print("   2. Install required packages:")
    print("      pip install pyrogram motor")
    print("   3. Make the bot admin in groups with delete messages permission")
    print("   4. Admins can edit messages without deletion")
    print("   5. Database automatically cleans up messages older than 7 days")
    print("   6. Reactions won't trigger message deletion")
    print("🚀 Bot is running with persistent MongoDB storage...")
    
    # Run startup tasks
    asyncio.get_event_loop().run_until_complete(startup())
    
    app.run()
