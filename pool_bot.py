import discord  # https://discordpy.readthedocs.io/en/latest/api.html
from Pool import *

pool = Pool()


def send_card(card, evo=False):
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


def send_exact_search(card):
    card = card[1].upper() + card[2:-1].lower()
    if card not in pool:
        return discord.Embed(title="That card doesn't exist.")
    return send_card(card)


def send_search(card, maxMatches):
    matches = pool.search(card, maxMatches)
    if matches:
        if len(matches) == 1:
            return send_card(matches[0])
        else:
            result = discord.Embed(title="Possible matches:")
            for i in range(len(matches)):
                result.add_field(name="{}. ".format(i), value=matches[i])
            return result
    return discord.Embed(title="Too many card matches or invalid card name.")


def send_random_card():
    return send_card(pool.get_random_card())


def react_to_card_embed(embeds):
    if embeds[0].description != discord.Embed.Empty and embeds[0].title != discord.Embed.Empty:
        return "Follower" in embeds[0].description and "[Evolved]" not in embeds[0].title


def reactions_to_card_embed():
    return ["🇪"]  # regional indicator E


def react_to_search_list(embeds):
    return "matches" in embeds[0].title


numEmote = {0: "0️⃣", 1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣",
            5: "5️⃣", 6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣",
            10: "🇦", 11: "🇧", 12: "🇨", 13: "🇩", 14: "🇪"}
emoteNum = {i: j for j, i in numEmote.items()}


def reactions_to_search_list(embeds):
    return [numEmote[i] for i in range(len(embeds[0].fields))]


def requested_send_card_evo(reaction):
    if reaction.message.embeds and reaction.message.embeds != discord.Embed.Empty \
            and str(reaction) == "🇪":
        return "Follower" in reaction.message.embeds[0].description


def card_name_from_embeds(embeds):
    return embeds[0].title


def requested_send_card_from_list(reaction):
    if reaction.message.embeds and reaction.message.embeds != discord.Embed.Empty \
            and str(reaction) in list(emoteNum)[:len(reaction.message.embeds[0].fields) - len(emoteNum)]:
        """str(reaction) in emoteNum doesn't take into account the cases where a list of n cards is reacted to with a
        number higher than n, so one needs to check if the reaction lives in the dictionary truncated to the first n
        entries."""
        return "matches" in reaction.message.embeds[0].title


def send_card_from_list(reaction):
    return send_card(reaction.message.embeds[0].fields[emoteNum[str(reaction)]].value)