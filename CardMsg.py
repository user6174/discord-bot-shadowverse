import asyncio
import json
import aiohttp
import discord
from emoji import emojize

from Card import SITE
from MyMsg import MyMsg
from MyMsg import LIB, CRAFTS, log
from MyMsg import chr_to_emoji, chr_emojis, int_to_emoji, int_emojis, hyperlink


def log_cls(curr_cls):
    """
    A smaller version of log_scope, registering only the current class. Why the class is passed explicitly is explained
    there.
    """
    return f'{curr_cls.__name__=}'


class CardMsg(MyMsg):
    """
    A subclass containing the general traits of messages dealing with cards.
    """

    def __init__(self, ctx, id_, evo=False):
        super().__init__(ctx)
        self.id_ = id_
        self.evo = evo
        card = LIB.ids[self.id_]
        if card.type_ == "Follower":
            self.monitored_emojis.add(':dna:')
        for i in range(len(card.alts_)):
            self.monitored_emojis.add(chr_to_emoji(chr(ord('a') + i)))
        log.info(self.log_scope(CardMsg))

    def edit_embed(self):
        """
        The name of the method is a bit inappropriate as far as this subclass is concerned, because what edit_embed
        does here is to initialize the skeleton of the embed that the subclasses below will actually edit. It follows
        that, when overridden, the super() call should be the first instruction.
        """
        self.embed = discord.Embed(title=f'{LIB.ids[self.id_].name_} {"Evolved" if self.evo else ""}')
        self.embed.url = f'https://shadowverse-portal.com/card/{self.id_}?lang=en'
        self.embed.colour = CRAFTS[LIB.ids[self.id_].craft_]['hex']

    def edit_args(self, emoji):
        new_args = self.__dict__
        if emoji == ':dna:':
            log.info('changing evo flag')
            new_args["evo"] = not new_args["evo"]
            return new_args
        if emoji in chr_emojis(self.monitored_emojis):
            new_args["id_"] = LIB.ids[self.id_].alts_[ord(emoji[-2]) - ord('a')]
            log.info(f'{new_args["id_"]=}')
            return new_args
        return super().edit_args(emoji)


# VoiceMsg formatter
def fmt_action(action, line):
    action = {"plays": "On Play",
              "deaths": "On Death",
              "other": "Other",
              "evolves": "On Evolve",
              "attacks": "On Attack"}[action]
    special = ''
    if 'enh' in line:
        special = ' (Enhance)'
    elif 'ub' in line:
        special = ' (Union Burst)'
    else:
        against_id = int(line.split('_')[-1].split('.')[0])
        if against_id in LIB.ids:
            special = f' (against {LIB.ids[against_id].name_})'
        else:
            log.info(f'WARNING: potentially unmatched special string {action} {line}')
    return action + special


class VoiceMsg(CardMsg):
    def __init__(self, ctx, id_, evo=False, lang='jp'):
        super().__init__(ctx, id_, evo)
        self.monitored_emojis.remove(':dna:')
        self.monitored_emojis.add(":speech_balloon:")
        self.lang = lang
        # The embed isn't built with edit_embed here, but when dispatching, because the bot needs to get the voice lines
        # online, so an async function is needed so that execution isn't blocked.
        log.info(self.log_scope(VoiceMsg))

    def edit_embed(self):
        """
        As hinted above, this method is only called when the user requests an edited embed.
        """
        fields = self.embed.fields
        old_lang = 'en' if self.lang == 'jp' else 'jp'
        emoji = emojize(':Japan:' if self.lang == 'jp' else ':United_Kingdom:')
        self.embed.title = emoji + f' {LIB.ids[self.id_].name_}'
        for i, field in enumerate(fields):
            self.embed.set_field_at(i, name=field.name, value=field.value.replace(old_lang, self.lang), inline=False)

    async def dispatch(self):
        """
        Also initializes the embed before sending the message, as anticipated in the init.
        """
        super().edit_embed()
        self.embed.title = emojize(':Japan:' if self.lang == 'jp' else ':United_Kingdom:') + f' {self.embed.title}'
        async with aiohttp.client.ClientSession() as s:
            async with s.get(f'{SITE}/api/voices/{self.id_}') as r:
                voice_lines = json.loads(await r.read())
        for game_action in voice_lines:
            for i, line in enumerate(voice_lines[game_action]):
                self.embed.add_field(name='\u200b',
                                     value=hyperlink(f'• {fmt_action(game_action, line)}',
                                                     f'{SITE}/assets/audio/{self.lang}/{line}'),
                                     inline=False)
        log.info(self.log_scope(VoiceMsg))
        await super().dispatch()

    def edit_args(self, emoji):
        if emoji == ":speech_balloon:":
            log.info('swapping language')
            new_args = self.__dict__
            new_args["lang"] = 'en' if new_args["lang"] == 'jp' else 'jp'
            return new_args
        return super().edit_args(emoji)


class PicMsg(CardMsg):
    def __init__(self, ctx, id_, censored=False, evo=False):
        super().__init__(ctx, id_, evo)
        self.censored = censored
        if LIB.ids[self.id_].censored:
            self.monitored_emojis.add(':peach:')
        self.edit_embed()
        log.info(self.log_scope(PicMsg))

    def edit_embed(self):
        log.info(log_cls(PicMsg))
        super().edit_embed()
        card = LIB.ids[self.id_]
        self.embed.set_image(url=card.pic(evo=self.evo, censored=self.censored))
        alts_ = card.alts_
        if alts_:
            footer_txt = ""
            for i, id_ in enumerate(alts_):
                chr_ = (chr(ord('a') + i)).upper()
                footer_txt += f'{chr_}: {card.expansion_}\n'
            self.embed.set_footer(text=f'Other artworks:\n{footer_txt}')

    def edit_args(self, emoji):
        if emoji == ':peach:':
            log.info('uncensoring')
            new_args = self.__dict__
            new_args["censored"] = not new_args["censored"]
            return new_args
        return super().edit_args(emoji)


class InfoMsg(CardMsg):
    def __init__(self, ctx, id_, evo=False, show_img=False):
        super().__init__(ctx, id_, evo)
        self.show_img = show_img
        for i in range(len(LIB.ids[self.id_].tokens_)):
            self.monitored_emojis.add(int_to_emoji(i))
        self.monitored_emojis.add(':artist_palette:')
        self.edit_embed()
        log.info(self.log_scope(InfoMsg))

    def edit_embed(self):
        super().edit_embed()
        card = LIB.ids[self.id_]
        # first row
        self.embed.add_field(name='\u200b',
                             value=f'**Cost**: {card.pp_}pp\n' +
                                   (f'**Trait**: {card.trait_}\n' if card.trait_ != "-" else "") +
                                   f'**Type**: {card.type_}\n' +
                                   (f'**Stats**: '
                                    f'{card.baseAtk_}/{card.baseDef_} → '
                                    f'{card.evoAtk_}/{card.evoDef_}' if card.type_ == "Follower"
                                    else ''),
                             inline=True)
        self.embed.add_field(name='\u200b',
                             value=f'**Rarity**: {card.rarity_}\n'
                                   f'**Expansion**: {card.expansion_}\n',
                             inline=True)
        if self.show_img:
            self.embed.set_image(url=card.pic(frame=True, evo=self.evo))
        if card.alts_:
            alts = ""
            for i, alt_id_ in enumerate(card.alts_):
                emoji = emojize(chr_to_emoji(chr(ord('a') + i)))
                alts += f'{emoji} {LIB.ids[alt_id_].expansion_}\n'
            self.embed.add_field(name="Alt versions:", value=alts, inline=True)
        # second row
        if card.tokens_:
            tokens = ""
            for i, tk_id_ in enumerate(card.tokens_):
                emoji = emojize(int_to_emoji(i))
                tokens += f'{emoji} {LIB.ids[tk_id_].name_}\n'
            self.embed.add_field(name="Related cards:", value=tokens, inline=True)
        # effects
        if card.type_ == "Follower":
            if card.baseEffect_ != "-":
                self.embed.add_field(name="Base:", value=f'{card.baseEffect_}', inline=False)
            if card.evoEffect_ != "-":
                self.embed.add_field(name="Evolved:", value=f'{card.evoEffect_}', inline=False)
        else:
            self.embed.add_field(name="Effect:", value=card.baseEffect_, inline=False)
        # flair
        if self.evo:
            self.embed.set_footer(text=card.evoFlair_)
        else:
            self.embed.set_footer(text=card.baseFlair_)
        self.embed.set_thumbnail(
            url=f'https://shadowverse-wins.com/common/img/leader_{CRAFTS[card.craft_]["icon"]}.png')

    def edit_args(self, emoji):
        new_args = self.__dict__
        if emoji == ':artist_palette:':
            log.info('swapping img flag')
            new_args["show_img"] = not new_args["show_img"]
            return new_args
        if emoji in int_emojis(self.monitored_emojis):
            # Sending the token as a separate message.
            tk_id = LIB.ids[self.id_].tokens_[int(emoji[-2])]
            log.info(f'sending info page of {tk_id=}')
            tk_msg = InfoMsg(self.ctx, tk_id)
            asyncio.create_task(tk_msg.dispatch())
            return new_args
        return super().edit_args(emoji)
