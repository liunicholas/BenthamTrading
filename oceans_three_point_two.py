from discord.ext import tasks
import os
import discord
import cv2
import pyautogui
import pyscreeze
import PIL
__PIL_TUPLE_VERSION = tuple(int(x) for x in PIL.__version__.split("."))
pyscreeze.PIL__version__ = __PIL_TUPLE_VERSION
import pytesseract
import time
import trading_clock as tc
import numpy as np

intents = discord.Intents(messages=True, message_content=True, guilds=True)
client = discord.Client(intents=intents)
TOKEN = "MTEyMTE1MzI3MjE3MDk0NjU5Mg.G3qbyD.-IhGrjmcKp4e_d3H2A7xwlXSNzmiOVuyvKslhA"

@tasks.loop(seconds=1)
async def send_message():
    image = pyautogui.screenshot()
    
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    width = image.shape[1]
    height = image.shape[0]
    image = image[:450, :600]
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.threshold(
        image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    image = cv2.GaussianBlur(image, (3, 3), 0)
    cv2.imwrite("tradingview.png", image)
    text = pytesseract.image_to_string(image, config="--psm 6")

    try:
        text = text.replace("uso", "usd")
        percent_index = text.lower().find("usd")
        if percent_index == -1:
            raise KeyError
        current_price = ""
        for char in text[percent_index-1:0:-1]:
            # print(char)
            if char.isdigit() or char in [" ", "."]:
                current_price = char + current_price
            else:
                current_price = current_price.strip().replace(" ","")
                break 
        # print(current_price)
        channel = client.get_channel(1138302357927641098)
        await channel.send(f"spx futures: {current_price}")
    except:
        pass

@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')
    send_message.start()

client.run(TOKEN)
