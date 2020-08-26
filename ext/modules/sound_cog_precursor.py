import asyncio
import os
from collections import deque
from typing import Union

import discord
from discord.ext import commands

from ext.modules.botBase import BaseBot
from ext.miscellaneous.custom_loger import setup_custom_logger
from ext.helpers.general_helpers import generate_error_message
from config import OPUS_LIBS, MAX_SONG_DURATION_MINS

logger = setup_custom_logger(__name__)

class GenericSoundCog(commands.Cog):
	servers_queues = {}
	banish_list = []

	def __init__(self, bot:BaseBot):
		self.bot = bot
		if not discord.opus.is_loaded():
			for opus_lib in OPUS_LIBS:
				try:
					discord.opus.load_opus(opus_lib)
					return
				except OSError:
					pass

	@staticmethod
	def voice_client_playing(voice_client:Union[discord.VoiceClient, None]) -> bool:
		if voice_client:
			if voice_client.is_playing(): return True
		return False

	async def connect_to_voice_channel(self, channel:discord.VoiceChannel) -> Union[discord.VoiceClient, None]:
		voice_client:discord.VoiceClient = discord.utils.get(self.bot.voice_clients, guild=channel.guild)
		if not voice_client:
			voice_client = await channel.connect()
		else:
			if voice_client.is_playing(): return None
			if voice_client.channel != channel:
				await voice_client.move_to(channel)
		return voice_client

	async def disconnect_from_voice_channel(self, guild:discord.Guild):
		voice_client:discord.VoiceClient = discord.utils.get(self.bot.voice_clients, guild=guild)
		if voice_client:
			try:
				if voice_client.is_playing():
					await voice_client.stop()
			except:
				pass
			if voice_client.is_connected():
				await voice_client.disconnect()
				return True
		return False

	async def play_source(self, ctx, volume, source_file:Union[str, dict]):
		if isinstance(source_file, str):
			if not os.path.isfile(source_file):
				return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid path to source file"))

		if 0 > volume > 1:
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Invalid value of volume - volume range <0 - 1>"))

		if not ctx.message.author.voice:
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message("You are not in voice channel!"))
		voice_channel = ctx.message.author.voice.channel

		voice = await self.connect_to_voice_channel(voice_channel)
		if not voice:
			return await self.bot.send_message_for_time(ctx, embed=generate_error_message("Failed to summon bot to yout voice channel!\nMaybe playing something"))

		plaing_message = None
		source = None

		try:
			if isinstance(source_file, dict):
				await asyncio.sleep(1)

				if source_file['duration'][0] > MAX_SONG_DURATION_MINS:
					await self.bot.send_message_for_time(ctx, embed=generate_error_message(f"Song: {source_file['title']} is too long!\nMaximum duration is {MAX_SONG_DURATION_MINS}min"))
				else:
					source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(source_file["source"]), volume=volume)
					voice.play(source)

					em = discord.Embed(title=":notes: | Playing", color=discord.Color.dark_blue())
					em.description = f"{source_file['title']}\n"
					em.add_field(name="Duration", value=f"{source_file['duration'][0]}min {source_file['duration'][1]}s", inline=True)
					if ctx.guild.id in self.servers_queues:
						if len(self.servers_queues[ctx.guild.id] != 0):
							em.add_field(name="Songs in queue", value=f"{len(self.servers_queues[ctx.guild.id])}", inline=True)
					em.add_field(name="Source", value=f"[Click]({source_file['url']})", inline=True)
					em.set_footer(text=f"Requester: {ctx.author.name}", icon_url=ctx.author.avatar_url)
					em.set_thumbnail(url=source_file["thumbnail"])

					if plaing_message:
						if isinstance(plaing_message, discord.Message):
							await plaing_message.edit(embed=em)
						else:
							plaing_message = await ctx.send(embed=em)
					else:
						plaing_message = await ctx.send(embed=em)

					while voice.is_playing():
						await asyncio.sleep(1)
						if ctx.guild.id in self.banish_list:
							self.banish_list = [x for x in self.banish_list if x != ctx.guild.id]
							await voice.stop()
							break
			else:
				await asyncio.sleep(1)
				source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(source_file), volume=volume)
				voice.play(source)

				while voice.is_playing():
					await asyncio.sleep(1)
					if ctx.guild.id in self.banish_list:
						self.banish_list = [x for x in self.banish_list if x != ctx.guild.id]
						await voice.stop()
						break

		except:
			await self.bot.send_message_for_time(ctx, embed=generate_error_message("Playing failed"))
		finally:
			if plaing_message: await plaing_message.delete(delay=5)
			if ctx.guild.id in self.servers_queues:
				if len(self.servers_queues[ctx.guild.id]) > 0:
					data = self.servers_queues[ctx.guild.id].popleft()
					await asyncio.sleep(1)
					if data: return await self.play_source(data["ctx"], data["volume"], data["source_file"])
				else:
					del self.servers_queues[ctx.guild.id]

			await asyncio.sleep(10)
			if source: source.cleanup()
			return await self.disconnect_from_voice_channel(ctx.guild)

	def add_to_queue(self, ctx:commands.Context, volume:float, source_file:Union[str, dict]):
		if not ctx.guild.id in self.servers_queues:
			self.servers_queues[ctx.guild.id] = deque()
		try:
			self.servers_queues[ctx.guild.id].append({"ctx": ctx, "volume": volume, "source_file": source_file})
			return True
		except:
			return False