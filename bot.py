#!/usr/bin/env python3
from discord.ext import commands  # https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html
from typing import Tuple

from Embeds import _info_embed, _help_command_embed, _help_embed, _img_embed
from Embeds import *
import aiohttp
import asyncio
import time
import io

print(sys.executable)
print(os.path.abspath(__file__))
print(*sys.argv)

########################################################################################################################
# GLOBALS ##############################################################################################################
########################################################################################################################

REACTIONS_COMMANDS_TIMEOUT = 120.0  # s
MAINTAINER_ID = 186585846906880001
MAX_MATCHES = 15
DEV = True  # False on raspberry
with open(f'token_{"testing" if DEV else "main"}.txt', 'r') as txt:
    token = txt.readline()
bot = commands.Bot(command_prefix='<')


########################################################################################################################
# EVENTS ###############################################################################################################
########################################################################################################################

@bot.event
async def on_ready():
    log.info(f'{bot.user} is active.')
    log.info(f'available commands: {", ".join(cmd.name for cmd in bot.commands)}')
    await bot.change_presence(activity=discord.Game(f'{bot.command_prefix}help/{bot.command_prefix}h'))


@bot.event
async def on_command_error(ctx, error):
    """Command prefix + string defaults to info(string)."""
    if isinstance(error, commands.CommandNotFound):
        log.info(f'requested a card info page with arguments {ctx.message.content[1:]} by {ctx.message.author} .')
        await info(ctx, ctx.message.content[1:])


@bot.event
async def on_message(message):
    if 'https://shadowverse-portal.com/deck' in message.content and message.author != bot.user:
        log.info(f'detected sv-portal url: sending deck code and img '
                 f'(message content by {message.author}: {message.content}')
        try:
            deck_hash = message.content.split('deck/')[1].split('lang')[0][:-1]
        except IndexError:
            deck_hash = message.content.split('hash=')[1].split('lang')[0][:-1]
        deck_code, _, deck_img = await deck_hash_assets(deck_hash)
        await message.channel.send(embed=discord.Embed(title=f'Deck code: {deck_code}'),
                                   file=discord.File(deck_img, 'deck.png'))
    await bot.process_commands(message)


########################################################################################################################
# GENERICS #############################################################################################################
########################################################################################################################

async def deck_hash_assets(deck_hash) -> Tuple[str, str, io.BytesIO]:
    """
        :return: deck code, deck url, deck img
    """
    async with aiohttp.ClientSession() as s:
        async with s.post('https://shadowverse-portal.com/api/v1/deck_code/publish?format=json&lang=en',
                          data={'hash': deck_hash}) as r:
            deck_code = json.loads(await r.text())["data"]["deck_code"]
        deck_url = f'https://shadowverse-portal.com/deck/{deck_hash}?lang=en'
        async with s.get('https://shadowverse-portal.com/image/1?lang=en', headers={'referer': deck_url}) as r:
            deck_img = io.BytesIO(await r.read())
    return deck_code, deck_url, deck_img


async def _card_command_embed(ctx, embed_maker, *search_terms) -> discord.Embed or None:
    """
    A template for the embed makers in Embed.py: it performs the card lookup, gives them the card name,
    handling search misses, and returns an embed.
    """
    log.info(f'Requested card command "{embed_maker.__name__}" with search terms "{" ".join(search_terms)}" '
             f'by {ctx.message.author} .')
    card = await search(ctx, ' '.join(search_terms))
    if card is None:
        return
    elif type(card) == str:
        return embed_maker(card)
    else:
        await ctx.send(embed=discord.Embed(title=f'{"0" if card is None else card} matches found.').add_field(
            name='\u200b',
            value=f'**TIP:** if you\'re looking up a card\'s name, try issuing a name search:\n\n'
                  f'`{bot.command_prefix}{embed_maker.__name__.strip("embed").strip("_")} '
                  f'{bot.command_prefix}{" ".join(search_terms)}`'))


async def emote_toggle(ctx, msg, emote, embed_maker, embed_maker_chks, spawn_new_msg=False):
    """
    Reacts to the input message with the input emote, and starts a thread that monitors for reaction_command_timeout
    seconds if that emote is toggled.
    If it is, a new embed is created with embed_maker(embed_maker_args), and either the original message is edited
    with it or a new message is created.
    NOTE: this needs its own thread, so it should be called in asyncio.ensure_future()

    :param ctx:
    :param msg:
    :param emote:
    :param embed_maker:
    :param embed_maker_chks:
    :param spawn_new_msg:
    :return:
    """

    # this first check happens because emote toggle can be called after one of various emotes of a message is toggled,
    # and one wishes to make it clickable again.
    await asyncio.sleep(.1)
    old_reactions = discord.utils.get(bot.cached_messages, id=msg.id).reactions
    old_emojis = [rctn.emoji for rctn in old_reactions]
    if emote in old_emojis:
        if old_reactions[old_emojis.index(emote)].me:
            log.info(f'Emote {emote} is already being reacted by the bot, skipping.')
            return
    await msg.add_reaction(emote)
    try:  # error raised on timeout
        reaction, user = await bot.wait_for("reaction_add",
                                            check=lambda rctn, usr: str(rctn.emoji) == emote
                                                                    and usr != msg.author and rctn.message.id == msg.id,
                                            timeout=REACTIONS_COMMANDS_TIMEOUT)
        # if toggled:
        embed_maker_args = tuple(chk(msg.embeds[0]) for chk in embed_maker_chks)
        log.info(f'{user} pressed emote {emote} on message {msg.id}, '
                 f'requesting {embed_maker.__name__} with arguments {embed_maker_args} .\n'
                 f'these arguments are obtained from applying the predicates {embed_maker_chks}.')
        # TODO documentare che è un casino, refactor da embed maker args che sono variabili a embed maker chks che
        #  sono predicati agenti sull'embed (scopo: si è sicuri che si sta agendo sull'embed attuale, altrimenti
        #  assegnando var e pigiando altre reactions l'embed rischia di cambiare stato e quando la reaction è pigiata
        #  si agisce su una cosa che non esiste più in quella maniera
        try:  # some embed makers are async, some sync
            new_embed = (await embed_maker(*embed_maker_args))[0]
        except TypeError:
            try:
                new_embed = embed_maker(*embed_maker_args)[0]
            except TypeError:  # executes trash emote
                return await msg.delete()
        await msg.remove_reaction(reaction.emoji, bot.user)
        try:  # on DMs
            await msg.remove_reaction(reaction.emoji, user)
        except discord.errors.Forbidden:
            pass
        if spawn_new_msg:
            new_msg = await ctx.send(embed=new_embed)
            log.info(f'Requested emote dressing of message {new_msg.id} with tag {embed_maker.__name__} .')
            await reaction_dress(ctx, new_msg, embed_maker.__name__)
        else:
            await msg.edit(embed=new_embed)
        await reaction_dress(ctx, msg, embed_maker.__name__)
    except asyncio.TimeoutError:
        try:
            log.info(f'Reactable status expired on message {msg.id} for emote {emote} .')
            await msg.remove_reaction(emote, bot.user)
        except discord.errors.NotFound:
            pass


async def reaction_dress(ctx, msg, embed_maker_name):
    """
    Adds a series of reactions to a message, depending on what function created its embed, and calls emote_toggle for
    each reaction, specifying what should be done if/when that emote is toggled.
    """
    log.info(f'Dressing message {msg.id} for an embed by {embed_maker_name} .')
    asyncio.ensure_future(emote_toggle(ctx, msg, emotes["trash"], lambda _: None, (lambda _: None,)))
    if embed_maker_name == '_help_embed':
        await asyncio.sleep(1)
        for command in bot.commands:
            asyncio.ensure_future(emote_toggle(ctx, msg, emotes[str(command)[0].upper()], _help_command_embed,
                                               (lambda _: str(command), lambda _: command.help), True))
    if embed_maker_name == '_help_command_embed':
        return

    def card_name(embed):
        return embed.title.split(" Evolved")[0]

    def is_follower(embed):
        return pool.names[embed.title.split(" Evolved")[0]]["type_"] == "Follower"

    def is_evo(embed):
        return len(embed.title.split(" Evolved")) == 2

    if embed_maker_name == '_info_embed':
        def has_img(embed):
            return embed.image.url != discord.Embed.Empty

        asyncio.ensure_future(
            emote_toggle(ctx, msg, emotes["img"], _info_embed, (card_name, is_evo, lambda e: not has_img(e))))
        if is_follower(msg.embeds[0]):
            asyncio.ensure_future(emote_toggle(ctx, msg, emotes["B"] if is_evo(msg.embeds[0]) else emotes["E"],
                                               _info_embed, (card_name, lambda e: not is_evo(e), has_img)))

        tokens = pool.names[card_name(msg.embeds[0])]["tokens_"]
        # works
        asyncio.ensure_future(emote_toggle(ctx, msg, emotes[0], _info_embed, (lambda _: tokens[0], lambda _: False, lambda _: False), True))
        asyncio.ensure_future(emote_toggle(ctx, msg, emotes[1], _info_embed, (lambda _: tokens[1], lambda _: False, lambda _: False), True))
        asyncio.ensure_future(emote_toggle(ctx, msg, emotes[2], _info_embed, (lambda _: tokens[2], lambda _: False, lambda _: False), True))
        # doesn't work (the 4+ is just for executing this together with the above)
        # for reproducing the bug look for medea, reactions 0 to 2 work as intended, 4 to 6 all show token 6
        for idx, tk in enumerate(tokens):
            asyncio.create_task(emote_toggle(ctx, msg, emotes[4 +idx], _info_embed, (lambda _: tk, lambda _: False, lambda _: False), True))

    elif embed_maker_name == '_img_embed':
        if is_follower(msg.embeds[0]):
            try:
                alt = int(msg.embeds[0].footer.text.split('#')[1][0])
            except IndexError:
                alt = None
            asyncio.ensure_future(
                emote_toggle(
                    ctx, msg, emotes["B"] if is_evo(msg.embeds[0]) else emotes["E"],
                    _img_embed, (card_name, lambda e: not is_evo(e), lambda _: alt)))
        # TODO small bug: alt arts link themselves
        #  bigger bug: fate's hand (same problem with help reactions?
        for alt_idx in range(len(pool.names[card_name(msg.embeds[0])]["alts_"])):
            asyncio.ensure_future(emote_toggle(ctx, msg, emotes[alt_idx], _img_embed,
                                               (card_name, lambda _: False, lambda _: alt_idx), True))


async def search(ctx, search_terms):
    log.info(f'Trying a card search with search terms {search_terms} requested by {ctx.message.author} ...')
    search_by_name = False
    if search_terms[0] == bot.command_prefix:
        search_by_name = True
        log.info("\tSearch by name requested...")
        search_terms = ' '.join([word[0].upper() + word[1:].lower() for word in search_terms[1:].split(' ')])
        matches = [pool.names[card]["name_"] for card in pool.names if pool.names[card]["name_"] == search_terms]
        if not matches:
            log.info("\t...no exact matches, relaxing the search to substrings...")
            matches = pool.search_by_name(search_terms)
    else:
        log.info("\tSearch by attributes requested...")
        matches = pool.search_by_attributes(search_terms)
        log.info(f'\t...found the following matches: [{", ".join(matches)}]...')
    if len(matches) == 0:
        log.info(f'...no cards found, allowing typos...')
        matches = pool.search_by_name(search_terms, exact=False)
        if len(matches) == 1:
            words = matches[0].replace('\'', ' ').split(' ')
            similarities = [fuzz.partial_ratio(i, search_terms) for i in words]
            return await search(ctx,
                                (bot.command_prefix * search_by_name) + words[similarities.index(max(similarities))])
        else:
            return 0
    elif len(matches) == 1:
        log.info(f'...exactly one card found: {matches[0]} .')
        return matches[0]
    elif len(matches) > MAX_MATCHES:
        log.info(f'...{len(matches)} cards found, too many to list (listing limit: {MAX_MATCHES}).')
        return len(matches)
    else:
        log.info(f'\t...{len(matches)} cards found, returning an option menu ')
        embed = discord.Embed(title="Possible matches:")
        for idx, card in enumerate(matches):
            embed.add_field(name=emotes[idx], value=card)
        msg = await ctx.send(embed=embed)
        log.info(f'\t...produced option menu {msg.id}...')
        monitored_emotes = []
        for i in range(len(matches)):
            await msg.add_reaction(emotes[i])
            monitored_emotes.append(emotes[i])
        asyncio.ensure_future(emote_toggle(ctx, msg, emotes["trash"], lambda _: None, (lambda _: None,)))
        try:
            reaction, user = await bot.wait_for("reaction_add",
                                                check=lambda r, u: str(r.emoji) in monitored_emotes
                                                                   and u != msg.author and r.message.id == msg.id,
                                                timeout=REACTIONS_COMMANDS_TIMEOUT)
            await msg.delete()
            card = matches[{v: k for k, v in emotes.items()}[reaction.emoji]]
            log.info(f'...returned card {card} from option menu {msg.id}, requested by {user} .')
            return card
        except asyncio.TimeoutError:
            log.info(f'Reactable status expired on message {msg.id} .')
            await msg.delete()
            return None


########################################################################################################################
# CARD COMMANDS ########################################################################################################
########################################################################################################################


@bot.remove_command('help')
@bot.command(aliases=['h'], help=":thinking:")
async def help(ctx):
    log.info(f'Requested help page by {ctx.message.author} .')
    msg = await ctx.send(embed=_help_embed(bot))
    await reaction_dress(ctx, msg, '_help_embed')


@bot.command(aliases=['f'], help=
f'**USAGE**\n\n'
f'As explained in the main help page. Additionally, a card search can be requested with this shorthand:\n'
f'• `{bot.command_prefix}<CARD ATTRIBUTES> <OPTIONAL PARAMETERS>`:\n'
f'• `{bot.command_prefix}{bot.command_prefix}<CARD NAME> <OPTIONAL PARAMETERS>`:\n'
f'\n**EXAMPLES**\n\n'
f'• `{bot.command_prefix}{bot.command_prefix}abominatioQ` -> `Abomination Awakened`\n'
f'• `{bot.command_prefix}abominatioQ` -> no results\n'
f'• `{bot.command_prefix}2/2 blood gold summon bat de` -> `Vania, Vampire Princess`\n'
f'• `{bot.command_prefix}{bot.command_prefix}azazel` -> `Azazel`\n'
f'• `{bot.command_prefix}{bot.command_prefix}azazel,` -> `Azazel, the Depraved`\n')
async def info(ctx, *args):
    try:
        embed, card, evo, img_ = await _card_command_embed(ctx, _info_embed, *(tuple(args)))
    except TypeError:
        return  # found no card
    msg = await ctx.send(embed=embed)
    await reaction_dress(ctx, msg, '_info_embed')


@bot.command(aliases=['img', 'art', 'fullpic', 'fullimg', 'fullart'], help="**Special parameters**:\n\nNone.")
async def pic(ctx, *args):
    embed, card_name, evo, alt = await _card_command_embed(ctx, _img_embed, *(tuple(args)))
    msg = await ctx.send(embed=embed)
    await reaction_dress(ctx, msg, '_img_embed')


@bot.command(aliases=['c'], help="Returns")
async def code(ctx, deck_code):
    async with aiohttp.ClientSession() as s:
        async with s.get(
                f'https://shadowverse-portal.com/api/v1/deck/import?format=json&deck_code={deck_code}&lang=en') as r:
            data = json.loads(await r.text())["data"]
    if data['clan'] is None:
        return await ctx.send(embed=discord.Embed(title="The deck code is invalid or has expired!"))
    _, deck_url, deck_img = await deck_hash_assets(data["hash"])
    await ctx.send(embed=discord.Embed().add_field(name='\u200b', value=f'**[Deck Link]({deck_url})**'),
                   file=discord.File(deck_img, 'deck.png'))


def colorize_craft(craft, craft_num):
    return f'```{crafts[craft]["markup"].replace("___", craft)}{" " * craft_num}{craft_num}```'


@bot.command(aliases=['j', 'tourney'], help="**Special parameters**:\n\n"
                                            "`ul`: displays the last Unlimited JCG.\n"
                                            "`no arguments/rot`: displays the last Rotation JCG.\n")
async def jcg(ctx, format_='rot'):
    format_ = 'unlimited' if format_ in ('ul', 'unlimited') else 'rotation'
    craft_names = ("", "Forestcraft", "Swordcraft", "Runecraft", "Dragoncraft",
                   "Shadowcraft", "Bloodcraft", "Havencraft", "Portalcraft")
    with open(f'{format_}.json', 'r') as f_:
        tourney = json.load(f_)
    embed = discord.Embed(title=tourney["name"])
    embed.url = f'https://sv.j-cg.com/compe/view/tour/{tourney["code"]}'
    for top in [k for k in tourney.keys() if k not in ["crafts", "code", "name"]]:
        decks = [" / ".join(f'[{craft_names[player["crafts"][i]]}]({player["tinydecks"][i]})'
                            for i in range(len(player["decks"]))) for player in tourney[top]]
        line = [f'{decks[idx]} - {player["player"]}\n' for idx, player in enumerate(tourney[top])]
        embed.add_field(name=f'**TOP{top}**:',
                        value=' '.join(line), inline=False)
    craft_distribution = ''
    for idx, craft in enumerate(tourney["crafts"]):
        craft_distribution += colorize_craft(craft_names[idx + 1], craft)
    embed.add_field(name='**Class distribution**:', value=craft_distribution)
    msg = await ctx.send(embed=embed)
    await reaction_dress(ctx, msg, '_jcg_embed')


@bot.command(aliases=['rr'], help="Maintainer only command.")
@commands.check(lambda ctx: (ctx.message.author.id == MAINTAINER_ID))
async def restart(ctx):
    await ctx.send("Restarting...")
    await bot.close()


@bot.command(alisases=[], help='ttt')
async def update_jcg(ctx):
    from Jcg_utils import update_jcg
    log.info(f'{ctx.message.author} requested a jcg tournament update.')
    msg = await ctx.send(embed=discord.Embed(title="Updating, this message will edit when done."))
    log.info(f'\tupdate started, produced wait message {msg.id}...')
    await update_jcg()
    log.info(f'\t...update terminated.')
    await msg.edit(embed=discord.Embed(title="Update done."))
    log.info(f'edited waiting message {msg.id}')


@bot.command(help='v')
async def sets(ctx):
    ret = ''
    print(expansions)
    for s in list(expansions)[2:]:
        ret += f'{expansions[s][1]:<10} **{s}**\n' + '\n' * (list(expansions).index(s) == len(expansions) - 5)
    msg = await ctx.send(embed=discord.Embed().add_field(name='\u200b', value=ret))
    await reaction_dress(ctx, msg, None)


bot.run(token)
# restart (when rr gets called)
time.sleep(5)
os.execl('/usr/bin/python', os.path.abspath(__file__), *sys.argv)
