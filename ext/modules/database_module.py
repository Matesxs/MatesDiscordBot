import motor.motor_asyncio
from typing import Union
import discord

from ext.miscellaneous.custom_loger import setup_custom_logger
from config import MONGO_DATABASE_USERNAME, MONGO_DATABASE_PASSWORD, MAX_CACHED_USERS, MAX_CACHED_GUILD_SETTINGS
from ext.helpers.database_helper_objects import GuildSettings, User

logger = setup_custom_logger(__name__)

class DatabaseHelper:
	try:
		client = motor.motor_asyncio.AsyncIOMotorClient(f"mongodb+srv://{MONGO_DATABASE_USERNAME}:{MONGO_DATABASE_PASSWORD}@mainbot-zlibo.mongodb.net/test?retryWrites=true")
	except Exception as e:
		logger.exception(f"Cant connect to database:\n{e}")

	cached_users = []
	cached_guild_settings = []

	def __init__(self):
		self.users = self.client.Databases.Users
		self.guilds_settings = self.client.Databases.GuildSettings
		self.users_statistics = self.client.Statistics.ConnectedUsers

	def find_cached_user(self, identifier:int) -> Union[User, None]:
		for cuser in self.cached_users:
			if cuser.id == identifier:
				return cuser
		return None

	def find_cached_guild_settings(self, identifier:int) -> Union[GuildSettings, None]:
		for cgsettings in self.cached_guild_settings:
			if cgsettings.id == identifier:
				return cgsettings
		return None

	def delete_cached_user(self, identifier:int):
		for idx, cuser in enumerate(self.cached_users):
			if cuser.id == identifier:
				del self.cached_users[idx]

	def delete_cached_guild_settings(self, identifier:int):
		for idx, cgsettings in enumerate(self.cached_guild_settings):
			if cgsettings.id == identifier:
				del self.cached_guild_settings[idx]

	async def get_user(self, user:Union[discord.Member, discord.User]) -> User:
		cached_user = self.find_cached_user(user.id)
		if cached_user:
			logger.debug(f"Found user {cached_user.username} in cache")
			return cached_user

		logger.debug(f"Loading user {user.name} from database")
		ruser = User(self.users, self.delete_cached_user)
		if not await self.users.find_one({"_id": user.id}):
			created_user = await ruser.create_new_user_in_database(user.id, user.name)
			if not created_user: raise Exception("Failed to create new user in database!")

		ruser.database_to_user(await self.users.find_one({"_id": user.id}))

		logger.debug(f"Adding user {user.name} to cache")
		self.cached_users.append(ruser)
		if len(self.cached_users) > MAX_CACHED_USERS: self.cached_users = self.cached_users[-MAX_CACHED_USERS:]

		return ruser

	async def get_guild_settings(self, guild:discord.Guild) -> GuildSettings:
		cached_guild_settings = self.find_cached_guild_settings(guild.id)
		if cached_guild_settings:
			logger.debug(f"Found guild settings for {cached_guild_settings.name} in cache")
			return cached_guild_settings

		logger.debug(f"Loading guild settings for {guild.name} from database")
		rguildsettings = GuildSettings(self.guilds_settings, self.delete_cached_guild_settings)
		if not await self.guilds_settings.find_one({"_id": guild.id}):
			created_guild_settings = await rguildsettings.create_new_guild_settings_in_database(guild.id, guild.name)
			if not created_guild_settings: raise Exception("Failed to create new user in database!")

		rguildsettings.database_to_settings(await self.guilds_settings.find_one({"_id": guild.id}))

		logger.debug(f"Adding guild settings for {guild.name} to cache")
		self.cached_guild_settings.append(rguildsettings)
		if len(self.cached_guild_settings) > MAX_CACHED_GUILD_SETTINGS: self.cached_guild_settings = self.cached_guild_settings[-MAX_CACHED_GUILD_SETTINGS:]

		return rguildsettings