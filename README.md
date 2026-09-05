# Discord Music Bot 🎵

A feature-rich Discord music bot built with Python that can play music from YouTube.

## Features ✨

### 🎵 Music Playback
- **Play single songs** with `/play <song name>`
- **Add multiple songs at once** with `/playlist <song1, song2, song3>`
- **Queue management** - Songs are automatically queued and played in order
- **YouTube integration** - Searches and plays music from YouTube

### 🎛️ Playback Controls
- **Skip** - `/skip` to skip the current song
- **Pause** - `/pause` to pause playback
- **Resume** - `/resume` to resume paused playback
- **Stop** - `/stop` to stop playback and clear the queue

### 🤖 Smart Voice Channel Management
- **Auto-join** - Automatically joins your voice channel when you use commands
- **Stay connected** - Remains in the channel when queue is empty (waiting for more songs)
- **Auto-disconnect** - Leaves when everyone exits the voice channel 


## Commands 📝

| Command | Description | Example |
|---------|-------------|---------|
| `/play <song>` | Play a single song or add it to queue | `/play never gonna give you up` |
| `/playlist <songs>` | Add multiple songs separated by commas | `/playlist song1, song2, song3` |
| `/skip` | Skip the currently playing song | `/skip` |
| `/pause` | Pause the current playback | `/pause` |
| `/resume` | Resume paused playback | `/resume` |
| `/stop` | Stop playback, clear queue, and disconnect | `/stop` |
| `!sync` | Sync slash commands to the server (text command) | `!sync` |

## Setup Instructions 🚀

### Prerequisites
- Python 3.8+
- On Linux, system FFmpeg is recommended (`sudo apt install ffmpeg` on Ubuntu/Debian)
- Deno 2.3+ is recommended for full YouTube support
- Discord Developer Application with bot token

### Installation

1. **Clone or download this project**
   ```bash
   git clone <repository-url>
   cd discord-bot
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   The dependencies include Discord's voice encryption support, yt-dlp's
   JavaScript challenge scripts, and a fallback FFmpeg executable. The bot
   prefers a system FFmpeg installation when one is available.

4. **Set up Discord Bot**
   - Create a Discord application at [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a bot and copy the token
   - Invite the bot to your server with these scopes:
     - `bot`
     - `applications.commands`
   - Required permissions:
     - Send Messages
     - Connect
     - Speak
     - Use Slash Commands

5. **Configure environment variables**
   - Create a `.env` file in the project root
   - Add your Discord bot token:
   ```
   DISCORD_TOKEN=your_bot_token_here
   ```

6. **Run the bot**
   ```bash
   python main.py
   ```

## Usage Examples 🎯

### Playing a single song
```
/play bohemian rhapsody
```

### Adding multiple songs at once
```
/playlist never gonna give you up, bohemian rhapsody, stairway to heaven
```

### With artist names
```
/playlist queen we will rock you, led zeppelin black dog, pink floyd comfortably numb
```

### Managing playback
```
/pause    # Pause the music
/resume   # Resume playback
/skip     # Skip to next song
/stop     # Stop everything and disconnect
```


### Bot Permissions Required
- **Read Messages** - To see commands
- **Send Messages** - To respond in chat
- **Connect** - To join voice channels
- **Speak** - To play audio
- **Use Slash Commands** - For slash command functionality


## License 📄

This project is for educational and personal use. Please respect YouTube's Terms of Service and Discord's Terms of Service when using this bot.

---
