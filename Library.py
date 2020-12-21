import json
from Card import Card, CURR_DIR
from typing import List
from fuzzywuzzy import fuzz

MIN_SIMILARITY = 80


class Library:
    def __init__(self):
        with open(f'{CURR_DIR}/shadowverse-json/en/all.json', 'r') as f:
            data = json.load(f)
        self.ids = dict((data[id_]["id_"], Card(data[id_])) for id_ in data)

    def main_id(self, id_) -> int:
        """
        Makes sure that search_by_name doesn't return some alt, promo or reprint of a card.
        """
        # The ID order of homonym cards matches the chronological order of their debut in the game.
        return min([id_] + self.ids[id_].alts_)

    def search_by_name(self, query: str, lax=False, begins=False) -> List[int]:
        """lax indicates whether to end the search if a match equal to the query is found. It's easy for this not to be
        what the user wants, because very short and simple card names usually have other, more interesting matches."""
        query = query.lower()
        matches_begins = []
        # Stores card names for which query is a substring found where the card's proper noun tends to be (for example,
        # "grea" matches [...]grea, [...], [...]grea [...], [...]grea'[...] and [...]grea).
        matches_noun = []
        # For matches stored here the query is a generic slice of the card name ("grea" matches [...]grea[...]).
        matches_substr = []
        # Finally if the query and the card name are similar enough the match is stored here (i.e. allowing typos).
        matches_fuzzy = []
        """
        These matches are presented in their priority order: matches_fuzzy is only returned if, and built while, the
        other two matches are empty. One could argue that it's better to build and return all 3 while caching the
        results, because this method may end up being called multiple times in the search routine in the bot, but in
        practice it's a rare occurrence, so the small boost of speed provided by interrupting the lower priority 
        searches is preferred.
        """
        for id_, card in self.ids.items():
            name = card.name_.lower()
            if not lax and query == name.lower():
                return [self.main_id(id_)]

            if begins and query == name.lower()[:len(query)]:
                matches_begins.append(self.main_id(id_))

            if query + ' ' in name.lower() \
                    or query + ', ' in name.lower() \
                    or query + '\'' in name.lower() \
                    or query in name.lower()[len(name) - len(query):]:
                matches_noun.append(self.main_id(id_))
            if matches_noun:
                continue

            if query in name.lower():
                matches_substr.append(self.main_id(id_))
            if matches_substr:
                continue

            if fuzz.partial_ratio(query, name.lower()) > MIN_SIMILARITY:
                matches_fuzzy.append(self.main_id(id_))
        ret = matches_begins if matches_begins else \
            matches_noun if matches_noun else \
            matches_substr if matches_substr else \
            matches_fuzzy
        return list(dict.fromkeys(ret))

    def search_by_attributes(self, query: str) -> List[int]:
        ret = []
        for id_, card in self.ids.items():
            if all(attr in card.searchable() for attr in query.lower().split(' ')):
                ret.append(id_)
        return ret


if __name__ == "__main__":
    l = Library()
    print(l.search_by_name("fighter"))
    print(l.search_by_name("fighter", lax=True))
    print(l.search_by_name("grea"))  # testing whole word
    print(l.search_by_name('infer'))  # testing substring overlap
    print(l.search_by_name("Abominecion"))  # testing fuzzy
    print(l.search_by_attributes("2/2 gold neutral banish"))
    print(l.search_by_name('figher'))
    print(l.ids[l.search_by_name('limil')[0]].censored)
    print(l.search_by_name('fate\'s hand', lax=True))
