import random
import os
import json
from fuzzywuzzy import fuzz
from typing import List

expansions = {"Token": ("TK", "1970-01-01"),
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


def full_pic(id_: int, evo: bool):
    return f'https://svgdb.me/assets/fullart/{str(id_) + str(int(evo))}.png'


class Cardpool:
    def __init__(self):
        with open(f'{os.getcwd()}/shadowverse-json/en/all.json', 'r') as f:
            ids = json.load(f)
        self.names = {}  # name-keyed dict for normal usage (card lookups)
        # the source json uses the card id as the dict key, changing that to the card's name
        for card in ids:
            name = ids[card]["name_"]
            # solving homonymy conflicts: preferring first prints
            if name not in self.names or int(card) < int(self.names[name]["id_"]):
                self.names[name] = ids[card]
                self.names[name]["tokens_"] = [ids[str(tk)]["name_"] for tk in self.names[name]["tokens_"]]
        self.ids = ids  # keeping a id-keyed dict for info about alt arts

    def pic(self, name, evo):
        return f'https://svgdb.me/assets/cards/{"E" if evo else "C"}_{self.names[name]["id_"]}.png'

    def searchable(self, name):
        """a text field (not added as an actual field to save space) for search functions to look at"""
        c = self.names[name]
        return f'{c["name_"]} {c["pp_"]}pp {c["rarity_"]} {c["craft_"]} {c["trait_"]} {c["type_"]} {c["expansion_"]} ' \
               f'{expansions[c["expansion_"]][0]} {c["baseAtk_"]}/{c["baseDef_"]} ' \
               f'{"rotation" if c["rotation_"] else "unlimited"} {c["baseEffect_"]} {c["evoEffect_"]}'.lower()

    def search_by_name(self, search_terms: str) -> List[str]:
        search_terms = search_terms.lower()
        whole_word_ret = []
        substring_ret = []
        fuzzy_ret = []
        for i in self.names:
            # first try: exact match with whole-word overlap
            # (example, "grea" matches [...]grea, [...], [...]grea [...], [...]grea'[...] and [...]grea)
            if search_terms + ' ' in i.lower() \
                    or search_terms + ', ' in i.lower() \
                    or search_terms + '\'' in i.lower() \
                    or search_terms in i.lower()[len(i) - len(search_terms):]:
                whole_word_ret.append(i)
                substring_ret = []
                fuzzy_ret = []
            # second try: exact match and substring overlap ("grea" matches [...]grea[...])
            elif (not whole_word_ret) and search_terms in i.lower():
                substring_ret.append(i)
                fuzzy_ret = []
            # third try: best fuzzy match (i.e. allowing typos)
            elif (not whole_word_ret) and (not substring_ret) and fuzz.partial_ratio(search_terms, i.lower()) > 75:
                fuzzy_ret.append(i)
        return fuzzy_ret if fuzzy_ret else substring_ret if substring_ret else whole_word_ret

    def search_by_attributes(self, search_terms: str) -> List[str]:
        ret = []
        for card in self.names:
            if all(attr in self.searchable(card) for attr in search_terms.lower().split(' ')):
                ret.append(card)
        return ret


def module_test():
    p = Cardpool()
    print(p.searchable("Robogoblin"))
    print(p.search_by_name("Vania"))
    print(p.search_by_name("Abominecion"))
    print(p.search_by_attributes("2/2 gold neutral banish"))
    print(p.pic("Goblin", True))
    inferno_id = p.names[p.search_by_name('infer')[0]]['id_']
    print(full_pic(inferno_id, False))


# module_test()
