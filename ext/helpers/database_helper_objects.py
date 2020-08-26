import json
from typing import Union

from ext.miscellaneous.custom_loger import setup_custom_logger
from config import MAXIMUM_INVENTORY_SIZE, RPG_ITEMS_PATH

logger = setup_custom_logger(__name__)

__f = open(RPG_ITEMS_PATH)
cached_items = json.load(__f)
__f.close()

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
			"log_channel": self.log_channel
		}

	def database_to_settings(self, data):
		self.id = data["_id"]
		self.name = data["name"]

		try:
			self.welcome_message = data["welcome_message"]
			self.default_role = data["default_role"]
			self.muted_role = data["muted_role"]
			self.log_channel = data["log_channel"]
		except:
			self.welcome_message = None
			self.default_role = None
			self.muted_role = None
			self.log_channel = None

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

class Item:
	__slots_dict = {
		"head": ["Helm", "(0)Helm"],
		"body": ["Armor", "(1)Armor"],
		"shoulders": ["Shoulders", "(2)Shoulders"],
		"gloves": ["Gloves", "(3)Gloves"],
		"legs": ["Legs", "(4)Legs"],
		"boots": ["Boots", "(5)Boots"],
		"ring": ["Ring", "(6)Ring"],
		"pet": ["Pet", "(7)Pet"]
	}

	stats_list = ["health", "strength", "agility", "regeneration"]

	def __init__(self, identifier:int=None, name:str=None, slot:str=None, rarity:str=None, health:int=0, strength:int=0, agility:int=0, regeneration:int=0, buy_price:int=None, sell_price:int=None):
		self.id = identifier
		self.name = name
		self.slot = slot
		self.rarity = rarity

		self.health = health
		self.strength = strength
		self.agility = agility
		self.regeneration = regeneration

		self.buy_price = buy_price
		self.sell_price = sell_price

	def __int__(self):
		return self.id

	def __str__(self):
		return self.name

	@staticmethod
	def slot_formater(slot:str) -> Union[str, None]:
		if slot not in Item.__slots_dict: return None
		return Item.__slots_dict[slot][0]

	@staticmethod
	def slot_formater_idx(slot: str) -> Union[str, None]:
		if slot not in Item.__slots_dict: return None
		return Item.__slots_dict[slot][1]

	@staticmethod
	def idx_to_slot(idx:int) -> Union[str, None]:
		if idx < 0 or idx > (len(Item.__slots_dict.values()) - 1): return None
		for index, slot in enumerate(Item.__slots_dict.keys()):
			if index == idx: return slot
		return None

	@staticmethod
	def valid_slots() -> list:
		return list(Item.__slots_dict.keys())

	@classmethod
	def json_to_item(cls, data:dict, identifier:int):
		try:
			buy_price = data["buy_price"]
		except:
			buy_price = None

		try:
			sell_price = data["sell_price"]
		except:
			sell_price = None

		try:
			rarity = data["rarity"]
		except:
			rarity = "Base"

		return cls(identifier, data["name"], data["slot"], rarity, data["health"], data["strength"], data["agility"], data["regeneration"], buy_price, sell_price)

	@staticmethod
	def item_id_to_item(identifier: int):
		if identifier is None: return None
		if str(identifier) not in cached_items.keys(): return None

		item_raw_data = cached_items[str(identifier)]
		return Item.json_to_item(item_raw_data, identifier)

class User:
	@staticmethod
	def blank_equip() -> dict:
		"""
		Helper method to generate blank equip dict
		return: dict - blank equip
		"""

		return {
		"head": None,
		"body": None,
		"shoulders": None,
		"gloves": None,
		"legs": None,
		"boots": None,
		"ring": None,
		"pet": None
	}

	def __init__(self, database_connection, cache_delete_callback):
		self.database = database_connection
		self.cache_delete_callback = cache_delete_callback

		self.id = None
		self.username = None

		self.level = 0
		self.xp = 0
		self.coins = 0
		self.items = []

		self.equip = self.blank_equip()

	def __eq__(self, other):
		if self.id == other.id and self.username == other.username and self.level == other.level and self.xp == other.xp and self.coins == other.coins and self.equip == other.equip and self.items == other.items and self.database is not None and other.database is not None:
			return True
		return False

	def __int__(self) -> int:
		return self.id

	def __str__(self) -> str:
		return self.username

	def get_stats(self) -> dict:
		"""
		Method to calculating user stats based on equip
		return: dict - named stats
		"""

		stats = {}
		for stat in Item.stats_list:
			if stat not in stats.keys(): stats[stat] = 0
			for item in self.equip.values():
				if item:
					val = getattr(item, stat)
					if val and isinstance(val, int) and val != 0: stats[stat] += val
		return stats

	def equip_to_ids(self) -> dict:
		"""
		Helper function to convert equip to ids dict
		return: dict - equip ids
		"""

		return_dict = {}
		for key in self.equip.keys():
			if self.equip[key] and key in Item.valid_slots():
				return_dict[key] = self.equip[key].id
			else:
				return_dict[key] = None
		return return_dict

	def ids_to_equip(self, equip_data) -> dict:
		"""
		Helper function for converting ids from database to equip dict
		args: dict - equip data
		return: dict - equip
		"""

		return_dict = {}
		for key in self.equip.keys():
			if key in Item.valid_slots():
				try:
					return_dict[key] = Item.item_id_to_item(equip_data[key])
				except:
					return_dict[key] = None
			else:
				return_dict[key] = None
		return return_dict

	def to_database_format(self):
		"""
		Helper function to format user for database
		return: dict - all user data (_id, username, level, xp, coins, equip, items)
		"""

		if len(self.items) >= MAXIMUM_INVENTORY_SIZE:
			logger.warning(f"User {self.username} have larger inventory than limit - trimming down!")
			self.items = self.items[:MAXIMUM_INVENTORY_SIZE]

		return {
			"_id": self.id,
			"username": self.username,
			"level": self.level,
			"xp": self.xp,
			"coins": self.coins,
			"equip": self.equip_to_ids(),
			"items": [x.id for x in self.items if x is not None]
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
			self.equip = self.ids_to_equip(data["equip"])
			self.items = [Item.item_id_to_item(x) for x in data["items"] if x is not None]
		except:
			self.level = 0
			self.xp = 0
			self.coins = 0
			self.equip = self.blank_equip()
			self.items = []

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