# ⚡ Edit Guard Bot ⚡
<div align="center">
  <img src="https://img.shields.io/badge/Edit%20Guard-Telegram-blue?style=for-the-badge&logo=telegram" alt="Edit Guard Bot">
  <br><br>
  
  ![Version](https://img.shields.io/badge/version-2.0-blue?style=for-the-badge)
  ![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python)
  ![Pyrogram](https://img.shields.io/badge/Pyrogram-2.0+-orange?style=for-the-badge&logo=telegram)
  ![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-red?style=for-the-badge&logo=mongodb)
  ![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)
  
  <p><i>Advanced Telegram bot that automatically deletes edited messages with persistent MongoDB storage.</i></p>
</div>

---

## 🔥 Features

- **🚫 Auto-Delete Edited Messages** - Instantly removes edited messages (except from admins)
- **👑 Admin Protection** - Group administrators can edit messages without deletion
- **💾 Persistent Storage** - MongoDB integration ensures data survives bot restarts
- **🧹 Auto Cleanup** - Automatically removes messages older than 7 days
- **📊 Real-time Monitoring** - Track edit attempts and bot performance
- **⚙️ Easy Setup** - Simple configuration with comprehensive status checking
- **🔒 Permission Management** - Smart admin detection and permission handling
- **📈 Statistics Dashboard** - View database stats and most active chats

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Telegram API credentials (API ID and API Hash)
- Bot token from [@BotFather](https://t.me/BotFather)
- MongoDB Atlas account (free tier available)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/edit-guard-bot.git
   cd edit-guard-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup MongoDB**
   - Create a free [MongoDB Atlas](https://www.mongodb.com/atlas) account
   - Create a new cluster
   - Get your connection URI

4. **Configure the bot**
   Edit the `.env` file:
   ```python
   API_ID=12345678  # Your API ID (integer)
   API_HASH=your_api_hash_here
   BOT_TOKEN=your_bot_token_here
   MONGODB_URI=your_mongo_string_here
   ```

5. **Run the bot**
   ```bash
   python3 editguard.py
   ```

---

## 💬 Bot Commands

| Command     | Description                               | Access Level |
|-------------|-------------------------------------------|--------------|
| `/start`    | Display welcome message and bot info     | Everyone     |
| `/status`   | Check bot status and permissions          | Group Only   |
| `/cleanup`  | Manually cleanup old messages            | Owner Only   |
| `/stats`    | View database statistics                  | Owner Only   |

---

## ⚙️ Setup Guide

### 1. Adding Bot to Groups
1. Start the bot with `/start`
2. Click "➕ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ"
3. Select your group and add the bot

### 2. Grant Permissions
1. Make the bot an **Administrator**
2. Enable **"Delete Messages"** permission
3. Use `/status` to verify setup

### 3. Bot Behavior
- ✅ **Regular Users**: Edited messages are deleted + notification sent
- ✅ **Group Admins**: Can edit messages freely (no deletion)
- ✅ **Auto Storage**: All messages stored in MongoDB for tracking
- ✅ **Smart Cleanup**: Old messages automatically removed after 7 days

---

## 🛡️ Security & Privacy

- **Admin Bypass**: Group administrators are never affected by message deletion
- **Secure Storage**: MongoDB Atlas provides enterprise-grade security
- **Data Retention**: Messages automatically deleted after 7 days
- **Permission Checks**: Bot verifies admin status before every action
- **Error Handling**: Comprehensive logging and error management

---

## 📊 Database Features

### Automatic Management
- **Persistent Storage**: Survives bot restarts and server maintenance
- **Auto Indexing**: Optimized queries for better performance  
- **Memory Efficient**: No RAM limitations like in-memory storage
- **Backup Ready**: MongoDB Atlas provides automatic backups

### Monitoring Tools
- **Status Dashboard**: Real-time bot and database status
- **Usage Statistics**: Track most active chats and message counts
- **Performance Metrics**: Monitor database operations and cleanup

---

## 🔧 Configuration Options

### Database Settings
```python
# Automatic cleanup interval (default: 7 days)
CLEANUP_DAYS = 7

# Maximum messages to store per cleanup (performance)
MAX_CLEANUP_BATCH = 1000
```

### Bot Behavior
```python
# Owner user ID for admin commands
OWNER_ID = 6878311635

# Support group and channel links
SUPPORT_GROUP = "https://t.me/FearlessCheats"
```

---

## 📱 Support & Updates

- **Support Group**: [Join FearlessCheats](https://t.me/FearlessCheats)
- **Bot Updates**: Regular feature updates and bug fixes
- **Developer**: Contact [@Fake_Scout](https://t.me/Fake_Scout)
- **Issues**: Report bugs via GitHub Issues

---

## 🚨 Troubleshooting

### Common Issues

**Bot not deleting messages?**
- Check if bot has admin rights with "Delete Messages" permission
- Use `/status` command to verify configuration

**Database connection failed?**
- Verify MongoDB URI is correct
- Check if IP address is whitelisted in MongoDB Atlas
- Ensure database user has read/write permissions

**Messages not being tracked?**
- Bot only tracks messages with text/caption content
- Ensure bot is running when messages are sent

### Error Codes
- `MessageDeleteForbidden`: Bot lacks delete permissions
- `ChatAdminRequired`: Bot needs admin rights
- `Connection Error`: MongoDB connection issues

---

## 📈 Performance

### Scalability
- **Multi-Group Support**: Handle unlimited groups simultaneously
- **High Throughput**: Process thousands of messages per minute
- **Resource Efficient**: Minimal server resource usage
- **Cloud Ready**: Deploy on any cloud platform

### Optimization Features
- **Database Indexing**: Fast message lookup and retrieval
- **Batch Operations**: Efficient bulk database operations
- **Connection Pooling**: Optimized MongoDB connections
- **Memory Management**: Automatic garbage collection

---

## 📜 License

This project is licensed under the MIT License. See `LICENSE` file for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

<div align="center">
  <h3>⚡ Created with love by Scout ⚡</h3>
  <p>Keeping your Telegram groups clean and organized.</p>
  
  <br>
  
  **⭐ Star this repo if you find it useful!**
  
  ![GitHub stars](https://img.shields.io/github/stars/FakeScoutBot/edit?style=social)
  ![GitHub forks](https://img.shields.io/github/forks/FakeScoutBot/edit?style=social)
</div>
