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

""" this is hardcoded below in case the site isn't up.
CENSORED = requests.get(f'{SITE}/api/censored').text
CENSORED = CENSORED.strip("][").split(', ')
CENSORED = set(int(id_[1:-1]) for id_ in CENSORED)
"""

CENSORED = [101324030, 102312040, 101314010, 102312050, 101311050, 102311050, 101324040, 101334030, 103311040,
            101321050, 101321070, 101341020, 701341010, 101312020, 100321030, 101331010, 101324010, 101334050,
            102334020, 101311090, 101321030, 103321020, 101334010, 900334010, 102324030, 100314070, 900334020,
            101411030, 101421010, 103421020, 101431070, 101414030, 101431030, 102431010, 103431020, 100711010,
            101721060, 103721030, 101713030, 102713010, 102723010, 101711030, 102711020, 101721020, 101721080,
            101714020, 101713050, 102732020, 100721020, 101721040, 101734030, 101721030, 101721100, 100714030,
            100723010, 100711020, 103711040, 103731020, 101024010, 103021030, 101014010, 101024040, 100012010,
            101011030, 101011040, 100031010, 100031020, 103031010, 103031020, 101031040, 103041020, 900041030,
            101621060, 101623010, 100611010, 100611020, 101611010, 102611010, 102611040, 101621020, 101621070,
            101614010, 102624040, 103624010, 101611070, 101611110, 101611130, 101611140, 101621030, 103634010,
            101633010, 100611050, 102621010, 100614030, 103621030, 101631030, 101641030, 101634010, 100611040,
            103611060, 101631060, 701641010, 102621020, 103641010, 101631010, 100111010, 101114010, 101114050,
            103114020, 101121020, 103121030, 100111060, 101111060, 102124020, 101112010, 102111040, 101121080,
            102121010, 900141010, 103121020, 101131030, 103131020, 102141010, 101141010, 101141030, 101211110,
            101221020, 101221090, 102211010, 101221070, 102221020, 101231030, 101214030, 101231010, 103231020,
            101214010, 103221020, 103211040, 101241030, 101234020, 102221040, 101231020, 101514010, 101532010,
            101511020, 102511010, 101521020, 101514020, 101524020, 102524030, 100511030, 102511020, 103511040,
            101521050, 103534010, 103521020, 101524010, 101534010, 101521060, 102521010, 101541010, 701541010,
            101534030, 101511100, 101541030, 103541010, 100311010, 101311100, 102341010, 101311070, 101431010,
            101711040, 101721070, 103711060, 101711060, 102021020, 100011030, 101031010, 101031020, 101611030,
            101631020, 100621020, 102641010, 101641010, 103111050, 100111040, 101111090, 101111050, 103111030,
            100121030, 100211060, 101211020, 101211040, 101221080, 101211100, 103211030, 101521040]


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
               f'{"rotation" if self.rotation_ else "unlimited"} {self.baseEffect_} {self.evoEffect_} {self.name_}'.lower()

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
