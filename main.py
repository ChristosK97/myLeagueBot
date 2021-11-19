import requests
import hashlib
import PIL.Image
import io
from discord.ext import commands
import discord
import json
import os
import mysql.connector

status = 'dance dance brimolution'
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Charset": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://developer.riotgames.com"
}
encryptedSummonerId = ''
riotapiKey = str(os.environ.get('apiToken'))

TOKEN = str(os.environ.get('discordToken'))
bot = commands.Bot(command_prefix='~', case_insensitive=True)


egirlChamps = ['350', '16', '37', '147', '267', '25', '99', '117', '43', '40']

champInfo = ''
myarray = []
newString = ''

client = discord.Client()

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(status))




@bot.command(name='go', help='Use command and word/sentence to search in google')
async def search(ctx, *args):

    newString = '+'.join(args)
    googlesearchUrl = "https://www.google.com/search?q=" + newString
    theSecretKey = hashlib.md5(((googlesearchUrl) + "brim").encode('utf-8')).hexdigest()
    params = {'access_key': str(os.environ.get('screenieApi')),
              'url': googlesearchUrl,
              'secret_key': theSecretKey,
              'delay': 1,
              'viewport': '1440x900'}

    response = requests.get("http://api.screenshotlayer.com/api/capture", params=params)
    image_bytes = io.BytesIO(response.content)
    img = PIL.Image.open(image_bytes)
    img = img.save("test.png")
    await ctx.send(file=discord.File('test.png'))

@bot.command(name='egirl', help='use command following league summer name to check for egirl')
async def egirl(ctx, *args):
    counter = 0
    summonerName = ' '.join(args)
    myDict = {}
    summonersTopFive = []
    with open('champion.json', 'r', encoding="utf8") as fp:
        data = json.load(fp)

    for x in data:
        if x == 'data':
            for y in data[x]:
                # print(data[x][y]['key'],data[x][y]['name'] )
                myDict[data[x][y]['key']] = data[x][y]['name']

    summonerLink = 'https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-name/{superSecret}?api_key='.format(
        superSecret=summonerName) + riotapiKey

    response = requests.get(summonerLink, headers=headers)

    if response.status_code == 200:
        jsonLoader = json.loads(response.text)


        encryptedSummonerId = str(jsonLoader['id'])

        masteryLink = 'https://na1.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-summoner/{encryptedSummonerId}?api_key='.format(
            encryptedSummonerId=encryptedSummonerId) + riotapiKey

        r = requests.get(masteryLink, headers=headers)
        jsonLoader = json.loads(r.text)

        for x in jsonLoader[:5]:
            tempArray = []
            tempArray.append(str(x['championId']))
            if str(x['championId']) in myDict:
                tempArray.append(myDict[str(x['championId'])])
            tempArray.append(str(x['championPoints']))
            summonersTopFive.append(tempArray)

        for x in summonersTopFive:
            for egirlchamp in egirlChamps:
                if egirlchamp == x[0]:
                    counter = counter + 1
                else:
                    pass  # here if i want to keep track which champs are a match

        if counter == 5:
            outputMsg = 'E-GIRL DETECTED. LEVELS THRU THA ROOF 5/5'  # create all these messages into a list --- instead of having a loop, just print with index of counter
        elif counter == 4:
            outputMsg = "CAN'T BE A FLUKE. 4/5. KINDA CRAZY"
        elif counter == 3:
            outputMsg = "High chance of E-girl detected. 3/5"
        elif counter == 2:
            outputMsg = "Decent chance of E-girl 2/5"
        elif counter == 1:
            outputMsg = "Very low chance of E-girl. 1/5"
        else:
            outputMsg = "0% chance of E-girl. Chad confirmed. 0/5"

        champInfo = summonersTopFive[0][1] + " " + summonersTopFive[0][2] + '\n' + summonersTopFive[1][1] + " " + \
                    summonersTopFive[1][2] + '\n' + summonersTopFive[2][1] + " " + summonersTopFive[2][2] + '\n' + \
                    summonersTopFive[3][1] + " " + summonersTopFive[3][2] + '\n' + summonersTopFive[4][1] + " " + \
                    summonersTopFive[4][2]
        finalMessage = outputMsg + '\n' + champInfo

        cnx = mysql.connector.connect(
            user=str(os.environ.get('herokuDbUser')),
            password=str(os.environ.get('herokuDbPw')),
            host=str(os.environ.get('herokuDbHost')),
            database=str(os.environ.get('herokuDb'))

        )

        myCursor = cnx.cursor()
        cnx.reconnect(attempts=1, delay=0)
        val = (summonerName,)
        checkIfSummonerExists = ("SELECT * FROM discorddata WHERE summonerId = %s")
        myCursor.execute(checkIfSummonerExists, val)
        myResult = myCursor.fetchone()

        if myResult:
            newOdds = '{}/{}'.format(counter, 5)  # when bot declares the variable, pass it here
            recurrence = myResult[3]
            databaseMessage = summonerName + ' ' + 'is a REPEAT OFFENDER. Count = {}'.format(recurrence)
            sqlQuery = ("UPDATE discorddata SET recurrence = %s, odds = %s WHERE summonerId = %s")
            val = ((recurrence + 1), newOdds, myResult[1],)
            myCursor.execute(sqlQuery, val)
            cnx.commit()
            cnx.close()
            print(myCursor.rowcount, "record(s) affected")
        else:
            newOdds = '{}/{}'.format(counter, 5)
            databaseMessage = summonerName + ' ' + 'Is a first time offender.'
            sqlQuery = "INSERT INTO discorddata (summonerId, odds, recurrence) VALUES (%s, %s, %s)"
            val = (summonerName, newOdds, 1)  # all variables here
            myCursor.execute(sqlQuery, val)
            cnx.commit()
            cnx.close()
            print(myCursor.rowcount, "record(s) affected")

        await ctx.channel.send(databaseMessage)
        await ctx.channel.send(finalMessage)
    else:
        await ctx.channel.send("Invalid summoner name. check yo spelling dawg")


@bot.command(name='rotation', help='Retrieve current free weekly league of legends champs')
async def search(ctx):
    freeChamps = []
    myDict = {}
    with open('champion.json', 'r', encoding="utf8") as fp:
        data = json.load(fp)

    for x in data:
        if x == 'data':
            for y in data[x]:
                # print(data[x][y]['key'],data[x][y]['name'] )
                myDict[data[x][y]['key']] = data[x][y]['name']


    masteryLink = 'https://na1.api.riotgames.com/lol/platform/v3/champion-rotations?api_key=' + riotapiKey
    response = requests.get(masteryLink, headers=headers)
    jsonLoader = json.loads(response.text)

    for item in jsonLoader['freeChampionIds']:
        if str(item) in myDict:
            freeChamps.append(myDict[str(item)])
    formattedFreeChamps = ", ".join(freeChamps)
    await ctx.channel.send("The current free champs are: \n " + formattedFreeChamps)

@bot.command(name='event', help='Responds with the next Ufc event')
async def next_event(ctx):
    currentEvent = ''
    url = 'http://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard'
    r = requests.get(url)
    jsonLoad = json.loads(r.text)
    for event in jsonLoad['events']:
        currentEvent = event['name']
    await ctx.send(currentEvent)

@bot.command(name='card', help='Responds with the main card of the next ufc event')
async def main_card(ctx):
    fightersList = []
    eventLineup = []
    champList = []
    url = 'http://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard'
    champsUrl = 'http://site.api.espn.com/apis/site/v2/sports/mma/ufc/rankings'
    r = requests.get(champsUrl)
    jsonLoad = json.loads(r.text)
    for whatever in jsonLoad['rankings']:
        if 'champion' in whatever['type']:
            champList.append(whatever['ranks'][0]['athlete']['displayName'])

    r = requests.get(url)
    jsonLoad = json.loads(r.text)
    for event in jsonLoad['events']:
        currentEvent = event['name']

    for competitions in jsonLoad['events'][0]['competitions']:
        # print(competitions['competitors'][0]['athlete']['fullName'])
        # print(competitions['competitors'][1]['athlete']['fullName'])
        if competitions['competitors'][0]['athlete']['fullName'] in champList and competitions['competitors'][1]['athlete']['fullName'] in champList:
            fightersList.append("(C) " + competitions['competitors'][0]['athlete']['fullName'] + ' vs ' + "(C) " + competitions['competitors'][1]['athlete']['fullName'])

        elif competitions['competitors'][0]['athlete']['fullName'] in champList:
            fightersList.append("(C) " + competitions['competitors'][0]['athlete']['fullName'] + ' vs ' + competitions['competitors'][1]['athlete']['fullName'])
        elif competitions['competitors'][1]['athlete']['fullName'] in champList:
            fightersList.append(competitions['competitors'][0]['athlete']['fullName'] + ' vs ' + "(C) " + competitions['competitors'][1]['athlete']['fullName'])
        else:
            fightersList.append(competitions['competitors'][0]['athlete']['fullName'] + ' vs ' + competitions['competitors'][1]['athlete']['fullName'])

    for matchups in reversed(fightersList[-5:]):
        eventLineup.append(matchups)

    await ctx.send(currentEvent)
    await ctx.send('\n'.join(eventLineup))

@bot.command(name='stream', help='Returns links to watch sports')
async def stream_link(ctx):
    await ctx.send('https://sportsurge.net/\n http://crackstreams.biz/\n https://www.streameast.live/')

bot.run(TOKEN)
