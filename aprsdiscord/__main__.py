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
from discord.commands import Option
import asyncio
from discord.ext import commands
import hashlib
from .send_message import send_message


import datetime

from threading import Thread

bot = discord.Bot()

MESSAGE_TIME = 4*60*60 # 4 hours in seconds

messages_heard = {}

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    print(bot.guilds)

@bot.slash_command(name="aprs", description="APRS help", guild_ids=[688681592318722112])
async def on_message(message):
        return await message.channel.send(f"Send APRS messages to `{os.getenv('SERVER_NAME')}` that start with `{channel_id_hash(message.channel.id)} ` for them to appear here")

CALLSIGN = os.getenv("CALLSIGN")
logging.getLogger().setLevel(logging.DEBUG)
logging.getLogger("aprslib").setLevel(logging.INFO)
logging.getLogger("discord").setLevel(logging.INFO)

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

def channel_id_hash(id):
    return hashlib.sha224(str(id).encode("utf-8")).hexdigest()[:8]

def get_channel_id_from_hash(hash):
    channels = {channel_id_hash(x.id) : x.id for x in bot.get_all_channels()}
    return channels[hash]

def isDup(callsign, message, messageno):
    # expire duplicates
    for k,v in messages_heard.copy().items():
        if v < datetime.datetime.utcnow() - datetime.timedelta(seconds=MESSAGE_TIME):
            logging.debug(f"Removing {k} from messages_heard : {v}")
            messages_heard.pop(k, None)

    if (callsign, message, messageno) in messages_heard:
        logging.debug(f"Message {(callsign, message, messageno)} already heard at {messages_heard[(callsign, message, messageno)]}")
        return True
    else:
        logging.debug(f"Adding {(callsign, message, messageno)} to messages_heard")
        messages_heard[(callsign, message, messageno)] = datetime.datetime.utcnow()
        return False

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
                    if isDup(thing['from'], message, thing['msgNo']): # remove duplicates
                        return
                #channels = {x.id : {"guild": x.guild, "name": x.name, "_": x} for x in client.get_all_channels()}
                channel_id, message = message.split(" ",1)
                if len(channel_id) == 8: # lookup short code
                    channel_id = get_channel_id_from_hash(channel_id)
                else:
                    channel_id = int(channel_id)
                channel = bot.get_channel(channel_id)
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


@bot.slash_command(name="sendaprs", description="Send APRS message")
async def sendaprs(ctx,
                    to_call: Option(str, "Person to send message to + SSID", required = True),
                    from_call: Option(str, "Person to send message from", required = True),
                    aprs_passcode: Option(str, "APRS Passcode", required = True),
                    message: Option(str, "The message", required = True)
                  ):
    message = f"[{from_call}:{channel_id_hash(ctx.channel.id)}] {message}"
    status = send_message(to_call, from_call, aprs_passcode,message)
    
    if status == 200:
        print(dir(ctx.user.avatar))
        await ctx.respond("Sent!")
        return await ctx.channel.send(embed=discord.Embed(
            title=f"APRS sent message to {to_call} from {from_call}",
            description=message,
            url=f"https://aprs.fi/?call=a%2F{to_call}",
            color=0x33cc33,
        ).set_author(name=ctx.user.name, icon_url=str(ctx.user.avatar))) 
    elif status == 403:
        return await ctx.respond("Invalid passcode")
    else:
        return await ctx.respond("Error sending")


a = aprs.TCP(CALLSIGN.encode(), str(aprslib.passcode(CALLSIGN)).encode(), aprs_filter=f"g/{os.getenv('SERVER_NAME')}".encode()) # filter position and balloon
a.start()

loop = asyncio.get_event_loop()
loop.create_task(bot.start(os.getenv("DISCORD_TOKEN")))
Thread(target=loop.run_forever).start()

a.interface.settimeout(None)
a.receive(callback=parser)
sys.exit()