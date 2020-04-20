from Deck import *


class Player:
    def __init__(self, user):
        self.id = user['id']
        self.name = user['name']
        self.mainDeck = Deck()
        self.sideBoard = Deck()
        self.picks = Deck()

    def move_card(self, card, pool1, pool2):
        """
        :param card:
        :param pool1: source
        :param pool2: destination
        :return:
        """
        try:
            assert card in pool1 and pool1, pool2 in [self.mainDeck, self.sideBoard, self.picks]
            pool1.remove_from_deck(card)
            pool2.add_to_deck(card)
        except AssertionError:
            print('Invalid Card')
            return -1


def module_test():
    user = []
    player = []
    user.append({'id': 77421312, 'name': 'Fanix'})
    user.append({'id': 78554315, 'name': 'gageeno'})
    player.append(Player(user[0]))
    player.append(Player(user[1]))
    player[0].picks.add_to_deck('Gabriel')
    player[0].picks.add_to_deck('Water Fairy')
    player[0].picks.add_to_deck('Bahamut')
    player[1].picks.add_to_deck('Abomination Awakened')
    player[1].picks.add_to_deck('Abomination Awakened')
    player[1].picks.add_to_deck('Mutagenic Bolt')
    player[0].move_card('Gabriel', player[0].picks, player[0].mainDeck)
    player[0].move_card('Bahamut', player[0].picks, player[0].mainDeck)
    player[1].move_card('Abomination Awakened', player[1].picks, player[1].mainDeck)
    player[1].move_card('Abomination Awakened', player[1].picks, player[1].mainDeck)
    player[1].move_card('Mutagenic Bolt', player[1].picks, player[1].mainDeck)
    print(player[0].mainDeck)
    print(player[1].mainDeck)
    player[1].move_card('Abomination Awakened', player[1].picks, player[1].sideBoard)
    print(player[1].sideBoard)
    player[1].move_card('Abomination Awakened', player[1].sideBoard, player[1].mainDeck)
    print(player[1].mainDeck)
    player[1].move_card('Mutagenic Bolt', player[1].mainDeck, player[1].sideBoard)
    print(player[1].mainDeck)
    print(player[1].sideBoard)


module_test()