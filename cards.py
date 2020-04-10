import json
import random

with open("en.json", 'r') as f:
    data = json.load(f)


class Card:

    def __init__(self, name):
        card = data[name]
        self.name = card['name']
        self.id = card['id']
        self.pic = "https://sv.bagoum.com/cardF/en/c/{}".format(self.id)
        self.evopic = "https://sv.bagoum.com/cardE/en/c/{}".format(self.id)
        self.craft = card['faction']
        self.rarity = card['rarity']
        self.trait = card['race']
        self.expac = card['expansion']
        self.type = card['type']
        self.pp = card['manaCost']
        self.flair = card['baseData']['flair']
        self.effect = card['baseData']['description'].replace('<br>', '')
        self.attack = card['baseData']['attack']
        self.defense = card['baseData']['defense']

    def __str__(self):
        return "\n{}" \
               "\n{}" \
               "\n {}/{} {} {} {}".format(self.pic,
                                          self.name,
                                          self.attack, self.defense, self.rarity, self.craft, self.type)


class Pool:

    def __init__(self, expac=''):
        self.cards = [Card(data[i]['name']) for i in data if data[i]['expansion'] != 'Token']
        if expac != '':
            self.cards = [i for i in self.cards if expac == i.expac]

    def __getitem__(self, index):
        return self.cards[index]

    def getRandomCard(self):
        return self.cards[random.randint(0, len(self.cards))]


### ONLY RUN THIS IF YOU DON'T HAVE THE IMAGE ASSETS
### RUN THIS FUNCTION IN THE DIRECTORY YOU WISH THE IMAGES TO BE SAVED IN
### THE CARD IMAGES AMOUNT TO ~1.5GB
### if the download gets stuck on a particular use a skip flag
def download_pics():
    import urllib.request
    for i in cards:
        print("downloading {}".format(i.name))
        urllib.request.urlretrieve(i.pic, "{}.jpg".format(i.name))


def moduleTest():
    p = Pool()
    print(p[0])
