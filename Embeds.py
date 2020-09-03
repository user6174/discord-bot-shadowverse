import sys
import logging
import discord  # https://discordpy.readthedocs.io/en/latest/api.html
from requests_html import AsyncHTMLSession

from Pool import *

root = logging.getLogger()
root.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
style = logging.Formatter('[%(asctime)s] %(levelname)s - %(funcName)s: %(message)s')
handler.setFormatter(style)
root.addHandler(handler)
pool = Pool()
emotes = {0: "0️⃣", 1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣", 6: "6️⃣", 7: "7️⃣",
          8: "8️⃣", 9: "9️⃣", 10: "🇦", 11: "🇧", 12: "🇨", 13: "🇩", 14: "🇪", 15: "🇫",
          "E": "🇪", "B": "🇧", "J": "🇯", "H": "🇭", "F": "🇫", "I": "🇮", "R": "🇷", "V": "🇻",
          "trash": "🗑", "img": "🖼️", "back": "⬅️", "down": "⬇️",
          "en": "🇬🇧", "jp": "🇯🇵"}


def _card_info_embed(card, evo=False, img_=False):
    logging.info(f'\tSending card {card + (" Evolved" if evo else "")}...')
    card = pool.p[card]
    embed = discord.Embed(title=card["name_"] + " Evolved" * evo)
    # first row
    embed.add_field(name='\u200b',
                    value=f'**Cost**: {card["pp_"]}pp\n'
                          f'**Trait**: {card["trait_"]}\n'
                          f'**Type**: {card["type_"]}\n' +
                          (f'**Stats**: {card["baseAtk_"]}/{card["baseDef_"]} → {card["evoAtk_"]}/{card["evoDef_"]}'
                           if card["type_"] == "Follower" else ''),
                    inline=True)
    embed.add_field(name='\u200b',
                    value=
                    f'**Rarity**: {card["rarity_"]}\n'
                    f'**Class**: {card["craft_"]}\n'
                    f'**Expansion**: {card["expansion_"]}\n' +
                    (f'**Alts**: {", ".join([pool.ids[str(alt)]["expansion_"] for alt in card["alts_"]])}'
                     if card["alts_"] else ''),
                    inline=True)
    if img_:
        embed.set_image(url=pool.pic(card["name_"], evo))
    # second row
    tokens = ""
    for idx, name in enumerate(card["tokens_"]):
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
    logging.info(f'...successfully sent.')
    return embed, card, evo, img_


def _help_command_embed(command):
    embed = discord.Embed(title=str(command))
    embed.add_field(name='\u200b', value=str(command.help))
    logging.info(f'Requested help info page of command {str(command)}')
    return embed,


def _help_embed(bot):
    embed = discord.Embed()
    val = '\n'.join(f'{emotes[str(command)[0].upper()]} {str(command)} [*{" ,".join(command.aliases)}*]' for command in bot.commands)
    embed.add_field(name="Available commands:\n\u200b", value=val, inline=False)
    embed.add_field(name="General card search usage:\n\u200b", value=
    f'\n• `{bot.command_prefix}<COMMAND> <CARD ATTRIBUTES> <OPTIONAL PARAMETERS>`:\n'
    "The search terms are matched to **every card attribute**, and minor typos are accepted.\n"
    f'• `{bot.command_prefix}<COMMAND> {bot.command_prefix}<CARD NAME> <OPTIONAL PARAMETERS>`:\n'
    "The search terms are matched to **the card name only**, typos aren't allowed.\n"
    "\nExamples:\n\n"
    f'• `{bot.command_prefix}img fighter` would return a list of cards whose name contains \"Fighter\",'
    f' or which make `Fighter` tokens.\n'
    f'• `{bot.command_prefix}img {bot.command_prefix}fighter` would return the image of `Fighter`.\n')
    embed.set_footer(
        icon_url="https://panels-images.twitch.tv/panel-126362130-image-d5e33b7d-d6ff-418d-9ec8-d83c2d49739e",
        text="Contact nyx#6294 for bug reports and feedback.")
    return embed


def _img_embed(card_name, evo=False, alt=None):
    id_ = pool.p[card_name]["id_"] if alt is None else pool.p[card_name]["alts_"][alt]
    embed = discord.Embed(title=card_name + " Evolved" * evo).set_footer(text=f'Alternative art #{alt}' if alt is not None else '\u200b').set_image(url=full_pic(id_, evo))
    return embed, card_name, evo, alt


async def _async_voice_embed(card, language='jp'):
    session = AsyncHTMLSession()
    embed = discord.Embed(title=f'{emotes[language]} {card}')
    r = await session.get(f'https://svgdb.me/cards/{pool.p[card]["id_"]}')
    await r.html.arender()
    mp3s = r.html.find('tbody')[0]
    mp3s = mp3s.find('tr')
    for mp3 in mp3s:
        content = mp3.find('td')
        action = content[0].text
        va = content[1 if language == 'jp' else 2].find('audio')[0].attrs["src"]
        embed.add_field(name='\u200b', value=f'**[{action}]({va})**', inline=False)
    return embed, card