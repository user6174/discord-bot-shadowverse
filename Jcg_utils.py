import json
import aiohttp
import async_timeout
import pyshorteners
from bs4 import BeautifulSoup


async def soup_from_url(session, url, timeout=10):
    async with async_timeout.timeout(timeout):
        async with session.get(url) as response:
            html = await response.text()
            return BeautifulSoup(html, 'html.parser')


def build_player(shortener, match_soup, player_idx):
    player_name = match_soup.find_all('p', class_="name_abbr webfont")[player_idx].text.strip().split('\n')[0]
    player_data = {"player": player_name, "decks": [], "tinydecks": [], "crafts": []}
    side = match_soup.find("div", class_=("team_wrap leftteam", "team_wrap rightteam")[player_idx])
    for deck in side.find_all('a', target="_svp"):
        player_data["decks"].append(
            f'https://shadowverse-portal.com/deck/{deck["href"].split("hash=")[1].split("&lang=en")[0]}?lang=en')
        player_data["tinydecks"].append(shortener.tinyurl.short(player_data["decks"][-1]))
        player_data["crafts"].append(int(player_data["decks"][-1][38]))
    return player_data


async def scrape_tournament(session, url, format_) -> dict or None:
    shortener = pyshorteners.Shortener()
    soup = await soup_from_url(session, url)
    name = f'{" ".join(word.text for word in soup.find_all("span", class_="nobr"))}'
    name = name.split('月')[0] + '/' + name.split('月')[1].split('日')[0] + '/2020'
    print(name)
    try:
        with open(f'{format_}.json', 'r') as f:
            try:
                tmp = json.load(f)
                if tmp["name"] == name:
                    print(f'already scraped, skipping')
                    return None
                else:
                    print(f'determined that {name} is newer than {tmp["name"]}')
            except json.decoder.JSONDecodeError:  # corrupt json, re-scrape
                pass
    except FileNotFoundError:  # no json, scrape
        pass
    soup = soup.find("div", class_="tourview-wrap")
    rounds = len(soup.find_all("ul", class_="matches")) + 1
    ret = {pos: [] for pos in [2 ** round_ for round_ in range(rounds)]}
    ret["name"] = name
    ret["crafts"] = [0] * 8
    ret["code"] = url.split('/')[-1]
    for round_ in range(1, rounds):
        matches = soup.find('div', class_=f'round{round_}')
        print(f'Scraping round {round_}...')
        _len = (len(matches.find_all('li', class_="match")))
        for idx, match in enumerate(matches.find_all('li', class_="match")):
            match_url = match["onclick"].split('\'')[-2]
            print(f'\tScraping match {idx + 1}/{_len}...')
            match_soup = await soup_from_url(session, match_url)
            score = match_soup.find('p', class_="score webfont").text.strip()
            try:
                loser_idx = int(score[0]) > int(score[-1])
            except ValueError:  # at least one player didn't show up, score is "-"
                continue
            player = build_player(shortener, match_soup, loser_idx)
            # position 38 is where the craft int is in the url
            crafts = (int(deck[38]) for deck in player["decks"])
            ret[2 ** (rounds - round_)].append(player)
            for craft in crafts:
                ret["crafts"][craft - 1] += 1
            if round_ == rounds - 1:  # registering the winner
                player = build_player(shortener, match_soup, not loser_idx)
                crafts = (int(deck[38]) for deck in player["decks"])
                ret[1].append(player)
                for craft in crafts:
                    ret["crafts"][craft - 1] += 1
    return ret


async def scrape_jcg(format_):
    url = f'https://sv.j-cg.com/compe/{format_}?perpage=20&start=0'
    print(url)
    async with aiohttp.ClientSession() as session:
        soup = await soup_from_url(session, url)
        for tourney in soup.find_all('tr', class_="competition"):
            # txt==end, qualifying not in
            if tourney.find('td', class_="status").text == '終了' and \
                    'グループ予選' not in ' '.join(t.text for t in tourney.find_all('a', class_="link-nodeco link-black")):
                url = f'https://sv.j-cg.com/compe/view/tour/' \
                      f'{tourney.find("a", class_="link-nodeco link-black")["href"].split("/")[-1]}'
                print(f'newest tourney: {url}')
                return await scrape_tournament(session, url, format_)


async def update_jcg():
    last = await scrape_jcg('rotation')
    if last is not None:
        with open('rotation.json', 'w+') as f:
            json.dump(last, f)
    last = await scrape_jcg('unlimited')
    if last is not None:
        with open('unlimited.json', 'w+') as f:
            json.dump(last, f)
