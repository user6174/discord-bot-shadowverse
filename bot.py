from pool_bot import *
from table_bot import *

pool = Pool()
token = 'Njg0MTQyODIwMTIyMjk2MzQ5.Xl13Ww.52HjCT9BrAxD75rf-TPHKe6dD2s'
BOT_PREFIX = '+'
MAX_MATCHES = 15


class MyClient(discord.Client):
    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_message(self, message):
        if message.author.id == self.user.id:
            reactions = []
            if react_to_card_embed(message.embeds):
                reactions = reactions_to_card_embed()
            elif react_to_search_list(message.embeds):
                reactions = reactions_to_search_list(message.embeds)
            if reactions:
                for i in reactions:
                    await message.add_reaction(i)
            return

        if message.content.startswith(BOT_PREFIX):
            messageString = message.content.replace(BOT_PREFIX, '')
            # out = ""
            dm = ""  # a possible direct message to be sent

            # Draft commands
            if messageString.startswith("join"):
                out, dm = send_join(message.author)
            elif messageString.startswith("players"):
                out = send_player_list()
            elif messageString.startswith("leave"):
                out, dm = send_leave(message.author)

            # Card display commands
            elif messageString.startswith("random"):
                out = send_random_card()
            elif messageString[0] == messageString[-1] == "\"":
                out = send_exact_search(messageString)
            else:
                out = send_search(messageString, MAX_MATCHES)

            await message.channel.send(embed=out)
            if dm != "":
                await message.author.send(dm)

    async def on_reaction_add(self, reaction, user):
        out = ""
        dm = ""
        if reaction.message.author.id == self.user.id and user != self.user:
            if requested_send_card_evo(reaction):
                out = send_card(card_name_from_embeds(reaction.message.embeds), evo=True)
            if requested_send_card_from_list(reaction):
                out = send_card_from_list(reaction)

            if out != "":
                await reaction.message.channel.send(embed=out)
            if dm != "":
                await reaction.message.author.send(dm)


client = MyClient()
client.run(token)
