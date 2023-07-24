import discord
import os
from discord.ext import tasks
import trading_clock as tc

printed_trade_orders = []

intents = discord.Intents(messages=True, message_content=True, guilds=True)
client = discord.Client(intents=intents)
TOKEN = "MTEyMTE1MzI3MjE3MDk0NjU5Mg.G3qbyD.-IhGrjmcKp4e_d3H2A7xwlXSNzmiOVuyvKslhA"
strategies = {"SilverBullet": 1121157472690909316}

@tasks.loop(seconds=10)
async def send_message():
    global printed_trade_orders

    for strategy in strategies:
        sum_path = f"trade_logs/{strategy}/{tc.get_today().date()}_summary.txt"
        if os.path.exists(sum_path):
            to_print = []
            with open(sum_path, 'r') as f:
                for line in f:
                    if "TRADE ORDER" in line:
                        trade_order_message = f"@everyone\nTRADE ORDER ({strategy}):\n"
                        for _ in range(8):
                            trade_order_message += f.readline()

                        to_print.append(trade_order_message)

            for trade_order_message in to_print:
                if trade_order_message not in printed_trade_orders:
                    channel = client.get_channel(strategies[strategy])
                    await channel.send(trade_order_message)
                    printed_trade_orders.append(trade_order_message)

        else:
            if tc.is_market_open(security_type="ETF", current_datetime=tc.real_time()):
                print(f"[ERROR]: {sum_path} does not exist")

@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')
    send_message.start()

client.run(TOKEN)