import discord
from discord import app_commands
from discord.ext import commands, tasks
import os, sys, io, asyncio
from flask import Flask
from threading import Thread
from waitress import serve

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "STABLE"

def run_flask():
    try:
        serve(app, host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), _quiet=True)
    except: pass

# --- BOT ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()

bot = MyBot()

@bot.tree.command(name="clear_all")
@app_commands.checks.has_permissions(administrator=True)
async def clear_all(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=None)
    await interaction.followup.send("Cleared!", ephemeral=True)

# --- THE STARTUP THAT PREVENTS EXIT 1 ---
async def start_everything():
    # Start Web Server thread
    Thread(target=run_flask, daemon=True).start()
    
    token = os.environ.get('DISCORD_TOKEN')
    if not token:
        print("ERROR: DISCORD_TOKEN is missing from Environment Variables!")
        return

    try:
        async with bot:
            await bot.start(token)
    except Exception as e:
        print(f"BOT CRASHED: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(start_everything())
    except (KeyboardInterrupt, RuntimeError):
        pass
