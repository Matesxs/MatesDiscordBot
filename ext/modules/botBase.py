import os
from typing import Union
import traceback
import time
from concurrent.futures import ThreadPoolExecutor
import discord
from discord.ext import commands

from ext.miscellaneous.custom_loger import setup_custom_logger
from ext.helpers.general_helpers import load_extensions, generate_error_message
from ext.modules.database_module import DatabaseHelper
from config import MODULES_PATH, STATUS_MESSAGE, IGNORE_COMMAND_ERRORS, WORKERS_OF_SYNC_TASKS_EXECUTOR

logger = setup_custom_logger(__name__)

class BaseBot(commands.AutoShardedBot):
	custom_extensions = None
	last_trace_callback = None
	ended = False

	def __init__(self, prefix, description):
		super().__init__(command_prefix=prefix, description=description)

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
		elif not IGNORE_COMMAND_ERRORS:
			self.last_trace_callback = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
			logger.error(f"\n\n{self.last_trace_callback}\n")
			await ctx.send(embed=discord.Embed(title="Error trace", color=discord.Color.red(), description=self.last_trace_callback))
		else:
			pass