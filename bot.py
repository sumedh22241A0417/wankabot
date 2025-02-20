import discord
from discord.ext import commands
import datetime
import os

# ✅ Check if BOT_TOKEN is set
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is not set! Check your Railway environment variables.")

print("✅ BOT_TOKEN found! Starting bot...")  # Debugging message

# ✅ Enable all required intents
intents = discord.Intents.all()

bot = commands.Bot(command_prefix='-', intents=intents)

# ✅ Hidden text channel where data is stored (Replace with actual channel ID)
DATA_CHANNEL_ID = 123456789012345678  

async def log_data(guild, message):
    """Logs data to the hidden Discord text channel."""
    channel = guild.get_channel(DATA_CHANNEL_ID)
    if channel:
        await channel.send(message)

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')
    for guild in bot.guilds:
        await log_data(guild, "Bot restarted! Tracking VC activity.")

@bot.event
async def on_voice_state_update(member, before, after):
    """Tracks when users join or leave a voice channel."""
    now = datetime.datetime.utcnow()
    guild = member.guild

    if before.channel is None and after.channel is not None:
        # User joined VC
        await log_data(guild, f"JOIN {member.id} {now.timestamp()}")

    elif before.channel is not None and after.channel is None:
        # User left VC
        async for message in guild.get_channel(DATA_CHANNEL_ID).history(limit=1000):
            if message.content.startswith(f"JOIN {member.id}"):
                _, _, join_timestamp = message.content.split()
                join_time = datetime.datetime.utcfromtimestamp(float(join_timestamp))
                duration = (now - join_time).total_seconds()
                minutes = int(duration // 60)
                hours = round(duration / 3600, 1)

                await log_data(guild, f"LOG {member.id} {now.timestamp()} {minutes} ({hours}h)")
                break  # Stop searching after finding the last join record

@bot.command()
async def m(ctx):
    """Shows total VC time (daily, weekly, monthly, yearly, all-time)."""
    user_id = ctx.author.id
    guild = ctx.guild
    now = datetime.datetime.utcnow()

    timeframes = {
        "Daily": now - datetime.timedelta(days=1),
        "Weekly": now - datetime.timedelta(weeks=1),
        "Monthly": now - datetime.timedelta(days=30),
        "Yearly": now - datetime.timedelta(days=365),
        "All-time": datetime.datetime.min
    }

    totals = {tf: 0 for tf in timeframes}
    
    async for message in guild.get_channel(DATA_CHANNEL_ID).history(limit=1000):
        if message.content.startswith(f"LOG {user_id}"):
            _, _, timestamp, minutes, _ = message.content.split()
            log_time = datetime.datetime.utcfromtimestamp(float(timestamp))
            for tf, start_time in timeframes.items():
                if log_time >= start_time:
                    totals[tf] += int(minutes)

    response = f"**VC Stats for {ctx.author.display_name}**\n"
    for tf, minutes in totals.items():
        response += f"**{tf}:** {minutes} mins ({round(minutes/60, 1)}h)\n"
    
    await ctx.send(response)

# ✅ Start the bot
bot.run(BOT_TOKEN)
