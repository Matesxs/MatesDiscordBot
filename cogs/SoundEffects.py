from discord.ext import commands

from ext.modules.botBase import BaseBot
from ext.miscellaneous.custom_loger import setup_custom_logger
from ext.modules.sound_cog_precursor import GenericSoundCog

logger = setup_custom_logger(__name__)

class SoundEffects(GenericSoundCog):
	def __init__(self, bot:BaseBot):
		super().__init__(bot)

	@commands.command(no_pm=True, name="horn", help="!horn for horn soundeffect")
	@commands.cooldown(1, 60, commands.BucketType.user)
	async def horn(self, ctx:commands.Context):
		await ctx.message.delete()
		await self.play_source(ctx, "data/soundeffects/horn.mp3")

	@commands.command(no_pm=True, name="haha", help="!haha for laugh soundeffect")
	@commands.cooldown(1, 60, commands.BucketType.user)
	async def haha(self, ctx: commands.Context):
		await ctx.message.delete()
		await self.play_source(ctx, "data/soundeffects/haha.mp3")

	@commands.command(no_pm=True, name="cha-ching", help="!cha-ching for cha-ching soundeffect")
	@commands.cooldown(1, 60, commands.BucketType.user)
	async def cha_ching(self, ctx: commands.Context):
		await ctx.message.delete()
		await self.play_source(ctx, "data/soundeffects/cha-ching.mp3")

def setup(bot):
	bot.add_cog(SoundEffects(bot))