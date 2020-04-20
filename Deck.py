from Pool import *

pool = Pool()


class Deck:
    def __init__(self):
        self.cards = {}
        # tolte le cose di test

    def __len__(self):
        return len(self.cards)

    def __contains__(self, item):
        return item in self.cards

    def add_to_deck(self, card):
        try:
            assert card in pool.cards
            if card in self:
                self.cards[card] += 1
            else:
                self.cards[card] = 1
        except AssertionError:
            print('Invalid Card')
            return -1

    def remove_from_deck(self, card):
            if card in self:
                self.cards[card] -= 1
                if self.cards[card] == 0:
                    del self.cards[card]
            else:
                print('Carta non nel mazzo')


    def __str__(self, rich=True):
        out = ''
        for cardName, copies in self.cards.items():
            out += "{}x {}\n".format(copies, cardName)
        if rich:
            curve = self.strCurve()
            out += "      1   5    10   15   20"
            for i in range(len(curve)):
                out += '\n{}pp {}'.format("<=" * (i == 0) + ">=" * (i == 7) + "  " * (0 < i < 7) + str(i + 1),
                                          '#' * curve[i])  # non fare caso a questo, l'ho solo imbellettato ma niente di rilevante
        return out  # importante il return invece che il print perchè è una conversione in stringa generica, non una print
    # (da notare che avrebbe funzionato allo stesso modo chiamando print(deck) che è la cosa principale, ma str(deck) sarebbe stata diversa ad esempio)

    def strCurve(self):
        ppCurve = [0] * 8  # non serve un dizionario qui, più maneggevole una lista
        for cardName, copies in self.cards.items():
            card = pool.cards[cardName]
            if card.pp <= 1:
                ppCurve[0] += copies
            elif card.pp >= 8:
                ppCurve[7] += copies
            else:
                ppCurve[card.pp - 1] += copies
        return ppCurve


'''

def module_test():
    deck = Deck()
    deck.add_to_deck('Gabriel')
    for i in range(13):
        deck.add_to_deck('Vania, Vampire Princess')
    deck.add_to_deck('Gabriel')
    try:
        deck.add_to_deck('feafa')  # se devi testare una cosa che sospetti darà errore usa try except
    except KeyError:
        print("Adding an invalid card gave an error.")
    deck.add_to_deck('Roland the Incorruptible')
    deck.add_to_deck('Dimension Shift')
    deck.remove_from_deck('Vania, Vampire Princess')
    deck.remove_from_deck('Bahamut')
    deck.remove_from_deck('Roland the Incorruptible')
    print(deck)

module_test()

'''