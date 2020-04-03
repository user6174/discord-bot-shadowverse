import discord
from images import *
from cards import *

token = 'Njg0MTQyODIwMTIyMjk2MzQ5.Xl13Ww.52HjCT9BrAxD75rf-TPHKe6dD2s'

p = Pool()
class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_message(self, message):
        if message.author.id == self.user.id:
            return
        if message.content.startswith('+random'):
            await message.channel.send(p.randomCard().name)

client = MyClient()
client.run(token)
