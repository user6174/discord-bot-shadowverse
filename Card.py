import os
import json

import aiohttp
import requests

CURR_DIR = os.path.dirname(os.path.realpath(__file__))
SITE = "https://svgdb.me"
EXPANSIONS = {"Token": ("TK", "1970-01-01"),
              "Promo": ("PR", "1970-01-01"),
              "Basic": ("Basic", "2016-06-21"),
              "Standard Card Pack": ("STD", "2016-06-21"),
              "Darkness Evolved": ("DE", "2016-09-29"),
              "Rise of Bahamut": ("ROB", "2016-12-29"),
              "Tempest of the Gods": ("TOTG", "2017-03-30"),
              "Wonderland Dreams": ("WLD", "2017-06-29"),
              "Starforged Legends": ("SL", "2017-09-28"),
              "Chronogenesis": ("CG", "2017-12-28"),
              "Dawnbreak Nightedge": ("DN", "2018-03-28"),
              "Brigade of the Sky": ("BOTS", "2018-06-27"),
              "Omen of the Ten": ("OOT", "2018-09-26"),
              "Altersphere": ("AS", "2018-12-26"),
              "Steel Rebellion": ("SR", "2019-03-27"),
              "Rebirth of Glory": ("ROG", "2019-06-27"),
              "Verdant Conflict": ("VC", "2019-09-25"),
              "Ultimate Colosseum": ("UC", "2019-12-27"),
              "World Uprooted": ("WU", "2020-03-29"),
              "Fortune's Hand": ("FH", "2020-06-29"),
              "Storm over Rivayle": ("SOT", "2020-09-23")}

CENSORED = requests.get(f'{SITE}/api/censored').text
CENSORED = CENSORED.strip("][").split(', ')
CENSORED = set(int(id_[1:-1]) for id_ in CENSORED)


class Card:
    def __init__(self, card_dict: dict):
        self.name_ = ""
        self.id_ = 0
        self.pp_ = 0
        self.craft_ = ""
        self.rarity_ = ""
        self.type_ = ""
        self.trait_ = ""
        self.expansion_ = ""
        self.baseEffect_ = ""
        self.baseFlair_ = ""
        self.rotation_ = False
        self.baseAtk_ = 0
        self.baseDef_ = 0
        self.evoAtk_ = 0
        self.evoDef_ = 0
        self.evoEffect_ = ""
        self.evoFlair_ = ""
        self.alts_ = []
        self.tokens_ = []
        for k, v in card_dict.items():
            self.__setattr__(k, v)
        self.censored = self.id_ in CENSORED
        if self.censored:
            CENSORED.remove(self.id_)

    def searchable(self) -> str:
        # Used when searching a card's attribute, and thus expressly lacking the card's name.
        return f'{self.pp_}pp {self.rarity_} {self.craft_} {self.trait_} {self.type_} {self.expansion_} ' \
               f'{EXPANSIONS[self.expansion_][0]} {self.baseAtk_}/{self.baseDef_} ' \
               f'{"rotation" if self.rotation_ else "unlimited"} {self.baseEffect_} {self.evoEffect_}'.lower()

    def pic(self, frame=False, evo=False, censored=False) -> str:
        if frame:
            return f'{SITE}/assets/cards/{"E" if evo else "C"}_{self.id_}.png'
        keyword = 'censored' if censored else 'fullart'
        return f'{SITE}/assets/{keyword}/{self.id_}{int(evo)}.png'


# Tests:
if __name__ == "__main__":
    # Make sure that shadowverse-json is in, or is symlinked into, discord-bot-shadowverse.
    with open(f'{CURR_DIR}/shadowverse-json/en/all.json', 'r') as f:
        data = json.load(f)
    c = Card(data['112011030'])
    c2 = Card(data['101334030'])
    for k, v in c.__dict__.items():
        print(f'self.{k} -> {v}')
    print(c.searchable())
    print(c.pic())
    print(c.pic(frame=True, evo=c.type_ == 'Follower'))
    print(c2.censored)
    print(c2.pic(censored=True))
    print(c2.pic())
