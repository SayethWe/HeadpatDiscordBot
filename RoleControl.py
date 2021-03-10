import os
import discord
from discord.ext import commands


def allowAll(message):
    return True

def allowMod():
    def predicate(ctx):
        permissions = ctx.channel.permissions_for(ctx.author)
        is_mod = permissions.administrator or permissions.manage_guild or permissions.manage_messages
        return is_mod
    return commands.check(predicate)

def allowAdmin(message):
    permissions = message.channel.permissions_for(message.author)
    is_admin = permissions.administrator
    return is_admin

ROLECONTROLDEFAULT = {
    '!usage' : allowAll,
    '!headpat' : allowAll,
    '!headpataddimage' : allowAll,
    '!headpatget' : allowAll,
    '!headpatremoveimage' : allowMod,
    '!waifu' : allowAll,
    '!waifuadd' : allowAll,
    '!waifustartpoll' : allowMod,
    '!waifuendpoll' : allowMod,
    '!waifuaddcsv' : allowMod,
    '!waifupollresults' : allowAll
}
