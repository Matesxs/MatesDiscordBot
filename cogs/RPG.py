import random
import datetime
import discord
from discord.ext import commands, tasks

from ext.modules.botBase import BaseBot
from ext.miscellaneous.custom_loger import setup_custom_logger
from ext.helpers.general_helpers import generate_error_message, generate_success_message
from config import GAMBLE_NUMBER_OF_DRAWN_NUMBERS, MAXIMUM_INVENTORY_SIZE, BASE_WORK_REVENUE_FOR_HOUR
from ext.helpers.database_helper_objects import Item
from ext.modules.prompt import PromptSession

logger = setup_custom_logger(__name__)

class BaseRPGSet(commands.Cog):
	def __init__(self, bot:BaseBot):
		self.bot = bot

	@commands.command(no_pm=True, name='level', help='!level <optional metion> shows level and xp of user')
	@commands.cooldown(3, 60, commands.BucketType.user)
	async def level(self, ctx, mention: str = None):
		await ctx.message.delete()

		if mention:
			try:
				mention_id = int(mention[3:-1])
			except:
				return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid mention"), time=5)

			disc_user = self.bot.get_user(mention_id)
			if not disc_user: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid mention"), time=5)

			icon = disc_user.avatar_url
			user = await self.bot.database_handler.get_user(disc_user)
		else:
			icon = ctx.message.author.avatar_url
			user = await self.bot.database_handler.get_user(ctx.message.author)

		if user and icon:
			missing_xp = user.xp_to_next_level()

			emb = discord.Embed(colour=discord.Color.blurple())
			emb.add_field(name='Level', value=str(user.level))
			emb.add_field(name='XP', value=str(user.xp))

			emb.set_author(name=user.username)
			emb.set_footer(text=f'{missing_xp} XP till next level', icon_url=icon)

			await self.bot.send_message_for_time(ctx, embed=emb, time=20)

	@commands.command(no_pm=True, name='bank', help='!bank <optional mention> shows coins you or someone have')
	@commands.cooldown(3, 60, commands.BucketType.user)
	async def bank(self, ctx, mention: str = None):
		await ctx.message.delete()

		if mention:
			try:
				mention_id = int(mention[3:-1])
			except:
				return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid mention"), time=5)

			disc_user = self.bot.get_user(mention_id)
			if not disc_user: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid mention"), time=5)

			icon = disc_user.avatar_url
			user = await self.bot.database_handler.get_user(disc_user)
		else:
			icon = ctx.message.author.avatar_url
			user = await self.bot.database_handler.get_user(ctx.message.author)

		if user and icon:
			emb = discord.Embed(title=":bank: | Bank", description=f"{str(user.coins)} :moneybag:", colour=discord.Color.blurple())
			emb.set_author(name=user.username, icon_url=icon)

			await self.bot.send_message_for_time(ctx, embed=emb, time=20)

	@commands.command(no_pm=True, name='gamble', help='!gamble <coin amount> to gamble some coins')
	@commands.cooldown(2, 60, commands.BucketType.user)
	async def gamble(self, ctx: commands.Context, *, coin_am: int):
		await ctx.message.delete()

		user = await self.bot.database_handler.get_user(ctx.author)
		if user.coins < coin_am: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("You have not enough money!"))

		if coin_am > (user.coins / 2):
			conf_prompt = PromptSession(self.bot, ctx, f"Do you realy want to gamble with {coin_am} :moneybag:?")
			res = await conf_prompt.run()
			if not res:
				return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Gamble canceled!"))

		random.seed()
		golden_number = random.randint(0, 100)
		win_numbers = []
		while len(win_numbers) < GAMBLE_NUMBER_OF_DRAWN_NUMBERS:
			n = random.randint(0, 100)
			if n not in win_numbers:
				win_numbers.append(n)

		strike_gold = False
		strike_norm = False
		won_ammount = -coin_am
		roll = random.randint(0, 100)
		if roll in win_numbers:
			won_ammount += (2 * coin_am)
			strike_norm = True
		if roll == golden_number:
			won_ammount += (5 * coin_am)
			strike_gold = True

		user.coins += won_ammount

		em = discord.Embed(title="Gamble", color=discord.Color.gold())
		em.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		em.add_field(name="Drawn numbers", value=str(win_numbers))
		em.add_field(name="Golden number", value=str([golden_number]), inline=False)
		em.add_field(name="Your number", value=str([roll]))
		if strike_gold or strike_norm:
			em.add_field(name="You won  ", value=str(won_ammount) + " :moneybag:")
		else:
			em.add_field(name="You lost  ", value=str(-won_ammount) + " :moneybag:")

		if not await user.update_user():
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant gamble - failed to connect to database"), time=5)
		return await self.bot.send_message_for_time(ctx, embed=em, time=10)

	@commands.command(no_pm=True, name='pay', help='!pay <mention of receiver> <coin ammount> to send some coins to user')
	@commands.cooldown(2, 40, commands.BucketType.user)
	async def pay(self, ctx: commands.Context, mention: str, ammount: int):
		await ctx.message.delete()

		database_user_sender = await self.bot.database_handler.get_user(ctx.author)
		if database_user_sender.coins < ammount: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("You have not enough money!"), time=5)

		try:
			mention_id = int(mention[3:-1])
		except:
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid mention"), time=5)

		disc_user_receiver = self.bot.get_user(mention_id)
		if not disc_user_receiver: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid mention"), time=5)
		database_user_receiver = await self.bot.database_handler.get_user(disc_user_receiver)

		conf_prompt = PromptSession(self.bot, ctx, f"Do you realy want to pay {ammount} :moneybag: to {database_user_receiver.username}?", color=discord.Color.dark_blue())
		res = await conf_prompt.run()
		if not res:
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Trade canceled!"))

		database_user_sender.coins -= ammount
		database_user_receiver.coins += ammount

		if not await database_user_sender.update_user():
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Failed to update sender in database - payment aborded!"), time=5)

		if not await database_user_receiver.update_user():
			database_user_sender.coins += ammount
			if not await database_user_sender.update_user():
				return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Failed to update receiver in database and return coins to sender - coins are gone!"), time=5)
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Failed to update receiver in database - coins are returned to sender!"), time=5)

		return await self.bot.send_message_for_time(ctx, embed=discord.Embed(title='Transaction', description=f'Transfered {ammount} :moneybag: from {ctx.message.author.name} to {disc_user_receiver.name}', colour=discord.Color.gold()), time=7)

	@commands.command(no_pm=True, name='inventory', help='!inventory to see your inventory')
	@commands.cooldown(3, 60, commands.BucketType.user)
	async def inventory(self, ctx: commands.Context):
		await ctx.message.delete()

		user = await self.bot.database_handler.get_user(ctx.author)

		em = discord.Embed(title=":toolbox: | Inventory", color=discord.Color.blurple())
		em.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		for idx, item in enumerate(user.items):
			if isinstance(item, Item):
				formed_string = ""
				if item.health > 0: formed_string += f"Health: {item.health}\n"
				if item.strength > 0: formed_string += f"Strength: {item.strength}\n"
				if item.agility > 0: formed_string += f"Agility: {item.agility}\n"
				if item.regeneration > 0: formed_string += f"Regeneration: {item.regeneration}\n"
				if item.sell_price: formed_string += f"\nSell Price: {item.sell_price} :moneybag:"
				if formed_string[-1] == "\n": formed_string = formed_string[:-1]
				em.add_field(name=f"({idx}){item.name} - {Item.slot_formater(item.slot)}\n-- {item.rarity} --", value=formed_string)
		if len(user.items) == 0:
			em.description = "Your inventory is empty\nCollect some items!"
		em.set_footer(text=f"{len(user.items)}/{MAXIMUM_INVENTORY_SIZE} used")

		await self.bot.send_message_for_time(ctx, embed=em, time=30)

	@commands.command(no_pm=True, name='char', help='!char to show equip and stats')
	@commands.cooldown(3, 60, commands.BucketType.user)
	async def character(self, ctx: commands.Context):
		await ctx.message.delete()

		user = await self.bot.database_handler.get_user(ctx.author)

		em = discord.Embed(title=":crown: | Character", color=discord.Color.blurple())
		em.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

		formated_stats = ""
		stats = user.get_stats()
		for stat_key in stats.keys():
			formated_stats += f"{stat_key}: {stats[stat_key]}\n"
		em.description = formated_stats

		for eq_slot in user.equip.keys():
			item = user.equip[eq_slot]
			if item:
				formed_string = f"{item.name}\n-- {item.rarity} --\n\n"
				if item.health > 0: formed_string += f"Health: {item.health}\n"
				if item.strength > 0: formed_string += f"Strength: {item.strength}\n"
				if item.agility > 0: formed_string += f"Agility: {item.agility}\n"
				if item.regeneration > 0: formed_string += f"Regeneration: {item.regeneration}"
				if formed_string[-1] == "\n": formed_string = formed_string[:-1]

				em.add_field(name=Item.slot_formater_idx(eq_slot), value=formed_string)
			else:
				em.add_field(name=Item.slot_formater_idx(eq_slot), value="Empty")

		await self.bot.send_message_for_time(ctx, embed=em, time=30)

	@commands.command(no_pm=True, name='sell', help='!sell <inventory index / all> to sell item of that index or all items to vendor')
	@commands.cooldown(2, 20, commands.BucketType.user)
	async def sell(self, ctx: commands.Context, *, inventory_index):
		await ctx.message.delete()

		sell_all = False
		if "all" in inventory_index: sell_all = True
		else:
			try:
				inventory_index = int(inventory_index)
			except:
				return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid inventory index"), time=5)

		user = await self.bot.database_handler.get_user(ctx.author)
		if not sell_all:
			if inventory_index > (len(user.items) - 1) or 0 > inventory_index: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid inventory index"), time=5)

		sold_value = 0
		if sell_all:
			for _ in range(len(user.items)):
				item = user.items.pop()
				if item.sell_price:
					user.coins += item.sell_price
					sold_value += item.sell_price

			if not await user.update_user(): return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant update user in database!"), time=5)
			return await self.bot.send_message_for_time(ctx, embed=generate_success_message(f"All items sold for {sold_value} :moneybag:"), time=5)
		else:
			item = user.items.pop(inventory_index)
			if item.sell_price:
				user.coins += item.sell_price
				sold_value = item.sell_price

			if not await user.update_user(): return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant update user in database!"), time=5)
			return await self.bot.send_message_for_time(ctx, embed=generate_success_message(f"{item.name} sold for {sold_value} :moneybag:"), time=5)

	@commands.command(no_pm=True, name='equip', help='!equip <inventory index> to equip item from inventory')
	@commands.cooldown(2, 10, commands.BucketType.user)
	async def equip(self, ctx: commands.Context, *, inventory_index:int):
		await ctx.message.delete()

		user = await self.bot.database_handler.get_user(ctx.author)
		if inventory_index > (len(user.items) - 1) or 0 > inventory_index: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid inventory index"))

		item = user.items.pop(inventory_index)

		if user.equip[item.slot]:
			user.items.append(user.equip[item.slot])
		user.equip[item.slot] = item

		if not await user.update_user(): return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant update user in database!"))
		return await self.bot.send_message_for_time(ctx, embed=generate_success_message(f"{item.name} equiped"))

	@commands.command(no_pm=True, name='unequip', help='!unequip <slot index / all> to unequip item')
	@commands.cooldown(2, 10, commands.BucketType.user)
	async def unequip(self, ctx: commands.Context, *, slot_index):
		await ctx.message.delete()

		unequip_all = False
		if "all" in slot_index: unequip_all = True

		user = await self.bot.database_handler.get_user(ctx.author)

		if unequip_all:
			for item in user.equip.values():
				if item:
					user.items.append(item)

			for slot in user.equip.keys():
				user.equip[slot] = None

			if not await user.update_user(): return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant update user in database!"))
			return await self.bot.send_message_for_time(ctx, embed=generate_success_message(f"All items unequiped"))
		else:
			try:
				inventory_index = int(slot_index)
			except:
				return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid inventory index"))

			slot_from_dict = Item.idx_to_slot(inventory_index)
			if not slot_from_dict: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid slot index"))

			item = user.equip[slot_from_dict]

			if not item: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Nothing to unequip!"))

			user.equip[slot_from_dict] = None
			user.items.append(item)
			if not await user.update_user(): return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant update user in database!"))
			return await self.bot.send_message_for_time(ctx, embed=generate_success_message(f"{item.name} unequiped"))

class RPG(BaseRPGSet):
	works = []

	def __init__(self, bot:BaseBot):
		super().__init__(bot)

		self.check_works.start()

	async def process_work(self, work):
		if work:
			work["user"].coins += work["rev"]

			# There is some chance to get some XP after finishing work
			if random.random() < (0.05 * work["hofw"]):
				work["user"].xp += 20
				work["user"].try_levelup()

			await work["user"].update_user()

			em = discord.Embed(title=":construction_worker: | Work", description="Work finished", color=discord.Color.blue())
			em.set_author(name=work["ctx"].author.name, icon_url=work["ctx"].author.avatar_url)
			em.add_field(name="Reward", value=f"{work['rev']} :moneybag:", inline=False)
			await self.bot.send_message_for_time(work["ctx"], embed=em, time=10)

	@tasks.loop(minutes=5)
	async def check_works(self):
		if self.works:
			for idx, work in enumerate(self.works):
				if datetime.datetime.now() >= work["end"]:
					await self.process_work(self.works.pop(idx))

	def __user_in_work(self, user_id:int):
		for idx, work in enumerate(self.works):
			if work["uid"] == user_id:
				return work, idx
		return None, None

	@commands.command(no_pm=True, name='work', help=f'!work <num of hours - 1-8h> to work for some :moneybag:')
	@commands.cooldown(2, 60, commands.BucketType.user)
	async def work(self, ctx: commands.Context, *, num_of_hours:int):
		await ctx.message.delete()

		work, _ = self.__user_in_work(ctx.author.id)
		if work: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("You are already in work!"))
		if not (1 <= num_of_hours <= 8): return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid work time!"))

		user = await self.bot.database_handler.get_user(ctx.author)
		revenue = num_of_hours * BASE_WORK_REVENUE_FOR_HOUR * (user.level + 1)
		work_end = datetime.datetime.now() + datetime.timedelta(hours=num_of_hours)

		self.works.append({"uid": ctx.author.id, "end": work_end, "rev": revenue, "user": user, "ctx": ctx, "hofw": num_of_hours})

		em = discord.Embed(title=":construction_worker: | Work", color=discord.Color.blue())
		em.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		em.add_field(name="Estimated reward", value=f"{revenue} :moneybag:", inline=False)
		em.add_field(name="Work end at", value=work_end.strftime('%H:%M:%S %d.%m.%Y'), inline=False)
		return await self.bot.send_message_for_time(ctx, embed=em, time=10)

	@commands.command(no_pm=True, name='workstat', help='!workstat to get status of your work, if not in work show estimated tax')
	@commands.cooldown(2, 120, commands.BucketType.user)
	async def workstat(self, ctx: commands.Context):
		await ctx.message.delete()

		work, _ = self.__user_in_work(ctx.author.id)
		if not work:
			user = await self.bot.database_handler.get_user(ctx.author)

			em = discord.Embed(title=":construction_worker: | Work", color=discord.Color.blue())
			em.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
			em.description = f"You are not in work!\nEstimated tax: {BASE_WORK_REVENUE_FOR_HOUR * (user.level + 1)} :moneybag:/h"
			return await self.bot.send_message_for_time(ctx, embed=em, time=10)

		em = discord.Embed(title=":construction_worker: | Work", color=discord.Color.blue())
		em.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
		em.add_field(name="Estimated reward", value=f"{work['rev']} :moneybag:", inline=False)
		em.add_field(name="Work end at", value=work["end"].strftime('%H:%M:%S %d.%m.%Y'), inline=False)
		return await self.bot.send_message_for_time(ctx, embed=em, time=10)

	@commands.command(no_pm=True, name='workstop', help='!workstop to stop your current work WITHOUT revenue')
	@commands.cooldown(2, 120, commands.BucketType.user)
	async def workstop(self, ctx: commands.Context):
		await ctx.message.delete()

		work, idx = self.__user_in_work(ctx.author.id)
		if not work: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("You are not in work!"))

		em = discord.Embed(title=":construction_worker: | Work", color=discord.Color.blue(), description="You are left your work")
		em.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)

		self.works.pop(idx)

		return await self.bot.send_message_for_time(ctx, embed=em)

def setup(bot):
	bot.add_cog(RPG(bot))