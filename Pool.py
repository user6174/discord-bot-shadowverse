import random
import os
import json
from fuzzywuzzy import fuzz


sets = {"Token": ("TK", "1970-01-01"),
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
        "Fortune's Hand": ("FH", "2020-06-29")}


def full_pic(id_, evo):
    return f'https://svgdb.me/assets/fullart/{str(id_) + ("1" if evo else "0")}.png'


class Pool:
    def __init__(self):
        with open(f'{os.getcwd()}/shadowverse-json/en/all.json', 'r') as f:
            ids = json.load(f)
        self.p = {}
        for card in ids:
            name = ids[card]["name_"]
            if name not in self.p or int(card) < int(self.p[name]["id_"]):
                self.p[name] = ids[card]
                self.p[name]["tokens_"] = [ids[str(tk)]["name_"] for tk in self.p[name]["tokens_"]]
        self.ids = ids  # for info about alt arts

    def searchable(self, name):
        c = self.p[name]
        return f'{c["name_"]} {c["pp_"]}pp {c["rarity_"]} {c["craft_"]} {c["trait_"]} {c["type_"]} {c["expansion_"]} ' \
               f'{c["baseAtk_"]}/{c["baseDef_"]} {"Rotation" if c["rotation_"] else "Unlimited"} ' \
               f'{c["baseEffect_"]} {c["evoEffect_"]} {sets[c["expansion_"]][0]}'.lower()

    def pic(self, name, evo):
        return f'https://svgdb.me/assets/cards/{"E" if evo else "C"}_{self.p[name]["id_"]}.png'

    def get_random_card(self):
        return self.p[random.choice(list(self.p.keys()))]["name_"]

    def search_by_name(self, search_terms, similarity_threshold=70):
        search_terms = search_terms.lower()
        ret = []
        fuzzy_ret = []
        for i in self.p:
            similarity = fuzz.partial_ratio(search_terms, i.lower())
            if search_terms in i.lower():
                ret.append(i)
            if similarity > similarity_threshold:
                fuzzy_ret.append(i)
        if not ret:
            return fuzzy_ret
        return ret

    def search_by_attributes(self, search_terms: str):
        result = []
        for card in self.p:
            if all(attr in self.searchable(card) for attr in search_terms.lower().split(' ')):
                result.append(card)
        return result


def module_test():
    p = Pool()
    print(p.searchable("Robogoblin"))
    print(p.get_random_card())
    print(p.search_by_name("Vania"))
    print(p.search_by_name("Abominecion"))
    print(p.search_by_attributes("2/2"))
    print(p.search_by_attributes("2/2 gold neutral banish"))
    print(p.pic("Goblin", True))
    print(p.search_by_attributes("7/4"))
    print(p.searchable("Hulking Dragonewt"))
    print(p.search_by_name("golem legend fortune") + p.search_by_attributes("golem legend fortune"))
    print(p.search_by_name("milteo shadow legend") + p.search_by_attributes("milteo shadow legend"))


# module_test()
