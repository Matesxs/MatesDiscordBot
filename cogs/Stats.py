import asyncio
import time
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import style
from pandas.plotting import register_matplotlib_converters
import os
from collections import deque
import discord
from discord.ext import commands, tasks
from pymongo import ASCENDING

from ext.modules.botBase import BaseBot
from ext.miscellaneous.custom_loger import setup_custom_logger
from config import STATS_AGREG_TIME_MINUTES, STATS_HISTORY_LOADING_DAYS, GRAPHS_CACHE

logger = setup_custom_logger(__name__)

style.use('fivethirtyeight')
register_matplotlib_converters()

class Stats(commands.Cog):
	users_count = deque(maxlen=((STATS_HISTORY_LOADING_DAYS * 24 * 60) // STATS_AGREG_TIME_MINUTES))

	def __init__(self, bot:BaseBot):
		self.bot = bot

		if not os.path.exists(GRAPHS_CACHE): os.makedirs(GRAPHS_CACHE)
		self.delete_graphs_cache()

	def get_uptime(self):
		total_seconds = float(time.time() - self.bot.boot_time)

		# Helper vars:
		MINUTE = 60
		HOUR = MINUTE * 60
		DAY = HOUR * 24
		MONTH = DAY * 30

		# Get the days, hours, etc:
		months = int(total_seconds / MONTH)
		days = int((total_seconds / MONTH) / DAY)
		hours = int((total_seconds % DAY) / HOUR)
		minutes = int((total_seconds % HOUR) / MINUTE)
		seconds = int(total_seconds % MINUTE)

		# Build up the pretty string (like this: "N days, N hours, N minutes, N seconds")
		string = ""
		if months > 0:
			string += str(months) + " " + (months == 1 and "month" or "months") + ", "
		if days > 0:
			string += str(days) + " " + (days == 1 and "day" or "days") + ", "
		if len(string) > 0 or hours > 0:
			string += str(hours) + " " + (hours == 1 and "hour" or "hours") + ", "
		if len(string) > 0 or minutes > 0:
			string += str(minutes) + " " + (minutes == 1 and "minute" or "minutes") + ", "
		string += str(seconds) + " " + (seconds == 1 and "second" or "seconds")

		return string

	@staticmethod
	def delete_graphs_cache():
		if os.path.exists(GRAPHS_CACHE):
			for file in os.listdir(GRAPHS_CACHE):
				os.remove(os.path.join(GRAPHS_CACHE, file))

	async def load_user_stats(self):
		try:
			min_time = datetime.datetime.now() - datetime.timedelta(days=STATS_HISTORY_LOADING_DAYS)
			ret_val = self.bot.database_handler.users_statistics.find({'timestamp': {'$gte': min_time.timestamp()}}).sort("timestamp", ASCENDING)
			docs = await ret_val.to_list(None)
			for doc in docs:
				self.users_count.append([doc["timestamp"], str(doc["all_users"]), str(doc["online"]), str(doc["idle"]), str(doc["dnd"]), str(doc["offline"])])

			await self.bot.database_handler.users_statistics.delete_many({'timestamp': {'$lt': min_time.timestamp()}})
		except:
			logger.exception("Failed to init statistics from database")

		try:
			self.stats_writer_task.start()
		except:
			logger.warning("Stats writer task already running")

	@commands.Cog.listener()
	async def on_ready(self):
		await self.load_user_stats()

	def user_counts_writer(self):
		all_users = [u for u in self.bot.get_all_members()]
		all_users_num = len(all_users)
		online_users = len([u for u in all_users if u.status is discord.Status.online])
		dnd_users = len([u for u in all_users if u.status is discord.Status.dnd])
		idle_users = len([u for u in all_users if u.status is discord.Status.idle])

		timestamp = datetime.datetime.now().timestamp()

		database_format = {
			"timestamp": timestamp,
			"all_users": all_users_num,
			"online": online_users,
			"idle": idle_users,
			"dnd": dnd_users,
			"offline": all_users_num - online_users - dnd_users - idle_users
		}

		try:
			self.bot.database_handler.users_statistics.insert_one(database_format)
			self.users_count.append([timestamp, str(all_users_num), str(online_users), str(idle_users), str(dnd_users), str(all_users_num - online_users - dnd_users - idle_users)])
		except:
			pass

	@tasks.loop(minutes=STATS_AGREG_TIME_MINUTES)
	async def stats_writer_task(self):
		while not self.bot.is_ready():
			await asyncio.sleep(1)

		if not self.bot.sync_tasks_executor: return

		try:
			future_ucw = self.bot.sync_tasks_executor.submit(self.user_counts_writer)
			future_ucw = asyncio.wrap_future(future_ucw)

			await asyncio.wait_for(future_ucw, timeout=None, loop=asyncio.get_event_loop())
		except Exception as e:
			logger.exception(f"Stats writer task exception\n{e}")

	@staticmethod
	async def post_fig_as_image(ctx, fig, time_delay:int=30):
		save_path = f'{GRAPHS_CACHE}/{len(os.listdir(GRAPHS_CACHE))}.png'
		plt.savefig(save_path)

		await ctx.send(file=discord.File(save_path), delete_after=time_delay)
		os.remove(save_path)
		plt.close(fig)

	@commands.command(no_pm=True, name="users", help="!users to show graph of users count on servers with this bot")
	@commands.cooldown(2, 60, commands.BucketType.user)
	async def show_users_history(self, ctx:commands.Context):
		await ctx.message.delete()

		df = pd.DataFrame(self.users_count, columns=["timestamp", "all_users", "online", "idle", "dnd", "offline"])
		df.sort_values(by="timestamp", ascending=True, inplace=True)

		fig, ax = plt.subplots(1)
		ax.plot(df["timestamp"], df["all_users"].astype(int), label='All', linewidth=1.3)
		ax.plot(df["timestamp"], df["online"].astype(int), label='Online', linewidth=1.3)
		ax.plot(df["timestamp"], df["idle"].astype(int), label='Idle', linewidth=1.3)
		ax.plot(df["timestamp"], df["dnd"].astype(int), label='DnD', linewidth=1.3)
		ax.plot(df["timestamp"], df["offline"].astype(int), label='Offline', linewidth=1.3)
		ax.set_xticklabels([])

		ax.legend(framealpha=0.7, fancybox=True, loc=2)
		plt.ylabel('Users', labelpad=1)
		plt.xlabel('Time')

		await self.post_fig_as_image(ctx, fig, 30)

	@commands.command(no_pm=True, name="uptime", help="!uptime to show server uptime")
	async def uptime(self, ctx):
		await ctx.message.delete()
		await self.bot.send_message_for_time(ctx, embed=discord.Embed(title=":clock1: | Uptime", color=discord.Color.blurple(), description=self.get_uptime()), time=10)

def setup(bot):
	bot.add_cog(Stats(bot))