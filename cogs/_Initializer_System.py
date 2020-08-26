import discord
from discord.ext import commands

from ext.modules.botBase import BaseBot
from ext.miscellaneous.custom_loger import setup_custom_logger
from ext.helpers.general_helpers import developer, generate_success_message, generate_error_message

logger = setup_custom_logger(__name__)

class Initializer_System(commands.Cog):
	def __init__(self, bot:BaseBot):
		self.bot = bot

	async def create_role(self, guild:discord.Guild, name:str, color:discord.Color, reason:str=None):
		try:
			if not discord.utils.get(guild.roles, name=name):
				await guild.create_role(reason=reason,
			                          name=name,
			                          color=color,
				                        mentionable=True)
		except Exception as e:
			logger.exception(f"Failed to create Bcommander role in {guild.name} guild\n'''{e}'''")

	async def initialize_guild(self, guild:discord.Guild):
		await self.create_role(guild, "Bcommander", discord.Color(0xffd500), reason="Main control over the bot")
		await self.bot.database_handler.get_guild_settings(guild)

	@commands.command(no_pm=False, name="reinit", hidden=True)
	@developer()
	async def reinit(self, ctx:commands.Context, *, guild_id:int=None):
		await ctx.message.delete()

		if guild_id:
			guild = discord.utils.get(self.bot.guilds, id=guild_id)
			if guild:
				await self.initialize_guild(guild)
			else:
				return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant find this guild"), time=5)
		else:
			await self.initialize_guild(ctx.guild)

		await self.bot.send_message_for_time(ctx, embed=generate_success_message("Reinit complete!"), time=5)

	@commands.Cog.listener()
	async def on_guild_join(self, guild:discord.Guild):
		logger.debug(f"{guild.name} added this bot")
		await self.initialize_guild(guild)

	@commands.Cog.listener()
	async def on_guild_remove(self, guild:discord.Guild):
		logger.debug(f"{guild.name} removed this bot")
		settings = await self.bot.database_handler.get_guild_settings(guild)
		await settings.delete_guild_settings()

	@commands.Cog.listener()
	async def on_member_join(self, member:discord.Member):
		logger.debug(f"{member.display_name} join {member.guild.name}")
		guild_settings = await self.bot.database_handler.get_guild_settings(member.guild)

		if guild_settings.default_role:
			def_role = discord.utils.get(member.guild.roles, name=guild_settings.default_role)
			if def_role:
				logger.debug(f"Adding {guild_settings.default_role} to {member.display_name} in {member.guild.name} server")
				await member.add_roles(def_role, reason="Default role is set for this guild")

		if guild_settings.welcome_message:
			em = discord.Embed(title=":sparkles: Welcome :sparkles:", color=discord.Color.blue())
			em.description = guild_settings.welcome_message
			em.set_author(name=member.guild.name, icon_url=member.guild.icon_url)
			await member.send(embed=em)

	@commands.Cog.listener()
	async def on_member_remove(self, member:discord.Member):
		logger.debug(f"{member.display_name} left {member.guild.name}")
		pass

def setup(bot):
	bot.add_cog(Initializer_System(bot))