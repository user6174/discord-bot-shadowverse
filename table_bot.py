import discord  # https://discordpy.readthedocs.io/en/latest/api.html
from Table import *

table = Table()


def send_join(user):
    if table.add(user):
        return discord.Embed(title="Registered {}!".format(user)), "Congratulations, you registered!"
    return discord.Embed(title="You are already registered."), ""


def send_leave(user):
    if table.remove(user):
        return discord.Embed(title="Unregistered {} ;_;".format(user)), "Ikanaide..."
    return discord.Embed(title="You are already unregistered."), ""


def send_player_list():
    result = discord.Embed(title="Currently registered players:")
    for i in range(len(table)):
        result.add_field(name="{}.".format(i + 1), value=table[i], inline=True)
    return result
