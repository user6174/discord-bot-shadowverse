import os
import json
from Card import Card
from typing import List
from fuzzywuzzy import fuzz


class Library:
    def __init__(self):
        with open(f'{os.getcwd()}/shadowverse-json/en/all.json', 'r') as f:
            data = json.load(f)
        self.ids = dict((data[id_]["id_"], Card(data[id_])) for id_ in data)

    def main_id(self, id_) -> int:
        """
        Makes sure that search_by_name doesn't return some alt, promo or reprint of a card.
        """
        # The ID order of homonym cards matches the chronology of their debut in the game.
        return min([id_] + self.ids[id_].alts_)

    def search_by_name(self, search_terms: str, lax=False) -> List[int]:
        """lax indicates whether to end the search if a match is equal to the search terms. It's easy for this not to be
        what the user wants because very short and simple card names usually have other, more interesting matches."""
        search_terms = search_terms.lower()
        # Stores matches with the preferred matching condition: search_terms is a slice of the card name that's where
        # the card's proper noun would tend to be (for example,
        # "grea" matches [...]grea, [...], [...]grea [...], [...]grea'[...] and [...]grea).
        matches_noun = []
        # search_terms is a a generic slice of the card name ("grea" matches [...]grea[...]).
        matches_substr = []
        # search_terms and the card name are similar enough (i.e. allowing typos).
        matches_fuzzy = []
        for id_, card in self.ids.items():
            name = card.name_.lower()
            if not lax and search_terms == name.lower():
                return [self.main_id(id_)]

            if search_terms + ' ' in name.lower() \
                    or search_terms + ', ' in name.lower() \
                    or search_terms + '\'' in name.lower() \
                    or search_terms in name.lower()[len(name) - len(search_terms):]:
                matches_noun.append(self.main_id(id_))
            # only the highest priority (noun, substr and fuzzy in this order) nonempty list is returned,
            # so as soon as noun gets a match search_by_name stops building the lower priority ones (same with substr).
            if matches_noun:
                continue

            if search_terms in name.lower():
                matches_substr.append(self.main_id(id_))
            if matches_substr:
                continue

            elif fuzz.partial_ratio(search_terms, name.lower()) > 75:
                matches_fuzzy.append(self.main_id(id_))
        # For testing.
        # return matches_noun, matches_substr, matches_fuzzy
        return matches_noun if matches_noun else matches_substr if matches_substr else matches_fuzzy

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
    print(l.search_by_name("grea"))  # testing whole word
    print(l.search_by_name('infer'))  # testing substring overlap
    print(l.search_by_name("Abominecion"))  # testing fuzzy
    print(l.search_by_attributes("2/2 gold neutral banish"))
    print(l.search_by_name('figher'))


# library_module_test()
