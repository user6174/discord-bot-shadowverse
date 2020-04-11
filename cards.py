import json
import random

with open("en.json", 'r') as f:
    data = json.load(f)


# data is a list of dictionaries (cards), whose key is the card name. Example:
# >>> data["Robogoblin"].keys()
# dict_keys(['name', '_name', 'id', 'faction', '_faction', 'rarity', '_rarity', 'race', 'expansion', '_expansion',
# 'type', '_type', 'hasEvo', 'hasAlt', 'hasAlt2', 'manaCost', 'baseData', 'evoData', 'rot', 'searchableText'])
#
# Note that baseData and evoData are dictionaries themselves:
# >>> data["Robogoblin"]["evoData"].keys()
# dict_keys(['description', 'flair', 'attack', 'defense'])

def cleanString(string):  # adjusts the formatting of effects and flairs
    return string.replace("<br>", '') \
        .replace('.', ".\n") \
        .replace(".\n)", ".)") \
        .replace("- ", "-\n")


class Card:
    def __init__(self, name):
        card = data[name]
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
        self.flair = cleanString(card['baseData']['flair'])
        self.effect = cleanString(card['baseData']['description']) + \
                      '\u200B' * (card["baseData"]["description"] == '')
        # this is because discord embeds don't accept empty strings as fields unless they're passed with this ASCII
        self.attack = card['baseData']['attack']
        self.defense = card['baseData']['defense']
        self.evoFlair = cleanString(card['evoData']['flair'])
        self.evoEffect = cleanString(card['evoData']['description']) + \
                         '\u200B' * (card["evoData"]["description"] == '')
        self.evoAttack = card['evoData']['attack']
        self.evoDefense = card['evoData']['defense']

    def __str__(self):  # just for debugging purposes, could print richer information
        return "\n{}" \
               "\n{}" \
               "\n {}/{} {} {} {}".format(self.pic,
                                          self.name,
                                          self.attack, self.defense, self.rarity, self.craft, self.type)


class Pool:

    def __init__(self):
        self.cards = {}
        for i in data:
            self.cards[data[i]["name"]] = Card(data[i]['name'])

    def __getitem__(self, key):
        return self.cards[key]

    def search(self, card, maxMatches):
        card = card.lower()
        result = []
        for i in self.cards:
            if card in i.lower():
                result.append(i)
            if len(result) > maxMatches:
                return []
        return result

    def __iter__(self):
        return enumerate(self.cards)

    def getRandomCard(self):
        return self.cards[random.choice(list(self.cards.keys()))]


# ONLY RUN THIS IF YOU DON'T HAVE THE IMAGE ASSETS
# RUN THIS FUNCTION IN THE DIRECTORY YOU WISH THE IMAGES TO BE SAVED IN
# THE CARD IMAGES AMOUNT TO ~1.5GB
# if the download gets stuck on a particular card use a skip flag
def downloadPics():
    import urllib.request
    p = Pool()
    for i in p:
        print("downloading {}".format(i.name))
        urllib.request.urlretrieve(i.pic, "{}.jpg".format(i.name))


del data
