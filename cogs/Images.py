import requests
import discord
from discord.ext import commands

from ext.modules.botBase import BaseBot
from ext.miscellaneous.custom_loger import setup_custom_logger

logger = setup_custom_logger(__name__)

class Images(commands.Cog):
	def __init__(self, bot:BaseBot):
		self.bot = bot

	@commands.command(no_pm=True, name='cat', help='!cat to generate random image of cat')
	@commands.cooldown(1, 30, commands.BucketType.user)
	async def cat(self, ctx):
		await ctx.message.delete()

		result = requests.get('https://aws.random.cat/meow').json()
		image = result['file']

		while '.mp4' in image:
			result = requests.get('https://aws.random.cat/meow').json()
			image = result['file']

		await ctx.send(embed=discord.Embed(title='Cat :cat:', colour=discord.Color.blue()).set_image(url=image).set_footer(text=image))

	@commands.command(no_pm=True, name='doggo', help='!doggo to generate random image of doggo')
	@commands.cooldown(1, 30, commands.BucketType.user)
	async def doggo(self, ctx):
		await ctx.message.delete()

		result = requests.get('https://random.dog/woof.json').json()
		image = result['url']

		while '.mp4' in image:
			result = requests.get('https://random.dog/woof.json').json()
			image = result['url']

		await ctx.send(embed=discord.Embed(title='Doggo :dog:', colour=discord.Color.blue()).set_image(url=image).set_footer(text=image))

def setup(bot):
	bot.add_cog(Images(bot))