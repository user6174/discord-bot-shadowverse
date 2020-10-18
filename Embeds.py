import sys
import logging
import discord  # https://discordpy.readthedocs.io/en/latest/api.html

from Cardpool import *

style = logging.Formatter('%(asctime)s [%(funcName)-19s]  %(message)s')

log = logging.getLogger('discord')
log.setLevel(logging.INFO)
to_log_file = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
to_log_file.setLevel(logging.DEBUG)
to_log_file.setFormatter(style)
log.addHandler(to_log_file)
to_stdout = logging.StreamHandler(sys.stdout)
to_stdout.setFormatter(style)
log.addHandler(to_stdout)

pool = Cardpool()
emotes = {0: "0️⃣", 1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣", 6: "6️⃣", 7: "7️⃣",
          8: "8️⃣", 9: "9️⃣", 10: "🇦", 11: "🇧", 12: "🇨", 13: "🇩", 14: "🇪", 15: "🇫",
          "A": "🇦", "B": "🇧", "C": "🇨", "D": "🇩", "E": "🇪", "F": "🇫", "G": "🇬", "H": "🇭", "I": "🇮", "J": "🇯",
          "K": "🇰", "L": "🇱", "M": "🇲", "N": "🇳", "O": "🇴", "P": "🇵", "Q": "🇶", "R": "🇷", "S": "🇸", "T": "🇹",
          "U": "🇺", "V": "🇻", "W": "🇼", "X": "🇽", "Y": "🇾", "Z": "🇿",
          "trash": "🗑", "img": "🖼️", "art": "🎨", "back": "⬅️", "down": "⬇️", "update": "🔄",
          "en": "🇬🇧", "jp": "🇯🇵", }
crafts = {
    "Neutral": {"hex": 0x0e0e0e},
    "Forestcraft": {"markup": "diff\n+ ___\n",
                    "hex": 0x446424},
    "Swordcraft": {"markup": "autohotkey\n%___%\n",
                   "hex": 0x9b8b26},
    "Runecraft": {"markup": "asciidoc\n= ___\n",
                  "hex": 0x3f48a1},
    "Dragoncraft": {"markup": "css\n[___]\n",
                    "hex": 0x744c1c},
    "Shadowcraft": {"markup": "bash\n#___\n",
                    "hex": 0x9354be},
    "Bloodcraft": {"markup": "diff\n- ___\n",
                   "hex": 0xae354e},
    "Havencraft": {"markup": "\n___\n",
                   "hex": 0x958c6a},
    "Portalcraft": {"markup": "cs\n'___'\n",
                    "hex": 0x2c444c}
}


def _info_embed(card, evo=False, img_=False):
    log.info(f'\tSending card {card + (" Evolved" if evo else "")}...')
    card = pool.names[card]
    embed = discord.Embed(title=card["name_"] + " Evolved" * evo)
    embed.colour = crafts[card["craft_"]]["hex"]
    # first row
    embed.add_field(name='\u200b',
                    value=f'**Cost**: {card["pp_"]}pp\n' +
                          (f'**Trait**: {card["trait_"]}\n' if card["trait_"] != "-" else "") +
                          f'**Type**: {card["type_"]}\n' +
                          (f'**Stats**: {card["baseAtk_"]}/{card["baseDef_"]} → {card["evoAtk_"]}/{card["evoDef_"]}'
                           if card["type_"] == "Follower" else ''),
                    inline=True)
    embed.add_field(name='\u200b',
                    value=
                    f'**Rarity**: {card["rarity_"]}\n'
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
        if card["baseEffect_"] != "-":
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
    sv_wins = {"Neutral": "all", "Forestcraft": "E", "Swordcraft": "R", "Runecraft": "W", "Dragoncraft": "D",
               "Shadowcraft": "Nc", "Bloodcraft": "V", "Havencraft": "B", "Portalcraft": "Nm"}
    embed.set_thumbnail(url=f'https://shadowverse-wins.com/common/img/leader_{sv_wins[card["craft_"]]}.png')
    log.info(f'...successfully sent.')
    return embed, card, evo, img_


def _help_command_embed(command, help_):
    embed = discord.Embed(title=command)
    embed.add_field(name='\u200b', value=help_)
    log.info(f'Requested help page of command {str(command)}')
    return embed,


def _help_embed(bot):
    embed = discord.Embed()
    val = '\n'.join(f'{emotes[str(command)[0].upper()]} {str(command)} [{" ,".join(command.aliases)}]' for command in
                    bot.commands)
    embed.add_field(name="AVAILABLE COMMANDS\n\u200b", value=val, inline=False)
    embed.add_field(name="\nGENERAL USAGE FOR CARD COMMANDS\n\u200b",
                    value=
                    f'• `{bot.command_prefix}<COMMAND> <CARD ATTRIBUTES> <OPTIONAL PARAMETERS>`:\n'
                    " The search terms are matched to **every card attribute**. Typos aren't allowed.\n"
                    f'\n• `{bot.command_prefix}<COMMAND> {bot.command_prefix}<CARD NAME> <OPTIONAL PARAMETERS>`:\n'
                    "The search terms are matched to **the card name only**. Minor typos are accepted.\n")
    embed.add_field(name="\nEXAMPLES\n\u200b", value=
    f'• `{bot.command_prefix}img fighter` would return a list of cards whose name contains \"Fighter\",'
    f' or which make `Fighter` tokens.\n'
    f'• `{bot.command_prefix}img {bot.command_prefix}fighter` would return the image of `Fighter`.\n')
    embed.add_field(name="\nOTHER FEATURES\n\u200b", value=
    '• When a [Shadowverse Portal](https://shadowverse-portal.com/?lang=en) deck link is detected, '
    'its deck code and image are automatically posted.\n', inline=False)
    embed.set_footer(
        icon_url="https://panels-images.twitch.tv/panel-126362130-image-d5e33b7d-d6ff-418d-9ec8-d83c2d49739e",
        text="Contact nyx#6294 for bug reports and feedback.")
    return embed


def _img_embed(card_name, evo=False, alt=None):
    id_ = pool.names[card_name]["id_"] if alt is None else pool.names[card_name]["alts_"][alt]
    embed = discord.Embed(title=card_name + " Evolved" * evo).set_footer(
        text=f'Alternative art #{alt}' if alt is not None else '\u200b').set_image(url=full_pic(id_, evo))
    return embed, card_name, evo, alt

# TODO FINIRE LOGGING E COMMENTI E DOC
