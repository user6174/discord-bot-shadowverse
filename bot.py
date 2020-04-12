from pool_bot import *
from table_bot import *

pool = Pool()
token = 'Njg0MTQyODIwMTIyMjk2MzQ5.Xl13Ww.52HjCT9BrAxD75rf-TPHKe6dD2s'
BOT_PREFIX = '+'


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
                await message.add_reaction("🇪")  # regional indicator E
            return  # to avoid unaccounted for self-replies

        if message.content.startswith(BOT_PREFIX):
            messageString = message.content.replace(BOT_PREFIX, '')
            dm = ""  # a possible direct message to be sent

            # Draft commands
            if messageString.startswith("join"):
                out, dm = out_join(message.author)
            elif messageString.startswith("players"):
                out = out_player_list()
            elif messageString.startswith("leave"):
                out, dm = out_leave(message.author)

            # Card display commands
            elif messageString.startswith("random"):
                out = out_random_card()
            elif messageString[0] == messageString[-1] == "\"":
                out = out_exact_search(messageString)
            else:
                out = out_search(messageString)

            await message.channel.send(embed=out)
            if dm != "":
                await message.author.send(dm)

    async def on_reaction_add(self, reaction, user):
        if reaction.message.author.id == self.user.id \
                and user != self.user \
                and reaction.message.embeds:
            if "Follower" in reaction.message.embeds[0].description:
                cardName = reaction.message.embeds[0].title
                await reaction.message.channel.send(embed=card_to_embed(cardName, evo=True))


client = MyClient()
client.run(token)
