import discord
from discord import app_commands
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# --- RENDER KEEP-ALIVE SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is active!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- DISCORD BOT SETUP ---
class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True  # Required for purging messages
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Syncs slash commands globally
        await self.tree.sync()
        print(f"Slash commands synced for {self.user}")

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
@bot.tree.command(name="clear_all", description="Purge all messages (Limited to last 14 days)")
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
    # Acknowledge the user
    await interaction.response.send_message(f"🚀 Reinstalling {channel.mention}...", ephemeral=True)
    
    # Capture channel state
    name, category, pos = channel.name, channel.category, channel.position
    overwrites, topic = channel.overwrites, channel.topic
    slow, nsfw = channel.slowmode_delay, channel.nsfw

    # Delete and recreate
    await channel.delete(reason=f"Reinstall requested by {interaction.user}")
    
    new_channel = await interaction.guild.create_text_channel(
        name=name, category=category, position=pos, 
        overwrites=overwrites, topic=topic, 
        slowmode_delay=slow, nsfw=nsfw
    )

    await new_channel.send(f"✨ **Channel Reinstalled.** History cleared by {interaction.user.mention}.")

# --- ERROR HANDLING ---
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ You don't have the required permissions!", ephemeral=True)
    else:
        print(f"Error: {error}")

# --- START BOT ---
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("CRITICAL ERROR: DISCORD_TOKEN not found in environment variables.")
