import disnake
from disnake.ext import commands

from features import base_cog
from config import Strings, cooldowns
from utils import message_utils, permission_utils

class AdminTools(base_cog.Base_Cog):
  def __init__(self, bot):
    super(AdminTools, self).__init__(bot, __file__)

  @commands.slash_command(description=Strings.admin_tools_clear_description)
  @commands.check(permission_utils.is_administrator)
  @cooldowns.default_cooldown
  @commands.guild_only()
  async def clear(self, inter: disnake.CommandInteraction, amount: int=commands.Param(default=100, description="Limit of messages to delete")):
    await inter.response.defer(with_message=True, ephemeral=True)
    deleted = await inter.channel.purge(limit=amount)
    await message_utils.generate_success_message(inter, Strings.admin_tools_clear_deleted(message_number=len(deleted)))

def setup(bot):
  bot.add_cog(AdminTools(bot))
