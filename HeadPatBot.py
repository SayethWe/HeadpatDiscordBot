# bot.py
import os
import random
import urllib
import HelpFunctions as hf

import discord
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')

TOKEN = os.environ['DISCORD_TOKEN']
DATABASE_HOST = os.environ['DATABASE_URL']
client = discord.Client()

WAIFU_REPLY = config.get('DEFAULT', 'WAIFU_REPLY')

DEFAULTUSAGE = (
            'Commands list:\n'
            '    !usage\n'
            '    !waifupoll\n' 
            '    !headpat\n'
            'Extra Functionality:\n'
            '    poll\n' 
            '!usage <any of the above commands or functionalities>')

USAGE = {
    '!usage' : 'de nada, nuh uh',
    '!headpat' : '!headpat <nothing>/setimage <url>/addimage <url>/removeimage <url>\nWant headpats? Why not? Have Some!',
    '!waifupoll' : '!waifupoll /<poll number (goes in reverse order, 0 is latest)>\nResults results results.',
    'poll' : ('Pinning a message in a channel called waifu-rating will cause it to be reacted to with 1-10 and '
    'the chequered flag\nEasy polls for lazy folk')
}

REPLY = {
    'setimage' : ("I'll never forgive you if the URL is broken or not wholesome, Baka!\n"
                    "I got rid of someone's image for you, too, so be thankful :relieved:"),
    'setimagenone' : ("There weren't any images to replace.\n"
                        "Were you making fun of me? You were, weren't you? :anger:\n"
                        "I've added your image anyway. It's not like it's a photo of me. Is it? :flushed:"),
    'addimage' : "I know you wouldn't give me a not wholesome URL.\nWould you?\nPerhaps I'll just ignore it next time",
    'removeall' : "I will curse you until the end of your days.\nThey're gone.\nAll of them!",
    'urlbroken' : "That doesn't work!\nIf you don't get me a working URL, I, I'll... I'll have to do it, y'know",
    'existingurl' : ("Are you making fun of me?\n"
                    "Even I can tell that I already have that one. :face_with_hand_over_mouth:\n"
                    "If you've got the time, maybe you should spend it on more worthwhile images! :anger:"),
    'removeimage': ("Ok, it's gone"),
    'imagedne': ("I don't have that one.")
}


@client.event
async def on_ready():
    hf.createTables(DATABASE_HOST)
    for guild in client.guilds:
        
        print(
            f'{client.user} is connected to the following guild:\n'
            f'{guild.name}(id: {guild.id})'
        )

@client.event
async def on_message_edit(before, after):
    print((not before.pinned) and after.pinned)
    print(after.channel.name)
    if((not before.pinned) and after.pinned and after.channel.name == 'waifu-rating'):
        for i in range(10):
            rString = f'{i}\N{COMBINING ENCLOSING KEYCAP}'
            print('i')
            await after.add_reaction(rString)
        await after.add_reaction(f'\N{CHEQUERED FLAG}')
    
@client.event
async def on_message(message):
    #try:
        print(message.content)
        if message.author == client.user:
            return
        
        commandArgs = getArgs(message)
        command = commandArgs[0].lower()

        if  command in COMMANDFUNCTION:
            await COMMANDFUNCTION[command](message, commandArgs)
            return

        command = '!waifupoll'
        if  command in message.content.lower():
            print('sending')
            channel = discord.utils.get(message.guild.channels, name = 'waifu-rating')
            print(channel.name)
            pins = await channel.pins()
            
            pin = pins[0]
            if  len(message.content) > len(command):
                indexString = message.content[len(command) + 1:].rstrip()
                pin = pins[int(indexString)]
            print(pin.content)
            await make_file(pin)
            await message.channel.send(content = WAIFU_REPLY, file = discord.File('waifupoll.txt'))
        
           
        
        
    #except Exception as e:
    #    print(e)
    #    exit(-1)
async def handleHeadpat(message, args):
    command = args[0].lower()
    if len(args) > 2:
        commandHelper = args[1].lower()
        args[1] = args[2]
        args[0] = args[0] + commandHelper
        await COMMANDFUNCTION[command+commandHelper](message, args)        
    elif len(args) == 1:
        await COMMANDFUNCTION[command+'get'](message, args)
    else:
        response = "That isn't how it works. Check !usage " + command
        message.reply(response)


async def handleHeadpatRemoveImage(message, args):
    url = args[1]
    await message.reply(await removeImage(url, message))

async def handleHeadpatAddImage(message, args):
    url = args[1]
    await message.reply(await addImage(url, message))

async def handleHeadpatGet(message, args):
    embed = discord.Embed()
    try:
        while(True):
            url = hf.getHeadpat(DATABASE_HOST, message.guild.id)
            if await verifyURL(url):
                embed.set_image(url=url)
                break
            else:
                await removeImage(url, message)                     
    except Exception as e:
        print(e)
        setDefaultHeadpat(embed)

    await message.reply('There there... Have a headpat, ' + message.author.display_name, embed = embed)

async def handleUsage(message, args):
    helpCommand = ''

    if(len(args) > 1):
        helpCommand = args[1].lower()

    if(helpCommand in USAGE):
        await message.reply(USAGE[helpCommand])
    else:
        await message.reply(DEFAULTUSAGE)

def getArgs(message):
    return message.content.split(' ')

def getArg(command, index):
    return command.split(' ')[index]

def setDefaultHeadpat(embed):
    embed.set_image(url = 'https://i.pinimg.com/originals/99/4b/4e/994b4e0be0832e8ebf03e97a09859864.jpg')
    embed.set_footer(text = 'There is no headpat')

async def setImage(url, urls):
    if not await verifyURL(url):
        return REPLY['urlbroken']
    if url +'\n' in urls:
        return REPLY['existingurl']
    urls[random.randrange(len(urls))] = url + '\n'
    await setWaifuURLs(urls)
    return ''

async def removeImage(url, message):
    if(hf.removeHeadpat(DATABASE_HOST, message.guild.id, url)):
        return REPLY['removeimage']
    else:
        return REPLY['imagedne']

async def addImage(url, message):
    if not await verifyURL(url):
        return REPLY['urlbroken']
    added = hf.addHeadpat(DATABASE_HOST, message.guild.id, url)
    if added:
        return REPLY['addimage']
    return REPLY['existingurl']

async def verifyURL(url):
    try:
        image_formats = ("image/png", "image/jpeg", "image/jpg", "image/gif")
        r = urllib.request.urlopen(url)
        print(r.headers['content-type'])
        if r.headers["content-type"] in image_formats:
            return True  
        return False
    except Exception as e:
        print(e)
        return False
    return True

async def make_file(message):
    message = await message.channel.fetch_message(message.id)
    print(message.reactions)
    f = open("waifupoll.txt", "w")
    for i in range(10):
        rString = f'1️\N{COMBINING ENCLOSING KEYCAP}'
        count = 0
        #await message.add_reaction(emoji)
        for r in message.reactions:
            if r.emoji[0] == str(i):
                count = r.count - (1 if r.me else 0)
        f.write(f'{count}\n')
    f.close()
    return 

COMMANDFUNCTION = {
    '!usage' : handleUsage,
    '!headpat' : handleHeadpat,
    '!headpataddimage' : handleHeadpatAddImage,
    '!headpatget' : handleHeadpatGet,
    '!headpatremoveimage' : handleHeadpatRemoveImage
} 

client.run(TOKEN)