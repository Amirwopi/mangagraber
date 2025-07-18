import asyncio
import logging
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Document
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode

from manga_grabber_enhanced import MangaGrabberEnhanced, FileInfo
from manga_utils import MangaUtils

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class MangaGrabberBot:
    def __init__(self, bot_token: str, api_id: int, api_hash: str, phone_number: str):
        self.bot_token = bot_token
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone_number = phone_number
        
        # Initialize grabber
        self.grabber = MangaGrabberEnhanced(api_id, api_hash, phone_number, headless=True)
        
        # User sessions
        self.user_sessions: Dict[int, Dict] = {}
        
        # Initialize bot application
        self.application = Application.builder().token(bot_token).build()
        
        # Add handlers
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup bot command and message handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("search", self.search_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("cancel", self.cancel_command))
        
        # Callback query handler for inline keyboards
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        
        welcome_text = """
🎌 *Welcome to Enhanced Manga Grabber Bot!*

This bot helps you search and download manga files from Telegram channels.

*Features:*
📦 Support for ZIP, RAR, CBZ files
🔍 Smart search with hashtag support
📊 Export results to JSON/CSV
⚡ Advanced caching for better performance

*Commands:*
/search - Start searching for manga files
/status - Check current search status
/help - Show this help message
/cancel - Cancel current operation

*Usage:*
1. Use /search to start
2. Enter channel username (e.g., @channel)
3. Enter manga title to search
4. Browse and download results

Let's get started! Use /search to begin.
        """
        
        await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
*📚 Manga Grabber Bot Help*

*Search Examples:*
• `The God of High School`
• `#The_God_Of_High_School`
• `Naruto`
• `One Piece`

*Supported Formats:*
• ZIP files
• RAR files
• CBZ files

*Tips:*
• Try shorter search terms if no results
• Use hashtag format (#Title_With_Underscores)
• Check channel accessibility
• Bot supports unlimited message scanning

*Commands:*
/search - Start new search
/status - Check current operation
/cancel - Cancel current operation
/help - Show this help

*Note:* First time setup requires Telegram API credentials.
        """
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def search_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /search command"""
        user_id = update.effective_user.id
        
        # Initialize user session
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {}
        
        session = self.user_sessions[user_id]
        session['state'] = 'waiting_channel'
        session['search_results'] = []
        
        await update.message.reply_text(
            "🔍 *Starting new search...*\n\n"
            "Please enter the channel username (with @):\n"
            "Example: `@channelname`",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_sessions:
            await update.message.reply_text("❌ No active session. Use /search to start.")
            return
        
        session = self.user_sessions[user_id]
        state = session.get('state', 'idle')
        
        status_messages = {
            'idle': '💤 No active operation',
            'waiting_channel': '📱 Waiting for channel username',
            'waiting_search': '🔍 Waiting for search term',
            'searching': '⏳ Searching for files...',
            'showing_results': f"📋 Found {len(session.get('search_results', []))} files",
            'downloading': '📥 Downloading files...'
        }
        
        status_text = f"*Current Status:* {status_messages.get(state, 'Unknown')}"
        
        if self.grabber.stats:
            stats_text = f"""
*Performance Stats:*
• Messages scanned: {self.grabber.stats['messages_scanned']}
• Files found: {self.grabber.stats['files_found']}
• Search time: {self.grabber.stats['search_time']:.2f}s
• Cache hits: {self.grabber.stats['cache_hits']}
            """
            status_text += stats_text
        
        await update.message.reply_text(status_text, parse_mode=ParseMode.MARKDOWN)
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel command"""
        user_id = update.effective_user.id
        
        if user_id in self.user_sessions:
            del self.user_sessions[user_id]
            await update.message.reply_text("❌ Operation cancelled.")
        else:
            await update.message.reply_text("❌ No active operation to cancel.")
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages based on user state"""
        user_id = update.effective_user.id
        text = update.message.text
        
        if user_id not in self.user_sessions:
            await update.message.reply_text(
                "❌ No active session. Use /search to start searching."
            )
            return
        
        session = self.user_sessions[user_id]
        state = session.get('state', 'idle')
        
        if state == 'waiting_channel':
            await self.handle_channel_input(update, context, text)
        elif state == 'waiting_search':
            await self.handle_search_input(update, context, text)
        else:
            await update.message.reply_text(
                "❓ I'm not sure what you want to do. Use /search to start a new search."
            )
    
    async def handle_channel_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, channel: str):
        """Handle channel username input"""
        user_id = update.effective_user.id
        session = self.user_sessions[user_id]
        
        # Validate channel format
        if not channel.startswith('@'):
            channel = '@' + channel
        
        session['channel'] = channel
        session['state'] = 'waiting_search'
        
        await update.message.reply_text(
            f"✅ Channel set to: `{channel}`\n\n"
            "Now enter the manga title to search for:\n"
            "Examples:\n"
            "• `The God of High School`\n"
            "• `#The_God_Of_High_School`\n"
            "• `Naruto`",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_search_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, search_term: str):
        """Handle search term input"""
        user_id = update.effective_user.id
        session = self.user_sessions[user_id]
        
        session['search_term'] = search_term
        session['state'] = 'searching'
        
        # Send searching message
        search_msg = await update.message.reply_text(
            f"🔍 Searching for `{search_term}` in `{session['channel']}`...\n"
            "⏳ This may take a while for large channels...",
            parse_mode=ParseMode.MARKDOWN
        )
        
        try:
            # Connect to Telegram if not already connected
            if not hasattr(self.grabber, 'client') or not self.grabber.client.is_connected():
                await self.grabber.start()
            
            # Perform search
            files = await self.grabber.search_files(session['channel'], search_term)
            
            session['search_results'] = files
            session['state'] = 'showing_results'
            
            # Update search message
            await search_msg.edit_text(
                f"✅ Search completed!\n"
                f"Found {len(files)} files matching `{search_term}`",
                parse_mode=ParseMode.MARKDOWN
            )
            
            if files:
                await self.show_search_results(update, context, files)
            else:
                await update.message.reply_text(
                    "❌ No files found.\n\n"
                    "💡 *Tips:*\n"
                    "• Try using fewer words\n"
                    "• Try hashtag format (#Title_With_Underscores)\n"
                    "• Check if the channel has the manga\n"
                    "• Make sure channel is accessible",
                    parse_mode=ParseMode.MARKDOWN
                )
                session['state'] = 'idle'
        
        except Exception as e:
            logger.error(f"Search error for user {user_id}: {str(e)}")
            await search_msg.edit_text(
                f"❌ Search failed: {str(e)}\n\n"
                "Please try again or use /cancel to start over."
            )
            session['state'] = 'idle'
    
    async def show_search_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE, files: List[FileInfo]):
        """Display search results with pagination"""
        user_id = update.effective_user.id
        
        # Show summary
        summary_text = f"""
📊 *Search Results Summary*

🔍 Found: {len(files)} files
📈 Messages scanned: {self.grabber.stats.get('messages_scanned', 0)}
⏱️ Search time: {self.grabber.stats.get('search_time', 0):.2f}s
🚀 Cache hits: {self.grabber.stats.get('cache_hits', 0)}

*File Types:*
        """
        
        # Count file types
        type_counts = {}
        for file in files:
            ext = file.filename.split('.')[-1].upper()
            type_counts[ext] = type_counts.get(ext, 0) + 1
        
        for ext, count in type_counts.items():
            summary_text += f"• {ext}: {count} files\n"
        
        await update.message.reply_text(summary_text, parse_mode=ParseMode.MARKDOWN)
        
        # Show first few files with inline buttons
        await self.show_file_page(update, context, files, 0)
    
    async def show_file_page(self, update: Update, context: ContextTypes.DEFAULT_TYPE, files: List[FileInfo], page: int = 0):
        """Show a page of files with inline keyboard"""
        files_per_page = 5
        start_idx = page * files_per_page
        end_idx = min(start_idx + files_per_page, len(files))
        
        if start_idx >= len(files):
            await update.message.reply_text("❌ No more files to display.")
            return
        
        # Build file list text
        file_list_text = f"📋 *Files ({start_idx + 1}-{end_idx} of {len(files)})*\n\n"
        
        for i, file in enumerate(files[start_idx:end_idx], start_idx + 1):
            file_list_text += f"`{i}.` {file.filename}\n"
            file_list_text += f"   📦 {MangaUtils.format_size(file.size)} | {file.mime_type.split('/')[-1].upper()}\n"
            file_list_text += f"   📅 {file.date.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        # Create inline keyboard
        keyboard = []
        
        # Download buttons for current page
        download_buttons = []
        for i in range(start_idx, end_idx):
            download_buttons.append(InlineKeyboardButton(
                f"📥 {i+1}", 
                callback_data=f"download_{i}"
            ))
        
        # Add download buttons (max 5 per row)
        for i in range(0, len(download_buttons), 5):
            keyboard.append(download_buttons[i:i+5])
        
        # Navigation buttons
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("◀️ Previous", callback_data=f"page_{page-1}"))
        
        if end_idx < len(files):
            nav_buttons.append(InlineKeyboardButton("Next ▶️", callback_data=f"page_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # Action buttons
        action_buttons = [
            InlineKeyboardButton("📥 Download All", callback_data="download_all"),
            InlineKeyboardButton("📊 Export JSON", callback_data="export_json"),
            InlineKeyboardButton("📋 Export CSV", callback_data="export_csv"),
        ]
        keyboard.append(action_buttons)
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            file_list_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        user_id = query.from_user.id
        data = query.data
        
        await query.answer()
        
        if user_id not in self.user_sessions:
            await query.message.reply_text("❌ Session expired. Use /search to start over.")
            return
        
        session = self.user_sessions[user_id]
        files = session.get('search_results', [])
        
        if data.startswith('download_'):
            if data == 'download_all':
                await self.download_files(query, files, list(range(len(files))))
            else:
                # Download specific file
                file_idx = int(data.split('_')[1])
                await self.download_files(query, files, [file_idx])
        
        elif data.startswith('page_'):
            page = int(data.split('_')[1])
            await self.show_file_page(query, context, files, page)
        
        elif data.startswith('export_'):
            format_type = data.split('_')[1]
            await self.export_results(query, files, format_type)
    
    async def download_files(self, query, files: List[FileInfo], indices: List[int]):
        """Download selected files"""
        user_id = query.from_user.id
        session = self.user_sessions[user_id]
        
        session['state'] = 'downloading'
        
        files_to_download = [files[i] for i in indices if 0 <= i < len(files)]
        
        if not files_to_download:
            await query.message.reply_text("❌ No valid files to download.")
            return
        
        download_msg = await query.message.reply_text(
            f"📥 Starting download of {len(files_to_download)} files...\n"
            "⏳ Please wait..."
        )
        
        try:
            downloaded_files = []
            for i, file_info in enumerate(files_to_download, 1):
                # Update progress
                await download_msg.edit_text(
                    f"📥 Downloading file {i}/{len(files_to_download)}\n"
                    f"📄 {file_info.filename}\n"
                    f"📦 {MangaUtils.format_size(file_info.size)}"
                )
                
                # Download file
                file_path = await self.grabber.download_file(file_info)
                if file_path:
                    downloaded_files.append(file_path)
                    
                    # Send file to user
                    with open(file_path, 'rb') as f:
                        await query.message.reply_document(
                            document=f,
                            filename=file_info.filename,
                            caption=f"📄 {file_info.filename}\n📦 {MangaUtils.format_size(file_info.size)}"
                        )
            
            await download_msg.edit_text(
                f"✅ Download completed!\n"
                f"📥 Successfully downloaded {len(downloaded_files)} files"
            )
            
            session['state'] = 'showing_results'
            
        except Exception as e:
            logger.error(f"Download error for user {user_id}: {str(e)}")
            await download_msg.edit_text(f"❌ Download failed: {str(e)}")
            session['state'] = 'showing_results'
    
    async def export_results(self, query, files: List[FileInfo], format_type: str):
        """Export search results"""
        user_id = query.from_user.id
        
        try:
            # Create export filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"manga_results_{timestamp}.{format_type}"
            
            # Export results
            await self.grabber.export_results(files, format_type, filename)
            
            # Send exported file
            export_path = self.grabber.download_folder / filename
            with open(export_path, 'rb') as f:
                await query.message.reply_document(
                    document=f,
                    filename=filename,
                    caption=f"📊 Search results exported to {format_type.upper()}\n"
                           f"📄 {len(files)} files included"
                )
            
        except Exception as e:
            logger.error(f"Export error for user {user_id}: {str(e)}")
            await query.message.reply_text(f"❌ Export failed: {str(e)}")
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")
        
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again or use /cancel to start over."
            )
    
    async def start_bot(self):
        """Start the bot"""
        logger.info("Starting Manga Grabber Bot...")
        
        # Connect to Telegram
        await self.grabber.start()
        logger.info("Connected to Telegram client")
        
        # Start bot
        await self.application.run_polling()
    
    async def stop_bot(self):
        """Stop the bot"""
        logger.info("Stopping Manga Grabber Bot...")
        
        # Disconnect from Telegram
        await self.grabber.close()
        
        # Stop bot
        await self.application.stop()

def main():
    """Main function to run the bot"""
    # Load configuration
    try:
        with open('bot_config.json', 'r') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("❌ Bot configuration file not found!")
        print("Please create 'bot_config.json' with the following structure:")
        print("""
{
    "bot_token": "YOUR_BOT_TOKEN",
    "api_id": YOUR_API_ID,
    "api_hash": "YOUR_API_HASH",
    "phone_number": "YOUR_PHONE_NUMBER"
}
        """)
        return
    
    # Create and start bot
    bot = MangaGrabberBot(
        bot_token=config['bot_token'],
        api_id=config['api_id'],
        api_hash=config['api_hash'],
        phone_number=config['phone_number']
    )
    
    try:
        asyncio.run(bot.start_bot())
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {str(e)}")

if __name__ == "__main__":
    main()
