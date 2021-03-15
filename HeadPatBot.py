# bot.py
import os
import random
import urllib
import HelpFunctions as hf
import gacha
import responses
from responses import Responses as rsp
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

ERRORS_HANDLED = {
    'MissingRequiredArgument' : "That's not enough information! Come back when you have more",
    'CheckFailure' : "Something tells me I'm not supposed to do this for you right now.",
    'CheckAnyFailure' : "You're not allowed to do that. Go find someone who is.",
    'CommandNotFound' : "That's not a command I recognize. Maybe you should ask for help?"
}

ACTIVITY = (discord.Game(name = "with your waifus while you're away. | !help"),
discord.Activity(type=discord.ActivityType.watching,name='your waifus for you | !help'))

TICKETS_PER_POLL = 2;

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
    #print(ctx)
    #print(error)
    key = type(error).__name__
    print(key)
    if not key in ERRORS_HANDLED:
        await ctx.reply(getResponse(rsp.ERROR_UNHANDLED)+"\n{}".format(error))
    else:
        await ctx.reply(ERRORS_HANDLED[key])


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

    Images may 403 and are not checked - be safe, use an imgur image address"""
    name=name.replace("'","") #make sure we don't breake anything in postgres
    code = hf.addContestant(DATABASE_HOST, ctx.guild.id, name, 0, 1, link)
    await ctx.reply(getResponse(rsp.WAIFU_ADD))

@waifu.command()
@commands.check_any(rc.allowMod())
async def remove(ctx, *, name : str):
    """remove a waifu from the poling system.

    not required for eliminated waifus, those are kept to prevent duplicates
    """
    hf.deleteContestant(DATABASE_HOST,ctx.guild.id,name)
    await ctx.reply(getResponse(rsp.WAIFU_REMOVE))

@waifu.command()
@commands.check_any(rc.allowMod())
async def startPoll(ctx):
    """start a poll round"""
    try:
        poll = await ctx.send(getResponse(rsp.WAIFU_POLL_START))
        roundID, contestantNo = hf.startRound(DATABASE_HOST, ctx.guild.id, f'{poll.channel.id};{poll.id}')
    except Exception as e:
        print(e)
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
        print(e)
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

    print(roundValues)
    messageID = roundValues[2].split(';')
    channel = bot.get_channel(int(messageID[0]))
    if not channel:
        print('NO CHANNEL')
        await reply.delete()
        await ctx.reply(getResponse(rsp.WAIFU_POLL_END_DELETED))
    poll = await channel.fetch_message(int(messageID[1]))
    if not poll:
        print('NO MESSAGE')
        await reply.delete()
        await ctx.reply(getResponse(rsp.WAIFU_POLL_END_DELETED))

    votes = []

        #await message.add_reaction(emoji)
    for r in poll.reactions:
        for i in range(len(roundValues[0])):
            if r.emoji[0] == str(i):
                count = r.count - (1 if r.me else 0)
                votes.append(count)
        #print(r.emoji)
        if r.emoji == f'\N{CHEQUERED FLAG}':
            #give out tickets for participation
            users=await r.users().flatten()
            print('flag found! has {} reactions'.format(r.count))
            for user in users:
                print('reaction from {}'.format(user.id))
                #give em tickets!
                balance=hf.fetchUserInfo(DATABASE_HOST,ctx.guild.id,user.id)[0]
                print('{} has {} tickets (going to {}) and {} score'.format(user.id,balance[0],balance[0]+TICKETS_PER_POLL,balance[1]))
                hf.updateTickets(DATABASE_HOST,ctx.guild.id,user.id,balance[0]+TICKETS_PER_POLL)
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
        await ctx.reply(getResponse(rsp.WAIFU_ADD_CSV_MISSING))
        return
    baseDir = os.path.dirname(__file__)
    csvPath = os.path.join(baseDir, f'waifu{ctx.guild.id}.csv')
    await attachments[0].save(csvPath)
    with open(csvPath, 'r') as f:
        for line in f.readlines():
            print(line)
            args = line.split(',')
            code = hf.addContestant(DATABASE_HOST, ctx.guild.id, args[0],args[1],args[2],args[3])
    await ctx.reply(getResponse(rsp.WAIFU_ADD_CSV))

### Gacha Commands

@waifu.command()
#@commands.cooldown(2,16*3600,commands.BucketType.user)
async def pull(ctx, tickets : int):
    balance = hf.fetchUserInfo(DATABASE_HOST, ctx.guild.id, ctx.author.id)[0]
    if balance[0] < tickets:
        await ctx.reply(getResponse(rsp.GACHA_PULL_INSUFFICIENT))
    elif tickets <= 0:
        await ctx.reply(getResponse(rsp.GACHA_PULL_NONPOSITIVE))
    else:
        contestants = hf.claimableWaifus(DATABASE_HOST, ctx.guild.id)
        names = [row[0] for row in contestants]
        challenge = [row[1] for row in contestants]
        pull = gacha.pull(names, challenge, tickets)
        hf.claimWaifu(DATABASE_HOST, ctx.guild.id, ctx.author.id, pull)
        hf.updateTickets(DATABASE_HOST, ctx.guild.id, ctx.author.id, balance[0]-tickets)
        await ctx.reply(getResponse(rsp.GACHA_PULL).format(pull))

@waifu.command()
async def challenge(ctx, other):
    pass

@waifu.command()
async def info(ctx, *, name : str):
    challenge = hf.getChallenge(DATABASE_HOST, ctx.guild.id, name)[0][0]
    image = hf.getImageURL(DATABASE_HOST, ctx.guild.id, name)
    claimID=int(hf.whoClaimed(DATABASE_HOST, ctx.guild.id, name)[0])
    print(claimID)
    #print(await bot.fetch_user(132650983011385347))
    claimaint = await bot.fetch_user(claimID)
    print(image)
    embed = discord.Embed()
    embed.set_image(url=image);
    await ctx.reply(f"{name}:\n  Strength:{challenge}\n  Claimed by:{claimaint.display_name}", embed=embed)

@waifu.command()
async def balance(ctx):
    balance = hf.fetchUserInfo(DATABASE_HOST, ctx.guild.id, ctx.author.id)[0]
    #print(balance)
    await ctx.reply('you have {} tickets and have scored {} points'.format(balance[0],balance[1]))

### Helper Functions and Legacy Code

def setDefaultHeadpat(embed):
    embed.set_image(url = 'https://i.pinimg.com/originals/99/4b/4e/994b4e0be0832e8ebf03e97a09859864.jpg')
    embed.set_footer(text = 'There is no headpat')

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

def getResponse(key : str):
    return random.choice(responses.REPLY[key])

bot.run(TOKEN)
