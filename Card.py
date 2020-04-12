def clean_string(string):  # adjusts the formatting of effects and flairs
    return string.replace("<br>", '') \
        .replace('.', ".\n") \
        .replace(".\n)", ".)") \
        .replace("- ", "-\n")


class Card:
    def __init__(self, card):
        self.name = card['name']
        self.id = card['id']
        self.pic = "https://sv.bagoum.com/cardF/en/c/{}".format(self.id)
        self.evoPic = "https://sv.bagoum.com/cardF/en/e/{}".format(self.id)
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
        self.evoFlair = clean_string(card['evoData']['flair'])
        self.evoEffect = clean_string(card['evoData']['description']) + \
                         '\u200B' * (card["evoData"]["description"] == '')
        self.evoAttack = card['evoData']['attack']
        self.evoDefense = card['evoData']['defense']

    def __str__(self):  # just for debugging purposes, could print richer information
        return "\n{}" \
               "\n{}" \
               "\n {}/{} {} {} {}".format(self.pic,
                                          self.name,
                                          self.attack, self.defense, self.rarity, self.craft, self.type)
