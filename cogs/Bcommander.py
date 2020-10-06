import asyncio
from typing import Union
import datetime
import discord
from discord.ext import commands

from ext.modules.botBase import BaseBot
from ext.miscellaneous.custom_loger import setup_custom_logger
from ext.helpers.general_helpers import generate_error_message, generate_success_message
from ext.modules.prompt import PromptSession

logger = setup_custom_logger(__name__)

class Bcommander(commands.Cog):
	def __init__(self, bot:BaseBot):
		self.bot = bot

	@commands.command(pass_context=True, no_pm=True, help='!clear <1 - 100> for clearing messages from curent channel')
	@commands.has_role('Bcommander')
	@commands.cooldown(2, 10, commands.BucketType.user)
	async def clear(self, ctx, amount: int):
		await ctx.message.delete()
		await asyncio.sleep(1)

		if 0 < amount <= 100:
			try:
				deleted = await ctx.channel.purge(limit=amount)
				await self.bot.send_message_for_time(ctx, embed=generate_success_message(f"Deleted {len(deleted)} messages!"), time=5)
			except:
				await self.bot.send_message_for_time(ctx, embed=generate_error_message('Failed to clear messages'), time=5)
		else:
			await self.bot.send_message_for_time(ctx, embed=generate_error_message('Bad argument, set number between 1 and 100'), time=5)

	@commands.command(no_pm=True, name='say', help='!say <message> for send message by bot')
	@commands.has_role('Bcommander')
	@commands.cooldown(5, 20, commands.BucketType.user)
	async def _say(self, ctx, *, message:str=None):
		await ctx.message.delete()

		if not message:
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message('Specify message you want to send'), time=5)

		await ctx.send(message)

	@commands.command(no_pm=True, name='counter', help='!counter <number 1 - 600> count from number to 0')
	@commands.has_role('Bcommander')
	@commands.cooldown(2, 30, commands.BucketType.user)
	async def counter(self, ctx, *, count: int):
		await ctx.message.delete()

		if 0 > count > 600: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Count number have to be greater than 0 and equal or smaller than 600"), time=5)

		msg = await ctx.send(embed=discord.Embed(title=':timer: | Counter', description=f'{count}', colour=discord.Color.green()))
		for i in range(count):
			await asyncio.sleep(1)

			count -= 1
			emb = discord.Embed(title=':timer: | Counter', description=f'{count}', colour=discord.Color.green())

			if count > 5:
				if count%5 == 0:
					await msg.edit(embed=emb)
			else:
				if count == 0:
					emb = discord.Embed(title=':timer: | Counter', description='Done!', colour=discord.Color.green())
				await msg.edit(embed=emb)

		await asyncio.sleep(5)
		await msg.delete()

	@commands.command(no_pm=True, name='set_def_role', help='!set_def_role <optional role name> to set default role for new users on your server, leave blank for remove current default role')
	@commands.has_role('Bcommander')
	@commands.cooldown(1, 30, commands.BucketType.user)
	async def set_def_role(self, ctx, *, role_name:str=None):
		await ctx.message.delete()

		if role_name:
			if not discord.utils.get(ctx.guild.roles, name=role_name): return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant find this role on your server!\nEnter valid role name."))

		guild_settings = await self.bot.database_handler.get_guild_settings(ctx.guild)
		guild_settings.default_role = role_name

		if not await guild_settings.update_guild_settings(): return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant update your guild in database!"))
		return await self.bot.send_message_for_time(ctx, embed=generate_success_message(f"Your default role was set to: {role_name}"))

	@commands.command(no_pm=True, name='set_mute_role', help='!set_mute_role <optional role name> to set mute role for muting users in server')
	@commands.has_role('Bcommander')
	@commands.cooldown(1, 30, commands.BucketType.user)
	async def set_mute_role(self, ctx, *, role_name:str=None):
		await ctx.message.delete()

		if role_name:
			if not discord.utils.get(ctx.guild.roles, name=role_name): return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant find this role on your server!\nEnter valid role name."))

		guild_settings = await self.bot.database_handler.get_guild_settings(ctx.guild)
		guild_settings.muted_role = role_name

		if not await guild_settings.update_guild_settings(): return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant update your guild in database!"))
		return await self.bot.send_message_for_time(ctx, embed=generate_success_message(f"Your mute role was set to: {role_name}"))

	@commands.command(no_pm=True, name='set_rpg_notifications', help='!set_rpg_notifications <0 / 1> to set rpg notifications ON or OFF')
	@commands.has_role('Bcommander')
	@commands.cooldown(1, 30, commands.BucketType.user)
	async def set_rpg_notifications(self, ctx, *, notification_status:bool):
		await ctx.message.delete()

		guild_settings = await self.bot.database_handler.get_guild_settings(ctx.guild)
		guild_settings.rpg_notifications = notification_status

		if not await guild_settings.update_guild_settings(): return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant update your guild in database!"))
		return await self.bot.send_message_for_time(ctx, embed=generate_success_message(f"RPG notifications were set to: {notification_status}"))

	@commands.command(no_pm=True, name='set_welcome_message',help='!set_welcome_message <optional message> to set welcome message on your server, leave blank for remove welcome message')
	@commands.has_role('Bcommander')
	@commands.cooldown(1, 30, commands.BucketType.user)
	async def set_welcome_message(self, ctx, *, welcome_message:str=None):
		await ctx.message.delete()

		guild_settings = await self.bot.database_handler.get_guild_settings(ctx.guild)
		guild_settings.welcome_message = welcome_message

		if not await guild_settings.update_guild_settings(): return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant update your guild in database!"))
		return await self.bot.send_message_for_time(ctx, embed=generate_success_message(f"Your welcome message was set to:\n{welcome_message}"))

	@commands.command(no_pm=True, name='set_log_channel', help='!set_log_channel <optional channel name> to set log channel on your server, leave blank for remove log channel')
	@commands.has_role('Bcommander')
	@commands.cooldown(1, 30, commands.BucketType.user)
	async def set_log_channel(self, ctx, *, log_channel:str=None):
		await ctx.message.delete()

		if log_channel:
			if not discord.utils.get(ctx.guild.text_channels, name=log_channel): return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant find this channel in your server!"))

		guild_settings = await self.bot.database_handler.get_guild_settings(ctx.guild)
		guild_settings.log_channel = log_channel

		if not await guild_settings.update_guild_settings(): return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant update your guild in database!"))
		return await self.bot.send_message_for_time(ctx, embed=generate_success_message(f"Your log channel was set to:\n{log_channel}"))

	@commands.command(no_pm=True, name='settings', help='!settings to show current guild settings')
	@commands.has_role('Bcommander')
	@commands.cooldown(1, 30, commands.BucketType.user)
	async def settings(self, ctx):
		await ctx.message.delete()

		guild_settings = await self.bot.database_handler.get_guild_settings(ctx.guild)

		em = discord.Embed(title="Current guild settings", color=discord.Color.blue())
		em.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
		em.add_field(name="Default role", value=str(guild_settings.default_role), inline=False)
		em.add_field(name="Muted role", value=str(guild_settings.muted_role), inline=False)
		em.add_field(name="Log Channel", value=str(guild_settings.log_channel), inline=False)
		em.add_field(name="Welcome message", value=str(guild_settings.welcome_message), inline=False)
		em.add_field(name="YT and SE volume", value=str(guild_settings.volume) + "%", inline=False)
		em.add_field(name="RPG Notifications", value=str(guild_settings.rpg_notifications), inline=False)

		return await self.bot.send_message_for_time(ctx, embed=em, time=20)

	@commands.command(no_pm=True, name='mute', help="!mute <mention> to add mute role to user")
	@commands.has_role('Bcommander')
	@commands.cooldown(3, 30, commands.BucketType.user)
	async def mute(self, ctx:commands.Context, mention:str):
		await ctx.message.delete()

		guild_settings = await self.bot.database_handler.get_guild_settings(ctx.guild)
		if not guild_settings.muted_role: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Your mute role is not set!"), time=5)

		mute_role = discord.utils.get(ctx.guild.roles, name=guild_settings.muted_role)
		if not mute_role: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Your mute role doesn't exist anymore!"), time=5)

		try:
			mention_id = int(mention[3:-1])
		except:
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid mention"), time=5)

		user:Union[discord.Member, None] = discord.utils.get(ctx.guild.members, id=mention_id)
		if not user: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid mention"), time=5)

		try:
			await user.add_roles(mute_role, reason="Muted")
		except:
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant mute this user!"), time=5)

		em_log = discord.Embed(title=":mute: | User muted", color=discord.Color(0xffd500))
		em_log.set_thumbnail(url=user.avatar_url)
		em_log.add_field(name='Muted User', value=user.display_name)
		em_log.add_field(name='Timestamp', value=f"{datetime.datetime.now():%Y-%m-%d}")
		em_log.set_footer(text=f"Muted by {ctx.author.name}", icon_url=ctx.author.avatar_url)

		if guild_settings.log_channel:
			log_channel:Union[discord.TextChannel, None] = discord.utils.get(ctx.guild.text_channels, name=guild_settings.log_channel)
			if log_channel:
				await log_channel.send(embed=em_log)

		return await self.bot.send_message_for_time(ctx, embed=em_log)

	@commands.command(no_pm=True, name='unmute', help="!unmute <mention> to remove mute role to user")
	@commands.has_role('Bcommander')
	@commands.cooldown(3, 30, commands.BucketType.user)
	async def unmute(self, ctx: commands.Context, mention: str):
		await ctx.message.delete()

		guild_settings = await self.bot.database_handler.get_guild_settings(ctx.guild)
		if not guild_settings.muted_role: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Your mute role is not set!"), time=5)

		mute_role = discord.utils.get(ctx.guild.roles, name=guild_settings.muted_role)
		if not mute_role: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Your mute role doesn't exist anymore!"), time=5)

		try:
			mention_id = int(mention[3:-1])
		except:
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid mention"), time=5)

		user: Union[discord.Member, None] = discord.utils.get(ctx.guild.members, id=mention_id)
		if not user: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid mention"), time=5)

		try:
			await user.remove_roles(mute_role, reason="Unmuted")
		except:
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant unmute this user!"), time=5)

		em_log = discord.Embed(title=":loud_sound: | User unmuted", color=discord.Color.green())
		em_log.set_thumbnail(url=user.avatar_url)
		em_log.add_field(name='Unmuted User', value=user.display_name)
		em_log.add_field(name='Timestamp', value=f"{datetime.datetime.now():%Y-%m-%d}")
		em_log.set_footer(text=f"Unmuted by {ctx.author.name}", icon_url=ctx.author.avatar_url)

		if guild_settings.log_channel:
			log_channel: Union[discord.TextChannel, None] = discord.utils.get(ctx.guild.text_channels, name=guild_settings.log_channel)
			if log_channel:
				await log_channel.send(embed=em_log)

		return await self.bot.send_message_for_time(ctx, embed=em_log)

	@commands.command(no_pm=True, name='kickplebs', help="!kickplebs <optional reason> to remove all users with ONLY default (set by guild setting or default @everyone) rank")
	@commands.has_role('Bcommander')
	@commands.cooldown(2, 600, commands.BucketType.user)
	async def kickplebs(self, ctx: commands.Context, *, reason:str=None):
		await ctx.message.delete()

		guild_settings = await self.bot.database_handler.get_guild_settings(ctx.guild)
		default_role_name = guild_settings.default_role if guild_settings.default_role else "@everyone"

		members_to_kick = []

		for member in ctx.guild.members:
			if member is not ctx.me:
				if isinstance(member, discord.Member):
					roles_of_member = [role.name for role in member.roles]
					if default_role_name in roles_of_member and len(roles_of_member) <= 2:
						members_to_kick.append(member)

		if members_to_kick:
			usrs = ""
			for usr in members_to_kick: usrs += f"{usr.display_name}\n"

			try:
				prompt_sesstion = PromptSession(self.bot, ctx, usrs + "\nDo you realy want to kick this users?")
				result = await prompt_sesstion.run()

				if result:
					prompt_sesstion = PromptSession(self.bot, ctx, "Realy?")
					result = await prompt_sesstion.run()

				if result:
					for usr in members_to_kick:
						try:
							await usr.kick(reason=reason)
						except:
							pass

					em_log = discord.Embed(title=":mechanical_leg: | Kick", color=discord.Color.orange())
					em_log.add_field(name='Kicked users', value=usrs, inline=False)
					em_log.add_field(name='Timestamp', value=f"{datetime.datetime.now():%Y-%m-%d}", inline=False)
					if reason:
						em_log.add_field(name="Reason", value=reason, inline=False)
					em_log.set_footer(text=f"Kicked by {ctx.author.name}", icon_url=ctx.author.avatar_url)

					if guild_settings.log_channel:
						log_channel: Union[discord.TextChannel, None] = discord.utils.get(ctx.guild.text_channels, name=guild_settings.log_channel)
						if log_channel:
							await log_channel.send(embed=em_log)

					await self.bot.send_message_for_time(ctx, embed=em_log)
				else:
					await self.bot.send_message_for_time(ctx, embed=generate_error_message("Users wont be kicked"))
			except Exception:
				await self.bot.send_message_for_time(ctx, embed=generate_error_message("Something failed"))
		else:
			await self.bot.send_message_for_time(ctx, embed=generate_error_message("Nobody to kick"))

	@commands.command(no_pm=True, name='banplebs', help="!banplebs <optional reason> to remove all users (and ban them) with ONLY default (set by guild setting or default @everyone) rank")
	@commands.has_role('Bcommander')
	@commands.cooldown(2, 600, commands.BucketType.user)
	async def banplebs(self, ctx: commands.Context, *, reason: str = None):
		await ctx.message.delete()

		guild_settings = await self.bot.database_handler.get_guild_settings(ctx.guild)
		default_role_name = guild_settings.default_role if guild_settings.default_role else "@everyone"

		members_to_ban = []

		for member in ctx.guild.members:
			if member is not ctx.me:
				if isinstance(member, discord.Member):
					roles_of_member = [role.name for role in member.roles]
					if default_role_name in roles_of_member and len(roles_of_member) <= 2:
						members_to_ban.append(member)

		if members_to_ban:
			usrs = ""
			for usr in members_to_ban: usrs += f"{usr.display_name}\n"

			try:
				prompt_sesstion = PromptSession(self.bot, ctx, usrs + "\nDo you realy want to ban this users?")
				result = await prompt_sesstion.run()

				if result:
					prompt_sesstion = PromptSession(self.bot, ctx, "Realy?")
					result = await prompt_sesstion.run()

				if result:
					for usr in members_to_ban:
						try:
							await usr.ban(reason=reason)
						except:
							pass

					em_log = discord.Embed(title=":hammer: | Ban", color=discord.Color.dark_red())
					em_log.add_field(name='Banned users', value=usrs, inline=False)
					em_log.add_field(name='Timestamp', value=f"{datetime.datetime.now():%Y-%m-%d}", inline=False)
					if reason:
						em_log.add_field(name="Reason", value=reason, inline=False)
					em_log.set_footer(text=f"Banned by {ctx.author.name}", icon_url=ctx.author.avatar_url)

					if guild_settings.log_channel:
						log_channel: Union[discord.TextChannel, None] = discord.utils.get(ctx.guild.text_channels, name=guild_settings.log_channel)
						if log_channel:
							await log_channel.send(embed=em_log)

					await self.bot.send_message_for_time(ctx, embed=em_log)
				else:
					await self.bot.send_message_for_time(ctx, embed=generate_error_message("Users wont be banned"))
			except Exception:
				await self.bot.send_message_for_time(ctx, embed=generate_error_message("Something failed"))
		else:
			await self.bot.send_message_for_time(ctx, embed=generate_error_message("Nobody to ban"))

def setup(bot):
	bot.add_cog(Bcommander(bot))