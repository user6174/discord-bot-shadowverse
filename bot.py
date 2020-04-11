import discord  # https://discordpy.readthedocs.io/en/latest/api.html
# from images import *
from cards import *

token = 'Njg0MTQyODIwMTIyMjk2MzQ5.Xl13Ww.52HjCT9BrAxD75rf-TPHKe6dD2s'
BOT_PREFIX = '+'
p = Pool()


def cardToEmbed(card, evo=False):
    card = p[card]
    embed = discord.Embed(title=card.name + " [Evolved]" * evo,
                          description="{} {} {}".format(card.rarity, card.craft, card.type))
    if card.type == "Follower":
        embed.add_field(name="Base effect: ", value=card.effect)
        embed.add_field(name="Base stats: ", value="{}/{}".format(card.attack, card.defense))
        embed.add_field(name="\u200B", value="\u200B", inline=False)  # Separator
        embed.add_field(name="Evo effect: ", value=card.evoEffect)
        embed.add_field(name="Evo stats: ", value="{}/{}".format(card.evoAttack, card.evoDefense))
    else:
        embed.add_field(name="Effect:", value=card.effect)
    if evo:
        embed.set_image(url=card.evoPic)
        embed.set_footer(text=card.evoFlair)
    else:
        embed.set_image(url=card.pic)
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
            if "Follower" in message.embeds[0].description \
                    and "[Evolved]" not in message.embeds[0].title:
                await message.add_reaction('\N{THUMBS UP SIGN}')
            return

        if message.content.startswith(BOT_PREFIX):
            messageString = message.content.replace(BOT_PREFIX, '')
            # Random card
            if messageString.startswith("random"):
                randomCard = cardToEmbed(p.getRandomCard().name)
                await message.channel.send(embed=randomCard)
            # Card search
            matches = p.search(messageString, maxMatches=25)
            if matches:
                if len(matches) == 1:
                    await message.channel.send(embed=cardToEmbed(matches[0]))
                else:
                    await message.channel.send("I found these cards: {}".format(matches))
            else:
                await message.channel.send("Too many card matches or invalid card name.")

    async def on_reaction_add(self, reaction, user):
        if reaction.message.author.id == self.user.id \
                and user != self.user \
                and reaction.message.embeds:
            if "Follower" in reaction.message.embeds[0].description:
                cardName = reaction.message.embeds[0].title
                await reaction.message.channel.send(embed=cardToEmbed(cardName, evo=True))


client = MyClient()
client.run(token)
