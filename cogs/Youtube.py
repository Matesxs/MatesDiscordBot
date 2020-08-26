import asyncio
import concurrent.futures
from typing import Union
import subprocess
import sys
import math
import json
import os
import youtube_dl
import ntpath
import time
import discord
from discord.ext import commands, tasks
from multiprocessing.pool import ThreadPool

from ext.modules.botBase import BaseBot
from ext.helpers.general_helpers import generate_error_message, generate_success_message, developerOrTester
from ext.miscellaneous.custom_loger import setup_custom_logger
from config import MAX_PLAYLIST_LENGTH, MAX_PLAYLIST_LENGTH_CACHED, DOWNLOADER_THREADS, VOLUME_NORMALIZER_THREADS, SONG_CACHE_DIRECTORY, DOWNLOAD_SONG_CACHE_DIRECTORY, DELETE_CACHE_OLD_AFTER_MINS, DELETE_DOWNLOAD_CACHE_OLD_AFTER_MINS, CACHE_CLEARING_ROUTINE_DELAY_MIN, ENABLE_SONGS_CACHING
from ext.modules.sound_cog_precursor import GenericSoundCog

logger = setup_custom_logger(__name__)

def test_ffmpeg_is_installed():
	try:
		proc = subprocess.Popen("ffmpeg", stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
		proc.wait()
		return True
	except:
		return False

def normalize_volume(data):
	def generate_new_name(data):
		base_name = ntpath.basename(data['source'])
		new_path = os.path.join(SONG_CACHE_DIRECTORY, base_name)
		return f"{os.path.splitext(new_path)[0]}.mp3"

	def process_files(data):
		new_name = generate_new_name(data)
		if os.path.exists(new_name): return

		try:
			subprocess.run(f"ffmpeg -i {data['source']} -filter:a loudnorm {new_name}", stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
			os.remove(data['source'])
		except:
			pass

		return True

	logger.debug(f"Normalizing {len(data)} songs")
	if len(data) == 1:
		process_files(data[0])
	else:
		with ThreadPool(processes=VOLUME_NORMALIZER_THREADS) as pool:
			pool.map(process_files, data)

	for i in range(len(data)):
		data[i]["source"] = generate_new_name(data[i])

	return data

def get_duration(url):
	try:
		cmd = f'ffprobe -v error -show_format -of json {url}'
		process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		output, error = process.communicate()
		data = json.loads(output)
		match = data['format']['duration']
		process.kill()
	except Exception:
		return duration_format(0)

	return duration_format(math.ceil(float(match)))

def duration_format(duration:int):
	mins = int(duration // 60)
	sec = duration - (mins * 60)
	return mins, sec

ytdlopts = {
	'format': 'bestaudio/best',
	'extractaudio': True,
  'audioformat': 'mp3',
	'restrictfilenames': True,
	'noplaylist': True,
	'nocheckcertificate': True,
	'ignoreerrors': False,
	'logtostderr': False,
	'quiet': True,
	'no_warnings': True,
	'default_search': 'auto',
	'source_address': '0.0.0.0',  # ipv6 addresses cause issues sometimes
	'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36 OPR/68.0.3618.104",
	'cachedir': False
}

class Youtube(GenericSoundCog):
	def __init__(self, bot:BaseBot):
		super().__init__(bot)

		if not test_ffmpeg_is_installed():
			logger.error("FFMPEG not found, install it first and add it to PATH!\nhttps://www.ffmpeg.org")
			sys.exit(1)

		if not os.path.exists(SONG_CACHE_DIRECTORY): os.makedirs(SONG_CACHE_DIRECTORY)
		if not os.path.exists(DOWNLOAD_SONG_CACHE_DIRECTORY): os.makedirs(DOWNLOAD_SONG_CACHE_DIRECTORY)

		self.delete_old_cache(SONG_CACHE_DIRECTORY)
		self.delete_old_cache(DOWNLOAD_SONG_CACHE_DIRECTORY)
		if ENABLE_SONGS_CACHING:
			try:
				self.clearing_music_cache_task.start()
			except:
				logger.warning("Clearing cache task already running")

	@staticmethod
	async def get_source_from_youtube(ctx, search, is_playlist:bool=False, cached:bool=False, limit_songs:int=50) -> Union[None, list]:
		ytdlopts["noplaylist"] = not is_playlist
		if cached: ytdlopts['outtmpl'] = f'{DOWNLOAD_SONG_CACHE_DIRECTORY}/{ctx.guild.id}-%(id)s-%(title)s.%(ext)s'

		ytdl = youtube_dl.YoutubeDL(ytdlopts)

		executor = concurrent.futures.ThreadPoolExecutor(max_workers=DOWNLOADER_THREADS)

		data = []
		future = executor.submit(ytdl.extract_info, url=search, download=False)
		future = asyncio.wrap_future(future)
		results = await asyncio.wait_for(future, timeout=None, loop=asyncio.get_event_loop())

		if "entries" in results:
			for result in results["entries"]:
				try:
					sec_res = None

					try:
						if f"{ctx.guild.id}-{result['id']}-{result['title']}.mp3".replace(" ", "_") in os.listdir(SONG_CACHE_DIRECTORY):
							sec_res = result
					except:
						pass

					if not sec_res:
						future = executor.submit(ytdl.extract_info, url=result["title"], download=cached)
						future = asyncio.wrap_future(future)
						sec_res = await asyncio.wait_for(future, timeout=None, loop=asyncio.get_event_loop())

					if "entries" in sec_res:
						sec_res = sec_res["entries"][0]

					if cached:
						sec_res["source"] = ytdl.prepare_filename(sec_res)
					else:
						sec_res["source"] = sec_res["url"]

					data.append({"url": sec_res["url"], "source": sec_res["source"], "duration": get_duration(sec_res['url']), "title": sec_res["title"], "thumbnail": sec_res["thumbnail"]})
					if not is_playlist: break
					if len(data) >= limit_songs: break
				except:
					continue
		else:
			try:
				sec_res = None

				try:
					if f"{ctx.guild.id}-{results['id']}-{results['title']}.mp3".replace(" ", "_") in os.listdir(SONG_CACHE_DIRECTORY):
						sec_res = results
				except:
					pass

				if not sec_res:
					future = executor.submit(ytdl.extract_info, url=results["title"], download=cached)
					future = asyncio.wrap_future(future)
					sec_res = await asyncio.wait_for(future, timeout=None, loop=asyncio.get_event_loop())

				if "entries" in sec_res:
					sec_res = sec_res["entries"][0]

				if cached:
					sec_res["source"] = ytdl.prepare_filename(sec_res)
				else:
					sec_res["source"] = sec_res["url"]

				data.append({"url": sec_res["url"], "source": sec_res["source"], "duration": get_duration(sec_res['url']), "title": sec_res["title"], "thumbnail": sec_res["thumbnail"]})
			except:
				return None

		if cached and data:
			future = executor.submit(normalize_volume, data=data)
			future = asyncio.wrap_future(future)
			res = await asyncio.wait_for(future, timeout=None, loop=asyncio.get_event_loop())
			if res: data = res

		executor.shutdown(wait=False)

		return data

	@commands.command(no_pm=True, name="kstop", help="!kstop to stop actual request and clear queue (Bcommander only)")
	@commands.has_role("Bcommander")
	async def kill_play(self, ctx: commands.Context):
		await ctx.message.delete()

		voice_client: discord.VoiceClient = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
		if not self.voice_client_playing(voice_client): return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Bot is not playing!"))

		self.banish_list.append(ctx.guild.id)
		return await self.bot.send_message_for_time(ctx, embed=generate_success_message("Bot being stopped"))

	@commands.command(no_pm=True, name="play", help="!play <volume 0-100> <search or source> to play song from Youtube")
	@commands.cooldown(2, 30, commands.BucketType.user)
	async def _play(self, ctx, volume: float, *, source: str):
		await ctx.message.delete()
		volume = volume / 100

		data = await self.get_source_from_youtube(ctx, source, is_playlist=False, cached=False)
		if not data: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant find anything to play!"))

		voice_client: discord.VoiceClient = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
		if self.voice_client_playing(voice_client):
			if self.add_to_queue(ctx, volume, data[0]):
				em = discord.Embed(title=":notes: | Added to queue", color=discord.Color.dark_blue())
				em.description = f"{data[0]['title']}\n"
				em.add_field(name="Duration", value=f"{data[0]['duration'][0]}min {data[0]['duration'][1]}s", inline=True)
				em.add_field(name="Source", value=f"[Click]({data[0]['url']})", inline=True)
				em.set_footer(text=f"Requester: {ctx.author.name}", icon_url=ctx.author.avatar_url)
				em.set_thumbnail(url=data[0]["thumbnail"])
				return await self.bot.send_message_for_time(ctx, embed=em)
			else:
				return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Failed to add your request to queue!"))

		await self.play_source(ctx, volume, data[0])

	@commands.command(no_pm=True, name="playp", help="!playp <volume 0-100> <source of playlist> to play Youtube playlist")
	@commands.cooldown(2, 40, commands.BucketType.user)
	async def _play_playlist(self, ctx, volume: float, *, source: str):
		await ctx.message.delete()
		volume = volume / 100

		data = await self.get_source_from_youtube(ctx, source, is_playlist=True, cached=False, limit_songs=MAX_PLAYLIST_LENGTH)
		if not data: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant find anything to play!"))

		voice_client: discord.VoiceClient = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
		if self.voice_client_playing(voice_client):
			try:
				for idx, d in enumerate(data):
					if not idx == 0:
						self.add_to_queue(ctx, volume, d)

				if len(data) > 1:
					return await self.bot.send_message_for_time(ctx, embed=generate_success_message("Your request is added to queue!"))
				else:
					em = discord.Embed(title=":notes: | Added to queue", color=discord.Color.dark_blue())
					em.description = f"{data[0]['title']}\n"
					em.add_field(name="Duration", value=f"{data[0]['duration'][0]}min {data[0]['duration'][1]}s", inline=True)
					em.add_field(name="Source", value=f"[Click]({data[0]['url']})", inline=True)
					em.set_footer(text=f"Requester: {ctx.author.name}", icon_url=ctx.author.avatar_url)
					em.set_thumbnail(url=data[0]["thumbnail"])
					return await self.bot.send_message_for_time(ctx, embed=em)
			except:
				return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Failed to add your request to queue!"))

		if len(data) > 1:
			try:
				for idx, d in enumerate(data):
					if not idx == 0:
						self.add_to_queue(ctx, volume, d)
			except:
				if ctx.guild.id in self.servers_queues: del self.servers_queues[ctx.guild.id]
				return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Failed to add your request!"))

		await self.play_source(ctx, volume, data[0])

	if ENABLE_SONGS_CACHING:
		@commands.command(no_pm=True, name="cplay", help="!cplay <volume 0-100> <search or source> to play song from Youtube with server caching - developer and testers only")
		@commands.cooldown(2, 30, commands.BucketType.user)
		@developerOrTester()
		async def _cplay(self, ctx, volume: float, *, source: str):
			await ctx.message.delete()
			volume = volume / 100

			await self.bot.send_message_for_time(ctx, embed=generate_success_message("Command is registered!"))
			data = await self.get_source_from_youtube(ctx, source, is_playlist=False, cached=True)
			if not data: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant find anything to play!"))

			voice_client: discord.VoiceClient = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
			if self.voice_client_playing(voice_client):
				if self.add_to_queue(ctx, volume, data[0]):
					em = discord.Embed(title=":notes: | Added to queue", color=discord.Color.dark_blue())
					em.description = f"{data[0]['title']}\n"
					em.add_field(name="Duration", value=f"{data[0]['duration'][0]}min {data[0]['duration'][1]}s", inline=True)
					em.add_field(name="Source", value=f"[Click]({data[0]['url']})", inline=True)
					em.set_footer(text=f"Requester: {ctx.author.name}", icon_url=ctx.author.avatar_url)
					em.set_thumbnail(url=data[0]["thumbnail"])
					return await self.bot.send_message_for_time(ctx, embed=em)
				else:
					return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Failed to add your request to queue!"))

			await self.play_source(ctx, volume, data[0])

		@commands.command(no_pm=True, name="cplayp", help="!cplayp <volume 0-100> <source of playlist> to play Youtube playlist with server caching - developer and testers only")
		@commands.cooldown(2, 60, commands.BucketType.user)
		@developerOrTester()
		async def _cplay_playlist(self, ctx, volume: float, *, source: str):
			await ctx.message.delete()
			volume = volume / 100

			await self.bot.send_message_for_time(ctx, embed=generate_success_message("Command is registered!"))
			data = await self.get_source_from_youtube(ctx, source, is_playlist=True, cached=True, limit_songs=MAX_PLAYLIST_LENGTH_CACHED)
			if not data: return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Cant find anything to play!"))

			voice_client: discord.VoiceClient = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
			if self.voice_client_playing(voice_client):
				try:
					for idx, d in enumerate(data):
						if not idx == 0:
							self.add_to_queue(ctx, volume, d)

					if len(data) > 1:
						return await self.bot.send_message_for_time(ctx, embed=generate_success_message("Your request is added to queue!"))
					else:
						em = discord.Embed(title=":notes: | Added to queue", color=discord.Color.dark_blue())
						em.description = f"{data[0]['title']}\n"
						em.add_field(name="Duration", value=f"{data[0]['duration'][0]}min {data[0]['duration'][1]}s", inline=True)
						em.add_field(name="Source", value=f"[Click]({data[0]['url']})", inline=True)
						em.set_footer(text=f"Requester: {ctx.author.name}", icon_url=ctx.author.avatar_url)
						em.set_thumbnail(url=data[0]["thumbnail"])
						return await self.bot.send_message_for_time(ctx, embed=em)
				except:
					return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Failed to add your request to queue!"))

			if len(data) > 1:
				try:
					for idx, d in enumerate(data):
						if not idx == 0:
							self.add_to_queue(ctx, volume, d)
				except:
					if ctx.guild.id in self.servers_queues: del self.servers_queues[ctx.guild.id]
					return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Failed to add your request!"))

			await self.play_source(ctx, volume, data[0])

	@tasks.loop(minutes=CACHE_CLEARING_ROUTINE_DELAY_MIN)
	async def clearing_music_cache_task(self):
		try:
			if not self.bot.sync_tasks_executor: return

			future = self.bot.sync_tasks_executor.submit(self.delete_old_cache, SONG_CACHE_DIRECTORY, DELETE_CACHE_OLD_AFTER_MINS)
			future = asyncio.wrap_future(future)
			await asyncio.wait_for(future, timeout=None, loop=asyncio.get_event_loop())

			future = self.bot.sync_tasks_executor.submit(self.delete_old_cache, DOWNLOAD_SONG_CACHE_DIRECTORY, DELETE_DOWNLOAD_CACHE_OLD_AFTER_MINS)
			future = asyncio.wrap_future(future)
			await asyncio.wait_for(future, timeout=None, loop=asyncio.get_event_loop())
		except Exception as e:
			logger.exception(f"Clearing music cache exception\n{e}")

	def delete_old_cache(self, directory, treshold:Union[int, float]=None):
		if not os.path.exists(directory): return

		for file_name in os.listdir(directory):
			can_delete = True
			file_path = os.path.join(directory, file_name)

			for client in self.bot.voice_clients:
				if isinstance(client, discord.VoiceClient):
					if client.source == file_path:
						can_delete = False
						break

					for data in self.servers_queues.values():
						if data:
							for sf in data["source_file"]:
								if sf:
									if sf["source"] == file_path:
										can_delete = False
										break

			if can_delete:
				if ENABLE_SONGS_CACHING:
					try:
						if (os.path.getctime(file_path) + (treshold * 60)) < time.time():
							if os.path.isfile(file_path):
								os.remove(file_path)
					except:
						pass
				else:
					if os.path.isfile(file_path):
						try:
							os.remove(file_path)
						except:
							pass

def setup(bot):
	bot.add_cog(Youtube(bot))