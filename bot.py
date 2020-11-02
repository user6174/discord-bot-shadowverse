#!/usr/bin/env python3
import io
import os
import sys
import time
import json
import discord
import aiohttp
from natsort import natsorted

from Card import EXPANSIONS
from discord.ext import commands
from emoji import demojize, emojize
from CardMsg import PicMsg, InfoMsg, VoiceMsg
from MyMsg import chr_to_emoji, NO_HELP, LIB, log, bot, hyperlink, has_help, MyMsg, MatchesMsg, JcgMsg, HelpMsg, \
    int_to_emoji

print(sys.executable)
print(os.path.abspath(__file__))
print(*sys.argv)

MAINTAINER_ID = 186585846906880001
MAX_MATCHES = 11

DEV = 1
# DEV = 0  # uncomment on raspberry
with open(f'token_{"testing" if DEV else "main"}.txt', 'r') as txt:
    TOKEN = txt.readline()


async def search(ctx, *search_terms, attrs, lax):
    search_terms = ' '.join(search_terms)
    if attrs:
        matches = LIB.search_by_attributes(search_terms)
    else:
        matches = LIB.search_by_name(search_terms, lax=lax)
        if not matches and not lax:
            matches = LIB.search_by_name(search_terms, lax=True)
        if not matches:
            matches = LIB.search_by_attributes(search_terms)
    if len(matches) < 2 or len(matches) > MAX_MATCHES:
        return matches
    else:
        matches_obj = MatchesMsg(ctx, matches)
        await matches_obj.dispatch()
        return await matches_obj.wait_for_toggle()


async def deck_hash_assets(deck_hash):
    async with aiohttp.ClientSession() as s:
        async with s.post('https://shadowverse-portal.com/api/v1/deck_code/publish?format=json&lang=en',
                          data={'hash': deck_hash}) as r:
            deck_code = json.loads(await r.text())["data"]["deck_code"]
        deck_url = f'https://shadowverse-portal.com/deck/{deck_hash}?lang=en'
        async with s.get('https://shadowverse-portal.com/image/1?lang=en', headers={'referer': deck_url}) as r:
            deck_img = io.BytesIO(await r.read())
    return deck_code, deck_url, deck_img


async def card_commands_template(ctx, msg_maker, *args):
    flags = tuple(filter(lambda x: x in ('-l', '--lax', '-a', '--attrs'), args))
    search_terms = tuple(filter(lambda x: x not in flags, args))
    attrs = '-a' in flags or '--attrs' in flags
    lax = '-l' in flags or '--lax' in flags
    matches = await search(ctx, *search_terms, attrs=attrs, lax=lax)
    if len(matches) == 1:
        card_msg = msg_maker(ctx, matches[0])
        await card_msg.dispatch()
    else:
        await ctx.send(embed=discord.Embed(title=f'{(len(matches))} matches found.'))


# COMMANDS #############################################################################################################

@bot.command(help=NO_HELP)
async def info(ctx, *args):
    await card_commands_template(ctx, InfoMsg, *args)


@bot.command(help=NO_HELP)
async def pic(ctx, *args):
    await card_commands_template(ctx, PicMsg, *args)


@bot.command(help=NO_HELP)
async def voice(ctx, *args):
    await card_commands_template(ctx, VoiceMsg, *args)


@bot.command(help='sets')
async def sets(ctx, *args):
    start_idx = -5 * ('-r' in args or '--rotation' in args)
    embed = discord.Embed()
    embed_val = ''
    for i, expac in enumerate(list(filter(lambda xpc: xpc not in ("Token", "Promo"), EXPANSIONS))[start_idx:], start=1):
        # -7 separates the crafts in Rotation, -(5 of them + 2 of the excluded above)
        embed_val += f'{EXPANSIONS[expac][1]} **{expac}**\n'
        # ('\n' if i == len(EXPANSIONS) - 7 else '')
    embed.add_field(name='\u200b', value=embed_val)
    # MyMsg is usually meant as an abstract superclass, but thanks to from_dict it can instantiate what would be an
    # anonymous subclass of itself (similar to what a lambda is for a function).
    await MyMsg().from_dict({"ctx": ctx, "embed": embed}).dispatch()


@bot.command(help='jcg')
async def jcg(ctx, mode='rotation'):
    await JcgMsg(ctx, mode).dispatch()


@bot.command(help='**SYNOPSIS**\n'
                  '\t**code** __DECK_CODE__\n\n'
                  '**DESCRIPTION**\n'
                  'Returns the Shadowverse-Portal link and image relative to '
                  'with the given 4-digits __DECK_CODE__.'
             )
async def code(ctx, deck_code):
    async with aiohttp.ClientSession() as s:
        async with s.get(
                f'https://shadowverse-portal.com/api/v1/deck/import?format=json&deck_code={deck_code}&lang=en') as r:
            data = json.loads(await r.text())["data"]
    if data['clan'] is None:
        return await ctx.send(embed=discord.Embed(title="The deck code is invalid or has expired!"))
    _, deck_url, deck_img = await deck_hash_assets(data["hash"])
    await ctx.send(embed=discord.Embed().add_field(name='\u200b', value=hyperlink('Deck Link', deck_url)),
                   file=discord.File(deck_img, 'deck.png'))


@bot.command()
@commands.check(lambda ctx: ctx.message.author.id == MAINTAINER_ID)
async def rr(ctx):
    await ctx.message.author.send('rr')
    await bot.close()


# EVENTS ###############################################################################################################

@bot.event
async def on_ready():
    log.info(f'{bot.user} is active.')
    log.info(f'available commands: {", ".join(cmd.name for cmd in bot.commands)}')
    await bot.change_presence(activity=discord.Game(f'{bot.command_prefix}help/{bot.command_prefix}h'))


@bot.event
async def on_reaction_add(reaction, user):
    if reaction.message.author == bot.user and user != bot.user:
        emoji = demojize(reaction.emoji)
        log.info(f'{user} pressed {emoji} on msg {reaction.message.id}')
        MyMsg.on_emoji_toggle(reaction.message.id, emoji, user)


@bot.event
async def on_command_error(ctx, error):
    # Command prefix + string defaults to info(string).
    if isinstance(error, commands.CommandNotFound):
        args = tuple(ctx.message.content[1:].split(' '))
        await card_commands_template(ctx, InfoMsg, *args)


@bot.event
async def on_message(message):
    # If the message contains a deck link, post deck code + image
    if 'https://shadowverse-portal.com/deck' in message.content and message.author != bot.user:
        try:
            deck_hash = message.content.split('deck/')[1].split('lang')[0][:-1]
        except IndexError:
            deck_hash = message.content.split('hash=')[1].split('lang')[0][:-1]
        deck_code, _, deck_img = await deck_hash_assets(deck_hash)
        await message.channel.send(embed=discord.Embed().add_field(name='Deck Code', value=f'**{deck_code}**'),
                                   file=discord.File(deck_img, 'deck.png'))
    await bot.process_commands(message)


# HELP & HELP DOCS #####################################################################################################

fmt_commands_list = ''
command_names = natsorted(str(cmd) for cmd in bot.commands)
for cmd in command_names:
    emoji = int_to_emoji('*') if not has_help(cmd) else chr_to_emoji(cmd[0])
    emoji = emojize(emoji)
    fmt_commands_list += f'{emoji} {cmd}\n'

help_doc = """
**AVAILABLE COMMANDS**
{fmt}
**OTHER FEATURES**
• When a {svportal_link} deck link is detected, its deck code and image are automatically posted.
""".format(fmt=fmt_commands_list,
           pfx=bot.command_prefix,
           svportal_link=hyperlink('Shadowverse Portal', 'https://shadowverse-portal.com/?lang=en'))


@bot.remove_command('help')
@bot.command(aliases=['h'], help=help_doc)
async def help(ctx, command='help'):
    if not has_help(command):
        command = 'help'
    await HelpMsg(ctx, bot.get_command(command)).dispatch()


# TAIL METHODS #########################################################################################################

bot.run(TOKEN)
# restart (when rr gets called)
time.sleep(5)
os.execl('/usr/bin/python', os.path.abspath(__file__), *sys.argv)

# TODO list
#  start from base files and go upwards with documentation and log, also solve pycharm warnings
#       done Card, Library, MyMsg
#  finish help docs for commands
#       not started, skeleton below
#  think about additional arguments for commands, flags if needed (see card_commands_template)
#  think about new commands

# skeleton:
"""**SYNOPSIS**

**DESCRIPTION**

**OPTIONS**

**EXAMPLES**
"""

# reading order:
# Card
#  v
# Library
#  v
# MyMsg
