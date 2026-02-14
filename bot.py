#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎬 CINEFLIX ULTIMATE BOT
Premium Video Bot with Full Admin Panel + Enhanced Features
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ConversationHandler
)
from telegram.constants import ParseMode
from telegram.error import BadRequest, TelegramError
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

# ===================== CONFIGURATION =====================
# All sensitive data from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
ADMIN_ID = os.getenv("ADMIN_ID")

# Validate required environment variables
if not BOT_TOKEN:
    print("❌ ERROR: BOT_TOKEN environment variable not set!")
    sys.exit(1)

if not MONGO_URI:
    print("❌ ERROR: MONGO_URI environment variable not set!")
    sys.exit(1)

if not ADMIN_ID:
    print("❌ ERROR: ADMIN_ID environment variable not set!")
    sys.exit(1)

try:
    ADMIN_ID = int(ADMIN_ID)
except ValueError:
    print("❌ ERROR: ADMIN_ID must be a number!")
    sys.exit(1)

# ===================== LOGGING SETUP =====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===================== MONGODB SETUP =====================
try:
    logger.info("🔄 Connecting to MongoDB...")
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    mongo_client.server_info()
    db = mongo_client['cineflix_bot']
    
    # Collections
    videos_col = db['videos']
    channels_col = db['channels']
    force_join_col = db['force_join_channels']
    users_col = db['users']
    settings_col = db['settings']
    messages_col = db['messages']
    buttons_col = db['buttons']
    
    logger.info("✅ MongoDB Connected Successfully!")
    
except (ConnectionFailure, OperationFailure) as e:
    logger.error(f"❌ MongoDB Connection Failed: {e}")
    logger.error("Bot cannot run without database. Please check MONGO_URI.")
    sys.exit(1)

# ===================== CONVERSATION STATES =====================
EDITING_MESSAGE = 1
ADDING_CHANNEL = 2
EDITING_SETTING = 3
BROADCASTING = 4

# Admin state tracking
admin_states = {}

# Track user's last video request messages (to delete duplicates)
user_video_messages = {}  # Format: {user_id: {video_id: [message_ids]}}

# NEW: Track user's ALL messages for cleanup (not just video-specific)
user_all_messages = {}  # Format: {user_id: [message_ids]}

# ===================== DEFAULT MESSAGES =====================
DEFAULT_MESSAGES = {
    'welcome': """🎬 **স্বাগতম CINEFLIX এ!**
**Welcome to CINEFLIX!**

━━━━━━━━━━━━━━━━━━━━

Hello **{name}**! 👋

আপনার সব পছন্দের Movies, Series এবং Exclusive Content এক জায়গায়!
All your favorite Movies, Series, and Exclusive Content in one place!

━━━━━━━━━━━━━━━━━━━━

**🚀 কীভাবে ভিডিও দেখবেন?**
**🚀 How to Watch Videos?**

**ধাপ ১:** নিচে "🎮 Open CINEFLIX App" ক্লিক করুন
**Step 1:** Click "🎮 Open CINEFLIX App" below

**ধাপ ২:** পছন্দের ভিডিও সিলেক্ট করুন
**Step 2:** Select your favorite video

**ধাপ ৩:** আমাদের চ্যানেলে জয়েন করুন (প্রথমবার)
**Step 3:** Join our channel (first time only)

**ধাপ ৪:** ভিডিও উপভোগ করুন! 🍿
**Step 4:** Enjoy the video! 🍿

━━━━━━━━━━━━━━━━━━━━

**📢 Important:**
✅ সব কন্টেন্ট আনলক করতে আমাদের চ্যানেল জয়েন করুন
✅ Premium quality HD videos
✅ প্রতিদিন নতুন আপডেট
✅ সম্পূর্ণ ফ্রি!

**🎉 Happy Streaming! 🎉**""",

    'help': """📚 **CINEFLIX Bot - Help Guide**
📚 **CINEFLIX Bot - সাহায্য গাইড**

**🎯 Commands / কমান্ড:**
/start - বোট শুরু করুন | Start bot
/help - সাহায্য দেখুন | Show help

**🎬 কীভাবে ভিডিও দেখবেন?**
**🎬 How to watch videos?**

**Step 1:** /start দিয়ে Mini App খুলুন
**Step 2:** পছন্দের ভিডিও সিলেক্ট করুন
**Step 3:** চ্যানেল জয়েন করুন (যদি বলা হয়)
**Step 4:** ভিডিও উপভোগ করুন! 🍿

**⚠️ সমস্যা? Having issues?**
- ভিডিও না দেখা গেলে চ্যানেল জয়েন করুন
- লিঙ্ক কাজ না করলে Mini App রিফ্রেশ করুন
- অন্য সমস্যায় Admin কে মেসেজ করুন""",

    'force_join': """🔒 **ভিডিও দেখতে চ্যানেল জয়েন করুন!**
🔒 **Join Channel to Watch Video!**

━━━━━━━━━━━━━━━━━━━━

**📱 কীভাবে দেখবেন? (How to Watch?)**

**ধাপ ১:** নিচের চ্যানেল বাটনে ক্লিক করুন
**Step 1:** Click the channel button below

**ধাপ ২:** চ্যানেল খুলে "Request to Join" ক্লিক করুন
**Step 2:** Click "Request to Join" in the channel

**ধাপ ৩:** বট এ ফিরে আসুন (বাট ফিরতে হবে না - অটোমেটিক!)
**Step 3:** Return to bot (or wait - it's automatic!)

━━━━━━━━━━━━━━━━━━━━

**🤖 অটোমেটিক আনলক:**
আপনি জয়েন রিকোয়েস্ট পাঠানোর 5-10 সেকেন্ড পরে ভিডিও নিজে নিজেই আনলক হয়ে যাবে!

**🤖 Auto Unlock:**
Video will automatically unlock 5-10 seconds after you send join request!

**⚡ দ্রুত পেতে চান?**
জয়েন করার পরে "✅ আমি জয়েন করেছি" বাটন ক্লিক করুন!

**⚡ Want it faster?**
Click "✅ I Joined" button after joining!

━━━━━━━━━━━━━━━━━━━━

**💡 মনে রাখবেন:**
• প্রাইভেট চ্যানেলে শুধু রিকোয়েস্ট পাঠালেই ভিডিও পাবেন
• এডমিন approve করার অপেক্ষা করতে হবে না
• বট নিজে নিজে চেক করে ভিডিও দিয়ে দেয়!

**💡 Remember:**
• Just send join request - no need to wait for approval
• Bot automatically detects and sends video
• Sit back and relax! 🍿

━━━━━━━━━━━━━━━━━━━━""",

    'after_video': """🎬 **ভিডিও উপভোগ করুন! Enjoy the Video!**

━━━━━━━━━━━━━━━━━━━━

**🌟 আরও ভিডিও দেখতে চান?**
**🌟 Want to watch more videos?**

নিচের বাটনে ক্লিক করে আমাদের Mini App এ যান এবং হাজারো ভিডিও দেখুন!
Click the button below to access our Mini App with thousands of videos!

**📺 প্রতিদিন নতুন কন্টেন্ট!**
**📺 New content daily!**

━━━━━━━━━━━━━━━━━━━━

**💝 ধন্যবাদ! Thank you!**

Stay connected with us! 🎉
আমাদের সাথে থাকুন! 🎉""",

    'video_not_found': """❌ **দুঃখিত! Video Not Found!**

এই ভিডিওটি আর পাওয়া যাচ্ছে না বা লিঙ্ক ভুল।
This video is no longer available or the link is incorrect.

**কী করবেন? What to do?**

✅ Mini App এ ফিরে অন্য ভিডিও দেখুন
✅ Go back to Mini App and watch other videos

✅ আমাদের চ্যানেলে জয়েন থাকুন — প্রতিদিন নতুন কন্টেন্ট!
✅ Stay joined to our channel — new content daily!""",

    'auto_reply': """👋 **Hello!**

আমি একটি Video Bot! 
I'm a Video Bot!

🎬 Videos দেখতে নিচের button এ ক্লিক করুন:
🎬 Click the button below to watch videos:

👇 Use /start to access the Mini App"""
}

DEFAULT_SETTINGS = {
    'mini_app_url': 'https://cinaflix-streaming.vercel.app/',
    'main_channel_id': -1003872857468,
    'main_channel_username': 'Cinaflixsteem',
    'video_protection': True,
    'bot_name': 'CINEFLIX',
    'auto_reply_enabled': True,
    'message_cleanup_enabled': True,
    'welcome_media_enabled': False,  # NEW: Welcome GIF/Video
    'welcome_media_file_id': None,   # NEW: Telegram file_id
    'welcome_media_type': None,      # NEW: 'photo', 'animation', 'video'
    'folder_link_enabled': False,    # NEW: Enable folder join link
    'folder_link_url': ''            # NEW: Telegram folder link (https://t.me/addlist/xxxxx)
}

# ===================== DATABASE HELPER FUNCTIONS =====================

def get_setting(key, default=None):
    """Get setting from database"""
    try:
        setting = settings_col.find_one({'key': key})
        return setting['value'] if setting else default
    except Exception as e:
        logger.error(f"Error getting setting {key}: {e}")
        return default

def set_setting(key, value):
    """Set setting in database"""
    try:
        settings_col.update_one(
            {'key': key},
            {'$set': {'key': key, 'value': value, 'updated_at': datetime.utcnow()}},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Error setting {key}: {e}")
        return False

def get_message(key):
    """Get message template from database"""
    try:
        msg = messages_col.find_one({'key': key})
        return msg['text'] if msg else DEFAULT_MESSAGES.get(key, '')
    except Exception as e:
        logger.error(f"Error getting message {key}: {e}")
        return DEFAULT_MESSAGES.get(key, '')

def set_message(key, text):
    """Set message template in database"""
    try:
        messages_col.update_one(
            {'key': key},
            {'$set': {'key': key, 'text': text, 'updated_at': datetime.utcnow()}},
            upsert=True
        )
        return True
    except Exception as e:
        logger.error(f"Error setting message {key}: {e}")
        return False

def initialize_defaults():
    """Initialize default settings and messages if not exists"""
    try:
        # Initialize settings
        for key, value in DEFAULT_SETTINGS.items():
            if not settings_col.find_one({'key': key}):
                set_setting(key, value)
        
        # Initialize messages
        for key, text in DEFAULT_MESSAGES.items():
            if not messages_col.find_one({'key': key}):
                set_message(key, text)
        
        logger.info("✅ Default settings and messages initialized")
    except Exception as e:
        logger.error(f"Error initializing defaults: {e}")

def save_video(channel_id, message_id, channel_name="Main", media_type="video"):
    """Save video/photo/animation to database"""
    try:
        video_data = {
            'channel_id': channel_id,
            'message_id': message_id,
            'channel_name': channel_name,
            'media_type': media_type,  # NEW: 'video', 'photo', 'animation', 'document'
            'saved_at': datetime.utcnow(),
            'views': 0
        }
        videos_col.update_one(
            {'channel_id': channel_id, 'message_id': message_id},
            {'$set': video_data},
            upsert=True
        )
        logger.info(f"✅ {media_type.title()} saved: {channel_name} - {message_id}")
        return True
    except Exception as e:
        logger.error(f"Error saving {media_type}: {e}")
        return False

def get_video(message_id):
    """Get video from database"""
    try:
        return videos_col.find_one({'message_id': int(message_id)})
    except Exception as e:
        logger.error(f"Error getting video: {e}")
        return None

def increment_video_view(message_id):
    """Increment video view count"""
    try:
        videos_col.update_one(
            {'message_id': int(message_id)},
            {'$inc': {'views': 1}}
        )
    except Exception as e:
        logger.error(f"Error incrementing view: {e}")

def add_force_join_channel(channel_id, username, invite_link=None):
    """Add force join channel with optional invite link for private channels"""
    try:
        channel_data = {
            'channel_id': channel_id,
            'username': username.replace('@', ''),
            'invite_link': invite_link,  # NEW: Support private channel invite links
            'added_at': datetime.utcnow(),
            'is_active': True
        }
        force_join_col.update_one(
            {'channel_id': channel_id},
            {'$set': channel_data},
            upsert=True
        )
        
        link_info = f" (invite: {invite_link})" if invite_link else ""
        logger.info(f"✅ Force join channel added: @{username}{link_info}")
        return True
    except Exception as e:
        logger.error(f"Error adding force join channel: {e}")
        return False

def remove_force_join_channel(channel_id):
    """Remove force join channel"""
    try:
        result = force_join_col.delete_one({'channel_id': channel_id})
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error removing force join channel: {e}")
        return False

def get_force_join_channels():
    """Get all active force join channels"""
    try:
        return list(force_join_col.find({'is_active': True}))
    except Exception as e:
        logger.error(f"Error getting force join channels: {e}")
        return []

def save_user(user_id, username, first_name):
    """Save user to database"""
    try:
        user_data = {
            'user_id': user_id,
            'username': username,
            'first_name': first_name,
            'last_active': datetime.utcnow()
        }
        users_col.update_one(
            {'user_id': user_id},
            {'$set': user_data, '$setOnInsert': {'first_seen': datetime.utcnow()}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"Error saving user: {e}")

def get_stats():
    """Get bot statistics"""
    try:
        # Basic stats
        total_users = users_col.count_documents({})
        total_videos = videos_col.count_documents({})
        total_force_join = force_join_col.count_documents({'is_active': True})
        
        # Active users (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        active_today = users_col.count_documents({
            'last_active': {'$gte': yesterday}
        })
        
        # Most viewed video
        top_video = videos_col.find_one(sort=[('views', -1)])
        top_views = top_video['views'] if top_video else 0
        
        return {
            'users': total_users,
            'videos': total_videos,
            'force_join': total_force_join,
            'active_today': active_today,
            'top_views': top_views
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {
            'users': 0,
            'videos': 0,
            'force_join': 0,
            'active_today': 0,
            'top_views': 0
        }

def get_all_users():
    """Get all user IDs for broadcasting"""
    try:
        users = users_col.find({}, {'user_id': 1})
        return [user['user_id'] for user in users]
    except Exception as e:
        logger.error(f"Error getting all users: {e}")
        return []

def get_buttons(location):
    """Get buttons for a specific location (welcome or after_video)"""
    try:
        buttons = list(buttons_col.find({'location': location, 'is_active': True}).sort('order', 1))
        return buttons
    except Exception as e:
        logger.error(f"Error getting buttons for {location}: {e}")
        return []

def add_button(location, text, url, button_type='url', order=0):
    """Add a custom button"""
    try:
        button_data = {
            'location': location,  # 'welcome' or 'after_video'
            'text': text,
            'url': url,
            'type': button_type,  # 'url' or 'web_app'
            'order': order,
            'is_active': True,
            'created_at': datetime.utcnow()
        }
        result = buttons_col.insert_one(button_data)
        logger.info(f"✅ Button added: {text} at {location}")
        return str(result.inserted_id)
    except Exception as e:
        logger.error(f"Error adding button: {e}")
        return None

def remove_button(button_id):
    """Remove a button"""
    try:
        from bson import ObjectId
        result = buttons_col.delete_one({'_id': ObjectId(button_id)})
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error removing button: {e}")
        return False

def update_button(button_id, text=None, url=None):
    """Update button text or URL"""
    try:
        from bson import ObjectId
        update_data = {}
        if text:
            update_data['text'] = text
        if url:
            update_data['url'] = url
        
        if update_data:
            result = buttons_col.update_one(
                {'_id': ObjectId(button_id)},
                {'$set': update_data}
            )
            return result.modified_count > 0
        return False
    except Exception as e:
        logger.error(f"Error updating button: {e}")
        return False

# ===================== NEW: MESSAGE CLEANUP FUNCTION =====================
async def cleanup_user_messages(context: ContextTypes.DEFAULT_TYPE, user_id: int, chat_id: int):
    """Clean up all previous bot messages for a user"""
    cleanup_enabled = get_setting('message_cleanup_enabled', True)
    
    if not cleanup_enabled:
        return
    
    if user_id in user_all_messages:
        deleted_count = 0
        for msg_id in user_all_messages[user_id]:
            try:
                await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                deleted_count += 1
            except Exception as e:
                logger.debug(f"Could not delete message {msg_id}: {e}")
        
        if deleted_count > 0:
            logger.info(f"🧹 Cleaned up {deleted_count} old messages for user {user_id}")
        
        # Clear the list
        user_all_messages[user_id] = []

# ===================== ADMIN PANEL KEYBOARDS =====================

def admin_main_keyboard():
    """Main admin panel keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("📺 Channel Manager", callback_data="admin_channels"),
            InlineKeyboardButton("📝 Edit Messages", callback_data="admin_messages")
        ],
        [
            InlineKeyboardButton("🔘 Button Manager", callback_data="admin_buttons"),
            InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings")
        ],
        [
            InlineKeyboardButton("📊 Statistics", callback_data="admin_stats"),
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton("🔄 Refresh", callback_data="admin_refresh"),
            InlineKeyboardButton("❌ Close", callback_data="admin_close")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def channel_manager_keyboard():
    """Channel manager keyboard"""
    channels = get_force_join_channels()
    keyboard = []
    
    for ch in channels:
        # Add 🔒 icon for private channels (those with invite link)
        channel_icon = "🔒" if ch.get('invite_link') else "📢"
        keyboard.append([
            InlineKeyboardButton(
                f"{channel_icon} @{ch['username']}", 
                callback_data=f"view_channel_{ch['channel_id']}"
            ),
            InlineKeyboardButton(
                "❌ Remove", 
                callback_data=f"remove_channel_{ch['channel_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("➕ Add New Channel", callback_data="add_channel")])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_main")])
    
    return InlineKeyboardMarkup(keyboard)

def message_editor_keyboard():
    """Message editor keyboard"""
    keyboard = [
        [InlineKeyboardButton("✏️ Welcome Message", callback_data="edit_msg_welcome")],
        [InlineKeyboardButton("✏️ Help Message", callback_data="edit_msg_help")],
        [InlineKeyboardButton("✏️ Force Join Message", callback_data="edit_msg_force_join")],
        [InlineKeyboardButton("✏️ After Video Message", callback_data="edit_msg_after_video")],
        [InlineKeyboardButton("✏️ Video Not Found Message", callback_data="edit_msg_video_not_found")],
        [InlineKeyboardButton("✏️ Auto Reply Message", callback_data="edit_msg_auto_reply")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def settings_keyboard():
    """Settings keyboard"""
    keyboard = [
        [InlineKeyboardButton("🎮 Mini App URL", callback_data="setting_mini_app")],
        [InlineKeyboardButton("📢 Main Channel", callback_data="setting_main_channel")],
        [InlineKeyboardButton("🔒 Video Protection", callback_data="setting_protection")],
        [InlineKeyboardButton("🤖 Bot Name", callback_data="setting_bot_name")],
        [InlineKeyboardButton("💬 Auto Reply", callback_data="setting_auto_reply")],
        [InlineKeyboardButton("🧹 Message Cleanup", callback_data="setting_cleanup")],
        [InlineKeyboardButton("🎬 Welcome Media", callback_data="setting_welcome_media")],
        [InlineKeyboardButton("📁 Folder Join Link", callback_data="setting_folder_link")],  # NEW
        [InlineKeyboardButton("🔙 Back", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def button_manager_keyboard():
    """Button manager keyboard"""
    keyboard = [
        [InlineKeyboardButton("➕ Add Welcome Button", callback_data="add_btn_welcome")],
        [InlineKeyboardButton("➕ Add After Video Button", callback_data="add_btn_after_video")],
        [InlineKeyboardButton("📋 View Welcome Buttons", callback_data="view_btn_welcome")],
        [InlineKeyboardButton("📋 View After Video Buttons", callback_data="view_btn_after_video")],
        [InlineKeyboardButton("🔙 Back", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ===================== START COMMAND =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    save_user(user.id, user.username, user.first_name)
    
    # NEW: Cleanup old messages first
    await cleanup_user_messages(context, user.id, update.effective_chat.id)
    
    # Check for video deep link
    if context.args and len(context.args) > 0:
        video_id = context.args[0]
        await handle_video_request(update, context, video_id)
        return
    
    # Get settings
    mini_app_url = get_setting('mini_app_url', DEFAULT_SETTINGS['mini_app_url'])
    
    # Build keyboard with custom buttons
    keyboard = []
    
    # Get custom welcome buttons from database
    custom_buttons = get_buttons('welcome')
    
    if custom_buttons:
        # Use custom buttons from database
        for btn in custom_buttons:
            if btn['type'] == 'web_app':
                keyboard.append([InlineKeyboardButton(btn['text'], web_app={"url": btn['url']})])
            else:  # url type
                keyboard.append([InlineKeyboardButton(btn['text'], url=btn['url'])])
    else:
        # Default buttons if no custom buttons set
        main_channel = get_setting('main_channel_username', DEFAULT_SETTINGS['main_channel_username'])
        keyboard = [
            [InlineKeyboardButton("🎮 Open CINEFLIX App", web_app={"url": mini_app_url})],
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{main_channel}")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
    
    welcome_text = get_message('welcome').format(name=user.first_name)
    
    try:
        # NEW: Send welcome media first (if enabled)
        welcome_media_enabled = get_setting('welcome_media_enabled', False)
        
        if welcome_media_enabled:
            media_file_id = get_setting('welcome_media_file_id')
            media_type = get_setting('welcome_media_type')
            
            if media_file_id and media_type:
                try:
                    media_msg = None
                    if media_type == 'photo':
                        media_msg = await update.message.reply_photo(photo=media_file_id)
                    elif media_type == 'animation':
                        media_msg = await update.message.reply_animation(animation=media_file_id)
                    elif media_type == 'video':
                        media_msg = await update.message.reply_video(video=media_file_id)
                    
                    # Track media message for cleanup
                    if media_msg:
                        if user.id not in user_all_messages:
                            user_all_messages[user.id] = []
                        user_all_messages[user.id].append(media_msg.message_id)
                        logger.info(f"✅ Welcome media sent to user {user.id}")
                except Exception as e:
                    logger.error(f"Error sending welcome media: {e}")
        
        # Send welcome text message with buttons
        sent_msg = await update.message.reply_text(
            welcome_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Track this message for cleanup
        if user.id not in user_all_messages:
            user_all_messages[user.id] = []
        user_all_messages[user.id].append(sent_msg.message_id)
        
    except Exception as e:
        logger.error(f"Error sending welcome message: {e}")

# ===================== VIDEO REQUEST HANDLER =====================
async def handle_video_request(update: Update, context: ContextTypes.DEFAULT_TYPE, video_id: str):
    """Handle video playback request"""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # NEW: Cleanup old messages first (for clean experience)
    await cleanup_user_messages(context, user.id, chat_id)
    
    try:
        message_id = int(video_id)
    except ValueError:
        msg = await update.message.reply_text(
            get_message('video_not_found'),
            parse_mode=ParseMode.MARKDOWN
        )
        # Track message
        if user.id not in user_all_messages:
            user_all_messages[user.id] = []
        user_all_messages[user.id].append(msg.message_id)
        return
    
    # Get video from database
    video = get_video(message_id)
    if not video:
        msg = await update.message.reply_text(
            get_message('video_not_found'),
            parse_mode=ParseMode.MARKDOWN
        )
        # Track message
        if user.id not in user_all_messages:
            user_all_messages[user.id] = []
        user_all_messages[user.id].append(msg.message_id)
        return
    
    # Check force join channels
    force_channels = get_force_join_channels()
    not_joined = []
    
    for channel in force_channels:
        try:
            # Try to get chat member status
            member = await context.bot.get_chat_member(channel['channel_id'], user.id)
            
            # ✅ UPDATED: Accept both 'member' AND 'restricted' (join request pending)
            # 'restricted' can mean: banned, muted, OR join request pending
            # We need to specifically check for join request pending
            
            # Log detailed status for debugging
            logger.info(f"🔍 Checking user {user.id} in {channel['username']}: status={member.status}, is_member={getattr(member, 'is_member', 'N/A')}")
            
            if member.status in ['left', 'kicked']:
                # Only block if user explicitly left or got kicked
                not_joined.append(channel)
                logger.info(f"❌ User {user.id} not in channel {channel['username']}: {member.status}")
            elif member.status == 'restricted':
                # Check if this is join request pending (not banned/muted)
                # Join request pending = is_member False + status restricted
                try:
                    if hasattr(member, 'is_member'):
                        if not member.is_member:
                            # Join request is pending - grant access!
                            logger.info(f"✅ User {user.id} has JOIN REQUEST PENDING in {channel['username']} - Granting access!")
                        else:
                            # is_member True but restricted = banned/muted
                            not_joined.append(channel)
                            logger.info(f"❌ User {user.id} restricted in {channel['username']} (banned/muted, not join pending)")
                    else:
                        # No is_member attribute - assume join request pending (safer)
                        logger.info(f"✅ User {user.id} restricted in {channel['username']} (no is_member attr) - Assuming join request, granting access!")
                except Exception as e:
                    # If any error, assume join request and grant access (safer for user experience)
                    logger.warning(f"⚠️ Error checking is_member for user {user.id}: {e} - Assuming join request, granting access!")
            else:
                # member, administrator, creator - all good
                logger.info(f"✅ User {user.id} is MEMBER of {channel['username']}: {member.status}")
                
        except BadRequest as e:
            error_msg = str(e).lower()
            if "chat not found" in error_msg:
                # Bot is not admin in channel or channel ID is wrong
                logger.error(f"⚠️ Bot cannot access channel {channel['username']} (ID: {channel['channel_id']}). Bot must be admin!")
                # Skip this channel - don't block user due to bot config issue
                continue
            elif "user not found" in error_msg:
                # User account issue - rare
                logger.warning(f"User {user.id} not found in Telegram")
                not_joined.append(channel)
            else:
                # Other errors - assume not joined for safety
                logger.error(f"Error checking {channel['username']} for user {user.id}: {e}")
                not_joined.append(channel)
        except Exception as e:
            # Unknown errors - assume not joined
            logger.error(f"Unexpected error checking {channel['username']}: {e}")
            not_joined.append(channel)
    
    if not_joined:
        # User hasn't joined all channels
        keyboard = []
        
        # Check if folder link is enabled
        folder_enabled = get_setting('folder_link_enabled', False)
        folder_url = get_setting('folder_link_url', '')
        
        if folder_enabled and folder_url:
            # ✅ ONE-CLICK JOIN: Show folder link button
            keyboard.append([InlineKeyboardButton(
                "📁 Join All Channels (1-Click)", 
                url=folder_url
            )])
        else:
            # Traditional: Show individual channel buttons
            channel_num = 1
            for ch in not_joined:
                # ✅ NEW: Use invite link if available (for private channels), otherwise username
                if ch.get('invite_link'):
                    # Private channel with invite link
                    button_url = ch['invite_link']
                    # Show numbered name for private channels (helps distinguish multiple private channels)
                    button_text = f"🔒 Join Private Channel {channel_num}"
                    channel_num += 1
                else:
                    # Public channel with username
                    button_url = f"https://t.me/{ch['username']}"
                    button_text = f"📢 Join @{ch['username']}"
                    button_text = f"📢 Join @{ch['username']}"
                
                keyboard.append([InlineKeyboardButton(button_text, url=button_url)])
        
        # ✅ NEW: Manual verify button (optional backup)
        keyboard.append([InlineKeyboardButton(
            "✅ I Joined - Unlock Now", 
            callback_data=f"verify_{video_id}"
        )])
        
        msg = await update.message.reply_text(
            get_message('force_join'),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Track this message for cleanup
        if user.id not in user_all_messages:
            user_all_messages[user.id] = []
        user_all_messages[user.id].append(msg.message_id)
        
        # ✅ NEW: Schedule auto-check job
        # Bot will automatically check every 5 seconds for 30 seconds
        # If user joins all channels, video will be sent automatically!
        context.job_queue.run_repeating(
            auto_check_and_unlock,
            interval=5,  # Check every 5 seconds
            first=5,  # Start after 5 seconds
            data={
                'user_id': user.id,
                'chat_id': chat_id,
                'video_id': video_id,
                'message_id': msg.message_id,
                'check_count': 0,
                'max_checks': 6  # 6 checks × 5 seconds = 30 seconds total
            },
            name=f"auto_check_{user.id}_{video_id}"
        )
        
        logger.info(f"🤖 Auto-check scheduled for user {user.id}, video {video_id}")
        
        return
    
    # User joined all channels - send video
    try:
        protect = get_setting('video_protection', True)
        
        video_msg = await context.bot.copy_message(
            chat_id=chat_id,
            from_chat_id=video['channel_id'],
            message_id=message_id,
            protect_content=protect
        )
        
        increment_video_view(message_id)
        
        # After video message with dynamic buttons
        after_buttons = get_buttons('after_video')
        
        if after_buttons:
            # Use custom buttons from database
            keyboard = []
            for btn in after_buttons:
                if btn['type'] == 'web_app':
                    keyboard.append([InlineKeyboardButton(btn['text'], web_app={"url": btn['url']})])
                else:  # url type
                    keyboard.append([InlineKeyboardButton(btn['text'], url=btn['url'])])
        else:
            # Default button
            mini_app_url = get_setting('mini_app_url', DEFAULT_SETTINGS['mini_app_url'])
            keyboard = [[InlineKeyboardButton("🔙 Back to App", web_app={"url": mini_app_url})]]
        
        after_msg = await update.message.reply_text(
            get_message('after_video'),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Track these messages for cleanup
        if user.id not in user_all_messages:
            user_all_messages[user.id] = []
        user_all_messages[user.id].extend([video_msg.message_id, after_msg.message_id])
        
        logger.info(f"✅ Video {message_id} sent to user {user.id}")
        
    except BadRequest as e:
        if "message to copy not found" in str(e).lower():
            msg = await update.message.reply_text(
                get_message('video_not_found'),
                parse_mode=ParseMode.MARKDOWN
            )
            # Track message
            if user.id not in user_all_messages:
                user_all_messages[user.id] = []
            user_all_messages[user.id].append(msg.message_id)
        else:
            logger.error(f"Error sending video: {e}")

# ===================== AUTO-CHECK AND UNLOCK =====================
async def auto_check_and_unlock(context: ContextTypes.DEFAULT_TYPE):
    """
    Automatically check if user has joined all channels and unlock video
    This runs every 5 seconds for up to 30 seconds
    """
    job = context.job
    data = job.data
    
    user_id = data['user_id']
    chat_id = data['chat_id']
    video_id = data['video_id']
    force_join_msg_id = data['message_id']
    check_count = data.get('check_count', 0)
    max_checks = data.get('max_checks', 6)
    
    # Increment check count
    data['check_count'] = check_count + 1
    
    logger.info(f"🔍 Auto-check #{check_count + 1}/{max_checks} for user {user_id}, video {video_id}")
    
    # If max checks reached, stop job
    if check_count >= max_checks:
        logger.info(f"⏱️ Max checks reached for user {user_id}. Stopping auto-check.")
        job.schedule_removal()
        return
    
    try:
        # Get video from database
        try:
            message_id = int(video_id)
        except ValueError:
            logger.error(f"Invalid video_id: {video_id}")
            job.schedule_removal()
            return
        
        video = get_video(message_id)
        if not video:
            logger.error(f"Video not found: {video_id}")
            job.schedule_removal()
            return
        
        # Check force join channels
        force_channels = get_force_join_channels()
        not_joined = []
        
        for channel in force_channels:
            try:
                member = await context.bot.get_chat_member(channel['channel_id'], user_id)
                
                # Check if user joined or sent request
                
                # Log detailed status
                logger.debug(f"🔍 Auto-check: user {user_id} in {channel['username']}: status={member.status}, is_member={getattr(member, 'is_member', 'N/A')}")
                
                if member.status in ['left', 'kicked']:
                    not_joined.append(channel)
                    logger.debug(f"❌ Auto-check: User {user_id} still not in {channel['username']}")
                elif member.status == 'restricted':
                    # Check if join request pending (grant access) or banned/muted (block)
                    try:
                        if hasattr(member, 'is_member'):
                            if not member.is_member:
                                logger.debug(f"✅ Auto-check: User {user_id} has JOIN REQUEST PENDING in {channel['username']} - OK!")
                            else:
                                # Restricted for other reasons
                                not_joined.append(channel)
                                logger.debug(f"❌ Auto-check: User {user_id} restricted (banned/muted) in {channel['username']}")
                        else:
                            # Assume join request pending
                            logger.debug(f"✅ Auto-check: User {user_id} restricted in {channel['username']} (no is_member) - Assuming join request - OK!")
                    except Exception as e:
                        # Assume join request pending
                        logger.debug(f"✅ Auto-check: User {user_id} restricted in {channel['username']} - Assuming join request - OK!")
                else:
                    logger.debug(f"User {user_id} is member of {channel['username']} - OK!")
                    
            except Exception as e:
                logger.debug(f"Error checking {channel['username']}: {e}")
                not_joined.append(channel)
        
        # If user still hasn't joined all channels
        if not_joined:
            # Create readable channel list (handle private channels properly)
            remaining_names = []
            private_num = 1
            for ch in not_joined:
                if ch.get('invite_link'):
                    # Private channel - show numbered
                    remaining_names.append(f"🔒 Private Channel {private_num}")
                    private_num += 1
                else:
                    # Public channel - show username
                    remaining_names.append(f"@{ch['username']}")
            
            remaining = ", ".join(remaining_names)
            logger.info(f"⏳ User {user_id} still not joined: {remaining}")
            
            # Update message to show remaining channels
            try:
                remaining_list = "\n".join([f"❌ {name}" for name in remaining_names])
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=force_join_msg_id,
                    text=f"{get_message('force_join')}\n\n"
                         f"**📊 Status:**\n"
                         f"Waiting for you to join:\n{remaining_list}\n\n"
                         f"⏱️ Auto-checking... ({check_count + 1}/{max_checks})",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton(
                            "✅ Check Again Now", 
                            callback_data=f"verify_{video_id}"
                        )]
                    ]),
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.debug(f"Could not update message: {e}")
            
            return  # Continue checking
        
        # ✅ ALL CHANNELS JOINED! Send video automatically!
        logger.info(f"🎉 User {user_id} joined all channels! Auto-unlocking video {video_id}...")
        
        # Stop the job
        job.schedule_removal()
        
        # Delete force join message
        try:
            await context.bot.delete_message(chat_id=chat_id, message_id=force_join_msg_id)
            logger.info(f"🗑️ Deleted force join message")
        except Exception as e:
            logger.debug(f"Could not delete force join message: {e}")
        
        # Clean up old messages
        await cleanup_user_messages(context, user_id, chat_id)
        
        # Send video
        try:
            protect = get_setting('video_protection', True)
            
            video_msg = await context.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=video['channel_id'],
                message_id=message_id,
                protect_content=protect
            )
            
            increment_video_view(message_id)
            
            # After video message
            after_buttons = get_buttons('after_video')
            
            if after_buttons:
                keyboard = []
                for btn in after_buttons:
                    if btn['type'] == 'web_app':
                        keyboard.append([InlineKeyboardButton(btn['text'], web_app={"url": btn['url']})])
                    else:
                        keyboard.append([InlineKeyboardButton(btn['text'], url=btn['url'])])
            else:
                mini_app_url = get_setting('mini_app_url', DEFAULT_SETTINGS['mini_app_url'])
                keyboard = [[InlineKeyboardButton("🔙 Back to App", web_app={"url": mini_app_url})]]
            
            after_msg = await context.bot.send_message(
                chat_id=chat_id,
                text=get_message('after_video'),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Send success notification
            await context.bot.send_message(
                chat_id=chat_id,
                text="✅ **ভিডিও আনলক হয়েছে! Video Unlocked!**\n\n"
                     "🤖 বট অটোমেটিক ডিটেক্ট করেছে যে আপনি চ্যানেল জয়েন করেছেন!\n"
                     "🤖 Bot automatically detected that you joined the channel!\n\n"
                     "🎉 এখন ভিডিও উপভোগ করুন! Enjoy! 🍿",
                parse_mode=ParseMode.MARKDOWN
            )
            
            logger.info(f"✅ Auto-unlock successful for user {user_id}, video {video_id}")
            
        except Exception as e:
            logger.error(f"Error auto-sending video: {e}")
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Error unlocking video. Please try again using /start",
                parse_mode=ParseMode.MARKDOWN
            )
    
    except Exception as e:
        logger.error(f"Error in auto_check_and_unlock: {e}")
        job.schedule_removal()

# ===================== CALLBACK QUERY HANDLER =====================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    # Help button
    if data == "help":
        await query.message.reply_text(
            get_message('help'),
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Video verification - re-check force join
    if data.startswith("verify_"):
        video_id = data.replace("verify_", "")
        user = query.from_user
        chat_id = query.message.chat_id
        
        try:
            message_id = int(video_id)
        except ValueError:
            await query.message.edit_text(
                get_message('video_not_found'),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Get video from database
        video = get_video(message_id)
        if not video:
            await query.message.edit_text(
                get_message('video_not_found'),
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Re-check force join channels
        force_channels = get_force_join_channels()
        not_joined = []
        
        for channel in force_channels:
            try:
                member = await context.bot.get_chat_member(channel['channel_id'], user.id)
                
                # ✅ UPDATED: Accept both 'member' AND 'restricted' (join request pending)
                
                # Log detailed status
                logger.info(f"🔍 Verify: Checking user {user.id} in {channel['username']}: status={member.status}, is_member={getattr(member, 'is_member', 'N/A')}")
                
                if member.status in ['left', 'kicked']:
                    # Only block if user explicitly left or got kicked
                    not_joined.append(channel)
                    logger.info(f"❌ Verify: User {user.id} still not in {channel['username']}: {member.status}")
                elif member.status == 'restricted':
                    # Check if join request pending (grant access) or banned/muted (block)
                    try:
                        if hasattr(member, 'is_member'):
                            if not member.is_member:
                                # Join request pending - grant access!
                                logger.info(f"✅ Verify: User {user.id} has JOIN REQUEST PENDING in {channel['username']} - Granting access!")
                            else:
                                # Restricted for other reasons
                                not_joined.append(channel)
                                logger.info(f"❌ Verify: User {user.id} restricted (banned/muted) in {channel['username']}")
                        else:
                            # Assume join request pending
                            logger.info(f"✅ Verify: User {user.id} restricted in {channel['username']} (no is_member) - Assuming join request, granting access!")
                    except Exception as e:
                        # Assume join request pending
                        logger.warning(f"⚠️ Verify: Error checking user {user.id}: {e} - Assuming join request, granting access!")
                else:
                    # member, administrator, creator - all good
                    logger.info(f"✅ Verify: User {user.id} confirmed MEMBER in {channel['username']}: {member.status}")
                    
            except BadRequest as e:
                error_msg = str(e).lower()
                if "chat not found" in error_msg:
                    # Bot cannot access channel
                    logger.error(f"⚠️ Verify: Bot cannot access channel {channel['username']}. Skipping check.")
                    # Skip - don't block user
                    continue
                elif "user not found" in error_msg:
                    logger.warning(f"Verify: User {user.id} not found")
                    not_joined.append(channel)
                else:
                    logger.error(f"Verify: Error checking {channel['username']}: {e}")
                    not_joined.append(channel)
            except Exception as e:
                logger.error(f"Verify: Unexpected error for {channel['username']}: {e}")
                not_joined.append(channel)
        
        if not_joined:
            # Still not joined all channels - show detailed message with buttons
            total_channels = len(get_force_join_channels())
            joined_count = total_channels - len(not_joined)
            
            # Build readable channel list
            remaining_list = []
            keyboard = []
            private_num = 1
            
            for ch in not_joined:
                if ch.get('invite_link'):
                    # Private channel
                    channel_name = f"🔒 Private Channel {private_num}"
                    remaining_list.append(channel_name)
                    # Add button with invite link
                    keyboard.append([InlineKeyboardButton(
                        f"🔒 Join Private Channel {private_num}",
                        url=ch['invite_link']
                    )])
                    private_num += 1
                else:
                    # Public channel
                    channel_name = f"📢 @{ch['username']}"
                    remaining_list.append(channel_name)
                    # Add button with username
                    keyboard.append([InlineKeyboardButton(
                        f"📢 Join @{ch['username']}",
                        url=f"https://t.me/{ch['username']}"
                    )])
            
            remaining_text = "\n".join(remaining_list)
            
            # Create smart message based on count
            if len(not_joined) == 1:
                message_text = f"""❌ **আরও ১টি চ্যানেল বাকি!**
❌ **1 More Channel Needed!**

━━━━━━━━━━━━━━━━━━━━

📊 **Progress: {joined_count}/{total_channels} channels joined**

📍 **Please join this channel:**
{remaining_text}

━━━━━━━━━━━━━━━━━━━━

**Steps:**
১. নিচের বাটন ক্লিক করুন
2. চ্যানেল জয়েন/রিকোয়েস্ট পাঠান
3. "✅ আমি জয়েন করেছি" ক্লিক করুন"""

            elif len(not_joined) == total_channels:
                message_text = f"""❌ **সব চ্যানেল জয়েন করুন!**
❌ **Join ALL Channels!**

━━━━━━━━━━━━━━━━━━━━

📊 **Progress: 0/{total_channels} channels joined**

📍 **Please join these channels:**
{remaining_text}

━━━━━━━━━━━━━━━━━━━━

**Steps:**
১. নিচের সব বাটন ক্লিক করুন
2. সব চ্যানেল জয়েন/রিকোয়েস্ট পাঠান
3. "✅ আমি জয়েন করেছি" ক্লিক করুন"""

            else:
                message_text = f"""❌ **আরও {len(not_joined)}টি চ্যানেল বাকি!**
❌ **{len(not_joined)} More Channels Needed!**

━━━━━━━━━━━━━━━━━━━━

📊 **Progress: {joined_count}/{total_channels} channels joined**

📍 **Please join these channels:**
{remaining_text}

━━━━━━━━━━━━━━━━━━━━

**Steps:**
১. নিচের বাটন গুলো ক্লিক করুন
2. চ্যানেল গুলো জয়েন/রিকোয়েস্ট পাঠান
3. "✅ আমি জয়েন করেছি" ক্লিক করুন"""
            
            # Add verify button
            keyboard.append([InlineKeyboardButton(
                "✅ আমি জয়েন করেছি - Check Again",
                callback_data=f"verify_{video_id}"
            )])
            
            # Send as new message (not popup!)
            await query.message.reply_text(
                message_text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Also show small alert
            await query.answer(
                f"❌ {len(not_joined)} more channel(s) needed!",
                show_alert=False
            )
            )
            return
        
        # All channels joined! Delete force join message and send video
        try:
            await query.message.delete()
        except:
            pass
        
        try:
            protect = get_setting('video_protection', True)
            
            # Send video
            video_msg = await context.bot.copy_message(
                chat_id=chat_id,
                from_chat_id=video['channel_id'],
                message_id=message_id,
                protect_content=protect
            )
            
            increment_video_view(message_id)
            
            # After video message with dynamic buttons
            after_buttons = get_buttons('after_video')
            
            if after_buttons:
                # Use custom buttons from database
                keyboard = []
                for btn in after_buttons:
                    if btn['type'] == 'web_app':
                        keyboard.append([InlineKeyboardButton(btn['text'], web_app={"url": btn['url']})])
                    else:  # url type
                        keyboard.append([InlineKeyboardButton(btn['text'], url=btn['url'])])
            else:
                # Default button
                mini_app_url = get_setting('mini_app_url', DEFAULT_SETTINGS['mini_app_url'])
                keyboard = [[InlineKeyboardButton("🔙 Back to App", web_app={"url": mini_app_url})]]
            
            after_msg = await context.bot.send_message(
                chat_id=chat_id,
                text=get_message('after_video'),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Track for cleanup
            if user.id not in user_all_messages:
                user_all_messages[user.id] = []
            user_all_messages[user.id].extend([video_msg.message_id, after_msg.message_id])
            
            logger.info(f"✅ Video {message_id} unlocked for user {user.id} after verification")
            
        except BadRequest as e:
            if "message to copy not found" in str(e).lower():
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=get_message('video_not_found'),
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                logger.error(f"Error sending video after verification: {e}")
        
        return
    
    # Admin only from here
    if user_id != ADMIN_ID:
        await query.answer("⛔ Admin only!", show_alert=True)
        return
    
    # Copy shortcode button - Now sends a copyable message
    if data.startswith("copy_"):
        shortcode = data.replace("copy_", "")
        # Send a new message that's easier to copy
        await context.bot.send_message(
            chat_id=user_id,
            text=f"📋 **Shortcode:**\n\n`{shortcode}`\n\n👆 Tap to copy!",
            parse_mode=ParseMode.MARKDOWN
        )
        await query.answer("✅ Check the new message to copy!", show_alert=False)
        return
    
    # Admin panel navigation
    if data == "admin_main":
        stats = get_stats()
        text = f"""🔧 **CINEFLIX ADMIN PANEL**

📊 **Statistics:**
👥 Total Users: {stats['users']}
🔥 Active Today: {stats['active_today']}
📹 Videos: {stats['videos']}
👁️ Top Views: {stats['top_views']}
🔒 Force Join: {stats['force_join']}

Select an option below:"""
        
        await query.edit_message_text(
            text,
            reply_markup=admin_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "admin_channels":
        await query.edit_message_text(
            "📺 **Channel Manager**\n\nManage force join channels:",
            reply_markup=channel_manager_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "admin_messages":
        await query.edit_message_text(
            "📝 **Message Editor**\n\nSelect a message to edit:",
            reply_markup=message_editor_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "admin_buttons":
        await query.edit_message_text(
            "🔘 **Button Manager**\n\n"
            "Add custom buttons to Welcome or After Video messages.\n\n"
            "You can add:\n"
            "• Channel/Group links\n"
            "• Mini App buttons\n"
            "• Any custom URL\n\n"
            "Select an option:",
            reply_markup=button_manager_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "admin_settings":
        # Get current settings
        mini_app = get_setting('mini_app_url', DEFAULT_SETTINGS['mini_app_url'])
        main_channel = get_setting('main_channel_username', DEFAULT_SETTINGS['main_channel_username'])
        protection = get_setting('video_protection', True)
        bot_name = get_setting('bot_name', DEFAULT_SETTINGS['bot_name'])
        auto_reply = get_setting('auto_reply_enabled', True)
        cleanup = get_setting('message_cleanup_enabled', True)
        welcome_media = get_setting('welcome_media_enabled', False)
        folder_enabled = get_setting('folder_link_enabled', False)  # NEW
        folder_url = get_setting('folder_link_url', '')  # NEW
        
        protection_status = "🔒 ON" if protection else "🔓 OFF"
        auto_reply_status = "✅ ON" if auto_reply else "❌ OFF"
        cleanup_status = "✅ ON" if cleanup else "❌ OFF"
        welcome_media_status = "✅ ON" if welcome_media else "❌ OFF"
        folder_status = "✅ ON" if folder_enabled else "❌ OFF"  # NEW
        
        settings_text = f"""⚙️ **Bot Settings**

🎮 **Mini App URL:**
`{mini_app}`

📢 **Main Channel:**
@{main_channel}

🔒 **Video Protection:** {protection_status}
💬 **Auto Reply:** {auto_reply_status}
🧹 **Message Cleanup:** {cleanup_status}
🎬 **Welcome Media:** {welcome_media_status}
📁 **Folder Join Link:** {folder_status}

🤖 **Bot Name:** {bot_name}

Click a button below to edit:"""
        
        await query.edit_message_text(
            settings_text,
            reply_markup=settings_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "admin_stats":
        stats = get_stats()
        
        # Calculate percentages
        active_percent = round((stats['active_today'] / stats['users'] * 100), 1) if stats['users'] > 0 else 0
        
        text = f"""📊 **Detailed Statistics**

👥 **Users:**
• Total: {stats['users']}
• Active Today: {stats['active_today']} ({active_percent}%)

📹 **Content:**
• Total Videos: {stats['videos']}
• Most Viewed: {stats['top_views']} views

🔒 **Security:**
• Force Join Channels: {stats['force_join']}

🤖 **System:**
• Bot Status: ✅ Running
• Database: ✅ Connected
• Auto Reply: {'✅ ON' if get_setting('auto_reply_enabled', True) else '❌ OFF'}
• Message Cleanup: {'✅ ON' if get_setting('message_cleanup_enabled', True) else '❌ OFF'}"""
        
        await query.answer(text, show_alert=True)
    
    elif data == "admin_broadcast":
        admin_states[user_id] = {'action': 'broadcast'}
        await query.message.reply_text(
            "📢 **Broadcast Message**\n\n"
            "Send the message you want to broadcast to all users.\n\n"
            "✅ You can send:\n"
            "• Text messages\n"
            "• Photos with captions\n"
            "• Videos with captions\n\n"
            "⚠️ This will be sent to ALL users!\n\n"
            "Or /cancel to cancel",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data == "admin_refresh":
        await query.answer("🔄 Refreshed!")
        # Re-trigger the current callback to refresh
        if data == "admin_main":
            await button_callback(update, context)
    
    elif data == "admin_close":
        await query.message.delete()
        await query.answer("Panel closed")
    
    elif data == "add_channel":
        admin_states[user_id] = {'action': 'add_channel'}
        await query.message.reply_text(
            "➕ **Add New Force Join Channel**\n\n"
            "**📢 Public Channel:**\n"
            "`channel_id username`\n\n"
            "**🔒 Private Channel (Easy):**\n"
            "`channel_id invite_link`\n"
            "_(Bot auto-generates username)_\n\n"
            "**🔒 Private Channel (Custom):**\n"
            "`channel_id username invite_link`\n\n"
            "**Examples:**\n\n"
            "Public:\n"
            "`-1001234567890 MyChannel`\n\n"
            "Private (Easy):\n"
            "`-1001234567890 https://t.me/+xxxxxx`\n\n"
            "Private (Custom):\n"
            "`-1001234567890 MyPrivateChannel https://t.me/+xxxxxx`\n\n"
            "Or /cancel to cancel",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data.startswith("remove_channel_"):
        channel_id = int(data.replace("remove_channel_", ""))
        if remove_force_join_channel(channel_id):
            await query.answer("✅ Channel removed!")
            await button_callback(update, context)  # Refresh list
        else:
            await query.answer("❌ Failed to remove channel", show_alert=True)
    
    elif data.startswith("add_btn_"):
        location = data.replace("add_btn_", "")
        admin_states[user_id] = {'action': 'add_button', 'location': location}
        
        location_name = "Welcome Message" if location == "welcome" else "After Video Message"
        
        await query.message.reply_text(
            f"➕ **Add Button to {location_name}**\n\n"
            f"Send button details in this format:\n"
            f"`Text | URL | Type`\n\n"
            f"**Type** can be:\n"
            f"• `url` - Regular link button\n"
            f"• `webapp` - Mini App button\n\n"
            f"**Examples:**\n"
            f"`📢 Join Channel | https://t.me/MyChannel | url`\n"
            f"`🎮 Open App | https://myapp.com/ | webapp`\n"
            f"`👥 Join Group | https://t.me/+grouplink | url`\n\n"
            f"Or /cancel to cancel",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data.startswith("view_btn_"):
        location = data.replace("view_btn_", "")
        buttons = get_buttons(location)
        
        location_name = "Welcome Message" if location == "welcome" else "After Video Message"
        
        if not buttons:
            await query.answer(f"No custom buttons for {location_name}", show_alert=True)
            return
        
        # Create keyboard with button list
        keyboard = []
        for btn in buttons:
            btn_id = str(btn['_id'])
            btn_type_icon = "🌐" if btn['type'] == 'web_app' else "🔗"
            keyboard.append([
                InlineKeyboardButton(f"{btn_type_icon} {btn['text']}", callback_data=f"dummy"),
                InlineKeyboardButton("🗑️", callback_data=f"remove_btn_{btn_id}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="admin_buttons")])
        
        await query.edit_message_text(
            f"📋 **{location_name} Buttons**\n\n"
            f"Total: {len(buttons)} button(s)\n\n"
            f"Click 🗑️ to remove a button:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data.startswith("remove_btn_"):
        button_id = data.replace("remove_btn_", "")
        if remove_button(button_id):
            await query.answer("✅ Button removed!")
            await button_callback(update, context)
        else:
            await query.answer("❌ Failed to remove button", show_alert=True)
    
    elif data.startswith("edit_msg_"):
        msg_key = data.replace("edit_msg_", "")
        admin_states[user_id] = {'action': 'edit_message', 'key': msg_key}
        
        current_msg = get_message(msg_key)
        await query.message.reply_text(
            f"✏️ **Editing {msg_key.replace('_', ' ').title()}**\n\n"
            f"Current message:\n\n{current_msg}\n\n"
            f"Send the new message text or /cancel to cancel",
            parse_mode=ParseMode.MARKDOWN
        )
    
    elif data.startswith("setting_"):
        setting_key = data.replace("setting_", "")
        
        # Handle toggles
        if setting_key == "protection":
            current = get_setting('video_protection', True)
            new_val = not current
            set_setting('video_protection', new_val)
            
            status = "🔒 ON" if new_val else "🔓 OFF"
            await query.answer(f"Video Protection: {status}")
            await button_callback(update, context)
            return
        
        elif setting_key == "auto_reply":
            current = get_setting('auto_reply_enabled', True)
            new_val = not current
            set_setting('auto_reply_enabled', new_val)
            
            status = "✅ ON" if new_val else "❌ OFF"
            await query.answer(f"Auto Reply: {status}")
            await button_callback(update, context)
            return
        
        elif setting_key == "cleanup":
            current = get_setting('message_cleanup_enabled', True)
            new_val = not current
            set_setting('message_cleanup_enabled', new_val)
            
            status = "✅ ON" if new_val else "❌ OFF"
            await query.answer(f"Message Cleanup: {status}")
            await button_callback(update, context)
            return
        
        # NEW: Welcome Media management
        elif setting_key == "welcome_media":
            current = get_setting('welcome_media_enabled', False)
            
            if not current:
                # Currently OFF, prompt to upload media
                admin_states[user_id] = {'action': 'upload_welcome_media'}
                await query.message.reply_text(
                    "🎬 **Upload Welcome Media**\n\n"
                    "Send me a photo, GIF, or short video that will be shown when users use /start.\n\n"
                    "📝 **Tips:**\n"
                    "• Keep videos under 5 seconds\n"
                    "• File size under 5 MB recommended\n"
                    "• GIFs work great for animations!\n\n"
                    "Or /cancel to cancel",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                # Currently ON, toggle OFF
                set_setting('welcome_media_enabled', False)
                await query.answer("✅ Welcome Media: OFF")
                await button_callback(update, context)
            return
        
        # NEW: Folder Link management
        elif setting_key == "folder_link":
            current_enabled = get_setting('folder_link_enabled', False)
            current_url = get_setting('folder_link_url', '')
            
            if not current_enabled or not current_url:
                # Ask for folder URL
                admin_states[user_id] = {'action': 'set_folder_link'}
                await query.message.reply_text(
                    "📁 **Setup Folder Join Link**\n\n"
                    "**How to create a folder link:**\n"
                    "1. Go to Telegram Settings > Folders\n"
                    "2. Create a folder with all your private channels\n"
                    "3. Share the folder and copy the link\n\n"
                    "**Example link format:**\n"
                    "`https://t.me/addlist/xxxxxxxxxxxxx`\n\n"
                    "Send me your folder link, or /cancel to cancel",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                # Toggle OFF
                set_setting('folder_link_enabled', False)
                await query.answer("✅ Folder Link: OFF (Individual channels will be shown)")
                await button_callback(update, context)
            return
        
        # For other settings, ask for input
        admin_states[user_id] = {'action': 'edit_setting', 'key': setting_key}
        
        # Map callback data to actual setting keys
        setting_map = {
            'mini_app': 'mini_app_url',
            'main_channel': 'main_channel_username',
            'bot_name': 'bot_name'
        }
        
        actual_key = setting_map.get(setting_key, setting_key)
        current = get_setting(actual_key)
        
        # Provide helpful hints
        hints = {
            'mini_app': "Example: https://yourapp.vercel.app/",
            'main_channel': "Example: YourChannel (without @)",
            'bot_name': "Example: CINEFLIX"
        }
        
        hint_text = f"\n\n💡 {hints.get(setting_key, '')}" if setting_key in hints else ""
        
        await query.message.reply_text(
            f"⚙️ **Editing {actual_key.replace('_', ' ').title()}**\n\n"
            f"Current value: `{current}`{hint_text}\n\n"
            f"Send the new value or /cancel to cancel",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Store the actual key for later use
        admin_states[user_id]['actual_key'] = actual_key

# ===================== CHANNEL POST HANDLER =====================
async def channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle videos posted in channels"""
    try:
        logger.info(f"📥 Channel post received! Update: {update}")
        
        message = update.channel_post
        
        if not message:
            logger.warning("⚠️ No message in channel_post update")
            return
        
        # NEW: Check for all media types including photos
        has_video = bool(message.video)
        has_document = bool(message.document)
        has_animation = bool(message.animation)
        has_photo = bool(message.photo)  # NEW: Photo support
        
        logger.info(f"📝 Message type - Video: {has_video}, Document: {has_document}, Animation: {has_animation}, Photo: {has_photo}")
        
        # NEW: Accept videos, documents, animations, and photos
        if not (has_video or has_document or has_animation or has_photo):
            logger.info("⏭️ Not a media file, skipping")
            return
        
        channel_id = message.chat.id
        message_id = message.message_id
        channel_name = message.chat.title or "Unknown"
        
        # NEW: Detect media type
        media_type = "video"  # default
        media_icon = "🎬"
        if has_photo:
            media_type = "photo"
            media_icon = "📸"
        elif has_animation:
            media_type = "animation"
            media_icon = "🎞️"
        elif has_document:
            media_type = "document"
            media_icon = "📄"
        
        logger.info(f"{media_icon} Processing {media_type} - Channel: {channel_name} ({channel_id}), Message ID: {message_id}")
        
        # Save to database with media type
        save_video(channel_id, message_id, channel_name, media_type)
        logger.info(f"💾 {media_type.title()} saved to database")
        
        # Get bot username for deep link
        bot_info = await context.bot.get_me()
        bot_username = bot_info.username
        
        # Create admin notification - USE HTML instead of MARKDOWN to avoid parsing errors
        deep_link = f"https://t.me/{bot_username}?start={message_id}"
        
        # Escape HTML special characters in channel name
        import html
        safe_channel_name = html.escape(channel_name)
        
        # Send notification with HTML format (more reliable than Markdown)
        info_text = f"""{media_icon} <b>New {media_type.title()} Uploaded!</b>

📺 Channel: {safe_channel_name}
📋 Message ID: <code>{message_id}</code>
📁 Type: {media_type.upper()}

🌐 Direct Link:
{deep_link}

✅ {media_type.title()} saved to database!
Users can now access this content!

👇 <b>Tap the number below to copy:</b>"""
        
        logger.info(f"📤 Sending notification to admin {ADMIN_ID}")
        
        # First message with info (using HTML parse mode)
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=info_text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        
        # Second message with ONLY the copyable shortcode
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"<code>{message_id}</code>",
            parse_mode=ParseMode.HTML
        )
        
        logger.info(f"✅ Successfully notified admin about {media_type} {message_id}")
        
    except Exception as e:
        logger.error(f"❌ Error in channel_post handler: {e}", exc_info=True)

# ===================== ADMIN MESSAGE HANDLER =====================
async def admin_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle admin text messages for editing"""
    user_id = update.effective_user.id
    
    # Check if this is a broadcast message (admin sending to users)
    if user_id in admin_states and admin_states[user_id].get('action') == 'broadcast':
        await handle_broadcast(update, context)
        return
    
    # Auto-reply for non-admin users
    if user_id != ADMIN_ID:
        auto_reply_enabled = get_setting('auto_reply_enabled', True)
        if auto_reply_enabled:
            mini_app_url = get_setting('mini_app_url', DEFAULT_SETTINGS['mini_app_url'])
            keyboard = [[InlineKeyboardButton("🎮 Open Mini App", web_app={"url": mini_app_url})]]
            
            await update.message.reply_text(
                get_message('auto_reply'),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode=ParseMode.MARKDOWN
            )
        return
    
    # Admin-specific handlers
    if user_id not in admin_states:
        return
    
    # NEW: Handle welcome media upload (photo/animation/video)
    if admin_states[user_id].get('action') == 'upload_welcome_media':
        if update.message.photo:
            file_id = update.message.photo[-1].file_id
            media_type = 'photo'
        elif update.message.animation:
            file_id = update.message.animation.file_id
            media_type = 'animation'
        elif update.message.video:
            file_id = update.message.video.file_id
            media_type = 'video'
        else:
            await update.message.reply_text(
                "❌ Please send a photo, GIF, or video!\n\nOr /cancel to cancel",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Save to settings
        set_setting('welcome_media_file_id', file_id)
        set_setting('welcome_media_type', media_type)
        set_setting('welcome_media_enabled', True)
        
        await update.message.reply_text(
            f"✅ **Welcome {media_type.title()} Saved!**\n\n"
            f"Users will now see this {media_type} when they use /start.\n\n"
            f"You can toggle it on/off anytime from Settings.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        del admin_states[user_id]
        logger.info(f"✅ Welcome media uploaded: {media_type}")
        return
    
    text = update.message.text
    state = admin_states[user_id]
    
    if text == "/cancel":
        del admin_states[user_id]
        await update.message.reply_text("❌ Cancelled")
        return
    
    # NEW: Handle folder link setup
    if state['action'] == 'set_folder_link':
        text = text.strip()
        
        # Validate folder link format
        if not text.startswith('https://t.me/addlist/'):
            await update.message.reply_text(
                "❌ **Invalid Folder Link!**\n\n"
                "Folder links must start with:\n"
                "`https://t.me/addlist/`\n\n"
                "Please send a valid folder link or /cancel to cancel",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Save folder link settings
        set_setting('folder_link_url', text)
        set_setting('folder_link_enabled', True)
        
        await update.message.reply_text(
            "✅ **Folder Link Saved!**\n\n"
            f"URL: `{text}`\n\n"
            "Users will now see a single '📁 Join All Channels (1-Click)' button instead of individual channel buttons.\n\n"
            "You can toggle it on/off anytime from Settings.",
            parse_mode=ParseMode.MARKDOWN
        )
        
        del admin_states[user_id]
        logger.info(f"✅ Folder link configured: {text}")
        return
    
    if state['action'] == 'add_channel':
        parts = text.split()
        
        # Support multiple formats:
        # Format 1: channel_id username (public)
        # Format 2: channel_id invite_link (private - auto generate username)
        # Format 3: channel_id username invite_link (private with custom username)
        
        if len(parts) < 2:
            await update.message.reply_text(
                "❌ Invalid format!\n\n"
                "**Public Channel:**\n`channel_id username`\n\n"
                "**Private Channel (Option 1):**\n`channel_id invite_link`\n"
                "Bot will auto-generate username\n\n"
                "**Private Channel (Option 2):**\n`channel_id username invite_link`\n\n"
                "Examples:\n"
                "`-1001234567890 MyChannel`\n"
                "`-1001234567890 https://t.me/+xxxxx`\n"
                "`-1001234567890 MyChannel https://t.me/+xxxxx`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        try:
            channel_id = int(parts[0])
            
            # Smart detection: Is part[1] a link or username?
            if parts[1].startswith('https://t.me/'):
                # Format 2: channel_id invite_link
                invite_link = parts[1]
                # Auto-generate username from channel_id
                username = f"Channel{abs(channel_id)}"
                logger.info(f"Auto-generated username: {username}")
            elif len(parts) >= 3 and parts[2].startswith('https://t.me/'):
                # Format 3: channel_id username invite_link
                username = parts[1].replace('@', '')
                invite_link = parts[2]
            else:
                # Format 1: channel_id username (public)
                username = parts[1].replace('@', '')
                invite_link = None
            
            # Validate invite link format if provided
            if invite_link and not (invite_link.startswith('https://t.me/+') or invite_link.startswith('https://t.me/joinchat/')):
                await update.message.reply_text(
                    "❌ Invalid invite link!\n\n"
                    "Private channel invite link must start with:\n"
                    "`https://t.me/+xxxxx` or `https://t.me/joinchat/xxxxx`",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
            
            if add_force_join_channel(channel_id, username, invite_link):
                channel_type = "🔒 Private" if invite_link else "📢 Public"
                link_info = f"\n**Invite Link:** `{invite_link}`" if invite_link else ""
                await update.message.reply_text(
                    f"✅ **Channel Added!**\n\n"
                    f"**Type:** {channel_type}\n"
                    f"**Username:** @{username}\n"
                    f"**ID:** `{channel_id}`{link_info}",
                    parse_mode=ParseMode.MARKDOWN
                )
                del admin_states[user_id]
            else:
                await update.message.reply_text("❌ Failed to add channel")
        except ValueError:
            await update.message.reply_text("❌ Channel ID must be a number")
    
    elif state['action'] == 'add_button':
        parts = text.split('|')
        if len(parts) != 3:
            await update.message.reply_text(
                "❌ Invalid format!\n\nUse: `Text | URL | Type`\n\n"
                "Example: `📢 Join Channel | https://t.me/MyChannel | url`",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        btn_text = parts[0].strip()
        btn_url = parts[1].strip()
        btn_type = parts[2].strip().lower()
        
        if btn_type not in ['url', 'webapp']:
            await update.message.reply_text(
                "❌ Type must be 'url' or 'webapp'",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        if not btn_url.startswith('http'):
            await update.message.reply_text("❌ URL must start with http:// or https://")
            return
        
        # Convert webapp to web_app
        if btn_type == 'webapp':
            btn_type = 'web_app'
        
        location = state['location']
        existing_count = len(get_buttons(location))
        
        if add_button(location, btn_text, btn_url, btn_type, order=existing_count):
            location_name = "Welcome Message" if location == "welcome" else "After Video Message"
            await update.message.reply_text(
                f"✅ **Button Added to {location_name}!**\n\n"
                f"Text: {btn_text}\n"
                f"URL: {btn_url}\n"
                f"Type: {btn_type}",
                parse_mode=ParseMode.MARKDOWN
            )
            del admin_states[user_id]
        else:
            await update.message.reply_text("❌ Failed to add button")
    
    elif state['action'] == 'edit_message':
        msg_key = state['key']
        if set_message(msg_key, text):
            await update.message.reply_text("✅ Message updated!")
            del admin_states[user_id]
        else:
            await update.message.reply_text("❌ Failed to update message")
    
    elif state['action'] == 'edit_setting':
        # Get the actual setting key (mapped from callback data)
        setting_key = state.get('actual_key', state['key'])
        
        # Clean up input
        text = text.strip()
        
        # Type conversion and validation
        if setting_key == 'main_channel_id':
            try:
                text = int(text)
            except ValueError:
                await update.message.reply_text("❌ Channel ID must be a number")
                return
        elif setting_key == 'main_channel_username':
            # Remove @ if user added it
            text = text.replace('@', '')
        elif setting_key == 'mini_app_url':
            # Validate URL format
            if not text.startswith('http'):
                await update.message.reply_text("❌ URL must start with http:// or https://")
                return
        elif setting_key == 'video_protection':
            text = text.lower() in ['true', 'yes', '1', 'on']
        
        if set_setting(setting_key, text):
            await update.message.reply_text(
                f"✅ **{setting_key.replace('_', ' ').title()} Updated!**\n\n"
                f"New value: `{text}`",
                parse_mode=ParseMode.MARKDOWN
            )
            del admin_states[user_id]
        else:
            await update.message.reply_text("❌ Failed to update setting")

# ===================== NEW: BROADCAST HANDLER =====================
async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle broadcast message from admin"""
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        return
    
    # Get all users
    all_users = get_all_users()
    
    if not all_users:
        await update.message.reply_text("❌ No users to broadcast to!")
        del admin_states[user_id]
        return
    
    # Confirm broadcast
    await update.message.reply_text(
        f"📢 **Broadcasting to {len(all_users)} users...**\n\n"
        f"This may take a few moments. Please wait...",
        parse_mode=ParseMode.MARKDOWN
    )
    
    success_count = 0
    fail_count = 0
    
    # Forward the message to all users
    for target_user_id in all_users:
        try:
            # Copy the message to each user
            if update.message.photo:
                # Photo message
                await context.bot.send_photo(
                    chat_id=target_user_id,
                    photo=update.message.photo[-1].file_id,
                    caption=update.message.caption,
                    parse_mode=ParseMode.MARKDOWN if update.message.caption else None
                )
            elif update.message.video:
                # Video message
                await context.bot.send_video(
                    chat_id=target_user_id,
                    video=update.message.video.file_id,
                    caption=update.message.caption,
                    parse_mode=ParseMode.MARKDOWN if update.message.caption else None
                )
            else:
                # Text message
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text=update.message.text,
                    parse_mode=ParseMode.MARKDOWN
                )
            
            success_count += 1
            logger.info(f"✅ Broadcast sent to user {target_user_id}")
            
        except Exception as e:
            fail_count += 1
            logger.error(f"❌ Failed to send broadcast to user {target_user_id}: {e}")
    
    # Send summary to admin
    await update.message.reply_text(
        f"✅ **Broadcast Complete!**\n\n"
        f"✅ Sent: {success_count}\n"
        f"❌ Failed: {fail_count}\n"
        f"📊 Total: {len(all_users)}",
        parse_mode=ParseMode.MARKDOWN
    )
    
    # Clear admin state
    del admin_states[user_id]
    
    logger.info(f"📢 Broadcast completed: {success_count} success, {fail_count} failed")

# ===================== ADMIN COMMANDS =====================
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin panel"""
    if update.effective_user.id != ADMIN_ID:
        return
    
    stats = get_stats()
    text = f"""🔧 **CINEFLIX ADMIN PANEL**

📊 **Statistics:**
👥 Total Users: {stats['users']}
🔥 Active Today: {stats['active_today']}
📹 Videos: {stats['videos']}
👁️ Top Views: {stats['top_views']}
🔒 Force Join: {stats['force_join']}

Select an option below:"""
    
    await update.message.reply_text(
        text,
        reply_markup=admin_main_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help"""
    await update.message.reply_text(
        get_message('help'),
        parse_mode=ParseMode.MARKDOWN
    )

# ===================== ERROR HANDLER =====================
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors"""
    logger.error(f"Update {update} caused error {context.error}")

# ===================== MAIN FUNCTION =====================
def main():
    """Start the bot"""
    logger.info("🚀 Starting CINEFLIX Ultimate Bot...")
    
    # Initialize defaults
    initialize_defaults()
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Admin message handlers - text and media
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_message_handler))
    application.add_handler(MessageHandler(
        (filters.PHOTO | filters.ANIMATION | filters.VIDEO) & filters.User(ADMIN_ID),
        admin_message_handler
    ))
    
    # Channel post handler - catches ALL channel posts first
    application.add_handler(MessageHandler(
        filters.ChatType.CHANNEL,
        channel_post
    ))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    logger.info("✅ CINEFLIX Ultimate Bot is running!")
    logger.info(f"👑 Admin: {ADMIN_ID}")
    logger.info(f"💾 MongoDB: Connected")
    logger.info(f"🎬 Ready to serve!")
    logger.info(f"✨ NEW FEATURES: Photo Support, Welcome Media, Auto Cleanup, Broadcast, Enhanced Stats, Auto-Reply")
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
