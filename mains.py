import discord
from discord.ext import commands
import os, asyncio
from flask import Flask
from threading import Thread
from waitress import serve

app = Flask('')
@app.route('/')
def home(): return "STABLE"

def run_flask():
    serve(app, host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), _quiet=True)

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True 
        super().__init__(command_prefix="!", intents=intents)

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        # We DON'T sync here to avoid triggering another ban immediately

bot = MyBot()

async def main():
    Thread(target=run_flask, daemon=True).start()
    token = os.environ.get('DISCORD_TOKEN')
    
    try:
        # Start the bot but catch the specific 429 error
        await bot.start(token)
    except discord.errors.HTTPException as e:
        if e.status == 429:
            print("STILL BANNED. Waiting 15 minutes before next attempt...")
            await asyncio.sleep(900) 
        else:
            print(f"Connection Error: {e}")
    
    # Keeps the process alive so Render stays "Healthy"
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
