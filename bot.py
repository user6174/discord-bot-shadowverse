#!/usr/bin/env python3

import asyncio
import shutil
import time
import requests

from discord.ext import commands  # https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html

from Embeds import *
from Embeds import _card_info_embed, _help_command_embed, _help_embed, _img_embed, _async_voice_embed
import pyshorteners

print(sys.executable)
print(os.path.abspath(__file__))
print(*sys.argv)

MAINTAINER_ID = 186585846906880001

#  TODO add a reaction to img for spawning card info page and vice versa

########################################################################################################################
# GLOBALS ##############################################################################################################
########################################################################################################################

with open("token_testing.txt", 'r') as txt:  # options: token_testing, token_main
    token = txt.readline()
bot = commands.Bot(command_prefix='!')
MAX_MATCHES = 15
REACTIONS_COMMANDS_TIMEOUT = 120.0  # s


########################################################################################################################
# EVENTS ###############################################################################################################
########################################################################################################################


@bot.event
async def on_ready():
    logging.info(f'{bot.user} is active.')
    await bot.change_presence(activity=discord.Game(f'{bot.command_prefix}help/{bot.command_prefix}h'))


@bot.event
async def on_command_error(ctx, error):
    """Command prefix + string defaults to find(string)."""
    if isinstance(error, commands.CommandNotFound):
        logging.info(f'Requested a card info page with arguments {ctx.message.content[1:]} by {ctx.message.author} .')
        await find(ctx, ctx.message.content[1:])


@bot.event
async def on_message(message):
    if 'https://shadowverse-portal.com/deck' in message.content and message.author != bot.user:
        try:
            hash_ = message.content.split('deck/')[1].split('lang')[0][:-1]
        except IndexError:
            hash_ = message.content.split('hash=')[1].split('lang')[0][:-1]
        deck_url = f'https://shadowverse-portal.com/deck/{hash_}?lang=en'
        deck_code = json.loads(requests.post(
            'https://shadowverse-portal.com/api/v1/deck_code/publish?format=json&lang=en',
            data={'hash': hash_}).text)["data"]["deck_code"]
        s = requests.Session()
        s.headers.update({'referer': deck_url})
        r = s.get('https://shadowverse-portal.com/image/1?lang=en', stream=True)
        with open('deck.png', 'wb') as out:
            shutil.copyfileobj(r.raw, out)
        embed = discord.Embed(title=f'**Deck Code:** {deck_code}')
        await message.channel.send(file=discord.File('deck.png'), embed=embed)
    await bot.process_commands(message)


########################################################################################################################
# GENERICS #############################################################################################################
########################################################################################################################


async def _card_command_embed(ctx, embed_maker, *search_terms) -> discord.Embed or None:
    """
    A template for the embed makers in Embed.py: it performs the card lookup, gives them the card name,
    handling search misses, and returns an embed.
    """
    logging.info(f'Requested card command "{embed_maker.__name__}" with search terms "{" ".join(search_terms)}" '
                 f'by {ctx.message.author} .')
    card = await search(ctx, ' '.join(search_terms))
    if type(card) == str:
        return embed_maker(card)
    else:
        await ctx.send(embed=discord.Embed(title=f'{"0" if card is None else card} matches found. Be more precise!'))


async def emote_toggle(ctx, msg, emote, embed_maker, embed_maker_args, spawn_new_msg=False):
    """
    Reacts to the input message with the input emote, and starts a thread that monitors for reaction_command_timeout
    seconds if that emote is toggled.
    If it is, a new embed is created with embed_maker(embed_maker_args), and either the original message is edited
    with it or a new message is created.
    NOTE: this needs its own thread, so it should be called in asyncio.ensure_future()
    """
    # this first check happens because emote toggle can be called after one of various emotes of a message is toggled,
    # and one wishes to make it clickable again.
    old_reactions = discord.utils.get(bot.cached_messages, id=msg.id).reactions
    old_emojis = [rctn.emoji for rctn in old_reactions]
    if emote in old_emojis:
        if old_reactions[old_emojis.index(emote)].me:
            logging.info(f'Emote {emote} is already being reacted by the bot, skipping.')
            return
    await msg.add_reaction(emote)
    try:  # error raised on timeout
        reaction, user = await bot.wait_for("reaction_add",
                                            check=lambda rctn, usr: str(rctn.emoji) == emote
                                                                    and usr != msg.author and rctn.message.id == msg.id,
                                            timeout=REACTIONS_COMMANDS_TIMEOUT)
        # if toggled:
        logging.info(f'{user} pressed emote {emote} on message {msg.id}, '
                     f'requesting {embed_maker.__name__} with arguments {embed_maker_args} .')
        try:  # some embed makers are async, some sync
            new_embed = (await embed_maker(*embed_maker_args))[0]
        except TypeError:
            new_embed = embed_maker(*embed_maker_args)[0]
        if new_embed is None:  # executes trash emote
            return await msg.delete()
        await msg.remove_reaction(reaction.emoji, bot.user)
        try:  # on DMs
            await msg.remove_reaction(reaction.emoji, user)
        except discord.errors.Forbidden:
            pass
        if spawn_new_msg:
            new_msg = await ctx.send(embed=new_embed)
            logging.info(f'Requested emote dressing of message {new_msg.id} with tag {embed_maker.__name__} .')
            await reaction_dress(ctx, new_msg, embed_maker.__name__)
        else:
            await msg.edit(embed=new_embed)
        await reaction_dress(ctx, msg, embed_maker.__name__)
    except asyncio.TimeoutError:
        try:
            logging.info(f'Reactable status expired on message {msg.id} for emote {emote} .')
            await msg.remove_reaction(emote, bot.user)
        except discord.errors.NotFound:
            pass


async def reaction_dress(ctx, msg, embed_maker_name):
    """
    Adds a series of reactions to a message, depending on what function created its embed, and calls emote_toggle for
    each reaction, specifying what should be done if/when that emote is toggled.
    """
    logging.info(f'Dressing message {msg.id} for an embed by {embed_maker_name} .')
    asyncio.ensure_future(emote_toggle(ctx, msg, emotes["trash"], lambda _: (None,), (None,)))
    card = msg.embeds[0].title.split(" Evolved")[0]
    is_follower = pool.p[card]["type_"] == "Follower"
    evo = len(msg.embeds[0].title.split(" Evolved")) == 2
    if embed_maker_name == '_help_embed':
        for command in bot.commands:
            asyncio.ensure_future(
                emote_toggle(ctx, msg, emotes[str(command)[0].upper()], _help_command_embed, (command,), True))
    elif embed_maker_name == '_card_info_embed':
        has_img = msg.embeds[0].image.value != discord.Embed.Empty
        asyncio.ensure_future(emote_toggle(ctx, msg, emotes["img"], _card_info_embed, (card, evo, not has_img)))
        if is_follower:
            asyncio.ensure_future(
                emote_toggle(
                    ctx, msg, emotes["B"] if evo else emotes["E"], _card_info_embed, (card, not evo, True)))
        for idx, related in enumerate(pool.p[card]["tokens_"]):
            asyncio.ensure_future(emote_toggle(ctx, msg, emotes[idx], _card_info_embed, (related, False, False), True))
    elif embed_maker_name == '_img_embed':
        if is_follower:
            try:
                alt = int(msg.embeds[0].footer.text.split('#')[1][0])
            except IndexError:
                alt = None
            asyncio.ensure_future(
                emote_toggle(
                    ctx, msg, emotes["B"] if evo else emotes["E"], _img_embed, (card, not evo, alt), False))
        for alt_idx in range(len(pool.p[card]["alts_"])):
            asyncio.ensure_future(
                emote_toggle(ctx, msg, emotes[alt_idx], _img_embed, (card, False, alt_idx), True))


async def search(ctx, search_terms):
    logging.info(f'Trying a card search with search terms {search_terms} requested by {ctx.message.author} ...')
    if search_terms[0] == bot.command_prefix:
        logging.info("\tSearch by name requested...")
        search_terms = ' '.join([word[0].upper() + word[1:].lower() for word in search_terms[1:].split(' ')])
        matches = [pool.p[card]["name_"] for card in pool.p if pool.p[card]["name_"] == search_terms]
        if not matches:
            logging.info("\t...no exact matches, relaxing the search to substrings...")
            matches = pool.search_by_name(search_terms, similarity_threshold=100)
    else:
        logging.info("\tSearch by attributes requested...")
        matches = pool.search_by_attributes(search_terms)
        logging.info(f'\t...found the following matches: [{", ".join(matches)}]...')
    if len(matches) == 0:
        logging.info(f'...no cards found.')
        return 0
    elif len(matches) == 1:
        logging.info(f'...exactly one card found: {matches[0]} .')
        return matches[0]
    elif len(matches) > MAX_MATCHES:
        logging.info(f'...{len(matches)} cards found, too many to list (listing limit: {MAX_MATCHES}).')
        return len(matches)
    else:
        logging.info(f'\t...{len(matches)} cards found, returning an option menu ')
        embed = discord.Embed(title="Possible matches:")
        for idx, card in enumerate(matches):
            embed.add_field(name=emotes[idx], value=card)
        msg = await ctx.send(embed=embed)
        logging.info(f'\t...produced option menu {msg.id}...')
        monitored_emotes = []
        for i in range(len(matches)):
            await msg.add_reaction(emotes[i])
            monitored_emotes.append(emotes[i])
        asyncio.ensure_future(emote_toggle(ctx, msg, emotes["trash"], lambda _: (None,), (None,)))
        try:
            reaction, user = await bot.wait_for("reaction_add",
                                                check=lambda r, u: str(r.emoji) in monitored_emotes
                                                                   and u != msg.author and r.message.id == msg.id,
                                                timeout=REACTIONS_COMMANDS_TIMEOUT)
            await msg.delete()
            card = matches[{v: k for k, v in emotes.items()}[reaction.emoji]]
            logging.info(f'...returned card {card} from option menu {msg.id}, requested by {user} .')
            return card
        except asyncio.TimeoutError:
            logging.info(f'Reactable status expired on message {msg.id} .')


########################################################################################################################
# CARD COMMANDS ########################################################################################################
########################################################################################################################


@bot.remove_command('help')
@bot.command(aliases=['h'], help=":thinking:")
async def help(ctx):
    logging.info(f'Requested help page by {ctx.message.author} .')
    embed = _help_embed(bot)
    msg = await ctx.send(embed=embed)
    await reaction_dress(ctx, msg, 'help')


@bot.command(aliases=['f'], help=
f'**Usage**:\n\n'
f'As explained in the main menu. Additionally, a card search can be requested with this shorthand:\n'
f'• `{bot.command_prefix}<CARD ATTRIBUTES> <OPTIONAL PARAMETERS>`:\n'
f'• `{bot.command_prefix}{bot.command_prefix}<CARD NAME> <OPTIONAL PARAMETERS>`:\n'
f'\n**Examples**:\n\n'
f'• `{bot.command_prefix}abominatioQ`\n'
f'• `{bot.command_prefix}6/6 rune wld`\n'
f'• `{bot.command_prefix}2/2 blood gold summon bat`\n'
f'• `{bot.command_prefix}{bot.command_prefix}azazel,`\n'
f'• `{bot.command_prefix}{bot.command_prefix}azazel`\n')
async def find(ctx, *args):
    try:
        embed, card, evo, img_ = await _card_command_embed(ctx, _card_info_embed, *(tuple(args)))
    except TypeError:
        return  # found no card
    msg = await ctx.send(embed=embed)
    await reaction_dress(ctx, msg, '_card_info_embed')


@bot.command(aliases=['pic', 'art', 'fullpic', 'fullart'], help="**Special parameters**:\n\nNone.")
async def img(ctx, *args):
    embed, card_name, evo, alt = await _card_command_embed(ctx, _img_embed, *(tuple(args)))
    msg = await ctx.send(embed=embed)
    await reaction_dress(ctx, msg, '_img_embed')


@bot.command(aliases=['v', 'sound', 's'], help="**Special parameters**:\n\nNone.")
async def voice(ctx, *args):
    embed, card_name = await _async_voice_embed(await search(ctx, ' '.join(args)))
    msg = await ctx.send(embed=embed)
    await reaction_dress(ctx, msg, 'voice')


@bot.command()
async def code(ctx, deck_code):
    url = requests.get(
        f'https://shadowverse-portal.com/api/v1/deck/import?format=json&deck_code={deck_code}&lang=en')
    data = json.loads(url.text)["data"]
    deck_url = f'https://shadowverse-portal.com/deck/{data["hash"]}?lang=en'
    s = requests.Session()
    s.headers.update({'referer': deck_url})
    r = s.get('https://shadowverse-portal.com/image/1?lang=en', stream=True)
    with open('deck.png', 'wb') as out:
        shutil.copyfileobj(r.raw, out)
    embed = discord.Embed().add_field(name='\u200b',
                                      value=f'**[Deck link]({pyshorteners.Shortener().tinyurl.short(deck_url)})**')
    await ctx.send(file=discord.File('deck.png'), embed=embed)


@bot.command(aliases=['j', 'tourney'], help="**Special parameters**:\n\n"
                                            "`ul`: displays the last Unlimited JCG.\n"
                                            "`no arguments/rot`: displays the last Rotation JCG.\n")
async def jcg(ctx, format_='rot'):
    shortener = pyshorteners.Shortener()
    format_ = 'unlimited' if format_ in ('ul', 'unlimited') else 'rotation'
    craft_names = ("", "Forestcraft", "Swordcraft", "Runecraft", "Dragoncraft",
                   "Shadowcraft", "Bloodcraft", "Havencraft", "Portalcraft")
    msg = await ctx.send('Fetching data...')
    with open(f'{format_}.json', 'r') as f_:
        tourney = json.load(f_)
    embed = discord.Embed(title=tourney["name"])
    embed.url = f'https://sv.j-cg.com/compe/view/tour/{tourney["code"]}'
    for top in [k for k in tourney.keys() if k not in ["crafts", "code", "name"]]:
        await msg.edit(embed=discord.Embed(title=f'Preparing top{top}...'))
        decks = [
            " / ".join(f'[{craft_names[int(deck[59])]}]({shortener.tinyurl.short(deck)})' for deck in player["decks"])
            for
            player in tourney[top]]
        line = [f'{decks[idx]} - {player["player"]}\n' for idx, player in enumerate(tourney[top])]
        embed.add_field(name=f'**TOP{top}**:',
                        value=' '.join(line), inline=False)
    craft_distribution = ''
    for idx, craft in enumerate(tourney["crafts"]):
        craft_distribution += f'**{craft}** {craft_names[idx + 1]}\n'
    embed.add_field(name='**Class distribution**:', value=craft_distribution)
    await msg.edit(embed=embed)
    await reaction_dress(ctx, msg, 'jcg')


@bot.command(aliases=['rr'], help="Maintainer only command.")
@commands.check(lambda ctx: (ctx.message.author.id == MAINTAINER_ID))
async def restart(ctx):
    await ctx.send("Restarting...")
    await bot.close()


bot.remove_command('voice')  # comment out when not on raspberry

bot.run(token)
# restart (when rr gets called)
time.sleep(5)
os.execl('/usr/bin/python', os.path.abspath(__file__), *sys.argv)
