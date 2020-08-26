import praw
import random
from typing import Union
import asyncio
from operator import itemgetter
import discord
from discord.ext import commands

from ext.modules.botBase import BaseBot
from ext.miscellaneous.custom_loger import setup_custom_logger
from config import REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USERNAME, REDDIT_PASSWORD, REDDIT_USER_AGENT
from ext.helpers.general_helpers import generate_error_message

logger = setup_custom_logger(__name__)

class Reddit(commands.Cog):
	def __init__(self, bot:BaseBot):
		self.bot = bot

		self.reddit = praw.Reddit(client_id=REDDIT_CLIENT_ID,
		                          client_secret=REDDIT_CLIENT_SECRET,
		                          username=REDDIT_USERNAME,
		                          password=REDDIT_PASSWORD,
		                          user_agent=REDDIT_USER_AGENT)

	def request_to_reddit(self, subreddit:str, limit:int=25) -> Union[None, list]:
		try:
			submissions = self.reddit.subreddit(subreddit).top("month", limit=limit)

			retval = []
			for subm in submissions:
				try:
					retval.append([subm.title, subm.score, subm.url, subm.subreddit, subm.selftext])
				except:
					pass
			return retval
		except:
			return None

	async def make_request_to_reddit(self, subreddit:str, limit:int=25) -> Union[None, list]:
		if not self.bot.sync_tasks_executor: return None

		future = self.bot.sync_tasks_executor.submit(self.request_to_reddit, subreddit=subreddit, limit=limit)
		future = asyncio.wrap_future(future)
		results = await asyncio.wait_for(future, timeout=None, loop=asyncio.get_event_loop())

		if results: results.sort(key=itemgetter(1), reverse=True)

		return results

	@commands.command(no_pm=True, name="totm", help="!totm <subreddit name (case sensitive)> for month top post of given subreddit")
	@commands.cooldown(1, 30, commands.BucketType.user)
	async def totm(self, ctx:commands.Context, *, subreddit:str):
		await ctx.message.delete()

		data = await self.make_request_to_reddit(subreddit, 25)
		if not data: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant find anything about this subreddit!"))

		idx = 0
		data_sel = data[0]
		while "jpg" not in data_sel[2] and "png" not in data_sel[2]:
			idx += 1
			if idx >= len(data): return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant find anything about this subreddit!"))
			data_sel = data[idx]

		em = discord.Embed(title=f"{data_sel[0]}", color=discord.Color.blue())
		em.set_footer(text=f"{data_sel[1]} Score")
		em.set_image(url=data_sel[2])
		em.set_author(name=data_sel[3])
		if data_sel[4]: em.description = data_sel[4]

		await ctx.send(embed=em)

	@commands.command(no_pm=True, name="rtotm", help="!rtotm <subreddit name (case sensitive)> for random post from month top 25 of given subreddit")
	@commands.cooldown(2, 30, commands.BucketType.user)
	async def rtotm(self, ctx: commands.Context, *, subreddit: str):
		await ctx.message.delete()

		data = await self.make_request_to_reddit(subreddit, 25)
		if not data: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant find anything about this subreddit!"))

		tries = 0
		data_sel = random.choice(data)
		while "jpg" not in data_sel[2] and "png" not in data_sel[2]:
			data_sel = random.choice(data)
			tries += 1
			if tries > 100:
				return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant find anything about this subreddit!"))

		em = discord.Embed(title=f"{data_sel[0]}", color=discord.Color.blue())
		em.set_footer(text=f"{data_sel[1]} Score")
		em.set_image(url=data_sel[2])
		em.set_author(name=data_sel[3])
		if data_sel[4]: em.description = data_sel[4]

		await ctx.send(embed=em)

def setup(bot):
	bot.add_cog(Reddit(bot))