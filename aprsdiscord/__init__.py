import socket
socket.setdefaulttimeout(10)
import aprs
import aprslib
import os
import logging 
import sys
import datetime
import pprint
import json
import discord
import asyncio
from discord.ext import commands



from threading import Thread

client = discord.Client()



@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):

    if message.content.startswith('!aprs'):
        await message.channel.send(f"Send APRS messages to `{os.getenv('SERVER_NAME')}` that start with `{str(message.channel.id)} ` for them to appear here")

CALLSIGN = os.getenv("CALLSIGN")
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger("aprslib").setLevel(logging.INFO)

class CustomFormatter(logging.Formatter):

    grey = "\x1b[2m"
    green = "\x1b[32;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: grey + format + reset,
        logging.INFO: green + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

ch.setFormatter(CustomFormatter())

logging.getLogger().addHandler(ch)


def parser(x):
    thing = aprslib.parse(bytes(x))
    
    if thing["format"] == "message":
        logging.info(f"{thing}")
        if thing['addresse'] == os.getenv('SERVER_NAME'):
            try:
                message = thing["message_text"]
                if 'msgNo' in thing:
                    logging.info(f"Sending ack to {thing['from']}")
                    sendAck(thing['from'], thing['msgNo'])
                    logging.info(f"Sent ack to {thing['from']}")
                #channels = {x.id : {"guild": x.guild, "name": x.name, "_": x} for x in client.get_all_channels()}
                channel_id, message = message.split(" ",1)
                channel_id = int(channel_id)
                channel = client.get_channel(channel_id)
                send_message = asyncio.run_coroutine_threadsafe(
                    channel.send(embed=discord.Embed(
                        title=f"APRS message from : {thing['from']}",
                        description=message,
                        url=f"https://aprs.fi/?call=a%2F{thing['from']}",
                        color=0x33cc33
                    )), loop
                    )
                logging.info(f"message: \n{pprint.pformat(message)}\n")
                logging.info(f"Discord published!")
            except:
                logging.exception("Error publishing to Discord topic")
    else:
        logging.debug(f"{thing}")

def sendAck(callsign, msgNo):
    callsign = callsign.ljust(9, ' ')
    a.send((f"{os.getenv('SERVER_NAME')}>APRS,TCPIP*::"+callsign+":ack"+msgNo).encode("ascii"))

a = aprs.TCP(CALLSIGN.encode(), str(aprslib.passcode(CALLSIGN)).encode(), aprs_filter=f"g/{os.getenv('SERVER_NAME')}".encode()) # filter position and balloon
a.start()

loop = asyncio.get_event_loop()
loop.create_task(client.start(os.getenv("DISCORD_TOKEN")))
Thread(target=loop.run_forever).start()

a.interface.settimeout(None)
a.receive(callback=parser)
