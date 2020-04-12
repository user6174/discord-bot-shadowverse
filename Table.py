"""
per ora i giocatori sono solo una stringa con il loro ID ma eventualmente dovranno essere una classe quando
bisognerà aggiungere metodi come user.printdeck (e pure deck sarà una classe!)
"""


class Table:
    def __init__(self):
        self.playerList = []

    def __str__(self):
        return str(self.playerList)

    def __contains__(self, item):
        return item in self.playerList

    def __iter__(self):
        return enumerate(self.playerList)

    def __getitem__(self, item):
        return self.playerList[item]

    def __len__(self):
        return len(self.playerList)

    def add(self, user):
        if user not in self.playerList:
            self.playerList.append(user)
            return True
        return False

    def remove(self, user):
        if user in self.playerList:
            self.playerList.remove(user)
            return True
        return False
