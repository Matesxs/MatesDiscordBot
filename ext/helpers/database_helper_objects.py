from ext.miscellaneous.custom_loger import setup_custom_logger

logger = setup_custom_logger(__name__)

class GuildSettings:
	def __init__(self, database, cache_delete_callback):
		self.database = database
		self.cache_delete_callback = cache_delete_callback

		self.id = None
		self.name = None

		self.welcome_message = None
		self.default_role = None
		self.muted_role = None
		self.log_channel = None
		self.volume = 50
		self.rpg_notifications = False

	def __int__(self):
		return self.id

	def __str__(self):
		return self.name

	def to_database_format(self):
		return {
			"_id": self.id,
			"name": self.name,
			"welcome_message": self.welcome_message,
			"default_role": self.default_role,
			"muted_role": self.muted_role,
			"log_channel": self.log_channel,
			"volume": self.volume,
			"rpg_notifications": self.rpg_notifications
		}

	def database_to_settings(self, data):
		self.id = data["_id"]
		self.name = data["name"]

		try:
			self.welcome_message = data["welcome_message"]
			self.default_role = data["default_role"]
			self.muted_role = data["muted_role"]
			self.log_channel = data["log_channel"]
			self.volume = data["volume"]
			self.rpg_notifications = data["rpg_notifications"]
		except:
			self.welcome_message = None
			self.default_role = None
			self.muted_role = None
			self.log_channel = None
			self.volume = 50
			self.rpg_notifications = False

	async def create_new_guild_settings_in_database(self, identifier, name):
		self.id = identifier
		self.name = name

		post = await self.database.insert_one(self.to_database_format())
		if post.inserted_id: return True
		return False

	async def update_guild_settings(self) -> bool:
		if self.name and self.id:
			dat_guild_settings = self.to_database_format()
			result = await self.database.update_one({"_id": dat_guild_settings["_id"]}, {"$set": dat_guild_settings})
			result = result.matched_count
			if result == 1: return True
		return False

	async def delete_guild_settings(self):
		self.cache_delete_callback(self.id)
		del_count = await self.database.delete_one({"_id": self.id})
		del_count = del_count.deleted_count
		if del_count == 1: return True
		return False

class User:
	def __init__(self, database_connection, cache_delete_callback):
		self.database = database_connection
		self.cache_delete_callback = cache_delete_callback

		self.id = None
		self.username = None

		self.level = 0
		self.xp = 0
		self.coins = 0

	def __eq__(self, other):
		if self.id == other.id and self.username == other.username and self.level == other.level and self.xp == other.xp and self.coins == other.coins and self.database is not None and other.database is not None:
			return True
		return False

	def __int__(self) -> int:
		return self.id

	def __str__(self) -> str:
		return self.username

	def to_database_format(self):
		"""
		Helper function to format user for database
		return: dict - all user data (_id, username, level, xp, coins, equip, items)
		"""

		return {
			"_id": self.id,
			"username": self.username,
			"level": self.level,
			"xp": self.xp,
			"coins": self.coins
		}

	def database_to_user(self, data):
		"""
		Helper function to populating user with data from database
		args: data - dict with data from database
		"""

		self.id = data["_id"]
		self.username = data["username"]

		try:
			self.level = data["level"]
			self.xp = data["xp"]
			self.coins = data["coins"]
		except:
			self.level = 0
			self.xp = 0
			self.coins = 0

	async def create_new_user_in_database(self, identifier, username) -> bool:
		"""
		Helper function for creating user in database
		args: identifier - int with user id
					username - username of user
		return: bool - success
		"""

		self.id = identifier
		self.username = username

		post = await self.database.insert_one(self.to_database_format())
		if post.inserted_id: return True
		return False

	async def update_user(self) -> bool:
		"""
		Update user in database
		return: bool - success
		"""

		if self.username and self.id:
			dat_user = self.to_database_format()
			result = await self.database.update_one({"_id": dat_user["_id"]}, {"$set": dat_user})
			result = result.matched_count
			if result == 1: return True
		return False

	async def delete_user(self) -> bool:
		"""
		Deletes user from database and cache
		return: bool - deleted
		"""

		self.cache_delete_callback(self.id)
		del_count = await self.database.delete_one({"_id": self.id})
		del_count = del_count.deleted_count
		if del_count == 1: return True
		return False

	# XP System
	def xp_for_next_level(self):
		"""Return xp needed for next level"""

		return int(10 * (2 ** self.level))

	def xp_to_next_level(self):
		"""Return xp missing to levelup"""

		xp_for_levelup = self.xp_for_next_level()
		return int(xp_for_levelup - self.xp)

	def try_levelup(self):
		"""
		This method serves for trying to level up user after getting some xp, without it user never get level
		return: bool - leveled up
		"""

		leveled_up = False

		xp_for_levelup = self.xp_for_next_level()
		while self.xp >= xp_for_levelup:
			leveled_up = True
			self.level += 1
			self.xp -= xp_for_levelup
			xp_for_levelup = self.xp_for_next_level()

		return leveled_up