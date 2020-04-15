import discord  # https://discordpy.readthedocs.io/en/latest/api.html
from discord.ext import commands  # https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html
from Pool import *
from Table import *

token = 'Njg0MTQyODIwMTIyMjk2MzQ5.Xl13Ww.52HjCT9BrAxD75rf-TPHKe6dD2s'
description = "questa appare all'inizio se si scrive prefisso + help"
bot = commands.Bot(command_prefix='+', description=description)
pool = Pool()
REACTIONS_COMMANDS_TIMEOUT = 60.0


@bot.event
async def on_ready():
    print("we in boi")


########################################################################################################################
# CARD COMMANDS ########################################################################################################
########################################################################################################################

async def send_card(ctx, card, evo=False):
    card = pool[card]
    embed = discord.Embed(title=card.name + " [Evolved]" * evo,
                          description="{} {} {}".format(card.rarity, card.craft, card.type))
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
    if card.type == "Follower" and not evo:
        await msg.add_reaction("🇪")  # regional indicator E
        await bot.wait_for("reaction_add",
                           check=lambda r, u: str(r.emoji) == "🇪" and u != msg.author and r.message.id == msg.id,
                           timeout=REACTIONS_COMMANDS_TIMEOUT)
        await msg.delete()  # Perhaps more elegant to edit the message and put a back to normal toggle reaction.
        await send_card(ctx, card.name, evo=True)


@bot.command()
async def random(ctx):
    """docstring di random"""
    randomCard = pool.get_random_card()
    await send_card(ctx, randomCard)


@bot.command()
async def find(ctx, *args, maxMatches=15):
    """docstring di find"""

    numEmote = {0: "0️⃣", 1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣",
                5: "5️⃣", 6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣",
                10: "🇦", 11: "🇧", 12: "🇨", 13: "🇩", 14: "🇪"}
    emoteNum = {i: j for j, i in numEmote.items()}

    if len(args) == 1:
        matches = pool.search_by_name(args[0], maxMatches=maxMatches)
    else:
        matches = pool.search_by_attributes(args, maxMatches=maxMatches)
    if matches:
        if len(matches) == 1:
            await send_card(ctx, matches[0])
        else:
            # [1] Send list of n result, react to it with n emotes and send the n-th item if requested.
            embed = discord.Embed(title="Possible matches:")
            for i in range(len(matches)):
                embed.add_field(name=str(i), value=matches[i])
            msg = await ctx.send(embed=embed)
            for i in range(len(matches)):
                await msg.add_reaction(numEmote[i])
            reaction, user = await bot.wait_for("reaction_add",
                                                check=lambda r, u: str(r.emoji) in list(emoteNum)[:len(matches)] \
                                                                   and u != msg.author and r.message.id == msg.id,
                                                timeout=REACTIONS_COMMANDS_TIMEOUT)
            card = matches[emoteNum[reaction.emoji]]
            await send_card(ctx, card)
            # End of [1].
    else:
        await ctx.send("Too many matches, or no match.")


@bot.event
async def on_command_error(ctx, error):
    if error == "CommandNotFound":
        await ctx.send("test")


@bot.command()
async def trash(ctx):
    msg = await ctx.send("🗑️")
    await msg.add_reaction("🗑️")
bot.run(token)
