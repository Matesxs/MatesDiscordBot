import time
import discord
from discord.ext import commands
from PIL import Image, ImageDraw
from io import BytesIO
import requests

from ext.modules.botBase import BaseBot
from ext.modules.paginator import PaginatorSession
from ext.miscellaneous.custom_loger import setup_custom_logger
from ext.helpers.general_helpers import get_creator, generate_success_message, generate_error_message, is_bcommander, is_developer
from config import ENABLE_INVITELINK, PERMISSION_INTEGER, DEVELOPER_CHANNEL_ID

logger = setup_custom_logger(__name__)

class Common(commands.Cog):
	reminders = []

	def __init__(self, bot:BaseBot):
		self.bot = bot

	# Copied from https://github.com/Toaster192/rubbergod
	@commands.cooldown(rate=5, per=20.0, type=commands.BucketType.user)
	@commands.command(no_pm=True, name='pet', help='!pet <optional mention of user> to pet user :)')
	async def pet(self, ctx, user: discord.Member = None):
		if user is None:
			user = ctx.author
		url = user.avatar_url_as(format='jpg')
		response = requests.get(url)
		avatarFull = Image.open(BytesIO(response.content))

		frames = []
		deformWidth = [-1, -2, 1, 2, 1]
		deformHeight = [4, 3, 1, 1, -4]
		width = 80
		height = 80

		for i in range(5):
			frame = Image.new('RGBA', (112, 112), (255, 255, 255, 1))
			hand = Image.open(f"data/images/pet/{i}.png")
			width = width - deformWidth[i]
			height = height - deformHeight[i]
			avatar = avatarFull.resize((width, height))
			avatarMask = Image.new('1', avatar.size, 0)
			draw = ImageDraw.Draw(avatarMask)
			draw.ellipse((0, 0) + avatar.size, fill=255)
			avatar.putalpha(avatarMask)

			frame.paste(avatar, (112 - width, 112 - height), avatar)
			frame.paste(hand, (0, 0), hand)
			frames.append(frame)

		with BytesIO() as image_binary:
			frames[0].save(image_binary, format='GIF', save_all=True,
			               append_images=frames[1:], duration=40,
			               loop=0, transparency=0, disposal=2, optimize=False)
			image_binary.seek(0)
			await ctx.send(file=discord.File(fp=image_binary, filename="pet.gif"))

	@commands.command(no_pm=True, name='help', help='!help for show all commands or info about them')
	@commands.cooldown(3, 20, commands.BucketType.user)
	async def help(self, ctx):
		comm_list = self.bot.commands
		pages = []

		bcommander = is_bcommander(ctx)
		developer = is_developer(ctx)

		for c_name in self.bot.custom_extensions:
			if str(c_name) == "Bcommander" and not bcommander: continue
			if str(c_name) == "Developer" and not developer: continue

			no_empty = False
			emb = discord.Embed(title=f'{c_name} Help', colour=discord.Color.green())
			for com in comm_list:
				if com.cog_name == c_name and not com.hidden:
					if com.help is None:
						emb.add_field(name=com.name, value='No help here!', inline=False)
					else:
						emb.add_field(name=com.name, value=com.help, inline=False)
					no_empty = True
			if no_empty:
				pages.append(emb)

		if pages:
			p_session = PaginatorSession(bot=self.bot, ctx=ctx, timeout=60, footer='Powered by custom Paginator!', pages=pages)
			await p_session.run()

	@commands.command(no_pm=False, name="ping", help="!ping for ping the bot")
	async def ping(self, ctx):
		await ctx.message.delete()

		em = discord.Embed(color=discord.Color.green())
		em.title = "Pong!"
		em.description = f'{round(self.bot.latency * 1000, 2)} ms'
		await self.bot.send_message_for_time(ctx, embed=em, time=10)

	@commands.command(name='bot', help="!bot for informations about this bot")
	async def _bot(self, ctx):
		creator = get_creator(self.bot)

		em = discord.Embed(color=discord.Color.green())
		em.title = 'Bot Info'
		em.set_author(name=creator.name, icon_url=creator.avatar_url)
		em.description = 'Universal bot made by MatesXs using Discord.py'
		em.add_field(name="Servers", value=str(len(self.bot.guilds)))
		em.add_field(name="Online Users", value=str(len({m.id for m in self.bot.get_all_members() if m.status is not discord.Status.offline})))
		em.add_field(name='Total Users', value=str(len(self.bot.users)))
		em.add_field(name='Channels', value=f"{sum(1 for g in self.bot.guilds for _ in g.channels)}")
		em.add_field(name="Library", value=f"[discord.py](https://pypi.org/project/discord.py/)")
		em.add_field(name="Bot Latency", value=f"{round(self.bot.latency * 1000, 2)} ms")
		if ENABLE_INVITELINK:
			em.add_field(name="Invite", value=f"[Click Here](https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions=8)")
		else:
			em.add_field(name="Invite", value=f"WIP")

		em.set_footer(text="MatesBot | Powered by discord.py")

		await ctx.message.delete()
		await self.bot.send_message_for_time(ctx, embed=em, time=30)

	@commands.command(no_pm=False, name='invite', help='!invite sends invite link for this bot, try it on your server :)')
	@commands.cooldown(1, 600, commands.BucketType.user)
	async def invite(self, ctx):
		emb = discord.Embed(title='Invite Link', colour=discord.Color.dark_blue())
		if ENABLE_INVITELINK:
			emb.description = f'[Click Here](https://discordapp.com/oauth2/authorize?client_id={self.bot.user.id}&scope=bot&permissions={PERMISSION_INTEGER})'
		else:
			emb.description = "WIP"
		emb.set_thumbnail(url=self.bot.user.avatar_url)
		await ctx.send(embed=emb)

	@commands.command(no_pm=False, name='report_bug', aliases=["bug"], help='!report_bug <description of bug> will send message to author with your problem')
	@commands.cooldown(2, 300, commands.BucketType.user)
	async def report_bug(self, ctx, *, message: str):
		message_to_save = f'{time.time()}: {ctx.message.author.name}/{ctx.message.guild.name} - {message}\n'
		await ctx.message.delete()

		if DEVELOPER_CHANNEL_ID:
			channel_out:discord.TextChannel = self.bot.get_channel(DEVELOPER_CHANNEL_ID)
			emb = discord.Embed(title="Bug report", color=discord.Color.dark_orange())
			emb.set_footer(text=ctx.message.author.name, icon_url=ctx.message.author.avatar_url)
			emb.add_field(name="Guild", value=ctx.message.guild.name, inline=False)
			emb.add_field(name="Description", value=message, inline=False)
			await channel_out.send(embed=emb)

		try:
			with open('data/BugReport.rep', 'a') as f:
				f.write(message_to_save)
		except Exception:
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant send your bugreport to creator!"))

		logger.warning('New Bugreport!')
		await self.bot.send_message_for_time(ctx, embed=generate_success_message('Your report was send to creator!'), time=10)

def setup(bot):
	bot.add_cog(Common(bot))