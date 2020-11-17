#!/usr/bin/env python3
import io
import os
import sys
import time
import json
import discord
import aiohttp

from typing import List, Tuple
from natsort import natsorted
from discord.ext import commands
from emoji import demojize, emojize

from Card import EXPANSIONS
from MyMsg import NO_HELP, LIB, log, bot
from MyMsg import chr_to_emoji, int_to_emoji, hyperlink, has_help
from MyMsg import MyMsg, MatchesMsg, JcgMsg, HelpMsg
from CardMsg import PicMsg, InfoMsg, VoiceMsg

log.info(sys.executable)
log.info(os.path.abspath(__file__))
log.info(*sys.argv)

MAINTAINER_ID = 186585846906880001
MAX_TOGGLABLE_MATCHES = 11
MAX_DISPLAYABLE_MATCHES = 35
SITE = 'https://shadowverse-portal.com'


DEV = 1  # 0 on Raspberry.
with open(f'token_{"testing" if DEV else "main"}.txt', 'r') as txt:
    TOKEN = txt.readline()


# CARD COMMANDS ########################################################################################################

async def search(ctx, *query, by_attrs, lax) -> List[int]:
    """
    An async extension of the Library class methods for card searches. Tries to fallback on other search methods
    upon unsuccessful lookups, and asks for user input with a MatchesMsg menu depending on the amount of matches.
    """
    query = ' '.join(query)
    if by_attrs:
        matches = LIB.search_by_attributes(query)
    else:
        matches = LIB.search_by_name(query, lax=lax)
        if not matches and not lax:
            matches = LIB.search_by_name(query, lax=True)
        if not matches:
            matches = LIB.search_by_attributes(query)
    log.info(f'{len(matches)} match{"es" if len(matches) != 1 else ""}')
    if len(matches) < 2 or len(matches) > MAX_TOGGLABLE_MATCHES:
        return matches
    else:
        matches_obj = MatchesMsg(ctx, matches)
        await matches_obj.dispatch()
        return await matches_obj.wait_for_toggle()


async def deck_hash_assets(deck_hash) -> Tuple[str, str, io.BytesIO]:
    async with aiohttp.ClientSession() as s:
        async with s.post(f'{SITE}/api/v1/deck_code/publish?format=json&lang=en',
                          data={'hash': deck_hash}) as r:
            deck_code = json.loads(await r.text())["data"]["deck_code"]
        deck_url = f'{SITE}/deck/{deck_hash}?lang=en'
        async with s.get(f'{SITE}/image/1?lang=en', headers={'referer': deck_url}) as r:
            deck_img = io.BytesIO(await r.read())
    return deck_code, deck_url, deck_img


async def card_commands_executor(ctx, msg_maker, *args):
    """
    Takes the user message relative to a card command request, handles card search options (if any are passed), issues
    a card search and dispatches the relative card command or sends info about the card search, depending on,
    respectively, if said search was successful or not.
    """
    flags = tuple(filter(lambda x: x in ('-l', '--lax', '-a', '--attrs'), args))
    query = tuple(filter(lambda x: x not in flags, args))
    by_attrs = '-a' in flags or '--attrs' in flags
    lax = '-l' in flags or '--lax' in flags
    matches = await search(ctx, *query, by_attrs=by_attrs, lax=lax)
    if len(matches) == 1:
        card_msg = msg_maker(ctx, matches[0])
        await card_msg.dispatch()
    elif len(matches) < MAX_DISPLAYABLE_MATCHES:
        matches = [LIB.ids[id_] for id_ in matches]
        matches = [f'{c.pp_}pp {c.craft_.strip("craft")} {c.rarity_} {c.type_} **{c.name_}**' for c in matches]
        embed = discord.Embed(title=f'{(len(matches))} matches found')\
            .add_field(name='\u200b', value='\n'.join(matches))
        await MyMsg.from_dict({"ctx": ctx, "embed": embed}).dispatch()
    else:
        await ctx.send(embed=discord.Embed(title=f'{(len(matches))} matches found.'))


# Card commands have no help doc because any additional arguments they may have are better implemented as a reaction
# toggle, and card search has its own help doc.
@bot.command(aliases=['i'], help=NO_HELP)
async def info(ctx, *args):
    await card_commands_executor(ctx, InfoMsg, *args)


@bot.command(aliases=['p', 'img', 'art'], help=NO_HELP)
async def pic(ctx, *args):
    await card_commands_executor(ctx, PicMsg, *args)


@bot.command(aliases=['v', 'sound', 'audio'], help=NO_HELP)
async def voice(ctx, *args):
    await card_commands_executor(ctx, VoiceMsg, *args)


# OTHER COMMANDS #######################################################################################################


@bot.command(aliases=['s', 'expacs'], help="""**SYNOPSIS**
`{pfx}s`
`{pfx}sets`
`{pfx}sets -r`

**DESCRIPTION**
Shows the list of expansions in chronological order, with their release date.

**OPTIONS**
**-r**, **--rotation**
Shows the set that's about to rotate and the ones currently in Rotation.
""".format(pfx=bot.command_prefix))
async def sets(ctx, flag='-u'):
    # Showing the last 6 sets.
    start_idx = -6 * (flag in ('-r', '--rotation'))
    embed = discord.Embed()
    embed_val = ''
    for i, expac in enumerate(list(filter(lambda xpc: xpc not in ("Token", "Promo"), EXPANSIONS))[start_idx:], start=1):
        markdown = '~~' if (start_idx == -6 and i == 1) else '**'
        embed_val += f'{EXPANSIONS[expac][1]} {markdown}{expac}{markdown}\n'
    embed.add_field(name='\u200b', value=embed_val)
    await MyMsg().from_dict({"ctx": ctx, "embed": embed}).dispatch()


@bot.command(aliases=['j', 'tour', 'tourney'], help="""**SYNOPSIS**
`{pfx}j`
`{pfx}jcg`
`{pfx}jcg -u`

**DESCRIPTION**
Shows the latest Rotation {jcg}.

**OPTIONS**
**-u**, **--unlimited**
Shows the latest Unlimited JCG instead."""
             .format(pfx=bot.command_prefix, jcg=hyperlink('JCG', 'https://sv.j-cg.com/')))
async def jcg(ctx, flag='-r'):
    mode = 'unlimited' if flag in ('-u', '--unlimited') else 'rotation'
    await JcgMsg(ctx, mode).dispatch()


@bot.command(aliases=['c'], help="""**SYNOPSIS**
`{pfx}c <DECK_CODE>`
`{pfx}code <DECK_CODE>`

**DESCRIPTION**
Shows the deck's image and link corresponding to a valid deck code.
""".format(pfx=bot.command_prefix))
async def code(ctx, deck_code):
    async with aiohttp.ClientSession() as s:
        async with s.get(
                f'{SITE}/api/v1/deck/import?format=json&deck_code={deck_code}&lang=en') as r:
            data = json.loads(await r.text())["data"]
    if data['clan'] is None:
        return await ctx.send(embed=discord.Embed(title="The deck code is invalid or has expired!"))
    _, deck_url, deck_img = await deck_hash_assets(data["hash"])
    await ctx.send(embed=discord.Embed().add_field(name='\u200b', value=hyperlink('Deck Link', deck_url)),
                   file=discord.File(deck_img, 'deck.png'))


@bot.command(help=NO_HELP)
@commands.check(lambda ctx: ctx.message.author.id == MAINTAINER_ID)
async def rr(ctx):
    await ctx.message.author.send('rr')
    await bot.close()


# EVENTS ###############################################################################################################

@bot.event
async def on_ready():
    log.info(f'{bot.user} is active.')
    log.info(f'available commands: {", ".join(cmd.name for cmd in bot.commands)}')
    await bot.change_presence(activity=discord.Game(f'{bot.command_prefix}h / {bot.command_prefix}help'))


@bot.event
async def on_reaction_add(reaction, user):
    if reaction.message.author == bot.user and user != bot.user:
        emoji = demojize(reaction.emoji)
        log_msg = f'[{reaction.message.channel}, {reaction.message.guild}] ' \
                  f'{user} pressed {emoji} on msg  `{reaction.message.embeds[0].title}` (id={reaction.message.id})'
        pad = '*'*len(log_msg)
        log.info(f'\n{pad}\n{log_msg}\n{pad}')
        MyMsg.on_emoji_toggle(reaction.message.id, emoji, user)


@bot.event
async def on_command_error(ctx, error):
    # Command prefix + string defaults to info(string).
    if isinstance(error, commands.CommandNotFound):
        args = tuple(ctx.message.content[1:].split(' '))
        await card_commands_executor(ctx, InfoMsg, *args)


@bot.event
async def on_message(message):
    # Log messages for the bot.
    if message.content.startswith(bot.command_prefix):
        log_msg = f'[{message.channel}, {message.guild}] {message.author}: {message.content}'
        pad = '*'*len(log_msg)
        log.info(f'\n{pad}\n{log_msg}\n{pad}')
    # If the message contains a deck link, its deck code + image are posted.
    if f'{SITE}/deck' in message.content and message.author != bot.user:
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
command_names.remove('rr')
for cmd in command_names:
    emoji = int_to_emoji('*') if not has_help(cmd) else chr_to_emoji(cmd[0])
    emoji = emojize(emoji)
    fmt_commands_list += f'{emoji} {cmd}\n'

help_doc = """
**AVAILABLE COMMANDS**
{fmt}
**OTHER**
• When a {svportal_link} deck link is detected, its deck code and image are automatically posted.
• Use this {link} to add this bot to your server.\n
""".format(fmt=fmt_commands_list,
           pfx=bot.command_prefix,
           svportal_link=hyperlink('Shadowverse Portal', '{SITE}/?lang=en'),
           link=hyperlink("link", "https://discord.com/oauth2/authorize?client_id=684142820122296349&scope=bot"))


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

