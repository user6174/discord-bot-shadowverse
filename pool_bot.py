import discord  # https://discordpy.readthedocs.io/en/latest/api.html
from Pool import *

pool = Pool()


def card_to_embed(card, evo=False):
    card = pool[card]
    embed = discord.Embed(title=card.name + " [Evolved]" * evo,
                          description="{} {} {}".format(card.rarity, card.craft, card.type))
    if card.type == "Follower":
        embed.add_field(name="Base effect: ", value=card.effect)
        embed.add_field(name="Base stats: ", value="{}/{}".format(card.attack, card.defense))
        embed.add_field(name="\u200B", value="\u200B", inline=False)  # Separator
        embed.add_field(name="Evo effect: ", value=card.evoEffect)
        embed.add_field(name="Evo stats: ", value="{}/{}".format(card.evoAttack, card.evoDefense))
    else:
        embed.add_field(name="Effect:", value=card.effect)
    if evo:
        embed.set_image(url=card.evoPic)
        embed.set_footer(text=card.evoFlair)
    else:
        embed.set_image(url=card.pic)
        embed.set_footer(text=card.flair)
    return embed


def out_exact_search(card):
    card = card[1].upper() + card[2:-1].lower()
    if card not in pool:
        return discord.Embed(title="That card doesn't exist.")
    return card_to_embed(card)


def out_search(card):
    matches = pool.search(card, maxMatches=25)
    if matches:
        if len(matches) == 1:
            return card_to_embed(matches[0])
        else:
            result = discord.Embed(title="Possible matches:")
            for i in range(len(matches)):
                result.add_field(name=str(i + 1), value=matches[i], inline=True)
            return result
    return discord.Embed(title="Too many card matches or invalid card name.")


def out_random_card():
    return card_to_embed(pool.get_random_card())
