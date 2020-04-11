"""
This is a discord bot to handle pounces and bounces in a quiz. A participant is assigned their team as a role (e.g. 'team1', 'team2') 
and has access only to the chat and voice channels of that team. They also have access to the general channels, but switching 
between channels is typically tiresome. This bot tries to make it easier for the participant by giving them no need to move out of 
their team's text chat channel. 

##########################################
Pouncing
##########################################
To pounce, a participant simply types
!p their pounce answer
This message is displayed as a popup to the quizmaster and appears in a separate channel for pounce answers that only the
quizmaster has access to. For example, if a quizzer named harish in team3 wants to submit "mahatma gandhi" as a pounce answer,
he simply types "!p mahatma gandhi" in team3's channel. The quizmaster would see the message "mahatma gandhi pounced by team3's harish".

##########################################
Bounce
##########################################
Similarly, for bounce, a team types in their team's private chat 
!b their bounce answer
The bot sends this message to the private chats of all teams. So, if harish of team 3 were to answer "mahatma gandhi" on bounce,
he would type "!b mahatma gandhi" and all teams would see "Guess on the bounce by team3's harish : mahatma gandhi". This will also appear 
in a separate bounces channel. 

##########################################
Scoring
##########################################
The 'quizmaster' or someone else who is assigned with the role of 'scorer' can simply type "!s 10 t4 t6" to add 10 points to the scores 
of team4 and team6. Likewise, "!s -15 t1 t8" subtracts 15 points from the scores of team1 and team8. All score updates will be visible on 
the dedicated scores channel and a message will be sent to every team that has an update. The score channel will also have the full table 
of points of every team after every update.

Typing !scores at any time from any channel will display all the scores. 

If there are connectivity issues, the bot may reload and the scores may reset to zero. A warning will be displayed and the scores will have 
to be entered again. Pounce/bounce should not be affected.  

##########################################
Cleanup
##########################################
This command deletes all messages in all channels with ids defined below
!clearAllChannels 
This command deletes all messages in the specific channel it is called
!clearThis
Discord has trouble deleting messages older than 14 days. You'd much rather run this command than clone/delete channels and update the 
channel IDs below.

"""

import os

from discord.ext import commands
bot = commands.Bot(command_prefix='!')

### Get bot token and guild ID from env file, make one if it doesn't exist ###

try:
    # if the .env file exists, we can read the bot token and server (guild) id
    # From that itself. Eliminates the need for hardcoding the tokens.
    with open('.env', 'r') as e:
        l = e.readline()
        token = l.split('TOKEN=')[1]
        l = e.readline()
        guildId = l.split('GUILD=')[1]

except FileNotFoundError:
    # otherwise, we take the token and guild ID as inputs, and write to 
    # .env for ease of use next time
    print("Setting up the bot for your server For details, refer to \
            \nhttps://github.com/harishkrishnav/PounceScoreBounceBot\
#running-the-bot-the-first-time")

    token = input("Enter bot developer token: ") 
    # You can find this in https://discordapp.com/developers/applications 
    # and in the Bot menu of the settings

    guildId = input("Enter Guild (Server) ID: ") # You get this by 
    # right-clicking on the server icon if you have enabled developer appearance

    with open('.env', 'w+') as envfile:
        envfile.write('TOKEN='+token+'\n')
        envfile.write('GUILD='+guildId+'\n')
except:
    print("An unknown exception occured. Please contact the developers")
    raise


while True:
    numberOfTeams = int(input("How many teams for the quiz (<= 8)? ")) #teams 
    # with team numbers greater than this are ignored
    if numberOfTeams <= 8:
        break
bounceChannel = 'bounce-guesses'
pounceChannel = 'pounce-guesses'
scoreChannel  = 'scores'
whitelistChannels = ['general','discord-and-bot-help'] #these channels are not
# touched by the bot and hence not cleared during reset
#It is assumed that every team has a name like `teamX-chat`

commonChannels = {}
teamChannels = {}
scores = {}

@bot.command(name="broadcast", help="")
async def broadcastToAllTeams(message):
    for team in teamChannels:
        await teamChannels[team].send(message)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

    guild =  bot.get_guild(int(guildId))
    for channel in guild.text_channels:
        if channel.name.startswith('team') and channel.name.endswith('-chat'): #I don't want to import re
            teamNo = int(''.join(char for char in channel.name if char.isdigit()))
            if teamNo <= numberOfTeams:
                teamChannels[channel.name.replace('-chat','')] = bot.get_channel(channel.id)
        elif channel.name not in whitelistChannels:
            commonChannels[channel.name] = bot.get_channel(channel.id)
    
    for team in teamChannels:
        scores[team] = 0

    await broadcastToAllTeams("Welcome to the quiz! \nCommands: !p to pounce, !b to answer on bounce, !scores to see scores.")
    
    response = "The bot is ready to bring the pounces to you"
    await commonChannels[pounceChannel].send(response)
    
    response = "Guesses on bounce you make by with !b command appear here"
    await commonChannels[bounceChannel].send(response)
    
    response = "The scores have been reset. If this has happened while a quiz was in progress, there was a connection issue."
    await commonChannels[scoreChannel].send(response)


@bot.command(name="p", help="Pounce: type \'!p your guess\' to send \"your guess\" to the quizmaster")
async def pounce(ctx, *args, **kwargs):
    message = ' '.join([word for word in args])
    author = ctx.message.author
    team = str([y.name.lower() for y in author.roles][1:])
    response = '\'{}\' pounced by {}\'s {}'.format(str(message), team, author)
    channel = commonChannels[pounceChannel]
    await channel.send(response)

@bot.command(name="b", help="Bounce: type \'!b your guess\' to send \"your guess\" to the quizmaster and all teams")
async def bounce(ctx, *args, **kwargs):
    message = ' '.join([word for word in args])
    author = ctx.message.author
    team = str([y.name.lower() for y in author.roles][1:])
    response = '{}\'s {}: {}'.format(team, author, str(message))
    channel = commonChannels[bounceChannel]
    await channel.send(response)
    response = 'Guess on the bounce by {}\'s {}: {}'.format(team, author, str(message))
    await broadcastToAllTeams(response)

@bot.command(name="scores", help="Displays the scores")
async def displayScores(ctx, *args, **kwargs):
    response = '\n'.join(str(team)+" : "+str(scores[team]) for team in scores)
    await ctx.message.channel.send(response)

@bot.command(name="s", help="scorer or quizmaster updates scores")
async def updateScores(ctx, *args, **kwargs):
    if len(args)<2:
        await ctx.send("example:   !s -5 t2 t8   to deduct 5 points from team2 and team8")
        return

    author = ctx.message.author
    authorRoles = [str(role).lower() for role in author.roles[1:]]
    if 'quizmaster' not in authorRoles and 'scorer' not in authorRoles:
        await ctx.send("Only a scorer or quizmaster can update scores.")
        return

    points = int(args[0])
    teams = [team.replace('t','team') for team in args[1:]]
    for team in teams:
        scores[team]+=points
    sign = lambda x: ('+', '')[x<0]
    response = '{}{} to {}. Points table now: \n'.format(sign(points),str(points), ' '.join(team for team in teams)) 
    response += '\n'.join(str(team)+" : "+str(scores[team]) for team in scores)
    channel = commonChannels[scoreChannel]
    await channel.send(response)

    for team in teams:
        channel=teamChannels[team]
        response = '{}{} to your team. Your score is now {}'.format(sign(points),str(points), scores[team])
        await channel.send(response)

@bot.command(name="clearAll", help="delete all messages in all important channel and resets score to 0")
async def clearAll(ctx, *args, **kwargs):
    author = ctx.message.author
    authorRoles = [str(role).lower() for role in author.roles[1:]]
    if 'quizmaster' not in authorRoles and 'scorer' not in authorRoles and 'admin' not in authorRoles:
        await ctx.send("Only a quizmaster or admin or scorer can purge all channels.")
        return

    for channel in list(commonChannels.values())+list(teamChannels.values()):
        while(True):
            deleted = await channel.purge(limit=1000)
            if not len(deleted):
                break

    for team in teamChannels:
        scores[team]=0

    return 

@bot.command(name="clearThis", help="delete all messages in a channel")
async def clearThis(ctx, *args, **kwargs):
    channel = ctx.message.channel
    offlimitChannels = [commonChannels[pounceChannel], commonChannels[bounceChannel], commonChannels[scoreChannel]]
    author = ctx.message.author
    authorRoles = [str(role).lower() for role in author.roles[1:]]
    if channel in offlimitChannels and ('quizmaster' not in authorRoles and 'scorer' not in authorRoles and 'admin' not in authorRoles):
        await ctx.send("Only a quizmaster or admin or scorer can clear this channel.")
        return

    while(True):
        deleted = await channel.purge(limit=1000)
        if not len(deleted):
            break
    return 


@bot.event
async def on_command_error(ctx, error):
    with open('err.log', 'a') as f:
        f.write(f'Unhandled message: {error}\n')
        await ctx.send("The command could not be run. Please type `!help` for the list of available commands")

bot.run(token)
