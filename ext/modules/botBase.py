import os
from typing import Union
import traceback
import time
from concurrent.futures import ThreadPoolExecutor
import discord
from discord.ext import commands

from ext.miscellaneous.custom_loger import setup_custom_logger
from ext.helpers.general_helpers import load_extensions, generate_error_message, cut_string
from ext.modules.database_module import DatabaseHelper
from config import MODULES_PATH, STATUS_MESSAGE, WORKERS_OF_SYNC_TASKS_EXECUTOR, DEVELOPER_CHANNEL_ID, DEVELOPER_SERVER_ID

logger = setup_custom_logger(__name__)

class BaseBot(commands.AutoShardedBot):
	custom_extensions = None
	last_trace_callback = None
	ended = False

	def __init__(self, prefix, description):
		intents = discord.Intents.all()
		super().__init__(command_prefix=prefix, description=description, intents=intents)

		self.remove_command("help")
		self.load_addons(MODULES_PATH, "cogs loaded")

		self.database_handler = DatabaseHelper()

		self.boot_time = time.time()

		self.sync_tasks_executor = ThreadPoolExecutor(max_workers=WORKERS_OF_SYNC_TASKS_EXECUTOR)

	def __del__(self):
		self.sync_tasks_executor.shutdown()

	async def stop_bot(self, end:bool=False):
		for client in self.voice_clients:
			try:
				if client.is_playing():
					await client.stop()
			except:
				pass
			try:
				if client.is_connected():
					await client.disconnect()
			except:
				pass

		await self.logout()
		self.ended = end

	@staticmethod
	async def send_message_for_time(source:Union[commands.Context, discord.TextChannel], cont=None, embed=None, time:int=5):
		msg = await source.send(cont, embed=embed)
		try:
			await msg.delete(delay=time)
		except:
			pass

	async def on_message(self, message:discord.Message):
		if not message.author.bot:
			await self.process_commands(message)

	def load_addons(self, path, description):
		self.custom_extensions = [x.replace('.py', '') for x in os.listdir(path) if x.endswith('.py')]
		num_of_loaded_extensions = load_extensions(self, self.custom_extensions, path)
		logger.info(f"{num_of_loaded_extensions} {description}")

	async def on_ready(self):
		logger.info('Logged in as: {0} (ID: {0.id})'.format(self.user))
		await self.change_presence(activity=discord.Game(name=STATUS_MESSAGE, type=0), status=discord.Status.online, afk=False)
		logger.info('Ready!')

	# Copied from https://github.com/Toaster192/rubbergod
	async def on_error(self, event_method, *args, **kwargs):
		output = traceback.format_exc()
		logger.error(output)

		if not DEVELOPER_CHANNEL_ID or not DEVELOPER_SERVER_ID: return
		channel_out:discord.TextChannel = self.get_channel(DEVELOPER_CHANNEL_ID)
		if not channel_out: return

		embeds = []
		for arg in args:
			if arg.guild_id:
				guild = self.get_guild(arg.guild_id)
				event_guild = guild.name
				channel = guild.get_channel(arg.channel_id)
				message = await channel.fetch_message(arg.message_id)
				message = message.content[:1000]
			else:
				event_guild = "DM"
				message = arg.message_id

			user = self.get_user(arg.user_id)
			if not user:
				user = arg.user_id
			else:
				channel = self.get_channel(arg.channel_id)
				if channel:
					message = await channel.fetch_message(arg.message_id)
					if message.content:
						message = message.content[:1000]
					elif message.embeds:
						embeds.extend(message.embeds)
						message = "Embed v předchozí zprávě"
					elif message.attachments:
						message_out = ""
						for attachment in message.attachments:
							message_out += f"{attachment.url}\n"
						message = message_out
				else:
					message = arg.message_id
				user = str(user)
			embed = discord.Embed(title=f"Ignoring exception in event '{event_method}'", color=0xFF0000)
			embed.add_field(name="Zpráva", value=message, inline=False)
			if arg.guild_id != DEVELOPER_SERVER_ID:
				embed.add_field(name="Guild", value=event_guild)

			if arg.member:
				reaction_from = str(arg.member)
			else:
				reaction_from = user
			embed.add_field(name="Reakce od", value=reaction_from)
			embed.add_field(name="Reaction", value=arg.emoji)
			embed.add_field(name="Typ", value=arg.event_type)
			if arg.guild_id:
				link = f"https://discord.com/channels/{arg.guild_id}/{arg.channel_id}/{arg.message_id}"
				embed.add_field(name="Link", value=link, inline=False)
			embeds.append(embed)

		if channel_out is not None:
			output = cut_string(output, 1900)
			for embed in embeds:
				await channel_out.send(embed=embed)
			for message in output:
				await channel_out.send(f"```\n{message}```")

	async def on_command_error(self, ctx, error):
		if isinstance(error, commands.CommandNotFound):
			await ctx.message.delete()
			await self.send_message_for_time(ctx, embed=generate_error_message('Unknown command - use !help for all commands'), time=5)
		elif isinstance(error, commands.CommandOnCooldown):
			await ctx.message.delete()
			await self.send_message_for_time(ctx, embed=generate_error_message(f'This command is on cooldown. Please wait {error.retry_after:.2f}s'), time=5)
		elif isinstance(error, commands.MissingPermissions):
			await ctx.message.delete()
			await self.send_message_for_time(ctx, embed=generate_error_message(f'You do not have the permissions to use this command.'), time=5)
		elif isinstance(error, commands.MissingRole):
			await ctx.message.delete()
			await self.send_message_for_time(ctx, embed=generate_error_message(f'You do not have {error.missing_role} role to use this command'), time=5)
		elif isinstance(error, commands.MissingRequiredArgument):
			await ctx.message.delete()
			await self.send_message_for_time(ctx, embed=generate_error_message(f'Some arguments of command missing, use help to get more info'), time=5)
		elif isinstance(error, commands.BadArgument):
			await ctx.message.delete()
			await self.send_message_for_time(ctx, embed=generate_error_message(f'Some arguments of command missing or wrong, use help to get more info'), time=5)
		else:
			pass