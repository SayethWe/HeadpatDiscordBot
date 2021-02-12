# bot.py
import os
import random
import urllib

import discord
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')

PATH_OF_GIT_REPO = os.path.dirname(os.path.realpath('waifu_urls.txt'))
TOKEN = os.environ['DISCORD_TOKEN']
client = discord.Client()

WAIFU_REPLY = config.get('DEFAULT', 'WAIFU_REPLY')

USAGE = {
    '!headpat' : '!headpat /setimage <url>/addimage <url>/removeall\nWant headpats? Why not? Have Some!',
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
                    "If you've got the time, maybe you should spend it on more worthwhile images! :anger:")
}

@client.event
async def on_ready():
    try:
        cp = cmd.run('cd ' + PATH_OF_GIT_REPO, check=True, shell=True)
        print("cp", cp)
        cmd.run('git init', check = True, shell = True)
        cmd.run('git config --global user.email = achintya194@gmail.com', check = True, shell = True)
        cmd.run('git config --global user.name = arock19', check = True, shell = True)
        cmd.run('git remote add origin https://github.com/SayethWe/HeadpatDiscordBot', check=True, shell=True)
    except:
        print('git init failed')
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
                response = "That isn't how it works. Check !usage " + command
                if 'setimage' in message.content.lower():
                    url = message.content[len(command) + 2 + len('setImage'):].rstrip()
                    if(len(urls) == 0):
                        response = await addImage(url, urls)
                        if not response:
                            response = REPLY['setimagenone']
                    else:
                        response = await setImage(url, urls)
                        if not response:
                            response = REPLY['setimage']
                if 'addimage' in message.content.lower():
                    url = message.content[len(command) + 2 + len('addImage'):].rstrip()
                    response = await addImage(url, urls)
                    if not response:
                        response = REPLY['addimage']

                if 'removeall' in message.content.lower():
                    await setWaifuURLs([])
                    response = REPLY['removeall']
                await message.channel.send(response)
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
    if not await verifyURL(url):
        return REPLY['urlbroken']
    if url +'\n' in urls:
        return REPLY['existingurl']
    urls[random.randrange(len(urls))] = url + '\n'
    await setWaifuURLs(urls)
    return ''

async def addImage(url, urls):
    if not await verifyURL(url):
        return REPLY['urlbroken']
    if url +'\n' in urls:
        return REPLY['existingurl']
    urls.append(url + '\n')
    await setWaifuURLs(urls)
    return ''

async def getWaifuURLs():
    with open('waifu_urls.txt', 'r') as f:
        lines = f.readlines()
        return lines

async def verifyURL(url):
    try:
        image_formats = ("image/png", "image/jpeg", "image/jpg", "image/gif")
        r = urllib.request.urlopen(url)
        print(r.headers['content-type'])
        if r.headers["content-type"] in image_formats:
            return True  
        return False
    except Exception as e:
        return False
    return True

async def setWaifuURLs(urls):
    with open('waifu_urls.txt', 'w') as f:
        for url in urls:
            f.write(url)
    print(PATH_OF_GIT_REPO)
    git_push_automation()

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
        
import subprocess as cmd
def git_push_automation():
    try:
        cp = cmd.run('cd ' + PATH_OF_GIT_REPO, check=True, shell=True)
        print("cp", cp)
        cmd.run('git add "waifu_urls.txt"', check=True, shell=True)
        cmd.run('git commit -m "message"', check=True, shell=True)
        cmd.run("git push -u origin master", check=True, shell=True)
        print("Success")
        return True
    except:
        print("Error git automation")
        return False

client.run(TOKEN)