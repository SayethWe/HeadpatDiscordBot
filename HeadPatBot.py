# bot.py
import os
import random
import urllib
import HelpFunctions as hf
import responses
from responses import Responses as rsp
import traceback
import RoleControl as rc
import discord
from discord.ext import commands
from discord.ext.commands import Bot
from configparser import ConfigParser
import logging
import sys

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
format=logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')

fhandler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
fhandler.setLevel('DEBUG')
fhandler.setFormatter(format)
logger.addHandler(fhandler)

chandler = logging.StreamHandler(stream = sys.stdout)
chandler.setFormatter(format)
chandler.setLevel('INFO')
logger.addHandler(chandler)

config = ConfigParser()
config.read('config.ini')

TOKEN = os.environ['DISCORD_TOKEN']
DATABASE_HOST = os.environ['DATABASE_URL']
bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'))

WAIFU_REPLY = config.get('DEFAULT', 'WAIFU_REPLY')

ERRORS_HANDLED = {
    'MissingRequiredArgument' : "That's not enough information! Come back when you have more",
    'CheckFailure' : "Something tells me I'm not supposed to do this for you right now.",
    'CheckAnyFailure' : "You're not allowed to do that. Go find someone who is.",
    'CommandNotFound' : "That's not a command I recognize. Maybe you should ask for help?"
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

        logger.info(
            f'{bot.user} is connected to the following guild:\n'
            f'{guild.name}(id: {guild.id})'
        )

@bot.event
async def on_command_error(ctx,error):
    logger.debug(ctx)
    logger.error(error)
    key = type(error).__name__
    logger.debug(key)
    if not key in ERRORS_HANDLED:
        await ctx.reply(getResponse(rsp.ERROR_UNHANDLED)+"\n{}".format(error))
    else:
        await ctx.reply(ERRORS_HANDLED[key])

#dinosaurs in the closet best be put to sleep
'''
@bot.event
async def on_message_edit(before, after):
    logger.debug('message was just pinned? '+(not before.pinned) and after.pinned)
    logger.debug('in channel: '+after.channel.name)
    if((not before.pinned) and after.pinned and after.channel.name == 'waifu-rating'):
        for i in range(10):
            rString = f'{i}\N{COMBINING ENCLOSING KEYCAP}'
            logger.debug('i')
            await after.add_reaction(rString)
        await after.add_reaction(f'\N{CHEQUERED FLAG}')
'''


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
                        logger.info('FAILED_REMOVE')
                        setDefaultHeadpat(embed)
                        break
        except Exception as e:
            logger.error(e)
            setDefaultHeadpat(embed)
        await ctx.reply(getResponse(rsp.HEADPAT) + ctx.author.display_name, embed = embed)


@headpat.command()
async def add(ctx, link : str):
    """Add a headpat to fetch later"""
    reply = getResponse(rsp.ERROR_UNHANDLED)
    if not verifyURL(link):
        reply =  getResponse(rsp.HEADPAT_IMAGE_ADD_URL_BROKEN)
    else:
        added = hf.addHeadpat(DATABASE_HOST, ctx.guild.id, link)
        if added == 0:
            reply = getResponse(rsp.HEADPAT_IMAGE_ADD)
        elif added == -1:
            reply = getResponse(rsp.HEADPAT_IMAGE_ADD_URL_EXISTS)
    await ctx.reply(reply)

@headpat.command()
@commands.check_any(rc.allowMod())
async def remove(ctx, link : str):
    """Allows a mod to remove an unwholesome headpat"""
    reply=getResponse(rsp.HEADPAT_IMAGE_REMOVE_EMPTY)
    if(hf.removeHeadpat(DATABASE_HOST, ctx.guild.id, link)):
        reply=getResponse(rsp.HEADPAT_IMAGE_REMOVE)
    await ctx.reply(reply)

### Waifu Commands

@bot.group()
async def waifu(ctx):
    """Run polls to select a server's favorite Waifus"""
    if ctx.invoked_subcommand is None:
        await ctx.send('Incomplete command - check the help documentation')

@waifu.command()
async def add(ctx, link : str, *, name : str):
    """add a waifu to the poll system

    Images may 403 but are checked - to be safe, use an imgur image address"""
    reply = getResponse(rsp.ERROR_UNHANDLED)
    if not verifyURL(link):
        reply = getResponse(rsp.WAIFU_ADD_URL_BROKEN)
    else:
        name=name.replace("'","") #make sure we don't breake anything in postgres
        code = hf.addContestant(DATABASE_HOST, ctx.guild.id, name, 0, 1, link)
        reply = getResponse(rsp.WAIFU_ADD)
        logger.error("ADDCODE:" + str(code))
        if code == -1:
            reply = getResponse(rsp.WAIFU_ADD_EXISTS)
        elif code == -2:
            reply = getResponse(rsp.ERROR_UNHANDLED)
    await ctx.reply(reply)

@waifu.command()
async def list(ctx, excludeElim : bool = True):
    """Get a list of the waifus in the server"""
    text=hf.getWaifuString(DATABASE_HOST,ctx.guild.id, excludeElim)
    await ctx.reply(getResponse(rsp.WAIFU_LIST)+'\n> '+text)

@waifu.command()
@commands.check_any(rc.allowMod())
async def remove(ctx, *, name : str):
    """remove a waifu from the poling system.

    not required for eliminated waifus, those are kept to prevent duplicates
    """
    reply = getResponse(rsp.WAIFU_REMOVE)
    res = hf.deleteContestant(DATABASE_HOST,ctx.guild.id,name)
    if res == -1:
        reply = getResponse(rsp.WAIFU_REMOVE_DNE)
    await ctx.reply(reply)

@waifu.command()
@commands.check_any(rc.allowMod())
async def startPoll(ctx):
    """start a poll round"""
    try:
        poll = await ctx.send(getResponse(rsp.WAIFU_POLL_START))
        roundID, contestantNo = hf.startRound(DATABASE_HOST, ctx.guild.id, f'{poll.channel.id};{poll.id}')
    except Exception as e:
        logger.error(e)
        await poll.delete()
        await ctx.reply(getResponse(rsp.ERROR_UNHANDLED))
        return
    await poll.delete()
    if roundID == -1:
        await ctx.reply(getResponse(rsp.WAIFU_POLL_START_EXISTS))
        return
    if roundID == -2:
        await ctx.reply(getResponse(rsp.WAIFU_POLL_START_EMPTY))
        return

    reply = await ctx.send(f'[ROUND {roundID}] '+getResponse(rsp.WAIFU_POLL_START_SUCCESS), file = discord.File('poll.jpg'))
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
        reply = await ctx.send(getResponse(rsp.WAIFU_POLL_END))
        roundVal = hf.getRoundMessage(DATABASE_HOST, ctx.guild.id)
    except Exception as e:
        logger.error(e)
        await reply.delete()
        await ctx.reply(getResponse(rsp.ERROR_UNHANDLED))
        return

    if roundVal == -1:
        await reply.delete()
        await ctx.reply(getResponse(rsp.WAIFU_POLL_END_CLOSED))
        return
    if roundVal == -2:
        await reply.delete()
        await ctx.reply(getResponse(rsp.WAIFU_POLL_END_EMPTY))

    roundValues = roundVal[0]
    roundNum = roundVal[1]

    logger.debug(roundValues)
    messageID = roundValues[2].split(';')
    channel = bot.get_channel(int(messageID[0]))
    if not channel:
        logger.info('NO CHANNEL')
        await reply.delete()
        await ctx.reply(getResponse(rsp.WAIFU_POLL_END_DELETED))
    poll = await channel.fetch_message(int(messageID[1]))
    if not poll:
        logger.info('NO MESSAGE')
        await reply.delete()
        await ctx.reply(getResponse(rsp.WAIFU_POLL_END_DELETED))

    votes = []
    for i in range(len(roundValues[0])):
        rString = f'1️\N{COMBINING ENCLOSING KEYCAP}'
        count = 0
        #await message.add_reaction(emoji)
        for r in poll.reactions:
            if r.emoji[0] == str(i):
                count = r.count - (1 if r.me else 0)
        votes.append(count)
    logger.debug(votes)
    hf.endRound(DATABASE_HOST, ctx.guild.id, votes, roundValues[0], roundNum)
    await reply.delete()
    await ctx.reply('I present to you, the results', files = [discord.File('plot1.jpg'), discord.File('plot2.jpg')])

@waifu.command()
@commands.check_any(rc.allowMod())
async def addCSV(ctx):
    """Load in a whole FILE worth of Waifus"""
    attachments = ctx.message.attachments
    if len(attachments) == 0:
        await ctx.reply(getResponse(rsp.WAIFU_ADD_CSV_MISSING))
        return
    baseDir = os.path.dirname(__file__)
    csvPath = os.path.join(baseDir, f'waifu{ctx.guild.id}.csv')
    await attachments[0].save(csvPath)
    with open(csvPath, 'r') as f:
        for line in f.readlines():
            logger.debug(line)
            args = line.split(',')
            code = hf.addContestant(DATABASE_HOST, ctx.guild.id, args[0],args[1],args[2],args[3])
    await ctx.reply(getResponse(rsp.WAIFU_ADD_CSV))

@waifu.command()
@commands.check_any(rc.allowMod())
async def exportCSV(ctx):
    """exports all your waifus at once."""
    contestants=hf.getContestants(DATABASE_HOST, ctx.guild.id)
    lines = [",".join(map(str,row)) for row in contestants]
    logger.debug(lines)

    baseDir = os.path.dirname(__file__)
    fileName=f'waifu{ctx.guild.id}export.csv'
    csvPath = os.path.join(baseDir, fileName)

    with open(csvPath, 'w') as f:
        for line in lines:
            if not line[-1] == '\n':
                line = line+'\n'
            f.write(line)
    await ctx.reply(getResponse(rsp.WAIFU_GET_CSV), files=[discord.File(fileName)])


### Helper Functions and Legacy Code

def setDefaultHeadpat(embed):
    embed.set_image(url = 'https://i.pinimg.com/originals/99/4b/4e/994b4e0be0832e8ebf03e97a09859864.jpg')
    embed.set_footer(text = 'There is no headpat')

def verifyURL(url):
    try:
        image_formats = ("image/png", "image/jpeg", "image/jpg", "image/gif")
        r = urllib.request.urlopen(url)
        logger.debug(r.headers['content-type'])
        if r.headers["content-type"] in image_formats:
            return True
        return False
    except Exception as e:
        traceback.print_exc()
        return False

def getResponse(key : str):
    return random.choice(responses.REPLY[key])

bot.run(TOKEN)
