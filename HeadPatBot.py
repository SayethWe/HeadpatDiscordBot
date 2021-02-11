# bot.py
import os
import random

import discord
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')

TOKEN = os.environ['DISCORD_TOKEN']
client = discord.Client()

WAIFU_REPLY = config.get('DEFAULT', 'WAIFU_REPLY')

USAGE = {
    '!headpat' : '!headpat /setimage <url>/addimage <url>/removeall\nWant headpats? Why not? Have Some!',
    '!waifupoll' : '!waifupoll /<poll number (goes in reverse order, 0 is latest)>\nResults results results.',
    'poll' : ('Pinning a message in a channel called waifu-rating will cause it to be reacted to with 1-10 and '
    'the chequered flag\nEasy polls for lazy folk')
}

@client.event
async def on_ready():
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
        
        command = '!usage'
        if  command in message.content.lower():
            helpCommand = ''
            if(len(message.content) > len(command)):
                helpCommand = message.content.lower()[len(command) + 1:].rstrip()
            if(helpCommand in USAGE):
                await message.channel.send(USAGE[helpCommand])
            else:
                await message.channel.send(
                ('Commands list:\n'
                 '      !usage\n'
                 '      !waifupoll\n' 
                 '      !headpat\n'
                 'Extra Functionality:\n'
                 '      poll\n' 
                 '!usage <any of the above commands or functionalities>'))
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
        command = '!headpat'
        if  command in message.content.lower():
            if  len(message.content) > len(command):
                urls = await getWaifuURLs()
                if 'setimage' in message.content.lower():
                    url = message.content[len(command) + 2 + len('setImage'):].rstrip()
                    if(len(urls) == 0):
                        await addImage(url, urls)
                    else:
                        await setImage(url, urls)
                if 'addimage' in message.content.lower():
                    url = message.content[len(command) + 2 + len('addImage'):].rstrip()
                    await addImage(url, urls)

                if 'removeall' in message.content.lower():
                    await setWaifuURLs([])
            else:
                embed = discord.Embed()
                try:
                    embed.set_image(url = random.choice(await getWaifuURLs())[:-1])
                except Exception as e:
                    print(e)
                    embed.set_image(url = 'https://i.pinimg.com/originals/99/4b/4e/994b4e0be0832e8ebf03e97a09859864.jpg')
                    embed.set_footer(text = 'There is no headpat')
                await message.reply('There there... Have a headpat, ' + message.author.display_name, embed = embed)
        
        
    #except Exception as e:
    #    print(e)
    #    exit(-1)

async def setImage(url, urls):
    urls[random.randrange(len(urls))] = url + '\n'
    await setWaifuURLs(urls)
async def addImage(url, urls):
    urls.append(url + '\n')
    await setWaifuURLs(urls)
async def getWaifuURLs():
    with open('waifu_urls.txt', 'r') as f:
        lines = f.readlines()
        return lines


async def setWaifuURLs(urls):
    with open('waifu_urls.txt', 'w') as f:
        for url in urls:
            f.write(url)

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
        


client.run(TOKEN)