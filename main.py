import discord
from discord import app_commands
from discord.ext import commands
import os
from flask import Flask
from threading import Thread
from waitress import serve

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Bot is Alive"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    serve(app, host='0.0.0.0', port=port)

# --- BOT SETUP ---
class MyBot(commands.Bot):
    def __init__(self):
        # We start with basic intents to ensure it boots
        intents = discord.Intents.default()
        intents.message_content = True 
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("Slash commands synced!")

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
    await interaction.followup.send("Wiped!", ephemeral=True)

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
    if token:
        bot.run(token)
    else:
        print("TOKEN NOT FOUND")
