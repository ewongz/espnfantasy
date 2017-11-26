from bs4 import BeautifulSoup
import requests
from operator import itemgetter
from flask import Flask, render_template, request, redirect, url_for
from urllib.parse import parse_qs, urlparse


def season_rankings():
    leagueId = request.args.get('leagueId')
    seasonId = request.args.get('seasonId')
    url = 'http://games.espn.com/fba/standings?leagueId={}&seasonId={}'.format(leagueId, seasonId)
    try:
        teams, categories, seasonData = setup(url)
    except:
        return redirect(url_for('index', invalidURL=True))
    season_rankings, season_matchups, season_analysis = computeStats(teams, categories, seasonData)
    return render_template('season_rankings.html', season_rankings=season_rankings, leagueId=leagueId, seasonId=seasonId)


def setup(url):
    source_code = requests.get(url)
    plain_text = source_code.text
    soup = BeautifulSoup(plain_text, 'lxml')
    teams = []
    # Season standings have a different URL than weekly scoreboard
    seasonData = url.startswith('http://games.espn.com/fba/standings')
    # Scrape table depending on whether it's season or weekly data.
    if seasonData:
        seasonStats = soup.find('table', {'id': 'statsTable'})
        categories = [link.string for link in seasonStats.findAll('tr')[2].findAll('a')]
        rows = seasonStats.findAll('tr')[3:]
    else:
        tableSubHead = soup.find_all('tr', class_='tableSubHead')
        tableSubHead = tableSubHead[0]
        listCats = tableSubHead.find_all('th')
        categories = []
        for cat in listCats:
            if 'title' in cat.attrs:
                categories.append(cat.string)
        rows = soup.findAll('tr', {'class': 'linescoreTeamRow'})

    # Creates a 2-D matrix which resembles the Season Stats table.
    for row in range(len(rows)):
        team_row = []
        # Season Data values always have 3 extra columns, weekly data always has 2 extra columns when scraping.
        if seasonData:
            columns = rows[row].findAll('td')[:(3 + len(categories))]
        else:
            columns = rows[row].findAll('td')[:(2 + len(categories))]
        for column in columns:
            team_row.append(column.getText())
        # Add each team to a teams matrix.
        teams.append(team_row)
    return teams, categories, seasonData