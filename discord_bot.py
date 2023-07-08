import discord
import os
from discord.ext import tasks
import trading_clock as tc

last_to_print = []

intents = discord.Intents(messages=True, message_content=True, guilds=True)
client = discord.Client(intents=intents)
TOKEN = "MTEyMTE1MzI3MjE3MDk0NjU5Mg.G3qbyD.-IhGrjmcKp4e_d3H2A7xwlXSNzmiOVuyvKslhA"

@tasks.loop(seconds=10)
async def send_message():
    global last_to_print
    sum_path = f"trade_logs/{tc.get_today().date()}_summary.txt"
    if os.path.exists(sum_path):
        with open(sum_path, 'r') as f:
            lines = f.readlines()

        count = 0
        for i in range(len(lines)-1,0, -1):
            if lines[i] == "\n":
                count += 1
            else:
                break
        
        for i in range(count):
            lines.pop()

        if len(lines) >= 9:
            last_lines = lines[-9:]
            if ("[TRADE ORDER]:" in last_lines[0]) and last_to_print != last_lines:
                channel = client.get_channel(1121157472690909316)
                message="@everyone\n"
                for l in last_lines:
                    message += l
                
                last_to_print = last_lines
                await channel.send(message)
    
@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')
    send_message.start()

client.run(TOKEN)