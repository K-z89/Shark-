import asyncio
import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SharkBot:
    def __init__(self):
        self.token = os.getenv("BOT_TOKEN", "")
        self.app = None
    
    async def start(self):
        self.app = Application.builder().token(self.token).build()
        
        self.app.add_handler(CommandHandler("start", self._start))
        self.app.add_handler(CommandHandler("help", self._help))
        self.app.add_handler(CommandHandler("stats", self._stats))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_link))
        self.app.add_handler(CallbackQueryHandler(self._button))
        
        await self.app.run_polling()
    
    async def _start(self, update: Update, context):
        user = update.effective_user
        text = f"""
🦈 SHARK v10
Hi {user.first_name}!

Send me links from:
• Instagram
• YouTube
• Twitter/X
• TikTok

I'll download them instantly.
        """
        await update.message.reply_text(text)
    
    async def _help(self, update: Update, context):
        text = """
📋 Supported:
- Instagram: Posts, Reels, Stories
- YouTube: Videos, Shorts
- Twitter: Videos, Images
- TikTok: Videos

Just send the link!
        """
        await update.message.reply_text(text)
    
    async def _stats(self, update: Update, context):
        import requests
        try:
            stats = requests.get("http://localhost:8000/stats").json()
            text = f"""
📊 Stats:
Total: {stats.get('total', 0)}
Success: {stats.get('success', 0)}
Failed: {stats.get('failed', 0)}
            """
            await update.message.reply_text(text)
        except:
            await update.message.reply_text("📊 Stats unavailable")
    
    async def _handle_link(self, update: Update, context):
        url = update.message.text.strip()
        
        if not url.startswith(('http://', 'https://')):
            await update.message.reply_text("❌ Invalid URL")
            return
        
        msg = await update.message.reply_text("🔄 Processing...")
        
        platform = self._get_platform(url)
        
        if not platform:
            await context.bot.edit_message_text(
                "❌ Platform not supported",
                chat_id=update.effective_chat.id,
                message_id=msg.message_id
            )
            return
        
        keyboard = [
            [InlineKeyboardButton("📥 Download HD", callback_data=f"dl_{platform}_hd")],
            [InlineKeyboardButton("📹 Video Only", callback_data=f"dl_{platform}_video")],
            [InlineKeyboardButton("🎵 Audio Only", callback_data=f"dl_{platform}_audio")],
            [InlineKeyboardButton("🖼️ Images Only", callback_data=f"dl_{platform}_image")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await context.bot.edit_message_text(
            f"✅ {platform.upper()} detected!\nChoose quality:",
            chat_id=update.effective_chat.id,
            message_id=msg.message_id,
            reply_markup=reply_markup
        )
    
    def _get_platform(self, url: str) -> str:
        if 'instagram.com' in url:
            return 'instagram'
        elif 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif 'twitter.com' in url or 'x.com' in url:
            return 'twitter'
        elif 'tiktok.com' in url:
            return 'tiktok'
        return ''
    
    async def _button(self, update: Update, context):
        query = update.callback_query
        await query.answer()
        
        data = query.data
        original_message = query.message.reply_to_message
        
        if not original_message:
            await query.edit_message_text("❌ Message not found")
            return
        
        url = original_message.text
        parts = data.split('_')
        
        if len(parts) < 3:
            await query.edit_message_text("❌ Invalid request")
            return
        
        platform = parts[1]
        quality = parts[2]
        
        await query.edit_message_text(f"📥 Downloading {quality}...")
        
        try:
            import requests
            import json
            
            payload = {
                "url": url,
                "quality": quality,
                "platform": platform
            }
            
            response = requests.post(
                "http://localhost:8000/download",
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            if result.get("status") == "success":
                await query.edit_message_text("✅ Download complete!")
                
                media_data = result.get("data", {})
                
                if media_data.get("media"):
                    for media in media_data["media"][:3]:
                        if media["type"] == "video":
                            await query.message.reply_video(media["url"])
                        elif media["type"] == "image":
                            await query.message.reply_photo(media["url"])
                
                elif result.get("download_url"):
                    await query.message.reply_document(result["download_url"])
                    
            else:
                await query.edit_message_text(f"❌ Error: {result.get('reason', 'Unknown')}")
                
        except Exception as e:
            logger.error(f"Download error: {e}")
            await query.edit_message_text("❌ Download failed")

async def main():
    bot = SharkBot()
    await bot.start()

if __name__ == "__main__":
    asyncio.run(main())
