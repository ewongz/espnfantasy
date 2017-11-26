import pandas as pd
from bs4 import BeautifulSoup
import requests
from flask import *
app = Flask(__name__)

league = ['WONG', 'Firo', 'PHAN', 'JETH', 'DHIN',
          'MONE', 'HDP', 'cc', 'SYED', 'BOBK']


# espn site text for player rankings
top50 = requests.get('http://games.espn.com/fba/playerrater?leagueId=214887&teamId=9')
pages = [top50]
intervals = range(50, 601, 50)
baselink = "http://games.espn.com/fba/playerrater?leagueId=214887&teamId=9&startIndex="

for i in intervals:
    pages.append(requests.get(baselink + str(i)))

ranks = pages
pt = []
for r in ranks:
    pt.append(r.text)


# Clean up the tables
rank_tbls = []
for text in pt:
    bs = BeautifulSoup(text, "lxml")
    table = bs.find(lambda tag: tag.name=='table' and tag.has_key('id') and tag['id']=="playertable_0")
    df = pd.read_html(str(table))
    ranktable = df[0].iloc[1:len(df[0]), [0, 1, 3] + range(6, 14) + [15]]
    colnames = ranktable.iloc[0, 0:(len(ranktable.columns) - 1)]
    ranktable.columns = list(colnames) + ["2018 PlayerRating"]
    rankings = ranktable.iloc[1:len(ranktable), :].set_index("RNK")
    rankings["position"] = rankings["PLAYER, TEAM POS"].apply(lambda p: p[-2:])
    rankings["PLAYER, TEAM POS"] = rankings["PLAYER, TEAM POS"].\
        apply(lambda p: p.split(",")[0])
    rank_tbls.append(rankings)

rankings = pd.concat(rank_tbls)

# Rank table for each owner
team_players = {}
owner_ranks = {}
buckets = []
for owner in league:
    team = rankings.loc[rankings["TYPE"] == owner]
    owner_ranks[owner] = team
    teamtop50 = len(rank_tbls[0].loc[rankings["TYPE"] == owner])
    teamtop100 = len(rank_tbls[1].loc[rankings["TYPE"] == owner]) + teamtop50
    teamtop150 = len(rank_tbls[2].loc[rankings["TYPE"] == owner]) + teamtop100
    teamtop200 = len(rank_tbls[3].loc[rankings["TYPE"] == owner]) + teamtop150
    team["2018 PlayerRating"] = team["2018 PlayerRating"].replace("--", 0)
    team_players[owner] = [sum(team["2018 PlayerRating"]), teamtop50,
                           teamtop100, teamtop150, teamtop200]

statnames = ["TeamRating", "nTop50Players", "nTop100Players",
             "nTop150Players", "nTop200Players"]

teamperformance = pd.DataFrame(pd.Series(team_players))
for n in range(len(statnames)):
    teamperformance[statnames[n]] = teamperformance[0].apply(lambda s: s[n])
standings = teamperformance.iloc[:, 1:len(teamperformance.columns)].\
    sort("TeamRating", ascending=False)


@app.route("/")
def show_tables():
    ranktbl = []
    ownernames = []
    for owner, team in owner_ranks.iteritems():
        ownernames.append(owner)
        ranktbl.append(team.to_html(classes=owner))
    return render_template('view.html',
                           tables=[standings.to_html()] + ranktbl,
                           titles=["na", "Team Rating"] + ownernames)


if __name__ == "__main__":
    app.run()
