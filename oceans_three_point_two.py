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
    channel = client.get_channel(1138302357927641098)

    image = pyautogui.screenshot()
    image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # image = cv2.threshold(
    #     image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # image = cv2.GaussianBlur(image, (3, 3) 0)
    cv2.imwrite("tradingview.png", image)

    try:
        spx_image = image[120:140, 320:570, :]
        spx_text = pytesseract.image_to_string(spx_image, config="--psm 6")
        spx_data = spx_text.split(" ")
        spx_entry = {"Open": float(spx_data[0][1:]), "High": float(
            spx_data[1][1:]), "Low": float(spx_data[2][1:]), "Close": float(spx_data[3][1:])}
        print("SPX", spx_entry)
        await channel.send(f"spx futures: {spx_entry}")

        ndq_image = image[488:503, 538:803, :]
        ndq_text = pytesseract.image_to_string(ndq_image, config="--psm 6")
        ndq_data = ndq_text.split(" ")
        ndq_entry = {"Open": float(ndq_data[0][1:]), "High": float(
            ndq_data[1][1:]), "Low": float(ndq_data[2][1:]), "Close": float(ndq_data[3][1:])}
        print("NDQ", ndq_entry)
        await channel.send(f"ndq futures: {ndq_entry}")
    except:
        print("STUPID SHIT HERE")

@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')
    send_message.start()

client.run(TOKEN)
