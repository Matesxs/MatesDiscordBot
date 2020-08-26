import subprocess
import math
import asyncio
import discord
from discord.ext import commands

from ext.modules.botBase import BaseBot
from ext.miscellaneous.custom_loger import setup_custom_logger
from ext.helpers.general_helpers import developer, generate_error_message, generate_success_message
from ext.modules.database_module import is_id_in_items
from ext.helpers.database_helper_objects import Item
from config import MAXIMUM_INVENTORY_SIZE

logger = setup_custom_logger(__name__)

class Developer(commands.Cog):
	def __init__(self, bot:BaseBot):
		self.bot = bot

	@commands.command(no_pm=False, help='!servers shows server names and ids')
	@developer()
	async def servers(self, ctx):
		emb = discord.Embed(title='Server List', colour=discord.Color.dark_blue())
		servers = list(self.bot.guilds)
		for server in servers:
			emb.add_field(name=server.name, value=str(int(server.id)), inline=True)

		await ctx.message.delete()
		await self.bot.send_message_for_time(ctx, embed=emb, time=10)

	@commands.command(no_pm=False, help="!ltrace for display last error trace callback")
	@developer()
	async def ltrace(self, ctx):
		await ctx.message.delete()

		if self.bot.last_trace_callback:
			emb = discord.Embed(title='Last trace callback', colour=discord.Color.dark_blue(), description = self.bot.last_trace_callback)
		else:
			emb = discord.Embed(title='Last trace callback', colour=discord.Color.dark_blue(), description="No error trace callbacks!")

		await self.bot.send_message_for_time(ctx, embed=emb, time=10)

	@commands.command(no_pm=False, help='!exec <bash command> to execute bash command on server machine')
	@developer()
	async def exec(self, ctx, *, command:str):
		try:
			ret = subprocess.run(command, stdout=subprocess.PIPE).stdout.decode('utf-8')
		except:
			await ctx.message.delete()
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Failed to run this command"))

		ret_num = math.ceil(len(ret) / 1500)

		msgs = []

		for i in range(ret_num):
			if len(ret[i:]) > 1500:
				msgs.append(await ctx.send(f'```\n{ret[i * 1500:(i + 1) * 1500]}\n```'))
			else:
				msgs.append(await ctx.send(f'```\n{ret[i * 1500:]}\n```'))
			await asyncio.sleep(0.5)

		await self.bot.send_message_for_time(ctx, embed=generate_success_message("Command finished!"))
		await ctx.message.delete()
		for mes in msgs:
			await asyncio.sleep(15)
			await mes.delete()

	@commands.command(no_pm=False, name='leaveg', help='!leaveg <server_id> for leave server with specified id')
	@developer()
	async def _leave_s(self, ctx, sid: int):
		server = self.bot.get_guild(sid)
		if server:
			try:
				await server.leave()
			except:
				await ctx.send(embed=generate_error_message(f'Cant leave server {server.name}'))
		else:
			await ctx.send(embed=generate_error_message(f'Cant find server with id: {sid}'))

	@commands.command(no_pm=False, name="shutdown", help="!shutdown to stop the bot")
	@developer()
	async def shutdown(self, ctx):
		logger.warning("Stopping bot from discord command")
		await ctx.send(embed=generate_success_message("Shutting Down, bye! :slight_smile:"))
		await self.bot.stop_bot(True)

	@commands.command(no_pm=False, name="restart", help="!restart for bot restart")
	@developer()
	async def _restart(self, ctx):
		logger.warning("Restarting bot from discord command")
		await ctx.send(embed=generate_success_message("Restarting! :slight_smile:"))
		await self.bot.stop_bot(False)

	@commands.command(no_pm=False, name="add_coins", help="!add_coins <mention> <amount> to add coins to person")
	@developer()
	async def add_coins(self, ctx, mention:str, ammount:int):
		await ctx.message.delete()

		if ammount < 1: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid ammount of coins, min 1"), time=5)

		try:
			mention_id = int(mention[3:-1])
		except:
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid mention"), time=5)

		disc_user = self.bot.get_user(mention_id)
		if not disc_user: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid mention"), time=5)

		user = await self.bot.database_handler.get_user(disc_user)
		user.coins += ammount
		if not await user.update_user(): return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Failed to update user in database!"), time=5)
		return await self.bot.send_message_for_time(ctx, embed=generate_success_message(f"{ammount} coins added to {disc_user.name} - Current coins: {user.coins}"), time=5)

	@commands.command(no_pm=False, name="add_xp", help="!add_xp <mention> <amount> to add xp to person")
	@developer()
	async def add_xp(self, ctx, mention: str, ammount: int):
		await ctx.message.delete()

		if ammount < 1: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid ammount of xp, min 1"), time=5)

		try:
			mention_id = int(mention[3:-1])
		except:
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid mention"), time=5)

		disc_user = self.bot.get_user(mention_id)
		if not disc_user: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid mention"), time=5)

		user = await self.bot.database_handler.get_user(disc_user)

		user.xp += ammount
		user.try_levelup()

		if not await user.update_user(): return await self.bot.send_message_for_time(ctx, embed=generate_error_message( "Failed to update user in database!"), time=5)
		return await self.bot.send_message_for_time(ctx, embed=generate_success_message(f"{ammount} xp added to {disc_user.name} - Current level: {user.level}, Current xp: {user.xp}"), time=5)

	@commands.command(no_pm=False, name="give_item", help="!give_item <mention> <item_id> specific item to person")
	@developer()
	async def give_item(self, ctx, mention:str, identifier:int):
		await ctx.message.delete()

		if identifier < 0: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid item id!"), time=5)
		if not is_id_in_items(identifier): return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Item with this id doesn't exist!"), time=5)

		try:
			mention_id = int(mention[3:-1])
		except:
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid mention"), time=5)

		disc_user = self.bot.get_user(mention_id)
		if not disc_user: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid mention"), time=5)

		user = await self.bot.database_handler.get_user(disc_user)
		if len(user.items) >= MAXIMUM_INVENTORY_SIZE: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Failed to give item - user have full inventory!"), time=5)
		item = Item.item_id_to_item(identifier)
		if not item: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Failed to found item in cached items"), time=5)

		user.items.append(item)

		if not await user.update_user(): return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Failed to update user in database!"), time=5)
		return await self.bot.send_message_for_time(ctx, embed=generate_success_message(f"Item: {item.name} was given to {user.username}"), time=5)

	@commands.command(no_pm=False, name='reload_items', help='!reload_items to reload items from file')
	@developer()
	async def reload_items(self, ctx):
		await ctx.message.delete()

		if not self.bot.database_handler.reload_items(): return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Unable to reload items!"))
		return await self.bot.send_message_for_time(ctx, embed=generate_success_message("Items reloaded!"))

def setup(bot):
	bot.add_cog(Developer(bot))