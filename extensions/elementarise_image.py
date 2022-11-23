from disnake.ext import commands
import elementarise

from features.base_cog import Base_Cog

class ElementariseImage(Base_Cog):
  def __init__(self, bot):
    super(ElementariseImage, self).__init__(bot, __file__)

def setup(bot):
  bot.add_cog(ElementariseImage(bot))
