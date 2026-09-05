import os
import shutil
import discord
import imageio_ffmpeg
from discord.ext import commands
from discord import app_commands
import yt_dlp 
from collections import deque 
import asyncio 
from dotenv import load_dotenv

load_dotenv()

SONG_QUEUES = {}
FFMPEG_EXECUTABLE = (
    os.getenv("FFMPEG_EXECUTABLE")
    or shutil.which("ffmpeg")
    or imageio_ffmpeg.get_ffmpeg_exe()
)

async def search_ytdlp_async(query, ydl_opts):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)


async def connect_to_user_voice(interaction: discord.Interaction):
    """Connect to the command user's voice channel and report failures in Discord."""
    voice_state = getattr(interaction.user, "voice", None)
    voice_channel = voice_state.channel if voice_state else None

    if voice_channel is None:
        await interaction.followup.send("You must be in a voice channel.")
        return None

    voice_client = interaction.guild.voice_client

    try:
        if voice_client is None:
            voice_client = await voice_channel.connect()
        elif voice_channel != voice_client.channel:
            await voice_client.move_to(voice_channel)
    except (RuntimeError, discord.ClientException, asyncio.TimeoutError) as error:
        print(f"Could not connect to voice channel: {error}")
        await interaction.followup.send(
            "I couldn't connect to your voice channel. Check my Connect/Speak "
            "permissions and make sure the bot's voice dependencies are installed."
        )
        return None

    return voice_client


# Setup of intents
intents = discord.Intents.default()
intents.message_content = True

# Bot setup
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} is online!")

@bot.event
async def on_voice_state_update(member, before, after):
    """Check if bot should disconnect when users leave voice channel"""
    if member.bot:
        return
    
    # Check if someone left a voice channel
    if before.channel is not None and after.channel != before.channel:
        voice_client = member.guild.voice_client
        
        if voice_client and voice_client.channel == before.channel:
            # Count remaining human members in the bot's voice channel
            human_members = [m for m in voice_client.channel.members if not m.bot]
            
            if len(human_members) == 0:
                # No humans left, disconnect after a short delay
                await asyncio.sleep(5)  # Wait 5 seconds in case someone rejoins quickly
                
                # Double-check that no one rejoined
                # This should be a diff function, I aint doing it
                if voice_client.channel:
                    current_humans = [m for m in voice_client.channel.members if not m.bot]
                    if len(current_humans) == 0:
                        await voice_client.disconnect()
                        guild_id = str(member.guild.id)
                        if guild_id in SONG_QUEUES:
                            SONG_QUEUES[guild_id] = deque()
                        
                        # Find a text channel to send message
                        text_channel = discord.utils.get(member.guild.text_channels, name='general')
                        if not text_channel:
                            text_channel = member.guild.text_channels[0] if member.guild.text_channels else None
                        
                        if text_channel:
                            await text_channel.send("🔇 Everyone left the voice channel. Disconnecting...")


@bot.tree.command(name="skip", description="Skips the current playing song")
async def skip(interaction: discord.Interaction):
    if interaction.guild.voice_client and (interaction.guild.voice_client.is_playing() or interaction.guild.voice_client.is_paused()):
        interaction.guild.voice_client.stop()
        await interaction.response.send_message("Skipped the current song.")
    else:
        await interaction.response.send_message("Not playing anything to skip.")


@bot.tree.command(name="pause", description="Pause the currently playing song.")
async def pause(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    # Check if the bot is in a voice channel
    if voice_client is None:
        return await interaction.response.send_message("I'm not in a voice channel.")

    # Check if something is actually playing
    if not voice_client.is_playing():
        return await interaction.response.send_message("Nothing is currently playing.")
    
    # Pause the track
    voice_client.pause()
    await interaction.response.send_message("Playback paused!")


@bot.tree.command(name="resume", description="Resume the currently paused song.")
async def resume(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    # Check if the bot is in a voice channel
    if voice_client is None:
        return await interaction.response.send_message("I'm not in a voice channel.")

    # Check if it's actually paused
    if not voice_client.is_paused():
        return await interaction.response.send_message("I’m not paused right now.")
    
    # Resume playback
    voice_client.resume()
    await interaction.response.send_message("Playback resumed!")


@bot.tree.command(name="stop", description="Stop playback and clear the queue.")
async def stop(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client

    # Check if the bot is in a voice channel
    if not voice_client or not voice_client.is_connected():
        return await interaction.response.send_message("I'm not connected to any voice channel.")

    # Clear the guild's queue
    guild_id_str = str(interaction.guild_id)
    if guild_id_str in SONG_QUEUES:
        SONG_QUEUES[guild_id_str].clear()

    # If something is playing or paused, stop it
    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()

    await voice_client.disconnect()

    await interaction.response.send_message("Stopped playback and disconnected!")


@bot.tree.command(name="playlist", description="Add multiple songs to the queue at once.")
@app_commands.describe(songs="List of songs separated by commas (e.g., 'song1, song2, song3')")
async def playlist(interaction: discord.Interaction, songs: str):
    await interaction.response.defer()

    voice_client = await connect_to_user_voice(interaction)
    if voice_client is None:
        return
    
    # Split songs by comma and clean up whitespace
    song_list = [song.strip() for song in songs.split(',') if song.strip()]
    
    if not song_list:
        await interaction.followup.send("Please provide at least one song.")
        return
    
    ydl_options = {
        "format": "bestaudio[abr<=96]/bestaudio",
        "noplaylist": True,
        "youtube_include_dash_manifest": False,
        "youtube_include_hls_manifest": False,
    }
    
    guild_id = str(interaction.guild_id)
    if SONG_QUEUES.get(guild_id) is None:
        SONG_QUEUES[guild_id] = deque()
    
    added_songs = []
    failed_songs = []
    
    await interaction.followup.send(f"🔍 Searching for {len(song_list)} songs...")
    
    for i, song_query in enumerate(song_list, 1):
        try:
            query = "ytsearch1: " + song_query
            results = await search_ytdlp_async(query, ydl_options)
            tracks = results.get("entries", [])
            
            if tracks and len(tracks) > 0:
                first_track = tracks[0]
                audio_url = first_track["url"]
                title = first_track.get("title", "Untitled")
                
                SONG_QUEUES[guild_id].append((audio_url, title))
                added_songs.append(title)
            else:
                failed_songs.append(song_query)
                
        except Exception as e:
            print(f"Error searching for '{song_query}': {e}")
            failed_songs.append(song_query)
        
        # Update progress every 3 songs
        if i % 3 == 0 or i == len(song_list):
            await interaction.edit_original_response(content=f"🔍 Processed {i}/{len(song_list)} songs...")
    
    summary = f"✅ Added {len(added_songs)} songs to the queue!"
    if failed_songs:
        summary += f"\n❌ Failed to find: {', '.join(failed_songs[:3])}"
        if len(failed_songs) > 3:
            summary += f" and {len(failed_songs) - 3} more..."
    
    await interaction.edit_original_response(content=summary)
    
    # Start playing if nothing is currently playing
    if not voice_client.is_playing() and not voice_client.is_paused():
        await play_next_song(voice_client, guild_id, interaction.channel)


@bot.tree.command(name="play", description="Play a song or add it to the queue.")
@app_commands.describe(song_query="Search query")
async def play(interaction: discord.Interaction, song_query: str):
    await interaction.response.defer()

    voice_client = await connect_to_user_voice(interaction)
    if voice_client is None:
        return

    ydl_options = {
        "format": "bestaudio[abr<=96]/bestaudio",
        "noplaylist": True,
        "youtube_include_dash_manifest": False,
        "youtube_include_hls_manifest": False,
    }

    query = "ytsearch1: " + song_query
    results = await search_ytdlp_async(query, ydl_options)
    tracks = results.get("entries", [])

    if not tracks:
        await interaction.followup.send("No results found.")
        return

    first_track = tracks[0]
    audio_url = first_track["url"]
    title = first_track.get("title", "Untitled")

    guild_id = str(interaction.guild_id)
    if SONG_QUEUES.get(guild_id) is None:
        SONG_QUEUES[guild_id] = deque()

    SONG_QUEUES[guild_id].append((audio_url, title))

    if voice_client.is_playing() or voice_client.is_paused():
        await interaction.followup.send(f"Added to queue: **{title}**")
    else:
        await interaction.followup.send(f"Now playing: **{title}**")
        await play_next_song(voice_client, guild_id, interaction.channel)


async def play_next_song(voice_client, guild_id, channel):
    if SONG_QUEUES[guild_id]:
        audio_url, title = SONG_QUEUES[guild_id].popleft()

        ffmpeg_options = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn -c:a libopus -b:a 96k",
        }

        source = discord.FFmpegOpusAudio(
            audio_url,
            executable=FFMPEG_EXECUTABLE,
            **ffmpeg_options,
        )

        def after_play(error):
            if error:
                print(f"Error playing {title}: {error}")
            asyncio.run_coroutine_threadsafe(play_next_song(voice_client, guild_id, channel), bot.loop)

        voice_client.play(source, after=after_play)
        asyncio.create_task(channel.send(f"Now playing: **{title}**"))
    else:
        # No more songs in queue - check if there are users in the voice channel
        if voice_client and voice_client.channel:
            # Count non-bot members in the voice channel
            human_members = [member for member in voice_client.channel.members if not member.bot]
            
            if len(human_members) == 0:
                await voice_client.disconnect()
                SONG_QUEUES[guild_id] = deque()
                asyncio.create_task(channel.send("🔇 No one left in the voice channel. Disconnecting..."))
            else:
                asyncio.create_task(channel.send("📭 Queue is empty. Add more songs with `/play` or `/playlist`!"))


# Get the Discord token from environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

if not DISCORD_TOKEN:
    print("Error: DISCORD_TOKEN not found in .env file")
    exit(1)

bot.run(DISCORD_TOKEN)
