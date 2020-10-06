import random
import datetime
import discord
from discord.ext import commands, tasks

from ext.modules.botBase import BaseBot
from ext.miscellaneous.custom_loger import setup_custom_logger
from ext.helpers.general_helpers import generate_error_message
from config import GAMBLE_NUMBER_OF_DRAWN_NUMBERS, BASE_WORK_REVENUE_FOR_HOUR
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

	@commands.command(no_pm=True, name='stopwork', help='!stopwork to stop your current work WITHOUT revenue')
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