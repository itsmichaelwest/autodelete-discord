import datetime
import discord
from discord import Embed
from discord.ext import commands, tasks
from discord_slash.context import ComponentContext, SlashContext
from discord_slash import cog_ext
import asyncio
from discord_slash.model import ButtonStyle
from datetime import date, datetime, time, timedelta
import os
from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_components import create_actionrow, create_button, wait_for_component
import requests
from urllib.parse import urlparse

from constants import BOT_NAME, VERSION, CODENAME

import cogs.db
from cogs.timeconvert import convert_secs

no_perms_embed = Embed()
no_perms_embed.title = ":no_entry: Missing permsissions"
no_perms_embed.description = "You do not have permission to use this command. Please contact a server administrator."
no_perms_embed.color = discord.Color.dark_red()

class AutoDelete(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as {self.bot.user}")
        self.cleanup_self.start()


    @tasks.loop(minutes=1)
    async def cleanup_self(self):
        info = cogs.db.get_all_info()
        for i in info:
            try:
                channel = await self.bot.fetch_channel(i["channel"])
                before_time = datetime.utcnow() - timedelta(minutes=i["timeout"])
                print(f"Cleaning up channel {channel} in server {channel.guild}, removing all messages sent before {before_time}.")
                try:
                    await channel.purge(before=before_time)
                except:
                    print(f"Unable to clean up {channel}")
            except:
                print(f"Unable to fetch information for channel {i['channel']}. The bot is likely not in this server.")


    @commands.command()
    async def archive(self, ctx):
        embed = Embed()
        if ctx.message.reference:
            message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            result = cogs.db.get_archive(message.channel.id)
            if result:
                member = await message.guild.fetch_member(message.author.id)
                embed.set_author(name=member.display_name, icon_url=member.avatar_url)
                embed.description = message.content
                embed.set_footer(text=f"Archived by {ctx.message.author.display_name}", icon_url=ctx.message.author.avatar_url)
                embed.timestamp = ctx.message.created_at

                channel_id = result
                try:
                    channel = await self.bot.fetch_channel(int(channel_id))

                    if message.attachments:
                        image_url = str(message.attachments[0])
                        url_path = urlparse(image_url).path
                        ext = os.path.splitext(url_path)[1]
                        image_data = requests.get(image_url).content
                        file_name = f"image{ext}"
                        with open(file_name, 'wb') as handler:
                            handler.write(image_data)
                        file_data = discord.File(file_name)
                        embed.set_image(url=f"attachment://{file_name}")
                        await channel.send(file=file_data, embed=embed)
                        os.remove(file_name)
                    else:
                        await channel.send(embed=embed)
                    await ctx.message.delete()
                except discord.errors.Forbidden:
                    error_embed = Embed()
                    error_embed.title = ":no_entry: Missing bot permsissions"
                    error_embed.description = f"""{BOT_NAME} does not have permission to send messages in **<#{channel_id}>**. Ask a server administrator to ensure that the {BOT_NAME} role has the following permissions:
                    • *View Channel*
                    • *Send Messages*
                    • *Embed Links*
                    • *Attach Files*"""
                    error_embed.color = discord.Color.dark_red()
                    await ctx.reply(embed=error_embed)
            else:
                embed.title = ":x: No archive channel configured"
                embed.description = "An archive channel needs to be set up before messages can be saved. Ask an administrator to run `/archive` and select a channel."
                embed.color = discord.Color.dark_red()
                await ctx.reply(embed=embed, delete_after=10)
        else:
            embed.title = ":exclamation: Error when archiving"
            embed.description = "You need to reply to a message with this command."
            embed.color = discord.Color.dark_red()
            await ctx.reply(embed=embed, delete_after=5)
            await asyncio.sleep(5)
            await ctx.message.delete()


    @cog_ext.cog_slash(
        name="info",
        description=f"Get current information about how {BOT_NAME} is set up in this channel."
    )
    async def get_info(self, ctx: SlashContext):
        result = cogs.db.get_info(ctx.channel.id)
        embed = Embed()
        if result:
            time = f"{str(timedelta(minutes=result['timeout']))}"
            
            embed.title = f":white_check_mark: {BOT_NAME} is active in this channel"
            embed.add_field(
                name="Timeout",
                value=time
            )
            embed.color = discord.Color.dark_green()

            if result["archive"]:
                embed.add_field(
                    name="Archive",
                    value=f"<#{result['archive']}>"
                )
            else:
                embed.add_field(
                    name="Archive",
                    value="*Not configured*"
                )
        else:
            embed.title = f":no_entry_sign: {BOT_NAME} is not set up in this channel."
            embed.description = f"Ask a server administrator to run the `/setup` command to configure {BOT_NAME} for this channel."
            embed.color = discord.Color.dark_red()

        await ctx.send(embed=embed)


    @cog_ext.cog_slash(
        name="timeout", 
        description=f"Set the timeout for {BOT_NAME} in this channel.",
        options=[
            create_option(
                name="minutes",
                description="Timeout in minutes.",
                option_type=4,
                required=True
            )
        ]
    )
    async def set_timeout(self, ctx: SlashContext, minutes):
        if ctx.author.guild_permissions.administrator:
            if cogs.db.set_timeout(ctx.channel.id, minutes):
                embed = Embed()
                embed.title = ":white_check_mark: Timeout set successfully"
                embed.description = f"Messages in this channel will delete after {minutes} minutes."
                embed.color = discord.Color.dark_green()
                await ctx.channel.edit(topic=f"Messages are deleted after {convert_secs(minutes * 60)}. Reply to a message with **!archive** to save it.")
                await ctx.send(embed=embed, hidden=True)
        else:
            await ctx.send(embed=no_perms_embed, hidden=True)


    # Archive command
    @cog_ext.cog_slash(
        name="archive",
        description="Set the channel that messages can be archived into.",
        options=[
            create_option(
                name="channel",
                description=f"A valid channel for {BOT_NAME} to archive messages into.",
                option_type=7,
                required=True
            )
        ]
    )
    async def set_archive(self, ctx: SlashContext, channel):
        if ctx.author.guild_permissions.administrator:
            if cogs.db.set_archive(ctx.channel.id, channel.id):
                embed = Embed()
                embed.title = ":white_check_mark: Archive set successfully"
                embed.description = f"Messages will be archived in the <#{channel.id}> channel."
                embed.color = discord.Color.dark_green()
                await ctx.send(embed=embed, hidden=True)
        else:
            await ctx.send(embed=no_perms_embed, hidden=True)


    # Clear command
    @cog_ext.cog_slash(
        name="clear",
        description="Clear messages in this channel."
    )
    async def clear_all(self, ctx: SlashContext):
        if ctx.author.guild_permissions.administrator:
            await ctx.defer(hidden=True)
            deleted = await ctx.channel.purge()
            embed = Embed()
            embed.title = ":white_check_mark: Clear successful"
            embed.description = f"Deleted {len(deleted)} messages from this channel."
            embed.color = discord.Color.dark_green()
            await ctx.send(embed=embed, hidden=True)
        else:
            await ctx.send(embed=no_perms_embed, hidden=True)


    # Help command
    @cog_ext.cog_slash(
        name="help",
        description=f"Get help on using {BOT_NAME}."
    )
    async def help(self, ctx: SlashContext):
        helpEmbed = Embed()
        helpEmbed.title = f"{BOT_NAME} Help"
        helpEmbed.description = f"""*{BOT_NAME}* is pretty simple to use. Most of the time, you won't even know its there.
        
        **Initializing {BOT_NAME}**
        Before {BOT_NAME} can be used in a channel, you need to type `/setup` and then choose the `initialize` option from the list. This will register the channel with {BOT_NAME} with a default timeout of 3 hours.

        **Archiving a message**
        To archive a message, reply to it with the text `!archive`.

        **Updating the deletion timeout**
        You can adjust the deletion timeout by typing `/timeout` followed by the number of minutes you would like messages to persist for. {BOT_NAME} will apply the timeout to all messages in the channel, and update the channel description.

        **Deleting all messages in a channel**
        Sometimes, you'll want to clear a channel of all messages. {BOT_NAME} also supports this functionality, use the `/clear` command and {BOT_NAME} will attempt to delete all the messages in the channel.
        """
        await ctx.send(embed=helpEmbed, hidden=True)


    # Changelog command
    @cog_ext.cog_slash(
        name="changelog",
        description=f"What's new in {BOT_NAME}?"
    )
    async def changelog(self, ctx: SlashContext):
        changelogEmbed = Embed()
        changelogEmbed.title = f"{BOT_NAME} {VERSION} *{CODENAME}*"
        changelogEmbed.color = discord.Color.blurple()
        changelogEmbed.description = f"""• {BOT_NAME} now deletes messages using a task loop as opposed to setting a timer when the message is sent. This is more robust, allows for deletion to occur after the bot has been restarted, and allows for the timeout to be adjusted for all messages on the fly.
        • The `/clear` command has been updated to be more robust and to return more detail once deletion has been completed.
        """
        changelogEmbed.set_footer(text="Last update: July 14, 2021")
        await ctx.send(embed=changelogEmbed)



    @cog_ext.cog_slash(
        name="setup",
        description=f"{BOT_NAME} setup."
    )
    async def admin(self, ctx: SlashContext):
        if ctx.author.guild_permissions.administrator:
            action_row = create_actionrow(
                create_button(
                    custom_id="autodelete-init",
                    style=ButtonStyle.blurple,
                    label=f"Initialize {BOT_NAME} in this channel"
                ),
                create_button(
                    custom_id="autodelete-cdel",
                    style=ButtonStyle.danger,
                    label=f"Remove {BOT_NAME} from this channel"
                )
            )
            await ctx.send("You can perform a variety of setup commands here. To cancel this, just dismiss the message.", components=[action_row], hidden=True)
            button_ctx: ComponentContext = await wait_for_component(self.bot, components=action_row)
            if button_ctx.custom_id == "autodelete-init":
                if cogs.db.init_bot(ctx.guild.id, ctx.channel.id):
                    await button_ctx.edit_origin(content="Channel has been initialized with a default timeout of 3 hours.")
                    try:
                        await ctx.channel.edit(topic="Messages are deleted after 3 hours. Reply to a message with **!archive** to save it.")
                    except:
                        pass
            elif button_ctx.custom_id == "autodelete-cdel":
                if cogs.db.reset_channel(ctx.channel.id):
                    await button_ctx.edit_origin(content=f"This channel has been removed from {BOT_NAME}. Re-run `/setup` and choose `Initialize` to set up {BOT_NAME} again.")
        else:
            await ctx.send(embed=no_perms_embed, hidden=True)
        

def setup(bot):
    bot.add_cog(AutoDelete(bot))