# bot.py
import os

import discord

TOKEN = os.environ['DISCORD_TOKEN']

client = discord.Client()
WAIFU_REPLY = 'Sure. Here are the last waifu poll\'s results:\n'

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
        command = '!waifupoll'
        if  command in message.content.lower():
            print('sending')
            channel = discord.utils.get(message.guild.channels, name = 'waifu-rating')
            print(channel.name)
            pins = await channel.pins()
            
            pin = pins[0]
            if(len(message.content) > len(command)):
                indexString = message.content[len(command) + 1].rstrip()
                pin = pins[int(indexString)]
            print(pin.content)
            await make_file(pin)
            await message.channel.send(content = WAIFU_REPLY, file = discord.File('waifupoll.txt'))
        command = '!headpat'
        if  command in message.content.lower():
            message.reply('There there... Have a headpat, ' + message.author.display_name)
    #except Exception as e:
    #    print(e)
    #    exit(-1)

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