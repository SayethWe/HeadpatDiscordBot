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
bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'))

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

ACTIVITY = (discord.Game(name = "with your waifus while you're away. | !help"),
discord.Activity(type=discord.ActivityType.watching,name='your waifus for you | !help'))

### Help Command

class MyHelpCommand(commands.MinimalHelpCommand):
    def __init__(self):
        self.no_category='Commands'
        super().__init__(no_category='Commands')

    async def send_pages(self):
        destination = self.get_destination()
        e = discord.Embed(color=discord.Color.dark_red(), description='Headpat Help: \n\n')
        for page in self.paginator.pages:
            e.description += page
        await destination.send(embed=e)

bot.help_command = MyHelpCommand()

### Events

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
async def on_command_error(ctx,error):
    print(ctx)
    print(error)
    await ctx.reply(error)


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

### Headpat commands

@bot.group()
async def headpat(ctx):
    """For when you really need a headpat"""
    if ctx.invoked_subcommand is None:
        embed = discord.Embed()
        try:
            while(True):
                url = hf.getHeadpat(DATABASE_HOST, ctx.guild.id)
                if not url:
                    setDefaultHeadpat(embed)
                    break
                elif verifyURL(url):
                    embed.set_image(url=url)
                    break
                else:
                    if not hf.removeHeadpat(DATABASE_HOST, message.guild.id, url):
                        print('FAILED_REMOVE')
                        setDefaultHeadpat(embed)
                        break
        except Exception as e:
            print(e)
            setDefaultHeadpat(embed)
        await ctx.reply('There there... Have a headpat, ' + ctx.author.display_name, embed = embed)


@headpat.command()
async def add(ctx, link : str):
    """Add a headpat to fetch later"""
    reply = REPLY['unhandled']
    if not verifyURL(link):
        reply =  REPLY['urlbroken']
    else:
        added = hf.addHeadpat(DATABASE_HOST, ctx.guild.id, link)
        if added == 0:
            reply = REPLY['addimage']
        elif added == -1:
            reply = REPLY['existingurl']
    await ctx.reply(reply)

@headpat.command()
@commands.check_any(rc.allowMod())
async def remove(ctx, link : str):
    """Allows a mod to remove an unwholesome headpat"""
    reply=REPLY['imagedne']
    if(hf.removeHeadpat(DATABASE_HOST, ctx.guild.id, link)):
        reply=REPLY['removeimage']
    await ctx.reply(reply)

### Waifu Commands

@bot.group()
async def waifu(ctx):
    """Maybe return a random waifu?"""
    if ctx.invoked_subcommand is None:
        await ctx.send('waifu command')

@waifu.command()
async def add(ctx, link : str, *, name : str):
    """add a waifu to the poll system

    Images may 403 and are not checked - be safe, use an imgur image address"""
    name=name.replace("'","") #make sure we don't breake anything in postgres
    code = hf.addContestant(DATABASE_HOST, ctx.guild.id, name, 0, 1, link)
    await ctx.reply(REPLY['waifuadd'])

@waifu.command()
@commands.check_any(rc.allowMod())
async def remove(ctx, *, name : str):
    """remove a waifu from the poling system.

    not required for eliminated waifus, those are kept to prevent duplicates
    also, not implemented
    """

    await ctx.send('Cannot remove {} at {} yet'.format(name, link))

@waifu.command()
@commands.check_any(rc.allowMod())
async def startPoll(ctx):
    """start a poll round"""
    try:
        poll = await ctx.send(REPLY['waifustartpoll'])
        roundID, contestantNo = hf.startRound(DATABASE_HOST, ctx.guild.id, f'{poll.channel.id};{poll.id}')
    except Exception as e:
        print(e)
        await poll.delete()
        await ctx.reply(REPLY['unhandled'])
        return
    await poll.delete()
    if roundID == -1:
        await ctx.reply(REPLY['unfinishedpoll'])
        return
    if roundID == -2:
        await ctx.reply(REPLY['novalidpicks'])
        return

    reply = await ctx.send(f'[ROUND {roundID}] '+DEFAULTPOLLMESSAGE, file = discord.File('poll.jpg'))
    hf.updateMessageID(DATABASE_HOST, ctx.guild.id, f'{reply.channel.id};{reply.id}', roundID)
    for i in range(contestantNo):
        rString = f'{i}\N{COMBINING ENCLOSING KEYCAP}'
        await reply.add_reaction(rString)
    await reply.add_reaction(f'\N{CHEQUERED FLAG}')

@waifu.command()
@commands.check_any(rc.allowMod())
async def endPoll(ctx):
    """Finish the last poll round"""
    try:
        reply = await ctx.send(REPLY['waifuendpoll'])
        roundVal = hf.getRoundMessage(DATABASE_HOST, ctx.guild.id)
    except Exception as e:
        print(e)
        await reply.delete()
        await ctx.reply(REPLY['unhandled'])
        return

    if roundVal == -1:
        await reply.delete()
        await ctx.reply(REPLY['endedpoll'])
        return
    if roundVal == -2:
        await reply.delete()
        await ctx.reply(REPLY['nopollmade'])

    roundValues = roundVal[0]
    roundNum = roundVal[1]

    print(roundValues)
    messageID = roundValues[2].split(';')
    channel = bot.get_channel(int(messageID[0]))
    if not channel:
        print('NO CHANNEL')
        await reply.delete()
        await ctx.reply(REPLY['polldne'])
    poll = await channel.fetch_message(int(messageID[1]))
    if not poll:
        print('NO MESSAGE')
        await reply.delete()
        await ctx.reply(REPLY['polldne'])

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
    hf.endRound(DATABASE_HOST, ctx.guild.id, votes, roundValues[0], roundNum)
    await reply.delete()
    await ctx.reply('I present to you, the results', files = [discord.File('plot1.jpg'), discord.File('plot2.jpg')])

@waifu.command()
@commands.check_any(rc.allowMod())
async def addCSV(ctx):
    """Load in a whole FILE worth of Waifus"""
    attachments = ctx.message.attachments
    if len(attachments) == 0:
        await handleError(message, args)
        return
    baseDir = os.path.dirname(__file__)
    csvPath = os.path.join(baseDir, f'waifu{ctx.guild.id}.csv')
    await attachments[0].save(csvPath)
    with open(csvPath, 'r') as f:
        for line in f.readlines():
            print(line)
            args = line.split(',')
            code = hf.addContestant(DATABASE_HOST, ctx.guild.id, args[0],args[1],args[2],args[3])
    await ctx.reply(REPLY['waifuaddcsv'])

### Helper Functions and Legacy Code

async def handleError(message, args):
    usage = getUsage(args)
    response = "That isn't how it works. Here:\n" + usage
    await message.reply(response)

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

bot.run(TOKEN)
