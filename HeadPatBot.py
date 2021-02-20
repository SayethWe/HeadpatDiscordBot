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

DEFAULTPOLLMESSAGE = ("Here's your round. But we all know that I'm the only one who deserves any votes.")

DEFAULTUSAGE = (
            'Commands list:\n'
            '    !usage\n'
            '    !waifu\n' 
            '    !headpat\n'
            'Extra Functionality:\n'
            '    poll [DEPRECATED]\n' 
            '!usage <any of the above commands or functionalities>')

USAGE = {
    '!usage' : 'de nada, nuh uh',
    '!headpat' : '!headpat <nothing>/setimage <url>/addimage/removeimage <url>\nWant headpats? Why not? Have Some!',
    '!waifupoll' : '!waifupoll /<poll number (goes in reverse order, 0 is latest)>\nResults results results.',
    'poll' : ('Pinning a message in a channel called waifu-rating will cause it to be reacted to with 1-10 and '
    'the chequered flag\nEasy polls for lazy folk [DEPRECIATED]'),
    '!waifu' : ('!waifu add/poll\n'
                'Easy polls for lazy folk, recommended use with waifus\n'),
    '!waifuadd' : ('!waifu add <name_underscores_for_spaces> <imageurl aspect ratio about 1:3>\n'
                   'Fulfill your deepest, darkest dream: being wholesome\n'
                   'Adds waifus to the poll candidates'),
    '!headpataddimage' : "!headpat addimage <url>\nYou want some of that action, don't you?",
    '!headpatsetimage' : ("!headpat setimage <url>\nThe headpat equivalent of a shotgun with a blindfold\n"
                          "Some random image will be removed, and replaced with yours\n"
                          "Overusing this is bad. Don't be bad"),
    '!headpatremoveimage' : ("")
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
    'removeimage': ("Ok, it's gone\n"
                    "It's not coming back..."),
    'imagedne': ("I don't have that one.\n"
                 "Do you? :face_with_hand_over_mouth:"),
    'waifuaddexisting' : ("They're in there, baka!\n"
                          "本当に何、この状況！:anger:"),
    'waifuadd' : ("Waifu Waifu Waifu! More Waifu!\n"
                  "They've been added to the pool"),
    'waifustartpoll' : ('Just a sec...'),
    'waifuendpoll' : ('Wait a bit...')
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
            await handleCallCommandFunction(message, commandArgs)

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
        
           
async def handleCallCommandFunction(message, args):
    command = args[0].lower()
    if command not in COMMANDFUNCTION or len(args) < REQLENGTH[command]:
        await handleError(message, args)
    else:   
        await COMMANDFUNCTION[command](message, args)

def checkValidSubCommand(args):
    return (args[0] + args[1]).lower() in COMMANDFUNCTION

async def handleHeadpat(message, args):
    if len(args) > 1 and checkValidSubCommand(args):
        await handleSubCommand(message, args)
    else:
        await handleHeadpatGet(message, args)
    
async def handleWaifu(message, args):
    if len(args) > 1  and checkValidSubCommand(args):
        await handleSubCommand(message, args)
    else:
        await handleError(message, args)

async def handleWaifuAdd(message, args):
    if(len(args) < 3):
        await handleError(args)
    name = args[1].replace('_', ' ')
    url = args[2]
    hf.addContestant(DATABASE_HOST, message.guild.id, name, url)
    await message.reply(REPLY['waifuadd'])
    

async def handleError(message, args):
    usage = getUsage(args)
    response = "That isn't how it works. Here:\n" + usage
    await message.reply(response)

def getUsage(args):
    if len(args) == 0:
        return DEFAULTUSAGE
    command = args[0].lower()
    if command in USAGE:
        if len(args) > 1:
            helperCommand = command + args[1].lower()
            print(helperCommand)
            if helperCommand in USAGE:
                return USAGE[helperCommand]
        return USAGE[command]
    return DEFAULTUSAGE

async def handleWaifuStartPoll(message, args):
    #try:
    poll = await message.channel.send(REPLY['waifustartpoll'])
    roundID, contestantNo = hf.startRound(DATABASE_HOST, message.guild.id, f'{poll.channel.id};{poll.id}')
    #except Exception as e: 
    #    print(e)
    #    await message.reply('Something happened')
    #    return
    if roundID == -1:
        await message.reply('Something happened')
        return
    await poll.delete()
    reply = await message.channel.send(f'[ROUND {roundID}] '+DEFAULTPOLLMESSAGE, file = discord.File('poll.jpg'))
    hf.updateMessageID(DATABASE_HOST, message.guild.id, f'{reply.channel.id};{reply.id}', roundID)
    for i in range(contestantNo):
        rString = f'{i}\N{COMBINING ENCLOSING KEYCAP}'
        await reply.add_reaction(rString)
    await reply.add_reaction(f'\N{CHEQUERED FLAG}')

async def handleWaifuEndPoll(message, args):
    #try:
        roundValues, roundNum = hf.getRoundMessage(DATABASE_HOST, message.guild.id)
        if roundValues == -1:
            await message.reply('Something happened')
            return   
        print(roundValues)
        messageID = roundValues[2].split(';')
        channel = client.get_channel(int(messageID[0]))
        poll = await channel.fetch_message(int(messageID[1]))
        votes = []
        for i in range(len(roundValues[0])):
            rString = f'1️\N{COMBINING ENCLOSING KEYCAP}'
            count = 0
            #await message.add_reaction(emoji)
            for r in poll.reactions:
                if r.emoji[0] == str(i):
                    count = r.count - (1 if r.me else 0)
            votes.append(count)
        print(votes)
        hf.endRound(DATABASE_HOST, message.guild.id, votes, roundValues[0], roundNum)
        await message.reply('I present to you, the results', files = [discord.File('plot1.jpg'), discord.File('plot2.jpg')])


        

async def handleSubCommand(message, args):
    assert(len(args) > 1)
    command = args[0].lower()
    commandHelper = args[1].lower()
    args = [args[0] + commandHelper] + (args[2:])
    print(args)
    await handleCallCommandFunction(message, args)    
        


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
    await message.reply(getUsage(args[1:]))

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
    '!headpatremoveimage' : handleHeadpatRemoveImage,
    '!waifu' : handleWaifu,
    '!waifuadd' : handleWaifuAdd,
    '!waifustartpoll' : handleWaifuStartPoll,
    '!waifuendpoll' : handleWaifuEndPoll
} 

REQLENGTH = {
    '!usage' : 1,
    '!headpat' : 1,
    '!headpataddimage' : 2,
    '!headpatremoveimage' : 2,
    '!waifu' : 2,
    '!waifuadd' : 3,
    '!waifustartpoll' : 1,
    '!waifuendpoll' : 1
}

client.run(TOKEN)