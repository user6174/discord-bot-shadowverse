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

with open("token.txt", 'r') as txt:
    token = txt.readline()
description = "~"
bot = commands.Bot(command_prefix='+', description=description)
REACTIONS_COMMANDS_TIMEOUT = 60.0

pool = Pool()


@bot.event
async def on_ready():
    logging.info(f'{bot.user} is active.')


########################################################################################################################
# CARD COMMANDS ########################################################################################################
########################################################################################################################


async def send_card(ctx, card, evo=False):
    logging.info(f'Trying to send card {card + " Evolved" if evo else ""} requested by {ctx.message.author} ')
    card = pool.p[card]
    embed = discord.Embed(title=card["name_"] + " Evolved" * evo)
    embed.add_field(name="Rarity:", value=card["rarity_"], inline=True)
    embed.add_field(name="Craft:", value=card["craft_"])
    embed.add_field(name="Type:", value=card["type_"])
    embed.add_field(name="Trait:", value=card["trait_"])
    embed.add_field(name="Expansion:", value=card["expansion_"])
    if card["type_"] == "Follower":
        embed.add_field(name="Stats: ", value=f'{card["baseAtk_"]}/{card["baseDef_"]} → '
                                              f'{card["evoAtk_"]}/{card["evoDef_"]}\n', inline=False)
        embed.add_field(name="Base effect: ", value=f'{card["baseEffect_"]}\n', inline=False)
        embed.add_field(name="Evo effect: ", value=card["evoEffect_"], inline=False)
    else:
        embed.add_field(name="Effect:", value=card["baseEffect"])
    if evo:
        embed.set_image(url=pool.pic(card["name_"], True))
        embed.set_footer(text=card["evoFlair_"])
    else:
        embed.set_image(url=pool.pic(card["name_"], False))
        embed.set_footer(text=card["baseFlair_"])
    logging.info("About to send...")
    msg = await ctx.send(embed=embed)
    logging.info(f'...successfully sent, producing message {msg.id}.')
    if card["type_"] == "Follower" and not evo:
        await msg.add_reaction("🇪")  # regional indicator E
    try:
        await bot.wait_for("reaction_add",
                           check=lambda r, u: str(r.emoji) == "🇪" and u != msg.author and r.message.id == msg.id,
                           timeout=REACTIONS_COMMANDS_TIMEOUT)
        # TODO: replace this by a message edit+ a toggle to display the normal image back
        await msg.delete()
        await send_card(ctx, card["name_"], evo=True)
    except asyncio.TimeoutError:
        logging.info(f'Reactable status expired on message {msg.id}.')


@bot.command(aliases=['r'], description="""
    Displays a random card[" Token cards are included by default.
    """)  # TODO: flag for excluding tokens, flag for filtering by expansion (or really, by any card attribute).
async def random(ctx):
    logging.info(f'Random card requested by {ctx.message.author}')
    randomCard = pool.get_random_card()
    await send_card(ctx, randomCard)


@bot.command(aliases=['f'], description="""
    Finds all the cards, if any, whose attributes match every card attribute given as input.
    Usage:
        {0}find <card_attribute1> <card_attribute2> ...
        {0}f <card_attribute1> <card_attribute2> ...
        {0}<card_attribute1> <card_attribute2> ...
    Examples: 
        {0}7/4
        {0}abomination
        {0}blood gold summon bat
    """.format(bot.command_prefix))
async def find(ctx, search_terms: list, max_matches=15):
    logging.info("Trying a card search with terms {} requested by {}...".format(search_terms, ctx.message.author))
    logging.info("Trying a search by name...")
    try:
        if len(search_terms.split(' ')) == 1:
            matches = pool.search_by_name(search_terms, max_matches=max_matches)
        else:
            matches = pool.search_by_attributes(search_terms, max_matches=max_matches)
        if len(matches) == 0:
            if len(search_terms.split(' ')) != 1:
                matches = pool.search_by_name(search_terms, max_matches=max_matches)
            else:
                matches = pool.search_by_attributes(search_terms, max_matches=max_matches)
        if len(matches) == 0:
            raise TooManyMatches(0)
    except TooManyMatches as t:
        await ctx.send(embed=discord.Embed(title=f'{t.matches} matches found. Be more precise!'))
    if len(matches) == 1:
        logging.info("...exactly one card found. Sending that.")
        await send_card(ctx, matches[0])
    elif len(matches) > 1:
        # Send list of n result, react to it with n emotes and send an item among those, if requested.
        embed = discord.Embed(title="Possible matches:")
        for i in range(len(matches)):
            embed.add_field(name=hex(i).replace('0x', '').upper(), value=matches[i])
        msg = await ctx.send(embed=embed)
        logging.info("...successfully found multiple matches, producing message {}.".format(msg.id))
        int_to_emote = {0: "0️⃣", 1: "1️⃣", 2: "2️⃣", 3: "3️⃣",
                        4: "4️⃣", 5: "5️⃣", 6: "6️⃣", 7: "7️⃣",
                        8: "8️⃣", 9: "9️⃣", 10: "🇦", 11: "🇧",
                        12: "🇨", 13: "🇩", 14: "🇪", 15: "🇫"}
        emote_to_int = {i: j for j, i in int_to_emote.items()}
        for i in range(len(matches)):
            await msg.add_reaction(int_to_emote[i])
        try:
            reaction, user = await bot.wait_for("reaction_add",
                                                check=lambda r, u: str(r.emoji) in list(emote_to_int)[:len(matches)]
                                                                   and u != msg.author and r.message.id == msg.id,
                                                timeout=REACTIONS_COMMANDS_TIMEOUT)
            card = matches[emote_to_int[reaction.emoji]]
            await send_card(ctx, card)
        except asyncio.TimeoutError:
            logging.info("Reactable status expired on message {}.".format(msg.id))



@bot.event
async def on_command_error(ctx, error):
    """
    If the bot detects a prefix+string message, where string isn't a command, it uses the string to fire a card search.
    """
    if isinstance(error, commands.CommandNotFound):
        search_terms = ctx.message.content.replace(bot.command_prefix, '')
        await find(ctx, search_terms)


bot.run(token)
