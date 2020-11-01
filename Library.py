import os
import json

from fuzzywuzzy import fuzz
from typing import List

from Card import Card


class Library:
    def __init__(self):
        with open(f'{os.getcwd()}/shadowverse-json/en/all.json', 'r') as f:
            data = json.load(f)
        self.ids = dict((data[id_]["id_"], Card(data[id_])) for id_ in data)
        
    def main_id(self, id_):
        return min([id_] + self.ids[id_].alts_)

    def search_by_name(self, search_terms, lax=False) -> List[int]:
        search_terms = search_terms.lower()
        whole_word_ret = []
        substring_ret = []
        fuzzy_ret = []
        for id_, card in self.ids.items():
            name = card.name_.lower()
            # zeroth try: exact match
            if not lax and search_terms == name.lower():
                return [self.main_id(id_)]
            # first try: exact match with whole-word overlap
            # (example, "grea" matches [...]grea, [...], [...]grea [...], [...]grea'[...] and [...]grea)
            if search_terms + ' ' in name.lower() \
                    or search_terms + ', ' in name.lower() \
                    or search_terms + '\'' in name.lower() \
                    or search_terms in name.lower()[len(name) - len(search_terms):]:
                whole_word_ret.append(self.main_id(id_))
                substring_ret = []
                fuzzy_ret = []
            # second try: exact match and substring overlap ("grea" matches [...]grea[...])
            elif (not whole_word_ret) and search_terms in name.lower():
                substring_ret.append(self.main_id(id_))
                fuzzy_ret = []
            # third try: best fuzzy match (i.e. allowing typos)
            elif (not whole_word_ret) and (not substring_ret) and fuzz.partial_ratio(search_terms, name.lower()) > 75:
                fuzzy_ret.append(self.main_id(id_))
        return fuzzy_ret if fuzzy_ret else substring_ret if substring_ret else whole_word_ret

    def search_by_attributes(self, search_terms: str) -> List[int]:
        ret = []
        for id_, card in self.ids.items():
            if all(attr in card.searchable() for attr in search_terms.lower().split(' ')):
                ret.append(id_)
        return ret


def library_module_test():
    l = Library()
    print(l.search_by_name("fighter"))
    print(l.search_by_name("fighter", lax=True))
    print(l.search_by_name("Vania"))  # testing whole word
    print(l.search_by_name('infer'))  # testing substring overlap
    print(l.search_by_name("Abominecion"))  # testing fuzzy
    print(l.search_by_attributes("2/2 gold neutral banish"))
    print(l.search_by_name('figher'))


# library_module_test()
