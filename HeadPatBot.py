# bot.py
import os
import random
import urllib
import HelpFunctions as hf
import traceback
import RoleControl as rc
import discord
from discord.ext import commands
from discord.ext.commands import Bot
from configparser import ConfigParser

config = ConfigParser()
config.read('config.ini')

TOKEN = os.environ['DISCORD_TOKEN']
DATABASE_HOST = os.environ['DATABASE_URL']
bot = commands.Bot(command_prefix=commands.when_mentioned_or('$'))

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
    'waifuendpoll' : ('Wait a bit...'),
    'unhandled' : 'Something happened, report this to the devs\nhttps://github.com/SayethWe/HeadpatDiscordBot/issues',
    'unfinishedpoll' : 'Nah uh uh, you have an unfinsihed poll, call !waifu endpoll starting a new one',
    'novalidpicks' : 'Not enough waifu, MOAR needed.\nYour waifus need a break, you know.',
    'endedpoll' : 'We already recorded and finished the poll. You can use !waifu pollresults to get results from now on',
    'nopollmade' : 'You gotta start a poll first',
    'polldne' : "The message with the previous poll might have been deleted, I can't find it",
    'forbidden' : "You can't do that, go ask a mod",
    'waifuaddcsv' : 'Waifus added. So much waifu. Fwoooooo'
}

ACTIVITY = (discord.Game(name = "with your waifus while you're away. | !usage"),discord.Activity(type=discord.ActivityType.watching,name='your waifus for you | !usage'))


@bot.event
async def on_ready():
    hf.createTables(DATABASE_HOST)

    await bot.change_presence(activity=ACTIVITY[random.randint(0,len(ACTIVITY)-1)])

    for guild in bot.guilds:

        print(
            f'{bot.user} is connected to the following guild:\n'
            f'{guild.name}(id: {guild.id})'
        )

@bot.event
async def on_message_edit(before, after):
    print((not before.pinned) and after.pinned)
    print(after.channel.name)
    if((not before.pinned) and after.pinned and after.channel.name == 'waifu-rating'):
        for i in range(10):
            rString = f'{i}\N{COMBINING ENCLOSING KEYCAP}'
            print('i')
            await after.add_reaction(rString)
        await after.add_reaction(f'\N{CHEQUERED FLAG}')

class TestCommands(commands.Cog):
    """Testing Commands for Testing Things"""

    @commands.command()
    async def test(self, ctx, *args):
        """check the handed arguments"""
        print(ctx)
        await ctx.send('{} arguments: {}'.format(len(args), ', '.join(args)))

    @commands.command()
    async def testSubs(self, ctx, *args):
        """See how subarguments work"""
        subs={
         '1':"one",
         '2':"two"
        }
        if len(args) > 0:
            sub=args[0]
            if sub in subs:
                await ctx.send('{} and {}'.format(subs[sub],', '.join(args[1:])))
        await ctx.send('Test successful?')

async def handleCallCommandFunction(message, args):
    command = args[0].lower()
    if command in COMMANDFUNCTION:
        if rc.ROLECONTROLDEFAULT[command](message):
            if len(args) >= REQLENGTH[command]:
                await COMMANDFUNCTION[command](message, args)
            else:
                await handleError(message, args)
        else:
            await message.reply(REPLY['forbidden'])
    else:
        await handleError(message, args)

def checkValidSubCommand(args):
    return (args[0] + args[1]).lower() in COMMANDFUNCTION

class Headpats(commands.Cog):
    """For when you really need that headpat"""

    @commands.command()
    async def headpat(self, ctx, *args):
        """Retreive a headpat"""
        message=ctx.message
        if len(args) > 0 and checkValidSubCommand(args):
            await handleSubCommand(message, args)
        else:
            await handleHeadpatGet(message, args)

    @commands.command()
    async def addHeadpat(self, ctx, *args):
        """Add a headpat to fetch later"""
        pass

    @commands.command()
    @commands.check_any(rc.allowMod())
    async def removeHeadpat(ctx, *args):
        """Allows a mod to remove an unwholesome headpat"""
        pass

class WaifuPolls(commands.Cog):
    """For Running Polls and selecting the best waifu"""

    @commands.command()
    async def addWaifu(self, ctx, link, *args):
        name=' '.join(args)
        await ctx.send('Cannot add {} at {} yet'.format(name, link))

    @commands.command()
    @commands.check_any(rc.allowMod())
    async def removeWaifu(self, ctx,*args):
        name=' '.join(args)
        await ctx.send('Cannot remove {} at {} yet'.format(name, link))

    @commands.command()
    async def endpoll(self, ctx):
        """Finish the last poll round"""
        pass

    @commands.command()
    @commands.check_any(rc.allowMod())
    async def startPoll(self, ctx):
        """start a poll round"""
        pass

async def handleWaifuAdd(message, args):
    code = waifuAdd(message, [args[1], 0, 1, args[2]])
    await message.reply(REPLY['waifuadd'])

def waifuAdd(message, args):
    name = args[0].replace('_', ' ')
    immunity = int(args[1])
    probability = float(args[2])
    url = args[3]
    code = hf.addContestant(DATABASE_HOST, message.guild.id, name, immunity, probability, url)
    return code


async def handleError(message, args):
    usage = getUsage(args)
    response = "That isn't how it works. Here:\n" + usage
    await message.reply(response)

def loadUsage():
    #Eventual place to load in the usage command returns
    #from readme.md or other storage text file
    return USAGE

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
    try:
        poll = await message.channel.send(REPLY['waifustartpoll'])
        roundID, contestantNo = hf.startRound(DATABASE_HOST, message.guild.id, f'{poll.channel.id};{poll.id}')
    except Exception as e:
        print(e)
        await poll.delete()
        await message.reply(REPLY['unhandled'])
        return
    await poll.delete()
    if roundID == -1:
        await message.reply(REPLY['unfinishedpoll'])
        return
    if roundID == -2:
        await message.reply(REPLY['novalidpicks'])
        return

    reply = await message.channel.send(f'[ROUND {roundID}] '+DEFAULTPOLLMESSAGE, file = discord.File('poll.jpg'))
    hf.updateMessageID(DATABASE_HOST, message.guild.id, f'{reply.channel.id};{reply.id}', roundID)
    for i in range(contestantNo):
        rString = f'{i}\N{COMBINING ENCLOSING KEYCAP}'
        await reply.add_reaction(rString)
    await reply.add_reaction(f'\N{CHEQUERED FLAG}')

async def handleWaifuEndPoll(message, args):
    try:
        reply = await message.channel.send(REPLY['waifuendpoll'])
        roundVal = hf.getRoundMessage(DATABASE_HOST, message.guild.id)
    except Exception as e:
        print(e)
        await reply.delete()
        await message.reply(REPLY['unhandled'])
        return

    if roundVal == -1:
        await reply.delete()
        await message.reply(REPLY['endedpoll'])
        return
    if roundVal == -2:
        await reply.delete()
        await message.reply(REPLY['nopollmade'])

    roundValues = roundVal[0]
    roundNum = roundVal[1]

    print(roundValues)
    messageID = roundValues[2].split(';')
    channel = bot.get_channel(int(messageID[0]))
    if not channel:
        print('NO CHANNEL')
        await reply.delete()
        await message.reply(REPLY['polldne'])
    poll = await channel.fetch_message(int(messageID[1]))
    if not poll:
        print('NO MESSAGE')
        await reply.delete()
        await message.reply(REPLY['polldne'])

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
    await reply.delete()
    await message.reply('I present to you, the results', files = [discord.File('plot1.jpg'), discord.File('plot2.jpg')])




async def handleSubCommand(message, args):
    assert(len(args) > 1)
    command = args[0].lower()
    commandHelper = args[1].lower()
    args = [args[0] + commandHelper] + (args[2:])
    print(args)
    await handleCallCommandFunction(message, args)

async def handleWaifuPollResults(message, args):
    roundNum = -1
    reply = await message.channel.send(REPLY['waifuendpoll'])
    if len(args) > 1 and args[1].isnumeric():
        roundNum = args[1]
    else:
        roundNum = hf.getRoundNum(DATABASE_HOST, message.guild.id)
    data = hf.getRound(DATABASE_HOST, message.guild.id, roundNum)
    if data == -1:
        await reply.delete()
        await message.reply(REPLY['noround'])

    hf.getRoundResults(data[1], data[0], roundNum)
    await reply.delete()
    await message.reply('I present to you, the results', files = [discord.File('plot1.jpg'), discord.File('plot2.jpg')])


async def handleWaifuAddCSV(message : discord.Message, args):
    attachments = message.attachments
    if len(attachments) == 0:
        await handleError(message, args)
        return
    baseDir = os.path.dirname(__file__)
    csvPath = os.path.join(baseDir, f'waifu{message.guild.id}.csv')
    await attachments[0].save(csvPath)
    with open(csvPath, 'r') as f:
        for line in f.readlines():
            print(line)
            args = line.split(',')
            code = waifuAdd(message, args)
    await message.reply(REPLY['waifuaddcsv'])

async def handleHeadpatRemoveImage(message, args):
    url = args[1]
    await message.reply(await removeImage(url, message))

async def handleHeadpatAddImage(message, args):
    url = args[1]
    reply = headpatAddImage(message,url)
    await message.reply(reply)

def headpatAddImage(message, url):
    reply = REPLY['unhandled']
    if not verifyURL(url):
        reply =  REPLY['urlbroken']
    else:
        added = hf.addHeadpat(DATABASE_HOST, message.guild.id, url)
        if added == 0:
            reply = REPLY['addimage']
        elif added == -1:
            reply = REPLY['existingurl']
    return reply

async def handleHeadpatGet(message, args):
    embed = discord.Embed()
    try:
        while(True):
            url = hf.getHeadpat(DATABASE_HOST, message.guild.id)
            if not url:
                setDefaultHeadpat(embed)
                break
            elif verifyURL(url):
                embed.set_image(url=url)
                break
            else:
                if await removeImage(url, message) == REPLY['imagedne']:
                    print('FAILED_REMOVE')
                    setDefaultHeadpat(embed)
                    break

    except Exception as e:
        print(e)
        setDefaultHeadpat(embed)

    await message.reply('There there... Have a headpat, ' + message.author.display_name, embed = embed)

@bot.command()
async def usage(ctx, *args):

    await ctx.message.reply(getUsage(args[1:]))

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

def verifyURL(url):
    try:
        image_formats = ("image/png", "image/jpeg", "image/jpg", "image/gif")
        r = urllib.request.urlopen(url)
        print(r.headers['content-type'])
        if r.headers["content-type"] in image_formats:
            return True
        return False
    except Exception as e:
        traceback.print_exc()
        return False

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
    '!usage' : usage,
    '!headpataddimage' : handleHeadpatAddImage,
    '!headpatget' : handleHeadpatGet,
    '!headpatremoveimage' : handleHeadpatRemoveImage,
    '!waifuadd' : handleWaifuAdd,
    '!waifustartpoll' : handleWaifuStartPoll,
    '!waifuendpoll' : handleWaifuEndPoll,
    '!waifuaddcsv' : handleWaifuAddCSV,
    '!waifupollresults' : handleWaifuPollResults
}

REQLENGTH = {
    '!usage' : 1,
    '!headpat' : 1,
    '!headpataddimage' : 2,
    '!headpatremoveimage' : 2,
    '!waifu' : 2,
    '!waifuadd' : 3,
    '!waifustartpoll' : 1,
    '!waifuendpoll' : 1,
    '!waifuaddcsv' : 1,
    '!waifupollresults' : 1
}

bot.add_cog(TestCommands())
bot.add_cog(Headpats())
bot.add_cog(WaifuPolls())
bot.run(TOKEN)
