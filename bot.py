import asyncio
import discord  # https://discordpy.readthedocs.io/en/latest/api.html
from discord.ext import commands  # https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html
import logging
import sys
from Pool import *

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
description = "~"
bot = commands.Bot(command_prefix='+', description=description)
# GLOBALS
REACTIONS_COMMANDS_TIMEOUT = 60.0
emotes = {0: "0️⃣", 1: "1️⃣", 2: "2️⃣", 3: "3️⃣",
          4: "4️⃣", 5: "5️⃣", 6: "6️⃣", 7: "7️⃣",
          8: "8️⃣", 9: "9️⃣", 10: "🇦", 11: "🇧",
          12: "🇨", 13: "🇩", 14: "🇪", 15: "🇫",
          "E": "🇪", "trash": "🗑", "B": "🇧"}
emote_to_int = {i: j for j, i in emotes.items()}
MAX_MATCHES_DISPLAY = 15
MAX_MATCHES_LIST = 60


@bot.event
async def on_ready():
    logging.info(f'{bot.user} is active.')


@bot.remove_command('help')
@bot.command(aliases=['h', 'c', 'commands'])
async def help(ctx):
    pfx = bot.command_prefix
    embed = discord.Embed()
    embed.add_field(name='Usage:', value=
    f'• **{pfx}find** <card attribute 1> <card attribute 2> <...>\n'
    f'• **{pfx}f** <card attribute 1> <card attribute 2> <...>\n'
    f'• **{pfx}**<card attribute 1> <card attribute 2> <...>\n'
    f'• **{pfx}find {pfx}**<card name>\n'
    f'• **{pfx}f {pfx}**<card name>\n'
    f'• **{pfx}{pfx}**<card name>',
                    inline=False)
    embed.add_field(name='Search terms', value=
    f'• **{pfx}<card name>** - An exact search on the given card name, case insensitive.\n'
    '• **<card attribute 1>, <card attribute 2>, <...>** - A search based on card attributes, '
    'case insensitive and accepting minor typos.',
                    inline=False)
    embed.add_field(name='Examples:', value=
    f'{pfx}{pfx}abomination awakened\n'
    f'{pfx}wld rune legend\n')
    await ctx.send(embed=embed)


########################################################################################################################
# CARD COMMANDS ########################################################################################################
########################################################################################################################

async def send_card(ctx, card, evo=False):
    logging.info(f'Trying to send card {card + " Evolved" if evo else ""} requested by {ctx.message.author} ')
    card = pool.p[card]
    embed = discord.Embed()
    # name and expansion
    embed.add_field(name=card["name_"] + " Evolved" * evo,
                    value=f'{card["rarity_"]} {card["craft_"]} {card["type_"]}', inline=True)
    embed.add_field(name="Expansion:", value=f'{card["expansion_"]}', inline=True)
    embed.set_image(url=pool.pic(card["name_"], evo))
    embed.add_field(name='\u200b', value='\u200b')  # separator
    # stats and related
    if card["type_"] == "Follower":
        embed.add_field(name="Stats:", value=f'{card["baseAtk_"]}/{card["baseDef_"]} → '
                                             f'{card["evoAtk_"]}/{card["evoDef_"]}\n', inline=True)
    tokens = "\u200b"
    for idx, name in enumerate(list(dict.fromkeys(card["tokens_"]))):
        tokens += f'{emotes[idx]} {name}\n'
    embed.add_field(name="Related cards:", value=tokens, inline=True)
    embed.add_field(name='\u200b', value='\u200b')
    # effect
    if card["type_"] == "Follower":
        embed.add_field(name="Base effect: ", value=f'\u200b{card["baseEffect_"]}', inline=False)
        embed.add_field(name="Evo effect: ", value=f'\u200b{card["evoEffect_"]}', inline=False)
    else:
        embed.add_field(name="Effect:", value=card["baseEffect_"], inline=False)
    # flair
    if evo:
        embed.set_footer(text=card["evoFlair_"])
    else:
        embed.set_footer(text=card["baseFlair_"])
    logging.info("About to send...")
    msg = await ctx.send(embed=embed)
    logging.info(f'...successfully sent, producing message {msg.id}.')
    # add E emote for displaying evo and see if it's pressed     # add numbers emotes for displaying related and see
    # if they're pressed
    await msg.add_reaction(emotes["trash"])
    monitored_emotes = [emotes["trash"]]
    if card["type_"] == "Follower":
        if not evo:
            await msg.add_reaction(emotes["E"])
            monitored_emotes.append(emotes["E"])
        else:
            await msg.add_reaction(emotes["B"])
            monitored_emotes.append(emotes["B"])
    for idx, related in enumerate(card["tokens_"]):
        await msg.add_reaction(emotes[idx])
        monitored_emotes.append(emotes[idx])

    try:
        reaction, user = \
            await bot.wait_for("reaction_add",
                               check=lambda r, u: str(
                                   r.emoji) in monitored_emotes and u != msg.author and r.message.id == msg.id,
                               timeout=REACTIONS_COMMANDS_TIMEOUT)
        if str(reaction.emoji) == emotes["E"]:
            await msg.delete()
            await send_card(ctx, card["name_"], evo=True)
        elif str(reaction.emoji) == emotes["trash"]:
            await msg.delete()
        elif str(reaction.emoji) == emotes["B"]:
            await msg.delete()
            await send_card(ctx, card["name_"])
        else:
            card = card["tokens_"][emote_to_int[reaction.emoji]]
            await send_card(ctx, card)
    except asyncio.TimeoutError:
        logging.info(f'Reactable status expired on message {msg.id}.')


@bot.command(aliases=['f'])
async def find(ctx, search_terms: list):
    logging.info("Trying a card search with terms {} requested by {}...".format(search_terms, ctx.message.author))
    logging.info("Trying a search by name...")
    if search_terms[0] == bot.command_prefix:
        try:
            search_terms = ' '.join([word[0].upper() + word[1:].lower() for word in search_terms[1:].split(' ')])
            await send_card(ctx, search_terms)
        except KeyError:
            await ctx.send(embed=discord.Embed(title='Exact search failed.'))
        return
    matches = pool.search_by_name(search_terms) + pool.search_by_attributes(search_terms)
    if len(matches) == 0:
        await ctx.send(embed=discord.Embed(title="No matches found. Be more precise!"))
    elif len(matches) == 1:
        logging.info(f'...exactly one card found: [{matches[0]}]. Sending that.')
        await send_card(ctx, matches[0])
    elif len(matches) > MAX_MATCHES_LIST:
        await ctx.send(embed=discord.Embed(title=f'{len(matches)} matches found. Be more precise!'))
    elif len(matches) < MAX_MATCHES_DISPLAY:
        # send list of n result, react to it with n emotes and send an item among those, if requested.
        embed = discord.Embed(title="Possible matches:")
        for idx, card in enumerate(matches):
            embed.add_field(name=emotes[idx], value=card)
        msg = await ctx.send(embed=embed)
        logging.info(f'...successfully found multiple matches, producing message {msg.id}')
        for i in range(len(matches)):
            await msg.add_reaction(emotes[i])
        try:
            reaction, user = await bot.wait_for("reaction_add",
                                                check=lambda r, u: str(r.emoji) in list(emote_to_int)[:len(matches)]
                                                                   and u != msg.author and r.message.id == msg.id,
                                                timeout=REACTIONS_COMMANDS_TIMEOUT)
            card = matches[emote_to_int[reaction.emoji]]
            await send_card(ctx, card)
        except asyncio.TimeoutError:
            logging.info("Reactable status expired on message {}.".format(msg.id))
    else:
        embed = discord.Embed(title="Possible matches:")
        embed.add_field(name='\u200b', value=f'{", ".join(card for card in matches)}')
        await ctx.send(embed=embed)


@bot.event
async def on_command_error(ctx, error):
    """
    If the bot detects a prefix+string message, where string isn't a command, it uses the string to fire a card search.
    """
    if isinstance(error, commands.CommandNotFound):
        search_terms = ctx.message.content[1:]
        await find(ctx, search_terms)


bot.run(token)
