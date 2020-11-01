import json
import sys
import asyncio
import logging
from abc import abstractmethod

import discord
import natsort
from discord.ext import commands  # https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html
from emoji import emojize, demojize

from Jcg_utils import update_jcgs
from Library import Library

# Logging is setup to write to .../current_directory/bot.log and to stdout.
style = logging.Formatter('%(asctime)s [%(funcName)-19s]  %(message)s')
log = logging.getLogger('discord')
log.setLevel(logging.INFO)
to_log_file = logging.FileHandler(filename='bot.log', encoding='utf-8', mode='w')
to_log_file.setFormatter(style)
log.addHandler(to_log_file)
to_stdout = logging.StreamHandler(sys.stdout)
to_stdout.setFormatter(style)
log.addHandler(to_stdout)

LIB = Library()
MAX_WATCHED_MSGS = 10
REACTIONS_TIMEOUT = 120  # s
PREFIX = '!'
bot = commands.Bot(command_prefix=PREFIX)

# markup: colorizes text in discord formatting (___ is the placeholder for the text)
# hex: color in hex
# icon: code for https://shadowverse-wins.com icons
CRAFTS = {
    "Neutral": {"markup": None, "hex": 0x0e0e0e, "icon": "all"},
    "Forestcraft": {"markup": "diff\n+ ___\n", "hex": 0x446424, "icon": "E"},
    "Swordcraft": {"markup": "autohotkey\n%___%\n", "hex": 0x9b8b26, "icon": "R"},
    "Runecraft": {"markup": "asciidoc\n= ___\n", "hex": 0x3f48a1, "icon": "W"},
    "Dragoncraft": {"markup": "css\n[___]\n", "hex": 0x744c1c, "icon": "D"},
    "Shadowcraft": {"markup": "bash\n#___\n", "hex": 0x9354be, "icon": "Nc"},
    "Bloodcraft": {"markup": "diff\n- ___\n", "hex": 0xae354e, "icon": "V"},
    "Havencraft": {"markup": "\n___\n", "hex": 0x958c6a, "icon": "B"},
    "Portalcraft": {"markup": "cs\n'___'\n", "hex": 0x2c444c, "icon": "Nm"}
}


def plot_craft(craft_name, craft_val):
    return f'```{CRAFTS[craft_name]["markup"].replace("___", craft_name)}{" " * craft_val}{craft_val}```'


def hyperlink(txt, link) -> str:
    return f'[**{txt}**]({link})'


def int_to_emoji(n):
    return f':keycap_{n}:'


def chr_to_emoji(c):
    return f':regional_indicator_symbol_letter_{c}:'


def int_emojis(l):
    return filter(lambda e: 'keycap' in e, l)


def chr_emojis(l):
    return filter(lambda e: 'regional' in e, l)


def local_scope_str(obj) -> str:
    """
    :returns the current couples field/value belonging to the input object, for logging purposes.
    """
    ret = '('
    for k, v in obj.__dict__.items():
        if k not in ("ctx", "msg"):
            ret += f'{k} -> {v}, '
    ret += '\b\b)'
    return f'{obj.__class__}\t{ret}'


class MyMsg(object):
    """
    This class creates and manages the messages requested by the bot commands.
    """
    __all__ = {}  # A cache of the last MAX_WATCHED_MSGS messages.

    def __init__(self, ctx=None):
        # Empty initialization of the typical variables used by the bot.
        self.ctx: discord.ext.commands.Context or None = ctx
        self.embed: discord.embeds.Embed or None = None
        self.msg: discord.message.Message or None = None
        # A list of the emojis that, if added to the message as a reaction, cause the class to modify the message.
        self.monitored_emojis = {':wastebasket:'}
        log.info(local_scope_str(self))

    @classmethod
    def from_dict(cls, dict_):
        """
        A constructor that initializes any subclass of MyMsg with the fields of another instance of that same class.
        Used to bypass the default begin-of-existence constructors,
        so that the embed of already existing messages can be immediately edited.
        :param dict_: obj.__dict__, where obj is the MyMsg object whose embed needs to be edited.
        """
        obj = MyMsg()
        obj.__class__ = cls  # Preparing an empty instance of the target class.
        for name, value in dict_.items():
            obj.__setattr__(name, value)
        log.info(local_scope_str(obj))
        return obj

    @abstractmethod
    def edit_embed(self):
        return

    def dress(self):
        """
        Reacts to the message with the emojis in monitored_emojis.
        """
        emojis = natsort.natsorted(self.monitored_emojis)
        log.info(emojis)
        for emoji in emojis:
            asyncio.create_task(self.msg.add_reaction(emojize(emoji)))

    async def dispatch(self):
        """
        Sends the message, dresses it and adds it to the class cache, making space if necessary.
        """
        self.msg = await self.ctx.send(embed=self.embed)
        self.dress()
        MyMsg.__all__[self.msg.id] = self
        log.info(f'sending msg {self.msg.id} (len(__all__) = {len(MyMsg.__all__)})')
        if len(MyMsg.__all__) > MAX_WATCHED_MSGS:
            oldest_msg = min(MyMsg.__all__.keys())  # msg.id is its timestamp
            await MyMsg.__all__[oldest_msg].abandon()

    async def abandon(self, delete_msg=False):
        """
        An abandoned message gets dropped from the internal cache and becomes inert to reactions.
        """
        log.info(f'abandoning msg {self.msg.id} (delete -> {delete_msg}, len(__all__) -> {len(MyMsg.__all__)})')
        del MyMsg.__all__[self.msg.id]
        if delete_msg:
            await self.msg.delete()

    @classmethod
    def on_emoji_toggle(cls, msg_id, emoji, user):
        """
        Modifies the embed in the internal cache with matching id according to the toggled emoji.
        The user reaction using the input emoji is cleared for convenience, making it easier for them to request
        corresponding command again.
        """
        try:
            obj = cls.__all__[msg_id]
        except KeyError:  # The message was already deleted due to __all__ being too full.
            log.info(f'msg {msg_id} has already been deleted')
            return
        new_args = obj.edit_args(emoji)
        if new_args is None:  # The trash emoji was pressed.
            asyncio.create_task(obj.abandon(delete_msg=True))
            return
        new_obj = obj.__class__.from_dict(new_args)
        new_obj.edit_embed()
        asyncio.create_task(obj.msg.edit(embed=new_obj.embed))
        asyncio.create_task(obj.msg.remove_reaction(emojize(emoji), user))

    def edit_args(self, emoji):
        """
        In the subclasses' implementations this method will manipulate the __dict__ of a message object according to the
        emote pressed. If an emote corresponds to some special instruction that goes beyond the scope of modifying the
        object's embed, side effects are also executed here.
        Returning None will delete the message, and returning an unmodified __dict__ won't edit it.
        """
        if emoji == ':wastebasket:':
            return
        return self.__dict__


card_search_doc = """
**SYNOPSIS FOR CARD COMMANDS**
`{pfx}<CARD_COMMAND> <CARD_NAME> <CARD_COMMAND_FLAGS>`
`{pfx}<CARD_COMMAND> <CARD_NAME> -l <CARD_COMMAND_FLAGS>`
`{pfx}<CARD_COMMAND> <CARD_ATTRIBUTES> -a <CARD_COMMAND_FLAGS>`

**DESCRIPTION**
The default search tries to present the cards you're most likely to want while being exhaustive, but should it happen that this results in too narrow or too wide a list of matches, you can make use of **-l** and **-a**. Case insensitive, minor typos are allowed only when looking up a card name.

**OPTIONS**
**-l**, **--lax**
Relaxes the search from returning the card name exactly matching with the search terms to the cards containing the search terms in the name.
**-a**, **--attrs**
Matches the search terms only with the card's attributes, such as attack, effect and expansion (expansion shorthands are supported).

**EXAMPLES**
"""
print(card_search_doc)


class HelpMsg(MyMsg):
    def __init__(self, ctx, command):
        super().__init__(ctx=ctx)
        self.command = command
        for cmd in bot.commands:
            initial_emoji = chr_to_emoji(str(cmd)[0])
            self.monitored_emojis.add(initial_emoji)
        self.monitored_emojis.add(':open_book:')
        self.edit_embed()
        log.info('went in edit embed')
        log.info(local_scope_str(self))

    def edit_embed(self):
        self.embed = discord.Embed(title=str(self.command)).add_field(name='\u200b', value=self.command.help)
        self.embed.set_footer(
            icon_url="https://panels-images.twitch.tv/panel-126362130-image-d5e33b7d-d6ff-418d-9ec8-d83c2d49739e",
            text="Contact nyx#6294 for bug reports and feedback.")

    def edit_args(self, emoji):
        if emoji == ':open_book:':
            asyncio.create_task(MyMsg().from_dict({"ctx": self.ctx, "embed": discord.Embed(title='help')
                                                   .add_field(name='\u200b', value=card_search_doc)}).dispatch())
            return self.__dict__
        if emoji in chr_emojis(self.monitored_emojis):
            new_args = self.__dict__
            new_args["command"] = list(filter(lambda c: str(c)[0] == emoji[-2], bot.commands))[0]
            return new_args
        return super().edit_args(emoji)


class MatchesMsg(MyMsg):
    """
    This subclass handles the embed used to narrow down a card search with multiple returns.
    """

    def __init__(self, ctx, matches):
        super().__init__(ctx)
        self.matches = matches
        for i, match in enumerate(self.matches):
            self.monitored_emojis.add(int_to_emoji(i))
        self.edit_embed()
        log.info(local_scope_str(self))

    def edit_embed(self):
        self.embed = discord.Embed(title='Possible matches:')
        for i, match in enumerate(self.matches):
            self.embed.add_field(name=emojize(int_to_emoji(i)), value=LIB.ids[match].name_)
        log.info(f'{self.embed.fields}')

    async def wait_for_toggle(self):
        try:
            rctn, _ = await bot.wait_for("reaction_add", check=lambda r, u: demojize(r.emoji) in
                                                                            int_emojis(self.monitored_emojis) and
                                                                            u != self.msg.author and
                                                                            r.message.id == self.msg.id,
                                         timeout=REACTIONS_TIMEOUT)
            return [self.matches[int(demojize(rctn.emoji)[-2])]]
        except TimeoutError:
            return []

    def edit_args(self, emoji):
        return  # We want MatchesMsg to be deleted on any reaction press.


class JcgMsg(MyMsg):
    def __init__(self, ctx, mode='rot'):
        super().__init__(ctx)
        self.mode = 'unlimited' if mode.lower() in ('unlimited', 'ul') else 'rotation'
        self.edit_embed()
        self.monitored_emojis.add(':counterclockwise_arrows_button:')
        log.info(local_scope_str(self))

    def edit_embed(self):
        try:
            with open(f'{self.mode}.json', 'r') as f_:
                tour = json.load(f_)
        except FileNotFoundError:
            asyncio.create_task(self.wait_for_scraper())
            return
        self.embed = discord.Embed(title=f'#{tour["code"]} - {tour["name"]}')
        self.embed.url = f'https://sv.j-cg.com/compe/view/tour/{tour["code"]}'
        for top in filter(lambda k: k.isdigit(), tour):
            top_str = ''
            for player in tour[top]:
                player_decks = ''
                for craft, deck_link in zip(player["crafts"], player["tinydecks"]):
                    player_decks += f'{hyperlink(list(CRAFTS)[craft], deck_link)} /'
                player_str = f'{player_decks[:-2]} - {player["player"]}\n'
                top_str += player_str
            print(top_str)
            self.embed.add_field(name=f'**TOP {top}**', value=top_str, inline=False)
        crafts_distribution = ''
        for i, craft in enumerate(tour["crafts"], start=1):
            crafts_distribution += plot_craft(list(CRAFTS)[i], craft)
        self.embed.add_field(name=f'**Class Distribution**',
                             value=crafts_distribution)
        log.info(local_scope_str(self))

    def edit_args(self, emoji):
        if emoji == ':counterclockwise_arrows_button:':
            # side effects
            asyncio.create_task(self.wait_for_scraper())
            asyncio.create_task(self.msg.clear_reaction(emojize(':counterclockwise_arrows_button:')))
            self.monitored_emojis.remove(':counterclockwise_arrows_button:')
            return self.__dict__
        return super().edit_args(emoji)

    async def wait_for_scraper(self):
        msg = await self.ctx.send(embed=discord.Embed(title='Fetching newer JCGs if present, please wait...'))
        await update_jcgs()
        await msg.delete()
        await MyMsg().from_dict({"ctx": self.ctx, "embed": discord.Embed(title='...update finished.')}).dispatch()
