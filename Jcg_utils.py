import asyncio
import json
import aiohttp
import async_timeout
import pyshorteners
import requests
from bs4 import BeautifulSoup
from selenium import webdriver


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
        while len(player_data["tinydecks"]) < len(player_data["decks"]):
            try:
                player_data["tinydecks"].append(shortener.tinyurl.short(player_data["decks"][-1]))
            except requests.exceptions.ReadTimeout:
                continue
        player_data["crafts"].append(int(player_data["decks"][-1][38]))
    return player_data


async def scrape_tournament(url, format_) -> dict or None:
    shortener = pyshorteners.Shortener()
    headless = webdriver.ChromeOptions()
    headless.add_argument('--headless')
    driver = webdriver.Chrome(options=headless)
    driver.get(url)
    name = driver.find_element_by_xpath('//div[@class="competition-title"]').text
    name = ' '.join(name.split()[:6])
    code = url.split('/')[4]
    print(f'name: {name}')
    try:
        with open(f'{format_}.json', 'r') as f:
            try:
                tmp = json.load(f)
                if tmp["code"] == code:
                    print(f'already scraped, skipping')
                    return None
                else:
                    print(f'{name} is newer than {tmp["name"]}, scraping')
            except json.decoder.JSONDecodeError:
                print('corrupt json, scraping')
                pass
    except FileNotFoundError:  # no json, scrape
        print('no json found, scraping')
        pass
    for roundd in driver.find_elements_by_xpath('//div[@_ngcontent-c3 class="roundTitle"]'):
        print(roundd.text)
    return
    rounds = len(soup.find_all("ul", class_="matches")) + 1
    ret = {pos: [] for pos in [2 ** round_ for round_ in range(rounds)]}
    ret["name"] = name
    ret["crafts"] = [0] * 8
    ret["code"] = code
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
    url = f'https://sv.j-cg.com/past-schedule/{format_}'
    print(url)
    async with aiohttp.ClientSession() as session:
        soup = await soup_from_url(session, url)
        for tourney in soup.find_all('a', class_="schedule-link"):
            # final in text
            if '決勝' in tourney.find('div', class_="schedule-title").text:
                url = tourney['href'] + '/bracket'
                print(f'newest tourney: {url}')
                return await scrape_tournament(url, format_)


async def update_jcgs():
    last = await scrape_jcg('rotation')
    if last is not None:
        with open('rotation.json', 'w+') as f:
            json.dump(last, f)
    last = await scrape_jcg('unlimited')
    if last is not None:
        with open('unlimited.json', 'w+') as f:
            json.dump(last, f)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(update_jcgs())
