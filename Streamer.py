import pandas as pd
import requests
from bs4 import BeautifulSoup
import os.path

from gephistreamer import graph
from gephistreamer import streamer

conferences = ['fbs', 'fcs', 'd2', 'd3']
alternate_names = {'Washington St.': 'Washington State',  # fbs
                   'Penn St.': 'Penn State',
                   'Army West Point': 'Army',
                   'Western Mich.': 'Western Michigan',
                   'Western Ky.': 'Western Kentucky',
                   'Mich. St. ': 'Michigan State',
                   'Northern Ill.': 'Northern Illinois',
                   'La.-Monroe': 'Louisiana-Monroe',
                   'Middle Tenn.': 'Middle Tennessee',
                   'New Mexico St.': 'New Mexico State',
                   'Central Mich.': 'Central Michigan',
                   'Oregon St.': 'Oregon State',
                   'Kansas St.': 'Kansas State',
                   'Arizona St.': 'Arizona State',
                   'Miami (Ohio)': 'Miami (OH)',
                   'Massachusetts': 'UMass',
                   'Appalachian St.': 'Appalachian State',
                   'Mississippi St.': 'Mississippi State',
                   'Ga. Southern': 'Georgia Southern',
                   'Eastern Mich.': 'Eastern Michigan',
                   'Ohio St. ': 'Ohio State',
                   'Coastal Caro.': 'Coastal Carolina',
                   'UNI': 'Northern Iowa',  # fcs
                   'Northern Ariz.': 'Northern Arizona',
                   'McNeese ': 'McNeese State',
                   'Northern Colo.': 'Northern Colorado',
                   'ETSU': 'East Tennessee State',
                   'Sam Houston St.': 'Sam Houston State',
                   'Youngstown St.': 'Youngstown State',
                   'Southeast Mo. St.': 'Southeast Missouri State',
                   'Nicholls State': 'Nicholls',
                   'Western Caro.': 'Western Carolina',
                   'Southeastern La.': 'Southeastern Louisiana',
                   'Charleston So.': 'Charleston Southern',
                   'S. Carolina St.': 'South Carolina State',
                   'Southern Ill.': 'Southern Illinois',
                   'St. Francis (Pa.)': 'Saint Francis',
                   'Jacksonville': 'Jacksonville State',
                   'N.C. A&T': 'North Carolina A&T',
                   'South Dakota St.': 'South Dakota State',
                   'N.C. Central': 'North Carolina Central',
                   'Central Ark.': 'Central Arkansas',
                   'Southern Univ.': 'Southern',
                   'Sacramento St.': 'Sacramento State',
                   'Lamar University': 'Lamar',
                   'SFA': 'Stephen F. Austin',
                   'North Dakota St.': 'North Dakota State',
                   'Grambling': 'Grambling State',
                   'Montana St.': 'Montana State',
                   'Incarnate Word': 'Incarnate Word',
                   'Ark.-Pine Bluff': 'Arkansas-Pine Bluff',
                   'N\'western St.': 'Northwestern State',
                   'Eastern Wash.': 'Eastern Washington',
                   'Cent. Conn. St.': 'Central Connecticut',
                   'Mississippi Val.': 'Mississippi Valley State'
                   }
conference_colors = {'ACC': (52, 77, 133),  # fbs
                     'American': (25, 37, 64),
                     'Big 12': (155, 47, 56),
                     'Big Ten': (76, 135, 202),
                     'C-USA': (142, 31, 49),
                     'Independent': (0, 0, 0),
                     'MAC': (33, 44, 70),
                     'Mountain West': (174, 173, 174),
                     'Pac-12': (51, 76, 137),
                     'SEC': (243, 208, 90),
                     'Sun Belt': (226, 168, 47),
                     'Big Sky': (52, 93, 168),  # fcs
                     'Big South': (218, 122, 44),
                     'CAA': (22, 38, 72),
                     'Ivy': (49, 86, 64),
                     'MEAC': (63, 25, 112),
                     'Missouri Valley': (195, 24, 54),
                     'Northeast': (58, 103, 162),
                     'Ohio Valley': (141, 25, 66),
                     'Patriot': (39, 57, 109),
                     'Pioneer': (138, 105, 82),
                     'Southern': (188, 40, 28),
                     'Southland': (238, 184, 56),
                     'SWAC': (204, 30, 49),
                     'default': (52, 69, 75)}
fbs_schools = set()


def hex_to_rgb(hex):
    return tuple(int(hex[i:i + 2], 16) for i in (0, 2, 4))


def collect_data():
    year = 2018
    for conference in conferences:
        for week in range(1, 17):
            get_and_save(week, year, conference)


def get_and_save(week_num, year=2019, conference='fbs'):
    url = 'https://www.ncaa.com/scoreboard/football/{}/{:04d}/{:02d}/all-conf'.format(conference,
                                                                                      year,
                                                                                      week_num)
    response = requests.get(url)
    with open("data/{}/{}week{}.html".format(conference, year, week_num), "w+") as f:
        f.write(str(response.content))


def add_schools(stream, mode='conference'):
    schools = pd.read_csv("FCS Teams.csv", header=0)
    for index, school in schools.iterrows():
        if mode == 'conference':
            r, g, b = conference_colors[school['Conference']]
        elif mode == 'school':
            if pd.isna(school['HEX']):
                r, g, b = 0, 0, 0
            else:
                r, g, b = hex_to_rgb(str(school['HEX']))
        else:
            r, g, b = 0, 0, 0

        # fbs_schools.add(school['Team'])  # for determining fcs schools
        node = graph.Node(school['Team'], label=school['Team'],
                          red=r / 256, green=r / 256, blue=b / 256, size=5)
        stream.add_node(node)


def scrape_games(week, year=2019, conference='fbs'):
    if not os.path.exists("data/{}/{}week{}.html".format(conference, year, week)):
        return []

    with open("data/{}/{}week{}.html".format(conference, year, week)) as f:
        soup = BeautifulSoup(f, "html.parser")

    games = []
    for game in soup.findAll('div', {'class': 'gamePod gamePod-type-game status-final'}):
        current_game = dict()
        for team in game.find_all('li'):
            team_name = team.contents[5].string
            score = team.contents[7].string

            if team_name in alternate_names.keys():
                team_name = alternate_names[team_name]

            if 'winner' in team['class']:
                current_game['winner'] = (team_name, score)
            else:
                current_game['loser'] = (team_name, score)

        if len(current_game) == 2:
            games.append(current_game)

    return games


def add_fcs_school(stream, name):
    r, g, b = conference_colors['FCS']
    node = graph.Node(name, label=name, red=r / 256, green=r / 256, blue=b / 256, size=5)
    stream.add_node(node)


def add_directed_edge(stream, game, misc_schools=False):
    winner = game['winner'][0]
    loser = game['loser'][0]

    if misc_schools:
        if winner not in fbs_schools:
            add_fcs_school(stream, winner)
        elif loser not in fbs_schools:
            add_fcs_school(stream, loser)

    edge = graph.Edge(winner, loser, directed=True)
    stream.add_edge(edge)


if __name__ == "__main__":
    # collect_data()

    stream = streamer.Streamer(streamer.GephiWS(workspace='workspace1'))
    add_schools(stream)

    for conference in ['fcs']:
        for week in range(1, 20):
            for game in scrape_games(week, 2018, conference):
                add_directed_edge(stream, game, False)
