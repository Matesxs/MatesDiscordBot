import discord
from discord.ext import commands
from config import TESTERS, CREATOR
import inspect

from ext.miscellaneous.custom_loger import setup_custom_logger

logger = setup_custom_logger(__name__)

def is_developer(ctx):
	if ctx.author.id == CREATOR:
		return True
	if ctx.author.id in TESTERS:
		return True
	return False

def is_developer_or_tester(ctx):
	if ctx.author.id == CREATOR:
		return True
	if ctx.author.id in TESTERS:
		return True

def is_bcommander(ctx):
	if discord.utils.get(ctx.author.roles, name="Bcommander"):
		return True
	else:
		return False

def developer():
	def wrapper(ctx):
		if is_developer(ctx): return True
		raise commands.MissingPermissions('You cannot use this command because you are not a developer.')
	return commands.check(wrapper)

def developerOrTester():
	def wrapper(ctx):
		if is_developer(ctx): return True
		raise commands.MissingPermissions('You cannot use this command because you are not a developer.')
	return commands.check(wrapper)

def get_creator(ins):
	return ins.get_user(CREATOR)

def cut_string(string: str, part_len: int):
	return list(string[0 + i: part_len + i] for i in range(0, len(string), part_len))

def load_extensions(ins, cogs, path='cogs'):
	for cog in cogs:
		members = inspect.getmembers(cog)
		for name, member in members:
			if name.startswith('on_'):
				ins.add_listener(member, name)
		try:
			ins.load_extension(f'{path}.{cog}')
		except Exception as e:
			logger.exception(f'LoadError: {cog}\n{type(e).__name__}: {e}')
			raise e
	return len(cogs)

def generate_error_message(text):
	return discord.Embed(color=discord.Color.dark_red(), title=":x: | Error", description=text)

def generate_success_message(text):
	return discord.Embed(color=discord.Color.green(), title=":white_check_mark: | Success", description=text)