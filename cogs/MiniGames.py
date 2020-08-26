import random
import discord
from discord.ext import commands

from ext.modules.botBase import BaseBot
from ext.miscellaneous.custom_loger import setup_custom_logger
from ext.helpers.general_helpers import generate_error_message
from config import THE8_RESPONSES

logger = setup_custom_logger(__name__)

class MiniGames(commands.Cog):
	def __init__(self, bot:BaseBot):
		self.bot = bot

	@commands.command(no_pm=False, name='dice', help='!dice to throw a dice')
	async def dice(self, ctx:commands.Context):
		await ctx.message.delete()
		emb = discord.Embed(title=":game_die: | Dice", description=f'Dice stopped at {random.randint(0, 6) + 1}', colour=discord.Color.blue())
		await ctx.send(embed=emb)

	@commands.command(no_pm=False, name='roll', help='!roll generate random number from 1 to 100')
	async def roll(self, ctx):
		await ctx.message.delete()
		emb = discord.Embed(title=f'{ctx.message.author.name} rolled {random.randint(0, 100) + 1}', colour=discord.Color.blue())
		await ctx.send(embed=emb)

	@commands.command(no_pm=True, name='8ball', help='!8ball <question> to ask 8ball')
	async def eight_ball(self, ctx, *, message: str):
		await ctx.message.delete()
		if "?" not in message: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("This dont look like question, try it again!"))
		await self.bot.send_message_for_time(ctx, embed=discord.Embed(title=':8ball: | 8Ball', description=f'Your question: {message}\nAnd the answer is: {random.choice(THE8_RESPONSES)}', colour=discord.Color.blue()), time=15)

def setup(bot):
	bot.add_cog(MiniGames(bot))