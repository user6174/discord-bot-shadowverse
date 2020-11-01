import asyncio
import json
import aiohttp
import discord
from emoji import emojize

from Card import SITE
from MyMsg import MyMsg
from MyMsg import LIB, CRAFTS, log
from MyMsg import chr_to_emoji, chr_emojis, int_to_emoji, int_emojis, local_scope_str, hyperlink


class CardMsg(MyMsg):
    def __init__(self, ctx, id_, evo=False):
        super().__init__(ctx)
        self.id_ = id_
        self.evo = evo
        self.card = LIB.ids[self.id_]
        if self.card.type_ == "Follower":
            self.monitored_emojis.add(':dna:')
        for i in range(len(self.card.alts_)):
            self.monitored_emojis.add(chr_to_emoji(chr(ord('a') + i)))
        log.info(local_scope_str(self))

    def edit_embed(self):
        log.info(local_scope_str(self))
        self.embed = discord.Embed(title=f'{self.card.name_} {"Evolved" if self.evo else ""}')
        self.embed.url = f'https://shadowverse-portal.com/card/{self.id_}?lang=en'
        self.embed.set_footer(text="Contact nyx#6294 for bug reports and feedback.")

    def edit_args(self, emoji):
        new_args = self.__dict__
        if emoji == ':dna:':
            new_args["evo"] = not new_args["evo"]
            return new_args
        card = LIB.ids[self.id_]
        if emoji in chr_emojis(self.monitored_emojis):
            new_args["id_"] = card.alts_[ord(emoji[-2]) - ord('a')]
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
    return action + special


class VoiceMsg(CardMsg):
    def __init__(self, ctx, id_, evo=False, lang='jp'):
        super().__init__(ctx, id_, evo)
        self.monitored_emojis.remove(':dna:')
        self.monitored_emojis.add(":speech_balloon:")
        self.lang = lang
        # self.edit_embed() isn't called in the init, and the embed is instead built when dispatching,
        # because constructors can't be async.
        log.info(local_scope_str(self))

    def edit_embed(self):
        fields = self.embed.fields
        old_lang = 'en' if self.lang == 'jp' else 'jp'
        for i, field in enumerate(fields):
            self.embed.set_field_at(i, name=field.name, value=field.value.replace(old_lang, self.lang))
        log.info(self.embed.fields)

    async def dispatch(self):
        """
        (side effects) VoiceMsg rides on this async call to also fetch audio links and build the embed.
        """
        async with aiohttp.client.ClientSession() as s:
            async with s.get(f'https://svgdb.me/api/voices/{self.id_}') as r:
                voice_lines = json.loads(await r.read())
        for game_action in voice_lines:
            for i, line in enumerate(voice_lines[game_action]):
                self.embed.add_field(name='\u200b',
                                     value=hyperlink(f'• {fmt_action(game_action, line)}',
                                                     f'{SITE}/assets/audio/{self.lang}/{line}'),
                                     inline=False)
        log.info(self.embed.fields)
        await super().dispatch()

    def edit_args(self, emoji):
        if emoji == ":speech_balloon:":
            new_args = self.__dict__
            new_args["lang"] = 'en' if new_args["lang"] == 'jp' else 'jp'
            return new_args
        return super().edit_args(emoji)


class PicMsg(CardMsg):
    def __init__(self, ctx, id_, evo=False):
        super().__init__(ctx, id_, evo)
        self.edit_embed()
        log.info(local_scope_str(self))

    def edit_embed(self):
        super().edit_embed()
        self.embed.set_image(url=self.card.pic(evo=self.evo))
        alts_ = self.card.alts_
        if alts_:
            footer_txt = ""
            for i, id_ in enumerate(alts_):
                chr_ = (chr(ord('a') + i)).upper()
                footer_txt += f'{chr_}: {self.card.expansion_}\n'
            self.embed.set_footer(text=f'Other artworks:\n{footer_txt}')


class InfoMsg(CardMsg):
    def __init__(self, ctx, id_, evo=False, show_img=False):
        super().__init__(ctx, id_, evo)
        self.show_img = show_img
        for i in range(len(self.card.tokens_)):
            self.monitored_emojis.add(int_to_emoji(i))
        self.monitored_emojis.add(':artist_palette:')
        self.edit_embed()
        log.info(local_scope_str(self))

    def edit_embed(self):
        super().edit_embed()
        self.embed.colour = CRAFTS[self.card.craft_]['hex']
        # first row
        self.embed.add_field(name='\u200b',
                             value=f'**Cost**: {self.card.pp_}pp\n' +
                                   (f'**Trait**: {self.card.trait_}\n' if self.card.trait_ != "-" else "") +
                                   f'**Type**: {self.card.type_}\n' +
                                   (f'**Stats**: '
                                    f'{self.card.baseAtk_}/{self.card.baseDef_} → '
                                    f'{self.card.evoAtk_}/{self.card.evoDef_}' if self.card.type_ == "Follower"
                                    else ''),
                             inline=True)
        self.embed.add_field(name='\u200b',
                             value=f'**Rarity**: {self.card.rarity_}\n'
                                   f'**Expansion**: {self.card.expansion_}\n',
                             inline=True)
        if self.show_img:
            self.embed.set_image(url=self.card.pic(framed=True, evo=self.evo))
        if self.card.alts_:
            alts = ""
            for i, alt_id_ in enumerate(self.card.alts_):
                emoji = emojize(chr_to_emoji(chr(ord('a') + i)))
                alts += f'{emoji} {LIB.ids[alt_id_].expansion_}\n'
            self.embed.add_field(name="Alt versions:", value=alts, inline=True)
        # second row
        if self.card.tokens_:
            tokens = ""
            for i, tk_id_ in enumerate(self.card.tokens_):
                emoji = emojize(int_to_emoji(i))
                tokens += f'{emoji} {LIB.ids[tk_id_].name_}\n'
            self.embed.add_field(name="Related cards:", value=tokens, inline=True)
        # effects
        if self.card.type_ == "Follower":
            if self.card.baseEffect_ != "-":
                self.embed.add_field(name="Base:", value=f'{self.card.baseEffect_}', inline=False)
            if self.card.evoEffect_ != "-":
                self.embed.add_field(name="Evolved:", value=f'{self.card.evoEffect_}', inline=False)
        else:
            self.embed.add_field(name="Effect:", value=self.card.baseEffect_, inline=False)
        # flair
        if self.evo:
            self.embed.set_footer(text=self.card.evoFlair_)
        else:
            self.embed.set_footer(text=self.card.baseFlair_)
        self.embed.set_thumbnail(
            url=f'https://shadowverse-wins.com/common/img/leader_{CRAFTS[self.card.craft_]["icon"]}.png')

    def edit_args(self, emoji):
        new_args = self.__dict__
        if emoji == ':artist_palette:':
            new_args["show_img"] = not new_args["show_img"]
            return new_args
        if emoji in int_emojis(self.monitored_emojis):
            # side effects
            tk_id = self.card.tokens_[int(emoji[-2])]
            tk_msg = InfoMsg(self.ctx, tk_id)
            asyncio.create_task(tk_msg.dispatch())
            return new_args
        return super().edit_args(emoji)
