import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
from flask import Flask
from threading import Thread

# --- KEEP ALIVE SERVER (For Render Free Tier) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and purging!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True 

class PurgeBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(f"Slash commands synced.")

bot = PurgeBot()

# --- COMMAND: /clear <number> ---
@bot.tree.command(name="clear", description="Delete a specific number of messages")
@app_commands.describe(amount="Number of messages to delete")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🗑️ Deleted {len(deleted)} messages.", ephemeral=True)

# --- COMMAND: /clear_all ---
@bot.tree.command(name="clear_all", description="Purge the entire channel (Max 14 days old)")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.checks.has_permissions(administrator=True) # Extra safety for 'All'
async def clear_all(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    try:
        # 'limit=None' tells the bot to keep going until it hits the 14-day limit
        deleted = await interaction.channel.purge(limit=None)
        await interaction.followup.send(f"💥 Channel purged! {len(deleted)} messages removed (limited to last 14 days).", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# --- RUN ---
if __name__ == "__main__":
    keep_alive()
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("MISSING DISCORD_TOKEN ENVIRONMENT VARIABLE")
