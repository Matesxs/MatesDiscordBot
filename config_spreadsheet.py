# Discord connection setting
TOKEN = "" ### Token to discord app ###
STATUS_MESSAGE = "" ### Status message of your bot ###

# Creator and testers IDs for permissions
CREATOR = int()  # Discord user id for creator permissions
TESTERS = [] # Ids of other users to tester permissins

# Developer settings
DEVELOPER_SERVER_ID = int()
DEVELOPER_CHANNEL_ID = int()

# Bot minor changes
# Logging settings
LOGLEVEL = "INFO"
LOG_FILE = "logFile.log"

ENABLE_INVITELINK = True

WORKERS_OF_SYNC_TASKS_EXECUTOR = 2
##end

## Database settings
# Database credentials
MONGO_DATABASE_USERNAME = "" ### Credential to mongodb database for saving users and server settings ###
MONGO_DATABASE_PASSWORD = ""

# Database cache settings
MAX_CACHED_USERS = 500
MAX_CACHED_GUILD_SETTINGS = 500
##end

## Project structure paths
MODULES_PATH = "cogs"
SONG_CACHE_DIRECTORY = "cache/songs_cache"
DOWNLOAD_SONG_CACHE_DIRECTORY = "cache/songs_download_cache"
##end

## RPG settings
# Pasive setting
COIN_MESSAGE_DROP_CHANCE = 0.02
COIN_MESSAGE_DROP_MIN = 1
COIN_MESSAGE_DROP_MAX = 5
COIN_MESSAGE_DROP_BONUS = 15

XP_MESSAGE_DROP_CHANCE = 0.8
XP_MESSAGE_DROP_AMMOUNT = 1

BASE_WORK_REVENUE_FOR_HOUR = 2

# Minor addons settings
GAMBLE_NUMBER_OF_DRAWN_NUMBERS = 20
##end

## Song config
DELETE_CACHE_OLD_AFTER_MINS = 180
DELETE_DOWNLOAD_CACHE_OLD_AFTER_MINS = 20
CACHE_CLEARING_ROUTINE_DELAY_MIN = 10

# Processing threads settings
ENABLE_SONGS_CACHING = True
DOWNLOADER_THREADS = 4
VOLUME_NORMALIZER_THREADS = 4

# Module limits
MAX_PLAYLIST_LENGTH = 50
MAX_PLAYLIST_LENGTH_CACHED = 50
MAX_SONG_DURATION_MINS = 60
##end

## Reddit config
REDDIT_CLIENT_ID = ""  ### Credentials for reddit aplication ###
REDDIT_CLIENT_SECRET = ""
REDDIT_USERNAME = ""
REDDIT_PASSWORD = ""
REDDIT_USER_AGENT = ""
##end

## Stats settings
STATS_AGREG_TIME_MINUTES = 10
STATS_HISTORY_LOADING_DAYS = 10
##end

## Minigames config
THE8_RESPONSES = [
	'Absolutely!',
	'Without a doubt.',
	'Most likely.',
	'Yes.',
	'Maybe.',
	'Perhaps.',
	'Nope.',
	'Very doubtful.',
	'Absolutely not.',
	'It is unlikely.'
]
##end

## Constants DONT CHANGE
OPUS_LIBS = ['libopus-0.x86.dll', 'libopus-0.x64.dll', 'libopus-0.dll', 'libopus.so.0', 'libopus.0.dylib']
##end