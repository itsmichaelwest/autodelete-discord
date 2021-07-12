import discord
from discord.ext import commands
from discord_slash import SlashCommand
import os
from dotenv import load_dotenv
from cogs.autodelete import AutoDelete

load_dotenv()
TOKEN = os.getenv('TOKEN')

bot = commands.Bot(
    command_prefix='!',
    Intents=discord.Intents.all()
)

slash = SlashCommand(bot, sync_commands=True, sync_on_cog_reload=True)

bot.add_cog(AutoDelete(bot))

bot.run(TOKEN)