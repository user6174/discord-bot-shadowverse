import asyncio

from discord.ext import commands  # https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html
from Embeds import *
from Embeds import _help_embed, _help_command_embed, _img_embed, _card_info_embed, _voice_embed
from Jcg_utils import *
import pyshorteners

# TODO think about indexing dict by ids, ready for jp ui (cv field), tidy up after embeds,
#  find a way to reuse reactions on message edit

########################################################################################################################
# GLOBALS ##############################################################################################################
########################################################################################################################

with open("token.txt", 'r') as txt:
    token = txt.readline()
bot = commands.Bot(command_prefix='+')
MAX_MATCHES_DISPLAY = 15
MAX_MATCHES_LIST = 60
REACTIONS_COMMANDS_TIMEOUT = 120.0  # seconds


########################################################################################################################
# EVENTS ###############################################################################################################
########################################################################################################################


@bot.event
async def on_ready():
    logging.info(f'{bot.user} is active.')
    await bot.change_presence(activity=discord.Game(f'{bot.command_prefix}help/{bot.command_prefix}h'))


@bot.event
async def on_command_error(ctx, error):
    """command prefix + string defaults to find(string)"""
    if isinstance(error, commands.CommandNotFound):
        logging.info(f'Requested a card info page with arguments {ctx.message.content[1:]} by {ctx.message.author}')
        await find(ctx, ctx.message.content[1:])


########################################################################################################################
# GENERICS #############################################################################################################
########################################################################################################################


async def _card_command_embed(ctx, *args):
    search_terms, embed_maker = args[:-1], args[-1]
    logging.info(f'Requested card command "{embed_maker.__name__}" with search terms "{" ".join(search_terms)}" '
                 f'by {ctx.message.author}')
    card = await search(ctx, ' '.join(search_terms))
    if card is None:
        return
    if type(card) == str:
        return embed_maker(card)
    else:
        await ctx.send(embed=discord.Embed(title=f'{card} matches found. Be more precise!'))


async def emote_toggle(msg, emote, main_embed, embed_maker, embed_maker_args):
    await msg.add_reaction(emote)
    try:
        reaction, user = await bot.wait_for("reaction_add",
                                            check=lambda rctn, usr: str(rctn.emoji) == emote
                                                                    and usr != msg.author and rctn.message.id == msg.id,
                                            timeout=REACTIONS_COMMANDS_TIMEOUT)
        logging.info(f'{user} pressed emote {emote} on message {msg.id}, '
                     f'requesting {embed_maker.__name__}{embed_maker_args}.')
        new_embed = embed_maker(*embed_maker_args)[0]
        if new_embed is None:  # for trash emote
            return await msg.delete()
        await msg.remove_reaction(member=user, emoji=reaction)
        await msg.remove_reaction(member=bot.user, emoji=reaction)
        await msg.edit(embed=new_embed)
        if new_embed != main_embed:
            return asyncio.ensure_future(emote_toggle(msg, emotes["back"], main_embed,
                                                      lambda _: (main_embed,), (None,)))
    except asyncio.TimeoutError:
        try:
            logging.info(f'Reactable status expired on message {msg.id} for emote {emote}.')
            await msg.remove_reaction(emote, bot.user)
        except discord.errors.NotFound:
            pass


async def search(ctx, search_terms) -> str:
    logging.info(f'Trying a card search with search terms "{search_terms}" requested by {ctx.message.author}...')
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
        logging.info(f'...exactly one card found. Returning that.')
        return matches[0]
    elif len(matches) > MAX_MATCHES_LIST:
        logging.info(f'...{len(matches)} cards found, too many to list (listing limit: {MAX_MATCHES_LIST}).')
        return len(matches)
    elif len(matches) < MAX_MATCHES_DISPLAY:
        logging.info(f'\t...{len(matches)} cards found, returning an option menu '
                     f'(displaying limit: {MAX_MATCHES_DISPLAY})...')
        embed = discord.Embed(title="Possible matches:")
        for idx, card in enumerate(matches):
            embed.add_field(name=emotes[idx], value=card)
        msg = await ctx.send(embed=embed)
        logging.info(f'\t...produced option menu {msg.id}...')
        monitored_emotes = []
        for i in range(len(matches)):
            await msg.add_reaction(emotes[i])
            monitored_emotes.append(emotes[i])
        try:
            reaction, user = await bot.wait_for("reaction_add",
                                                check=lambda r, u: str(r.emoji) in monitored_emotes
                                                                   and u != msg.author and r.message.id == msg.id,
                                                timeout=REACTIONS_COMMANDS_TIMEOUT)
            await msg.delete()
            card = matches[{v: k for k, v in emotes.items()}[reaction.emoji]]
            logging.info(f'...returned card {card} from option menu {msg.id}, requested by {user}.')
            return card
        except asyncio.TimeoutError:
            logging.info(f'Reactable status expired on message {msg.id}.')
    else:
        logging.info(f'...found {len(matches)} matches, listing them.')
        embed = discord.Embed(title="Possible matches:")
        embed.add_field(name='\u200b', value=f'{", ".join(card for card in matches)}')
        await ctx.send(embed=embed)
        return None


########################################################################################################################
# CARD COMMANDS ########################################################################################################
########################################################################################################################

@bot.remove_command('help')
@bot.command(aliases=['h'], help=":thinking:")
async def help(ctx):
    logging.info(f'Requested help page by {ctx.message.author}')
    embed = _help_embed(bot)
    msg = await ctx.send(embed=embed)
    asyncio.ensure_future(emote_toggle(msg, emotes["trash"], discord.Embed(), lambda _: (None,), (None,)))
    for command in bot.commands:
        asyncio.ensure_future(emote_toggle(msg, emotes[str(command)[0].upper()], embed, _help_command_embed, (command,)))


@bot.command(help=
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
    embed, card, evo, img_ = await _card_command_embed(ctx, *(tuple(args) + (_card_info_embed,)))
    msg = await ctx.send(embed=embed)
    asyncio.ensure_future(emote_toggle(msg, emotes["trash"], discord.Embed(), lambda _: (None,), (None,)))
    asyncio.ensure_future(
        emote_toggle(msg, emotes["img"], embed, _card_info_embed, (card["name_"], evo, not img_)))
    if card["type_"] == "Follower":
        if not evo:
            asyncio.ensure_future(emote_toggle(msg, emotes["E"], embed, _card_info_embed,
                                               (card["name_"], True, True)))
        else:
            asyncio.ensure_future(emote_toggle(msg, emotes["B"], embed, _card_info_embed,
                                               (card["name_"], evo, img_)))
    for idx, related in enumerate(card["tokens_"]):
        asyncio.ensure_future(emote_toggle(msg, emotes[idx], embed, _card_info_embed,
                                           (related, False, img_)))


@bot.command(aliases=['pic', 'art'], help="**Special parameters**:\n\nNone.")
async def img(ctx, *args):
    embed, card_name, evo, alt = await _card_command_embed(ctx, *(tuple(args) + (_img_embed,)))
    msg = await ctx.send(embed=embed)
    asyncio.ensure_future(emote_toggle(msg, emotes["trash"], embed, lambda _: (None,), (None,)))
    if pool.p[card_name]["type_"] == "Follower":
        asyncio.ensure_future(emote_toggle(msg, emotes["B"] if evo else emotes["E"], embed, _img_embed,
                                           (card_name, not evo, None)))
    for alt_idx in range(len(pool.p[card_name]["alts_"])):
        asyncio.ensure_future(emote_toggle(msg, emotes[alt_idx], embed, _img_embed, (card_name, evo, alt_idx)))


@bot.command(aliases=['v', 'sound', 's'], help="**Special parameters**:\n\nNone.")
async def voice(ctx, *args):
    embed, card_name = await _card_command_embed(ctx, *(tuple(args) + (_voice_embed,)))
    msg = await ctx.send(embed=embed)
    asyncio.ensure_future(emote_toggle(msg, emotes["trash"], discord.Embed(), lambda _: (None,), (None,)))
    asyncio.ensure_future(emote_toggle(msg, emotes["en"], embed, _voice_embed, (card_name, 'en')))


@bot.command(help="**Special parameters**:\n\n"
                  "`ul`: displays the last Unlimited JCG."
                  "`no arguments/rot`: displays the last Rotation JCG."
                  "\n\n**Note**:\n\n"
                  "The program may need a minute to fetch the latest JCG if it's not in the internal database yet.")
async def jcg(ctx, format_='rot'):
    shortener = pyshorteners.Shortener()
    format_ = 'unlimited' if format_ in ('ul', 'unlimited') else 'rotation'
    craft_names = ("", "Forestcraft", "Swordcraft", "Runecraft", "Dragoncraft",
                   "Shadowcraft", "Bloodcraft", "Havencraft", "Portalcraft")
    msg = await ctx.send(embed=discord.Embed(title="Fetching data..."))
    name = scrape_jcg(format_, once=True)
    logging.info(f'Using {name}')
    file_path = f'{os.getcwd()}/jcg/{format_}/{name}'
    try:
        with open(file_path, 'r') as f_:
            tourney = json.load(f_)
            tourney["crafts"]  # KeyError probe
    except FileNotFoundError:
        logging.info(f'Failed opening file {file_path}.')
        await ctx.send('Failed retrieving data :wilted_rose:')
    except KeyError:
        logging.info(f'File {file_path} is corrupt. Deleting it and trying again.')
        os.remove(file_path)
        return await jcg(ctx, format_)
    embed = discord.Embed(title=name[:-5])
    embed.url = f'https://sv.j-cg.com/compe/view/tour/{tourney["code"]}'
    for top in [k for k in tourney.keys() if k not in ["crafts", "code"]]:
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
    asyncio.ensure_future(emote_toggle(msg, True, emotes["trash"], lambda _: (None,), (None,)))

bot.run(token)
