import datetime
import discord
from discord import Embed
from discord.ext import commands
from discord_slash.context import ComponentContext, SlashContext
from discord_slash import cog_ext
import asyncio
from discord_slash.model import ButtonStyle
from datetime import date, datetime, time, timedelta

from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_components import create_actionrow, create_button, wait_for_component

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
        print("Telling all active channels I was restarted...")
        all_channels = cogs.db.get_all_info()
        for c in all_channels:
            try:
                channel = await self.bot.fetch_channel(c["channel"])
                embed = Embed()
                embed.title = f":warning: {BOT_NAME} was restarted"
                embed.description = f"Due to the privacy-preserving nature of this bot, {BOT_NAME} may not be able to delete messages sent before the restart occurred. A server administrator can run `/clear` in the channel to remove all messages instead of manually deleting them."
                embed.color = discord.Color.dark_gold()
                await channel.send(embed=embed)
            except discord.errors.Forbidden:
                pass
        

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        else:
            messages = await message.channel.history(limit=300).flatten()
            delta_mins = cogs.db.get_is_autodelete_active(message.channel.id)

            if delta_mins:
                compare_timestamp = datetime.utcnow() - timedelta(minutes=delta_mins)

                for m in messages:
                    if compare_timestamp > m.created_at:
                        try:
                            await m.delete()
                        except:
                            print('Could not delete the message')

                await asyncio.sleep(int(delta_mins) * 60)
                await message.delete()


    @commands.command()
    async def archive(self, ctx):
        embed = Embed()
        if ctx.message.reference:
            message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            result = cogs.db.get_archive(message.channel.id)
            if result:
                embed.set_author(name=message.author.display_name, icon_url=message.author.avatar_url)
                embed.description = message.content
                embed.set_footer(text=f"Archived by {ctx.message.author.display_name}", icon_url=ctx.message.author.avatar_url)
                embed.timestamp = ctx.message.created_at

                if message.attachments:
                    embed.set_image(url=message.attachments[0])

                if message.stickers:
                    print(message.stickers)

                channel_id = result
                try:
                    channel = await self.bot.fetch_channel(int(channel_id))
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
            time = f"{str(datetime.timedelta(minutes=result['timeout']))}"
            
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
            messages = await ctx.channel.history(limit=None).flatten()
            await ctx.channel.delete_messages(messages)
            await ctx.send('Done! Messages have been deleted.', hidden=True)
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
        You can adjust the deletion timeout by typing `/timeout` followed by the number of minutes you would like messages to persist for. {BOT_NAME} will apply the timeout to all new messages, and update the channel description.

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
        changelogEmbed.description = f"""• {BOT_NAME} has been rewritten using Python for improved development experience.
        • Administration commands are now accessed as slash commands. Simply type a forward slash (`/`) to see the available commands.
        • Timeouts can now be modified without first requiring you to delete the channel from the bot configuration.
        • Setting the archive channel is now significantly easier using the updated channel picker!
        """
        changelogEmbed.set_footer(text="Last update: July 12, 2021")
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
                    await ctx.channel.edit(topic="Messages are deleted after 3 hours. Reply to a message with **!archive** to save it.")
            elif button_ctx.custom_id == "autodelete-cdel":
                if cogs.db.reset_channel(ctx.channel.id):
                    await button_ctx.edit_origin(content=f"This channel has been removed from {BOT_NAME}. Re-run `/setup` and choose `Initialize` to set up {BOT_NAME} again.")
        else:
            await ctx.send(embed=no_perms_embed, hidden=True)
        

def setup(bot):
    bot.add_cog(AutoDelete(bot))