import asyncio
import discord  # https://discordpy.readthedocs.io/en/latest/api.html
from discord.ext import commands  # https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html

from Pool import *
pool = Pool()
from Table import *
table = Table()

import logging
import sys
root = logging.getLogger()
root.setLevel(logging.DEBUG)
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


@bot.event
async def on_ready():
    logging.info("{} is now active.".format(bot.user))


########################################################################################################################
# CARD COMMANDS ########################################################################################################
########################################################################################################################


async def send_card(ctx, card, evo=False):
    logging.info("Trying to send card [{}] {} requested by {}...".format(card, "(evolved)" * evo, ctx.message.author))
    card = pool[card]
    embed = discord.Embed(title=card.name + " [Evolved]" * evo,
                          description="{} {} {} from {}".format(card.rarity, card.craft, card.type, card.expac))
    if card.type == "Follower":
        embed.add_field(name="Stats: ", value="{}/{} → {}/{}\n".format(card.attack, card.defense,
                                                                       card.evoAttack, card.evoDefense))
        embed.add_field(name="Base effect: ", value="{}\n".format(card.effect), inline=False)
        embed.add_field(name="Evo effect: ", value=card.evoEffect, inline=False)
    else:
        embed.add_field(name="Effect:", value=card.effect)
    if evo:
        embed.set_image(url=card.evoPic)
        embed.set_footer(text=card.evoFlair)
    else:
        embed.set_image(url=card.pic)
        embed.set_footer(text=card.flair)
    msg = await ctx.send(embed=embed)
    logging.info("...successfully sent, producing message {}.".format(msg.id))
    if card.type == "Follower" and not evo:
        await msg.add_reaction("🇪")  # regional indicator E
        try:
            await bot.wait_for("reaction_add",
                               check=lambda r, u: str(r.emoji) == "🇪" and u != msg.author and r.message.id == msg.id,
                               timeout=REACTIONS_COMMANDS_TIMEOUT)
            await msg.delete()  # TODO: replace this by a message edit+ a toggle to display the normal image back
            await send_card(ctx, card.name, evo=True)
        except asyncio.TimeoutError:
            logging.info("Reactable status expired on message {}.".format(msg.id))


@bot.command(aliases=['r'], description="""
    Displays a random card. Token cards are included by default.
    """)  # TODO: flag for excluding tokens, flag for filtering by expansion (or really, by any card attribute).
async def random(ctx):
    logging.info("Random card requested by {}.".format(ctx.message.author))
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
async def find(ctx, *searchTerms, maxMatches=15):
    numEmote = {0: "0️⃣", 1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣",
                5: "5️⃣", 6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣",
                10: "🇦", 11: "🇧", 12: "🇨", 13: "🇩", 14: "🇪"}
    emoteNum = {i: j for j, i in numEmote.items()}

    searchTerms = list(searchTerms)
    logging.info("Trying a card search with terms {} requested by {}...".format(searchTerms, ctx.message.author))
    if len(searchTerms) == 1:
        logging.info("Only one parameter passed, trying a search by name...")
        matches = pool.search_by_name(searchTerms[0], maxMatches=maxMatches)
        if not matches:
            logging.info("...search by name failed, trying a search by single attribute...")
            matches = pool.search_by_attributes(searchTerms[0], maxMatches=maxMatches)
    else:
        logging.info("Multiple parameters passed, trying a search by multiple attributes...")
        matches = pool.search_by_attributes(*searchTerms, maxMatches=maxMatches)
    if matches:
        if len(matches) == 1:
            logging.info("...exactly one card found. Sending that.")
            await send_card(ctx, matches[0])
        else:
            # [1] Send list of n result, react to it with n emotes and send an item among those, if requested.
            embed = discord.Embed(title="Possible matches:")
            for i in range(len(matches)):
                embed.add_field(name=str(i), value=matches[i])
            msg = await ctx.send(embed=embed)
            logging.info("...successfully found multiple matches, producing message {}.".format(msg.id))
            for i in range(len(matches)):
                await msg.add_reaction(numEmote[i])
            try:
                reaction, user = await bot.wait_for("reaction_add",
                                                    check=lambda r, u: str(r.emoji) in list(emoteNum)[:len(matches)] \
                                                                       and u != msg.author and r.message.id == msg.id,
                                                    timeout=REACTIONS_COMMANDS_TIMEOUT)
                card = matches[emoteNum[reaction.emoji]]
                await send_card(ctx, card)
            except asyncio.TimeoutError:
                logging.info("Reactable status expired on message {}.".format(msg.id))
            # End of [1].
    else:
        await ctx.send("Too many matches, or no match.")


@bot.event
async def on_command_error(ctx, error):
    """
    If the bot detects a prefix+string message, where string isn't a command, it uses the string to fire a card search.
    """
    if isinstance(error, commands.CommandNotFound):
        searchTerms = tuple(ctx.message.content.replace(bot.command_prefix, '').split())
        await find(ctx, *searchTerms)


########################################################################################################################
# CUBE COMMANDS ########################################################################################################
########################################################################################################################

# TODO

########################################################################################################################
# MEME COMMANDS ########################################################################################################
########################################################################################################################

@bot.command()
async def trash(ctx):
    """
    Mattia special guest in the house tonight
    """
    msg = await ctx.send("🗑️")
    await msg.add_reaction("🗑️")


bot.run(token)
