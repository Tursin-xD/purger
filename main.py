import discord
from discord.ext import commands
import os, asyncio
from flask import Flask
from threading import Thread
from waitress import serve

# --- WEB SERVER (Required for Render) ---
app = Flask('')
@app.route('/')
def home(): return "STABLE"

def run_flask():
    try:
        # Port 10000 is default for Render
        serve(app, host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), _quiet=True)
    except Exception as e:
        print(f"Web Server Error: {e}")

# --- BOT ---
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

async def main():
    # 1. Start the web server immediately in a background thread
    Thread(target=run_flask, daemon=True).start()
    print(">>> Web Server Thread Started")

    token = os.environ.get('DISCORD_TOKEN')
    if not token:
        print(">>> CRITICAL ERROR: Token missing in Environment Variables.")
    else:
        try:
            print(">>> Attempting Discord Login...")
            async with bot:
                await bot.start(token)
        except Exception as e:
            print(f">>> Bot Failed to Start: {e}")
    
    # 2. THE FAIL-SAFE: Prevents "Exited Early"
    # This keeps the process alive even if the bot is banned/offline
    print(">>> Keeping process alive for Render logs...")
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, RuntimeError):
        pass
