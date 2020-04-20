def clean_string(string):  # Adjusts the formatting of effects and flairs.
    return string.replace("<br>", '') \
        .replace('.', ".\n") \
        .replace(".\n)", ".)") \
        .replace("- ", "-\n") \
        .replace(".\n.\n.\n", "...")


class Card:
    def __init__(self, card):
        self.name = card['name']
        self.id = card['id']
        self.pic = "https://sv.bagoum.com/cardF/en/c/{}".format(self.id)
        self.evo_pic = "https://sv.bagoum.com/cardF/en/e/{}".format(self.id)
        self.craft = card['faction']
        self.rarity = card['rarity']
        self.trait = card['race']
        self.expac = card['expansion']
        self.type = card['type']
        self.pp = card['manaCost']
        self.flair = clean_string(card['baseData']['flair'])
        self.effect = clean_string(card['baseData']['description']) + \
                      '\u200B' * (card["baseData"]["description"] == '')
        # this is because discord embeds don't accept empty strings as fields unless they're passed with this ASCII
        self.attack = card['baseData']['attack']
        self.defense = card['baseData']['defense']
        self.evo_flair = clean_string(card['evoData']['flair'])
        self.evo_effect = clean_string(card['evoData']['description']) + \
                          '\u200B' * (card["evoData"]["description"] == '')
        self.evo_attack = card['evoData']['attack']
        self.evo_defense = card['evoData']['defense']
        self.searchable = card['searchableText']

    def __str__(self):
        return "\n{}" \
               "\n{} - {} {} {} from {}" \
               "\n {}/{} -> {}/{}" \
               "\n {}" \
               "\n {}".format(self.pic,
                              self.name, self.rarity, self.craft, self.type, self.expac,
                              self.attack, self.defense, self.evo_attack, self.evo_defense,
                              self.effect,
                              self.evo_effect)


"""
A test function for this class is in Pool.py, since Card is initialized with data in a json that's loaded there.
"""
