import sys

import asyncio
import discord  # https://discordpy.readthedocs.io/en/latest/api.html
from discord.ext import commands  # https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html

import selenium
from selenium.webdriver.chrome.options import Options

from Pool import *
from Jcg_utils import *

# TODO logging, maybe documentation

########################################################################################################################
# GLOBALS ##############################################################################################################
########################################################################################################################

root = logging.getLogger()
root.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
style = logging.Formatter('[%(asctime)s] %(levelname)s - %(funcName)s: %(message)s')
handler.setFormatter(style)
root.addHandler(handler)
pool = Pool()

with open("token.txt", 'r') as txt:
    token = txt.readline()
bot = commands.Bot(command_prefix='+')
emotes = {0: "0️⃣", 1: "1️⃣", 2: "2️⃣", 3: "3️⃣",
          4: "4️⃣", 5: "5️⃣", 6: "6️⃣", 7: "7️⃣",
          8: "8️⃣", 9: "9️⃣", 10: "🇦", 11: "🇧",
          12: "🇨", 13: "🇩", 14: "🇪", 15: "🇫",
          "E": "🇪", "trash": "🗑", "B": "🇧",
          "J": "🇯", "H": "🇭", "F": "🇫", "I": "🇮", "V": "🇻",
          "img": "🖼️", "back": "⬅️", "down": "⬇️"}
MAX_MATCHES_DISPLAY = 15
MAX_MATCHES_LIST = 60
REACTIONS_COMMANDS_TIMEOUT = 60.0  # seconds


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


async def emote_toggle(msg, delete_original, emote, when_toggled, when_toggled_args):
    await msg.add_reaction(emote)
    try:
        reaction, _ = await bot.wait_for("reaction_add",
                                         check=lambda rctn, usr: str(rctn.emoji) == emote
                                                                 and usr != msg.author and rctn.message.id == msg.id,
                                         timeout=REACTIONS_COMMANDS_TIMEOUT)
        logging.info(f'{_} pressed emote {emote} on message {msg.id}, '
                     f'requesting {when_toggled} with arguments {when_toggled_args}.')
        if delete_original:
            await msg.delete()
        await when_toggled(*when_toggled_args)
    except asyncio.TimeoutError:
        logging.info(f'Reactable status expired on message {msg.id} for emote {emote}.')
        await msg.remove_reaction(emote, bot.user)


async def search(ctx, search_terms):
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
        matches = tuple(dict.fromkeys(pool.search_by_name(search_terms) + pool.search_by_attributes(search_terms)))
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


async def send_card(ctx, card, evo=False, img=False, made_by=None):
    logging.info(f'\tSending card {card + (" Evolved" if evo else "")} requested by {ctx.message.author}...')
    card = pool.p[card]
    embed = discord.Embed(title=card["name_"] + " Evolved" * evo)
    # first row
    embed.add_field(name='\u200b',
                    value=f'**Trait**: {card["trait_"]}\n'
                          f'**Type**: {card["type_"]}\n' +
                          (f'**Stats**: {card["baseAtk_"]}/{card["baseDef_"]} → {card["evoAtk_"]}/{card["evoDef_"]}'
                           if card["type_"] == "Follower" else ''),
                    inline=True)
    embed.add_field(name='\u200b',
                    value=
                    f'**Rarity**: {card["rarity_"]}\n'
                    f'**Class**: {card["craft_"]}\n'
                    f'**Expansion**:\n{card["expansion_"]}',
                    inline=True)
    if img:
        embed.set_image(url=pool.pic(card["name_"], evo))
    # second row
    tokens = ""
    for idx, name in enumerate(tuple(dict.fromkeys(card["tokens_"]))):
        tokens += f'{emotes[idx]} {name}\n'
    if tokens != "":
        embed.add_field(name="Related cards:", value=tokens, inline=True)
    # effects
    if card["type_"] == "Follower":
        if card["baseEffect_"] != "":
            embed.add_field(name="Base:", value=f'{card["baseEffect_"]}', inline=False)
        if card["evoEffect_"] != "-":
            embed.add_field(name="Evolved:", value=f'{card["evoEffect_"]}', inline=False)
    else:
        embed.add_field(name="Effect:", value=card["baseEffect_"], inline=False)
    # flair
    if evo:
        embed.set_footer(text=card["evoFlair_"])
    else:
        embed.set_footer(text=card["baseFlair_"])
    msg = await ctx.send(embed=embed)
    logging.info(f'...successfully sent, producing message {msg.id}.')
    # add toggleable emotes
    if made_by is not None:
        asyncio.ensure_future(emote_toggle(msg, True, emotes["back"], send_card, (ctx, made_by, False, img)))
    asyncio.ensure_future(emote_toggle(msg, True, emotes["trash"], lambda _: None, ()))
    asyncio.ensure_future(
        emote_toggle(msg, True, emotes["img"], send_card, (ctx, card["name_"], evo, not img, made_by)))
    if card["type_"] == "Follower":
        if not evo:
            asyncio.ensure_future(emote_toggle(msg, True, emotes["E"], send_card,
                                               (ctx, card["name_"], True, True, made_by)))
        else:
            asyncio.ensure_future(emote_toggle(msg, True, emotes["B"], send_card,
                                               (ctx, card["name_"], evo, img, made_by)))
    for idx, related in enumerate(card["tokens_"]):
        asyncio.ensure_future(emote_toggle(msg, True, emotes[idx], send_card,
                                           (ctx, related, False, img, card["name_"])))


async def card_command_template(ctx, *args):
    print(args)
    args, command = args[:-1], args[-1]
    print(args)
    logging.info(f'Requested card command "{command.__name__}" with search terms "{" ".join(args)}" '
                 f'by {ctx.message.author}')
    card = await search(ctx, ' '.join(args))
    if card is None:
        return
    if type(card) == str:
        await command(ctx, card)
    else:
        await ctx.send(embed=discord.Embed(title=f'{card} matches found. Be more precise!'))


########################################################################################################################
# CARD COMMANDS ########################################################################################################
########################################################################################################################

@bot.remove_command('help')
@bot.command(aliases=['h'], help=":thinking:")
async def help(ctx):
    logging.info(f'Requested help page by {ctx.message.author}')
    await _help(ctx)


async def _help(ctx):
    embed = discord.Embed()
    val = '\n'.join(f'{emotes[str(command)[0].upper()]} {bot.command_prefix}{str(command)}' for command in bot.commands)
    embed.add_field(name="Available commands:\n\u200b", value=val, inline=False)
    embed.add_field(name="General card search usage:\n\u200b", value=
    f'\n• `{bot.command_prefix}<COMMAND> <CARD ATTRIBUTES> <OPTIONAL PARAMETERS>`:\n'
    "The search terms are matched to every card attribute, and minor typos are accepted.\n"
    f'• `{bot.command_prefix}<COMMAND> {bot.command_prefix}<CARD NAME> <OPTIONAL PARAMETERS>`:\n'
    "The search terms are matched to the card name only, typos aren't allowed.\n"
    "\nExamples:\n\n"
    f'• `{bot.command_prefix}img fighter` would return a list of cards whose name contains \"Fighter\",'
    f' or which make `Fighter` tokens.\n'
    f'• `{bot.command_prefix}img {bot.command_prefix}fighter` would return the image of `Fighter`.\n')
    embed.set_footer(
        icon_url="https://panels-images.twitch.tv/panel-126362130-image-d5e33b7d-d6ff-418d-9ec8-d83c2d49739e",
        text="Contact nyx#6294 for bug reports and feedback.")
    msg = await ctx.send(embed=embed)
    asyncio.ensure_future(emote_toggle(msg, True, emotes["trash"], lambda _: None, ()))
    for command in bot.commands:
        asyncio.ensure_future(emote_toggle(msg, True, emotes[str(command)[0].upper()], send_command_help,
                                           (ctx, command)))


async def send_command_help(ctx, command):
    embed = discord.Embed(title=str(command))
    embed.add_field(name='\u200b', value=str(command.help))
    logging.info(f'Requested help info page of command {str(command)}')
    msg = await ctx.send(embed=embed)
    asyncio.ensure_future(emote_toggle(msg, True, emotes["trash"], lambda _: None, ()))
    asyncio.ensure_future(emote_toggle(msg, True, emotes["back"], _help, (ctx,)))


@bot.command(help=
             f'**Usage**:\n\n'
             f'As explained in the main menu. Additionally, a card search can be requested with this shorthand:\n'
             f'• `{bot.command_prefix}<CARD ATTRIBUTES> <OPTIONAL PARAMETERS>`:\n'
             f'• `{bot.command_prefix}{bot.command_prefix}<CARD NAME> <OPTIONAL PARAMETERS>`:\n'
             f'\n**Examples**:\n\n'
             f'• `{bot.command_prefix}abominatioQ`\n'
             f'• `{bot.command_prefix}6/6 rune wld`\n'
             f'• `{bot.command_prefix}2/2 blood gold summon bat` '
             f'(because typos are allowed a search with many terms might contain unusual results)\n'
             f'• `{bot.command_prefix}{bot.command_prefix}azazel,`\n'
             f'• `{bot.command_prefix}{bot.command_prefix}azazel`\n')
async def find(ctx, *args):
    await card_command_template(ctx, *(tuple(args) + (send_card,)))


@bot.command(aliases=['pic', 'art'], help="**Special parameters**:\n\nNone.")
async def img(ctx, *args):
    await card_command_template(ctx, *(tuple(args) + (_img,)))


async def _img(ctx, card_name, evo=False):
    embed = discord.Embed().set_image(url=pool.full_pic(card_name, evo))
    msg = await ctx.send(embed=embed)
    asyncio.ensure_future(emote_toggle(msg, True, emotes["trash"], lambda _: None, ()))
    if pool.p[card_name]["type_"] == "Follower":
        asyncio.ensure_future(emote_toggle(msg, True, emotes["B"] if evo else emotes["E"], _img,
                                           (ctx, card_name, not evo)))


@bot.command(aliases=['v', 'sound', 's'], help="**Special parameters**:\n\nNone.")
async def voice(ctx, *args):
    await card_command_template(ctx, *(tuple(args) + (_voice,)))


async def _voice(ctx, card, language='jp'):
    embed = discord.Embed(title=card)
    options = Options()
    options.add_argument("--headless")
    driver = selenium.webdriver.Chrome(options=options)
    driver.get(f'https://svgdb.me/cards/{pool.p[card]["id_"]}')
    table = driver.find_element_by_xpath("//table")
    print(table)
    game_actions = [action.text for action in table.find_elements_by_xpath("//td") if action.text != ""]
    mp3s = [mp3.get_attribute('src') for mp3 in table.find_elements_by_xpath("//audio")
            if language in mp3.get_attribute('src')]
    print(game_actions)
    print(mp3s)
    for action, mp3 in zip(game_actions, mp3s):
        embed.add_field(name='\u200b', value=f'[{action}]({mp3})', inline=False)
    driver.close()
    msg = await ctx.send(embed=embed)
    asyncio.ensure_future(emote_toggle(msg, True, emotes["trash"], lambda _: None, ()))


@bot.command(help="**Special parameters**:\n\n"
                  "`ul`: displays the last Unlimited JCG."
                  "`no arguments/rot`: displays the last Rotation JCG."
                  "\n\n**Note**:\n\n"
                  "The program may need a minute to fetch the latest JCG if it's not in the internal database yet.")
async def jcg(ctx, format_='rot', tops=('1', '2', '4', '8'), name=None):
    format_ = 'unlimited' if format_ in ('ul', 'unlimited') else 'rotation'
    craft_names = ("", "Forestcraft", "Swordcraft", "Runecraft", "Dragoncraft",
                   "Shadowcraft", "Bloodcraft", "Havencraft", "Portalcraft")
    if tops == ('1', '2', '4', '8'):
        msg = await ctx.send(embed=discord.Embed(title="Fetching data..."))
        name = scrape_jcg(format_, once=True)
        await msg.delete()
    with open(f'{os.getcwd()}/jcg/{format_}/{name}', 'r') as f_:
        tourney = json.load(f_)
    embed = discord.Embed(title=name[:-5])
    embed.url = f'https://sv.j-cg.com/compe/view/tour/{tourney["code"]}'
    for top in tops:
        embed.add_field(name=f'**TOP{top}**', value='\u200b', inline=False)
        for idx, player in enumerate(tourney[top]):
            if idx > 0 and idx % 2:
                embed.add_field(name='\u200b', value='\u200b')
            decks = '\n'.join(f'**[{craft_names[int(deck[59])]}]({deck})**' for deck in player["decks"])
            embed.add_field(name=player["player"], value=decks, inline=True)
    if tops == ('1', '2', '4', '8'):
        craft_distribution = ''
        for idx, craft in enumerate(tourney["crafts"]):
            craft_distribution += f'**{craft}** {craft_names[idx + 1]}\n'
        embed.add_field(name="Class Distribution", value=craft_distribution)
    msg = await ctx.send(embed=embed)
    asyncio.ensure_future(emote_toggle(msg, True, emotes["trash"], lambda _: None, ()))
    if tops == ('1', '2', '4', '8'):
        asyncio.ensure_future(emote_toggle(msg, False, emotes["down"], jcg, (ctx, format_, ('16',), name)))


bot.run(token)
