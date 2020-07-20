import json
import logging
import os

from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry


def scrape_tournament(url, format_):
    logging.basicConfig(level=logging.DEBUG)
    req = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    req.mount('https://', HTTPAdapter(max_retries=retries))
    page = req.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    name = f'{" ".join(word.text for word in soup.find_all("span", class_="nobr"))}.json'
    soup = soup.find("div", class_="tourview-wrap")
    if soup is None:  # link didn't exist, redirected to main page
        return
    file_path = f'{os.getcwd()}/jcg/{format_}/{name}'
    if name in os.listdir(f'{os.getcwd()}/jcg/rotation/') + \
                os.listdir(f'{os.getcwd()}/jcg/unlimited/') + \
                os.listdir(f'{os.getcwd()}/jcg/other/') or \
            'グループ予選' in name or \
            '2Pick' in name:  # skip already parsed and qualifying and 2pick tournaments
        print(f'Skipping {name}')
        return name
    print(name)
    rounds = len(soup.find_all("ul", class_="matches")) + 1
    to_json = {pos: [] for pos in [2**round_ for round_ in range(rounds)]}
    to_json["crafts"] = [0] * 8
    to_json["code"] = url.split('/')[-1]
    for round_ in range(1, rounds):
        matches = soup.find('div', class_=f'round{round_}')
        print(f'Scraping round {round_}...')
        for match in matches.find_all('li', class_="match"):
            match_url = match["onclick"].split('\'')[-2]
            match_page = req.get(match_url)
            match_soup = BeautifulSoup(match_page.content, 'html.parser')
            score = match_soup.find('p', class_="score webfont").text.strip()
            try:
                loser_idx = int(score[0]) > int(score[-1])
            except ValueError:  # at least one player didn't show up, score is "-"
                continue
            player = build_player(match_soup, loser_idx)
            # position 59 is where the craft int is in the url
            crafts = (int(deck[59]) - 1 for deck in player["decks"])
            to_json[2 ** (rounds - round_)].append(player)
            for craft in crafts:
                to_json["crafts"][craft] += 1
            if round_ == rounds - 1:  # registering the winner
                player = build_player(match_soup, not loser_idx)
                crafts = (int(deck[59]) - 1 for deck in player["decks"])
                to_json[1].append(player)
                for craft in crafts:
                    to_json["crafts"][craft] += 1
    with open(file_path, 'w+') as f:
        json.dump(to_json, f)
    return name


def build_player(match_soup, player_idx):
    player_name = match_soup.find_all('p', class_="name_abbr webfont")[player_idx].text.strip().split('\n')[0]
    player_data = {"player": player_name, "decks": []}
    side = match_soup.find("div", class_=("team_wrap leftteam", "team_wrap rightteam")[player_idx])
    for deck in side.find_all('a', target="_svp"):
        player_data["decks"].append(deck["href"])
    return player_data


def scrape_jcg(format_, page=0, once=False):
    url = f'https://sv.j-cg.com/compe/{format_}?perpage=20&start={20 * page}'
    print(url)
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    for tourney in soup.find_all('tr', class_="competition"):
        # txt==end, qualifying not in
        if tourney.find('td', class_="status").text == '終了' and \
                'グループ予選' not in ' '.join(t.text for t in tourney.find_all('a', class_="link-nodeco link-black")):
            url = f'https://sv.j-cg.com/compe/view/tour/' \
                  f'{tourney.find("a", class_="link-nodeco link-black")["href"].split("/")[-1]}'
            print(url)
            if once:
                return scrape_tournament(url, format_)
            scrape_tournament(url, format_)


def scrape_everything(format_):
    for page in range(35):
        print(f'{"*" * 75} page {page + 1} {"*" * 75}')
        scrape_jcg(format_, page)


def scrape_pre_split():
    for code in range(750):
        url = f'https://sv.j-cg.com/compe/view/tour/{code}'
        print(url)
        scrape_tournament(url, 'other')


# format_ = "rotation"
# name = "JCG Shadowverse Open 14th Season Vol.8 7月12日 ローテーション大会 決勝トーナメント.json"
# file_path = f'{os.getcwd()}/jcg/{format_}/{name}'
# shortener = pyshorteners.Shortener()
# with open(file_path, 'r') as f:
#     tourney = json.load(f)
# for top in ['1', '2', '4']:
#     craft_names = ("", "Forestcraft", "Swordcraft", "Runecraft", "Dragoncraft",
#                    "Shadowcraft", "Bloodcraft", "Havencraft", "Portalcraft")
#     decks = ["/".join(f'[{craft_names[int(deck[59])]}]({shortener.tinyurl.short(deck)})' for deck in player["decks"]) for
#              player in tourney[top]]
#     line = [f'{player["player"]}: {decks[idx]}\n' for idx, player in enumerate(tourney[top])]
#     print(", ".join(line))



# scrape_everything('rotation')
# scrape_everything('unlimited')
# scrape_jcg('rotation', once=True)
# scrape_jcg('unlimited')
# scrape_pre_split()
