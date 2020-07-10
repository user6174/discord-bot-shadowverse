import json
import logging
import os
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry


def scrape_tournament(url):
    logging.basicConfig(level=logging.DEBUG)
    req = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    req.mount('https://', HTTPAdapter(max_retries=retries))
    page = req.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    name = f'{" ".join(word.text for word in soup.find_all("span", class_="nobr")[3:7])}.json'
    file_path = f'{os.getcwd()}/jcg/{name}'
    try:
        with open(file_path, 'r'):
            return
    except IOError:
        pass
    to_json = {pos: [] for pos in [1, 2, 4, 8, 16]}
    to_json["crafts"] = [0] * 8
    to_json["code"] = url[-4:]
    for i in range(1, 5):
        round_ = soup.find('div', class_=f'round{i}')
        print(f'Scraping round {i}...')
        for match in round_.find_all('li', class_="match"):
            match_url = match["onclick"].split('\'')[-2]
            match_page = requests.get(match_url)
            match_soup = BeautifulSoup(match_page.content, 'html.parser')
            score = match_soup.find('p', class_="score webfont").text.strip()
            try:
                score = [int(score[0]), int(score[-1])]
            except ValueError:
                continue
            player, left_craft, right_craft = build_player(match_soup, score[0] > score[1])
            if player is not None:
                to_json[2 ** (5 - i)].append(player)
                to_json["crafts"][left_craft] += 1
                to_json["crafts"][right_craft] += 1
            if i == 4:
                player, left_craft, right_craft = build_player(match_soup, score[1] > score[0])
                to_json[1].append(player)
                to_json["crafts"][left_craft] += 1
                to_json["crafts"][right_craft] += 1
    with open(file_path, 'w+') as f:
        json.dump(to_json, f)


def build_player(match_soup, player_idx):
    player_name = match_soup.find_all('p', class_="name_abbr webfont")[player_idx].text.strip().split('\n')[0]
    player_data = {"player": player_name, "decks": []}
    for deck in match_soup.find_all('a', target="_svp")[2 * player_idx:2 * (player_idx + 1)]:
        player_data["decks"].append(deck["href"])
    # position 59 is where the craft int is in the url
    try:
        return player_data, int(player_data["decks"][0][59]) - 1, int(player_data["decks"][1][59]) - 1
    except IndexError:
        return None, None, None


def scrape_last_jcg(format_):
    url = f'https://sv.j-cg.com/compe/{format_}'
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    for tourney in soup.find_all('tr', class_="competition"):
        # txt==end, qualifying not in
        if tourney.find('td', class_="status").text == '終了' and \
                'グループ予選' not in ' '.join(t.text for t in tourney.find_all('a', class_="link-nodeco link-black")):
            url = f'https://sv.j-cg.com/compe/view/tour/' \
                  f'{tourney.find("a", class_="link-nodeco link-black")["href"][-4:]}'
            print(url)
            return scrape_tournament(url)


def show_last_jcg():
    craft_names = ["", "Forestcraft", "Swordcraft", "Runecraft", "Dragoncraft",
                   "Shadowcraft", "Bloodcraft", "Havencraft", "Portalcraft"]
    with open(max([f for f in os.listdir(os.curdir) if f.endswith(".json")], key=os.path.getctime), 'r') as f_:
        tourney = json.load(f_)
    for top in ['1', '2', '4', '8', '16']:
        print(f'TOP{top}')
        for idx, player in enumerate(tourney[top]):
            print(f'{player["player"]}\n'
                  f'{craft_names[int(player["decks"][0][59])]} {player["decks"][0]} \n'
                  f'{craft_names[int(player["decks"][1][59])]} {player["decks"][1]} \n')
    craft_distribution = ''
    for idx, craft in enumerate(tourney["crafts"]):
        craft_distribution += f'{craft} {craft_names[idx + 1]}\n'
    print(craft_distribution)
