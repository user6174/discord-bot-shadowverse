import discord  # https://discordpy.readthedocs.io/en/latest/api.html
# from images import *
from cards import *

token = 'Njg0MTQyODIwMTIyMjk2MzQ5.Xl13Ww.52HjCT9BrAxD75rf-TPHKe6dD2s'

p = Pool()


def cardToEmbed(card):
    embed = discord.Embed(title="{} {} {}".format(card.rarity, card.craft, card.type))
    embed.set_image(url=card.pic)
    embed.add_field(name="effect:", value=card.effect)
    embed.set_footer(text=card.flair)
    return embed


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
            randomCard = cardToEmbed(p.getRandomCard())
            await message.channel.send(embed=randomCard)
            message.react(":regional_indicator_e:")


client = MyClient()
client.run(token)
