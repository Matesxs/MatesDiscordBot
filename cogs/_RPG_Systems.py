import random
import discord
from discord.ext import commands

import config
from ext.modules.botBase import BaseBot
from ext.miscellaneous.custom_loger import setup_custom_logger
from ext.helpers.general_helpers import developer, generate_error_message, generate_success_message
from ext.helpers.database_helper_objects import Item
from config import XP_MESSAGE_DROP_AMMOUNT, COIN_MESSAGE_DROP_BONUS, COIN_MESSAGE_DROP_MIN, COIN_MESSAGE_DROP_MAX

logger = setup_custom_logger(__name__)

class RPG_Systems(commands.Cog):
	def __init__(self, bot:BaseBot):
		self.bot = bot
		self.xp_message_drop_chance = config.XP_MESSAGE_DROP_CHANCE
		self.coin_message_drop_chance = config.COIN_MESSAGE_DROP_CHANCE
		self.item_message_drop_chance = config.ITEM_MESSAGE_DROP_CHANCE
		
	@commands.command(no_pm=True, name="xp_message_drop_chance", aliases=["xpmdch"], hidden=True)
	@developer()
	async def xp_drop_chance_change(self, ctx, *, val:float):
		await ctx.message.delete()

		if 0 > val > 1:
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid value"), time=5)
		self.xp_message_drop_chance = val
		await self.bot.send_message_for_time(ctx, embed=generate_success_message(f"XP message drop chance temporary changed to: {val * 100}%"), time=5)

	@commands.command(no_pm=True, name="coin_message_drop_chance", aliases=["cmdch"], hidden=True)
	@developer()
	async def coin_message_drop_chance_change(self, ctx, *, val: float):
		await ctx.message.delete()

		if 0 > val > 1:
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid value"), time=5)
		self.coin_message_drop_chance = val
		await self.bot.send_message_for_time(ctx, embed=generate_success_message(f"Coin message drop chance temporary changed to: {val * 100}%"), time=5)

	@commands.command(no_pm=True, name="item_message_drop_chance", aliases=["imdch"], hidden=True)
	@developer()
	async def item_message_drop_chance_change(self, ctx, *, val: float):
		await ctx.message.delete()

		if 0 > val > 1:
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid value"), time=5)
		self.item_message_drop_chance = val
		await self.bot.send_message_for_time(ctx, embed=generate_success_message(f"Item message drop chance temporary changed to: {val * 100}%"), time=5)

	@commands.Cog.listener()
	async def on_message(self, message:discord.Message):
		if message.author.id == self.bot.user.id:
			return

		if message.author.bot:
			return

		ctx = await self.bot.get_context(message)

		if not ctx.valid:
			user = None
			if random.random() < self.xp_message_drop_chance:
				if not user:
					user = await self.bot.database_handler.get_user(message.author)

				user.xp += XP_MESSAGE_DROP_AMMOUNT
				leveltup = user.try_levelup()

				if leveltup:
					em = discord.Embed(description='Levelup!', colour=discord.Color.blue())
					em.set_author(name=ctx.message.author.name, icon_url=ctx.message.author.avatar_url)
					em.add_field(name='Actual Level:', value=str(user.level))

					await self.bot.send_message_for_time(ctx, embed=em, time=5)

			if random.random() < self.coin_message_drop_chance:
				if not user:
					user = await self.bot.database_handler.get_user(message.author)

				if random.randint(0, 200) == 186:
					em = discord.Embed(title=":moneybag: BONUS Coins :moneybag:", description=f'You get {COIN_MESSAGE_DROP_BONUS} :moneybag:', colour=discord.Color.gold())
					em.set_author(name=str(ctx.message.author.name), icon_url=ctx.message.author.avatar_url)
					await self.bot.send_message_for_time(ctx, embed=em, time=5)

					user.coins += COIN_MESSAGE_DROP_BONUS
				else:
					amount = random.randint(COIN_MESSAGE_DROP_MIN, COIN_MESSAGE_DROP_MAX)
					em = discord.Embed(description=f'You get {amount} :moneybag:', colour=discord.Color.gold())
					em.set_author(name=str(ctx.message.author.name), icon_url=ctx.message.author.avatar_url)
					await self.bot.send_message_for_time(ctx, embed=em, time=3)

					user.coins += amount

			if config.ITEM_MESSAGE_DROP_IDS:
				if random.random() < self.item_message_drop_chance:
					if not user:
						user = await self.bot.database_handler.get_user(message.author)

					if len(user.items) < config.MAXIMUM_INVENTORY_SIZE:
						item = Item.item_id_to_item(random.choice(config.ITEM_MESSAGE_DROP_IDS))
						user.items.append(item)
						em = discord.Embed(title=":pouch: Random Loot :pouch:",description=f'You get {item.name}', colour=discord.Color.blurple())
						em.set_author(name=str(ctx.message.author.name), icon_url=ctx.message.author.avatar_url)
						await self.bot.send_message_for_time(ctx, embed=em, time=5)

			if user:
				if not await user.update_user():
					logger.warning("Failed to update user - on_message")

def setup(bot):
	bot.add_cog(RPG_Systems(bot))