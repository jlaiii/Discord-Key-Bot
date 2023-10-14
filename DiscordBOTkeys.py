import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
import signal
import sys

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

keys_file_path = 'generated_keys.txt'
cooldown_timers = {}  # Dictionary to store user cooldown timers

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    update_status.start()  # Start the status update task

@tasks.loop(minutes=1)
async def update_status():
    # Read the number of keys remaining from the file
    try:
        with open(keys_file_path, 'r') as file:
            keys = file.readlines()
            keys_remaining = len(keys) - 1 if keys else 0
            await bot.change_presence(activity=discord.Game(name=f'Keys remaining: {keys_remaining}'))
    except FileNotFoundError:
        print("Error: Keys file not found.")

@bot.event
async def on_message(message):
    if bot.user.mentioned_in(message):
        await send_key(message)
        return

    await bot.process_commands(message)
    # Print detailed information about the message in console
    print(f"Message from {message.author} in {message.channel}: {message.content}")

async def send_key(message):
    try:
        user = message.author

        # Check if the user is on cooldown
        if user.id in cooldown_timers and cooldown_timers[user.id] > datetime.now():
            remaining_time = cooldown_timers[user.id] - datetime.now()
            remaining_minutes = (remaining_time.total_seconds() // 60) + 1  # Round up to the nearest minute
            await message.channel.send(f"You're on cooldown. Please wait {int(remaining_minutes)} minutes before getting another key.")
            return

        with open(keys_file_path, 'r+') as file:
            keys = file.readlines()

            if not keys:
                await message.channel.send("No more keys available.")
                return

            key_to_send = keys[0].strip()

            try:
                await user.send(f'Here is your wrap+ key: {key_to_send}')
                await message.channel.send('Key sent via DM.')

                # Remove the sent key from the file
                file.seek(0)
                file.truncate()
                file.writelines(keys[1:])

                # Update cooldown timer for the user
                cooldown_timers[user.id] = datetime.now() + timedelta(minutes=10)

                # Display the number of keys left
                await message.channel.send(f'Keys remaining: {len(keys) - 1}')
            except discord.Forbidden:
                await message.channel.send("Unable to send a DM to the user.")

    except FileNotFoundError:
        await message.channel.send("Error: Keys file not found.")

def signal_handler(signal, frame):
    print("Received termination signal. Shutting down gracefully.")
    bot.loop.create_task(bot.logout())

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

TOKEN = 'NTMyODU5MzI0NTMyMjYwODY0.G-KC5k.KIZhEfuIDGcySxTSinKGexUG3RIfG4T9oVTAf4'  # Replace with your actual bot token

try:
    bot.run(TOKEN)
except discord.LoginFailure:
    print("Invalid token. Please provide a valid bot token.")
except discord.HTTPException as e:
    print(f"An HTTP exception occurred: {e}")
except discord.ClientException as e:
    print(f"A client exception occurred: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

while True:
    try:
        input("Press Enter to exit.")
        break
    except KeyboardInterrupt:
        pass

print("Exiting the script. Goodbye!")
