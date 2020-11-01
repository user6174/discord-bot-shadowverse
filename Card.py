import os
import json

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


class Card:
    def __init__(self, card_dict):
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
        for key in card_dict.keys():
            self.__setattr__(key, card_dict[key])

    def searchable(self):
        return f'{self.pp_}pp {self.rarity_} {self.craft_} {self.trait_} {self.type_} {self.expansion_} ' \
               f'{EXPANSIONS[self.expansion_][0]} {self.baseAtk_}/{self.baseDef_} ' \
               f'{"rotation" if self.rotation_ else "unlimited"} {self.baseEffect_} {self.evoEffect_}'.lower()

    def pic(self, framed=False, evo=False):
        if framed:
            return f'{SITE}/assets/cards/{"E" if evo else "C"}_{self.id_}.png'
        else:
            return f'{SITE}/assets/fullart/{self.id_}{(int(evo))}.png'


def card_module_test():
    with open(f'{os.getcwd()}/shadowverse-json/en/all.json', 'r') as f:
        data = json.load(f)
    c = Card(data['112011030'])
    for k, v in c.__dict__.items():
        print(f'self.{k} -> {v}')
    print(c.searchable())
    print(c.pic())
    print(c.pic(framed=True, evo=True))

# card_module_test()