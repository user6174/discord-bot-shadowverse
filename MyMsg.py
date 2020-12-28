import sys
import json
import discord
import asyncio
import logging.handlers
from typing import Optional, Union, List
from natsort import natsorted
from discord.ext import commands  # https://discordpy.readthedocs.io/en/latest/ext/commands/commands.html
from emoji import emojize, demojize
from Jcg_utils import update_jcgs
from Library import Library

LIB = Library()

# Logging is setup to write to .../current_directory/bot.log and to stdout.
style = logging.Formatter('%(asctime)s [%(funcName)-10s]  %(message)s')
log = logging.getLogger('discord')
log.setLevel(logging.INFO)

to_log_file = logging.handlers.TimedRotatingFileHandler(filename='bot.log', when='midnight',
                                                        backupCount=7, encoding='utf-8')
to_log_file.setFormatter(style)
log.addHandler(to_log_file)

to_stdout = logging.StreamHandler(sys.stdout)
to_stdout.setFormatter(style)
log.addHandler(to_stdout)

MAX_WATCHED_MSGS = 50
REACTIONS_TIMEOUT = 300  # seconds
bot = commands.Bot(command_prefix='<')

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


def hyperlink(txt: str, link: str) -> str:
    return f'[**{txt}**]({link})'


def int_to_emoji(n: Union[int, chr]) -> str:
    return f':keycap_{n}:'


def chr_to_emoji(c: chr) -> str:
    return f':regional_indicator_symbol_letter_{c}:'


def int_emojis(l: iter) -> iter:
    """:param l: list of emoji strings in the format :emoji_name:"""
    return filter(lambda e: 'keycap' in e, l)


def chr_emojis(l: iter) -> iter:
    """:param l: list of emoji strings in the format :emoji_name:"""
    return filter(lambda e: 'regional' in e, l)


class MyMsg(object):
    """
    This class creates and manages the messages requested by the bot commands.
    """
    __all__ = {}  # A cache of the last MAX_WATCHED_MSGS messages.

    def log_scope(self, curr_cls) -> str:
        """
        Returns the current couples field/value belonging to the input object, for logging purposes.
        The current class isn't read through self.__class__ because this fails to recognize the "classes walk" done
        by a function following multiple super calls. Also note that the logging can't happen here because the logger is
        formatted to look at the name of the function executing it.
        """
        ret = ''
        for k, v in self.__dict__.items():
            if k not in ("ctx", "msg", "embed"):
                ret += f'{k}={v}, '
        ret += '\b\b'
        return f'{curr_cls.__name__=}, {ret}'

    def __init__(self, ctx: Optional[discord.ext.commands.Context] = None):
        self.ctx = ctx
        self.embed: Optional[discord.embeds.Embed] = None
        self.msg: Optional[discord.message.Message] = None
        # A list of the emojis that, if added to the message as a reaction, cause the class to modify the message.
        self.monitored_emojis = {':wastebasket:'}
        log.info(self.log_scope(MyMsg))

    @classmethod
    def from_dict(cls, fields: dict) -> 'MyMsg':
        """
        An alternative constructor instantiating a cls instance (right now a MyMsg object, but critically,
        an instance of any MyMsg subclass that this method is called onto) with the input fields.
        This is mainly used as a quick lane to edit the fields of an existing (read: whose msg field has already been
        dispatched by the bot) MyMsg subclass instance, with the goal of editing its embed.
        It can also act as a constructor, if one wishes to create a MyMsg message with minimal functionality
        (one that can be deleted by pressing :wastebasket:).
        The base arguments in this case are {"ctx": ctx, "embed": embed}.
        """
        obj = MyMsg()
        obj.__class__ = cls  # Preparing an empty instance of the target class by "casting" it over MyMsg.
        for name, value in fields.items():
            obj.__setattr__(name, value)
        log.info(obj.log_scope(obj.__class__))
        return obj

    def edit_embed(self):
        """
        The embed that gets edited in the subclasses is either a template created in their init, or a from_dict field.
        """
        return

    async def dispatch(self):
        """
        Sends the message, dresses it and adds it to the class cache, making space if necessary.
        """
        self.msg = await self.ctx.send(embed=self.embed)
        self.dress()
        MyMsg.__all__[self.msg.id] = self
        log.info(f'sending msg {self.msg.id} {len(MyMsg.__all__)=})')
        while len(MyMsg.__all__) >= MAX_WATCHED_MSGS:
            oldest_msg = min(MyMsg.__all__.keys())  # msg.id is its timestamp
            await MyMsg.__all__[oldest_msg].abandon()
        with open('__history__.txt', 'a+') as f:
            f.write(f'{self.ctx.channel.id} {self.msg.id}\n')

    def dress(self):
        """
        Reacts to the message with the emojis in monitored_emojis.
        """
        emojis = natsorted(self.monitored_emojis)
        log.info(f'{emojis=}')
        for emoji in emojis:
            asyncio.create_task(self.msg.add_reaction(emojize(emoji)))

    async def abandon(self, delete_msg=False):
        """
        An abandoned message gets dropped from the internal cache and becomes inert to reactions.
        """
        try:  # Can fail in DMs.
            await self.msg.clear_reactions()
        except discord.errors.Forbidden:
            pass
        del MyMsg.__all__[self.msg.id]
        if delete_msg:
            await self.msg.delete()
        log.info(f'abandoned msg {self.msg.id} ({delete_msg=}, {len(MyMsg.__all__)=})')

    @classmethod
    def on_emoji_toggle(cls, msg_id, emoji, user):
        """
        If the message identified by msg_id is in the internal cache, edits its embed as indicated by the toggled emoji.
        The emoji user reaction is cleared for convenience, making it easier for them to toggle it again.
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

    def edit_args(self, emoji) -> Optional[dict]:
        """
        Manipulates the __dict__ of a message instance according to the emote pressed.
        If an emote corresponds to some special instruction going beyond the scope of modifying the object's embed,
        side effects are also executed here.
        Returning None will delete the message, and if there's no edits to make, self.__dict__ is returned.
        """
        if emoji == ':wastebasket:':
            return
        return self.__dict__


# HELP #################################################################################################################

card_search_doc = """**SYNOPSIS FOR CARD COMMANDS**
`{pfx}<CARD_COMMAND> <CARD_NAME> <CARD_COMMAND_FLAGS>`

**DESCRIPTION**
Case insensitive, minor typos are allowed only when looking up a card name. The default search tries to present the cards you're most likely to want while being exhaustive, but should it happen that this results in too narrow or too wide a list of matches, you can make use of **-l** and **-a**. 

**FLAGS**
**-l**, **--lax**
Relaxes the search from returning the card name exactly matching with the search terms to the cards containing the search terms in the name.
**-a**, **--attrs**
Matches the search terms to the card's attributes, such as attack, effect and expansion (expansion shorthands are supported).
**-b**, **--begins**
Matches the search to the beginning of the card's name.

**EXAMPLES** (using the {pfx}info command)
`{pfx}pluto -a` -> `Pact with the Nethergod`
`{pfx}owlcat --lax` -> `Owlcat, Peckish Owlcat`
`{pfx}abominatioQ` -> `Abomination Awakened`
`{pfx}ra, -b` -> `Ra, Radiance Incarnate`
""".format(pfx=bot.command_prefix)
NO_HELP = '~'
print(len(card_search_doc))


def has_help(cmd) -> bool:
    return bot.get_command(cmd).help != NO_HELP


class HelpMsg(MyMsg):
    """
    This subclass manages the help pages of the commands.
    """

    def __init__(self, ctx, command):
        super().__init__(ctx)
        self.command = command
        for cmd in filter(lambda c: c != 'rr', (str(c) for c in bot.commands)):
            if has_help(cmd):
                self.monitored_emojis.add(chr_to_emoji(cmd[0]))
        self.monitored_emojis.add(':open_book:')
        self.edit_embed()

    def edit_embed(self):
        log.info(f'{self.__class__=}')
        self.embed = discord.Embed(title=str(self.command)) \
            .add_field(name=f'{emojize(":open_book:")} - card search help page\n'
                            f'{emojize(chr_to_emoji("h"))} - main help menu\n\u200b',
                       value=self.command.help)
        self.embed.set_footer(
            icon_url="https://panels-images.twitch.tv/panel-126362130-image-d5e33b7d-d6ff-418d-9ec8-d83c2d49739e",
            text='Contact nyx#6294 for bug reports and feedback.')

    def edit_args(self, emoji):
        if emoji == ':open_book:':
            log.info('requested card search doc')
            # An example of from_dict used as a constructor.
            asyncio.create_task(MyMsg().from_dict({"ctx": self.ctx, "embed": discord.Embed(title='help')
                                                  .add_field(name='\u200b', value=card_search_doc)}).dispatch())
            return self.__dict__
        if emoji in chr_emojis(self.monitored_emojis):
            new_args = self.__dict__
            new_args["command"] = list(filter(lambda c: str(c)[0] == emoji[-2], bot.commands))[0]
            log.info(f'{new_args["command"]=}')
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
        log.info(self.log_scope(MatchesMsg))

    def edit_embed(self):
        self.embed = discord.Embed(title='Possible matches:')
        for i, match in enumerate(self.matches):
            self.embed.add_field(name=emojize(int_to_emoji(i)), value=LIB.ids[match].name_)

    async def wait_for_toggle(self) -> List[int]:
        """
        Since MatchesMsg needs to provide a card name to the search function in bot.py, the synchronous reactions
        infrastructure provided by MyMsg can't be used to answer to the user selecting a card.
        """
        try:
            rctn, _ = await bot.wait_for("reaction_add", check=lambda r, u: demojize(r.emoji) in
                                                                            int_emojis(self.monitored_emojis) and
                                                                            u != self.msg.author and
                                                                            r.message.id == self.msg.id,
                                         timeout=REACTIONS_TIMEOUT)
            return [self.matches[int(demojize(rctn.emoji)[-2])]]
        except asyncio.exceptions.TimeoutError:
            log.info(f'timeout {self.msg.id}')
            return []

    def edit_args(self, emoji):
        return  # We want MatchesMsg to be deleted on any reaction press.


# JCG ##################################################################################################################

def plot_craft(craft_name, craft_val):
    """
    Formats the craft name so that it gets colored by discord's markup text, and creates a row of a horizontal histogram
    showing that craft's representation in the tournament.
    """
    return f'```{CRAFTS[craft_name]["markup"].replace("___", craft_name)}{" " * craft_val}{craft_val}```'


class JcgMsg(MyMsg):
    def __init__(self, ctx, mode='rotation'):
        super().__init__(ctx)
        self.mode = mode
        self.edit_embed()
        self.monitored_emojis.add(':counterclockwise_arrows_button:')
        log.info(self.log_scope(JcgMsg))

    def edit_embed(self):
        try:
            with open(f'{self.mode}.json', 'r') as f_:
                tour = json.load(f_)
        except (FileNotFoundError, json.JSONDecodeError):
            asyncio.create_task(self.wait_for_scraper(error=True))
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
            self.embed.add_field(name=f'**TOP {top}**', value=top_str, inline=False)
        crafts_distribution = ''
        for i, craft in enumerate(tour["crafts"], start=1):
            crafts_distribution += plot_craft(list(CRAFTS)[i], craft)
        self.embed.add_field(name=f'**Class Distribution**',
                             value=crafts_distribution)

    def edit_args(self, emoji):
        if emoji == ':counterclockwise_arrows_button:':
            log.info('requested JCG update')
            asyncio.create_task(self.wait_for_scraper())
            # One can't wait for a subroutine in a synchronous function, and multiple update calls wouldn't make sense,
            # so the emoji is disabled.
            asyncio.create_task(self.msg.clear_reaction(emojize(':counterclockwise_arrows_button:')))
            self.monitored_emojis.remove(':counterclockwise_arrows_button:')
            return self.__dict__
        return super().edit_args(emoji)

    async def wait_for_scraper(self, error=False):
        log.info(f'{error=}')
        if error:
            msg = await self.ctx.send(embed=discord.Embed(title='There was a problem reading the tournament data. '
                                                                'Trying to fetch it again, please wait...'))
        else:
            msg = await self.ctx.send(embed=discord.Embed(title='Fetching newer JCGs if present, please wait...'))
        await update_jcgs()
        await msg.delete()
        await MyMsg().from_dict({"ctx": self.ctx, "embed": discord.Embed(title='...update finished.')}).dispatch()
