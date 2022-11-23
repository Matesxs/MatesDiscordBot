import disnake

from config import config

def is_administrator(ctx):
  if ctx.bot.owner_id == ctx.author.id:
    return True

  if not isinstance(ctx.author, disnake.Member):
    return False

  if ctx.author.id == ctx.guild.owner_id:
    return True

  if disnake.utils.get(ctx.author.roles, id=config.roles.admin_role_id) is not None:
    return True

  return False