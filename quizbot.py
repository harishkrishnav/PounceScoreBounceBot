"""
For more information, please see the repo README https://github.com/harishkrishnav/PounceScoreBounceBot/blob/master/README.md 
The guild must have the following with appropriate permissions
- roles: quizmaster, scorer, team1, team2, ...
- text channels: bounce-guesses, pounce-guesses, scores
- text channels: team1, team2, ...

Summary of commands

- !newQuiz or !startQuiz or !setNumTeams
example: !newQuiz 7
sets number of teams, clears channels, creates new scores.txt file, sends welcome messages

- !endQuiz or !stopQuiz
example: !stopQuiz
clears channels, creates new finalscores.txt file, deletes scores.txt, displays final scores and team composition

- !p or !pounce 
example: !pounce mahatma gandhi
pounces-guesses channel sees "mahatma gandhi pounced by <teams>'s <sender's name>"
sender's channel gets the message "Pounce submitted"

- !b or !bounce
example: !b mahatma gandhi
bounces-guesses channel sees "<team>'s <sender's name> : mahatma gandhi"
every team channel sees "Guess on the bounce by <team>'s <sender's name> : mahatma gandhi"

- !scores or !pointstable
example: !scores
sender's channel sees "<team> <score> <all members with the role as the team>" one team per line

- !s or !plus
example: !s -5 t2 t4 t6
-5 added to score of team2, team4, team6
scores-channel sees "<points> to <list of teams>. Points table now: <pointstable>"
channels of teams with update see "<points> to your team. Your score is now <total points>"
action only when sender has role quizmaster, scorer

- !minus or !deduct
example: !minus 5 t2 t4 t6
5 subtracted from score of team2, team4, team6
scores-channel sees "<points> to <list of teams>. Points table now: <pointstable>"
channels of teams with update see "<points> off your team score. Your score is now <total points>"
action only when sender has role quizmaster, scorer

- !clearAllChannels
example: !clearAllChannels
all messages from all non-whitelisted channels deleted
all scores reset to 0
action only when sender has role quizmaster, scorer

- !clearThis
example !clearThis 
all messages in that caller's channel are deleted
action on channels bounce-guesses, pounce-guesses, scores  when sender has role quizmaster, scorer

- !resetRoles
example !resetRoles
all members of the guild with a role beginning with team are removed from the role
action when sender has role quizmaster, scorer, admin

- !join or !assignMe
example !join
if member does not have a role beginning with "team", assigned a random team from teams that have least members
"""

import random
import os
import json

from discord.ext import commands
bot = commands.Bot(command_prefix='!')

### Get bot token and guild ID from env file, make one if it doesn't exist ###

try:
    # if the .env file exists, we can read the bot token and server (guild) id
    # From that itself. Eliminates the need for hardcoding the tokens.
    with open('.env', 'r') as e:
        l = e.readline()
        token = l.split('TOKEN=')[1]
        assert len(token)>50
        l = e.readline()
        guildId = l.split('GUILD=')[1]
        assert len(guildId)>16

except FileNotFoundError:
    # otherwise, we take the token and guild ID as inputs, and write to 
    # .env for ease of use next time
    print("Setting up the bot for your server For details, refer to \nhttps://github.com/harishkrishnav/PounceScoreBounceBot/\#running-the-bot-the-first-time")
    print("You will need to enter these credentials only the first time you run on a guild")
    token = input("Enter bot developer token: ") 
    # You can find this in https://discordapp.com/developers/applications 
    # and in the Bot menu of the settings

    guildId = input("Enter Guild (Server) ID: ") # You get this by 
    # right-clicking on the server icon if you have enabled developer appearance

    with open('.env', 'w+') as envfile:
        envfile.write('TOKEN='+token+'\n')
        envfile.write('GUILD='+guildId+'\n')
except:
    print("An unknown exception occured. There might be a problem with the .env file or its contents. Try deleting the file and running this script again")
    raise


numberOfTeams = 8
bounceChannel = 'bounce-guesses'
pounceChannel = 'pounce-guesses'
scoreChannel  = 'scores'
whitelistChannels = ['general','discord-and-bot-help'] #these channels are not cleared during reset
#It is assumed that every team has a name like `teamX-chat`

commonChannels = {}
teamChannels = {}
scores = {}
quizOn = False

@bot.command(name="broadcast", help="")
async def broadcastToAllTeams(message):
    for team in teamChannels:
        await teamChannels[team].send(message)

@bot.command(name="stopQuiz", aliases = ["stopquiz", "endQuiz", "endquiz"], help="Stop the quiz and clear channels")
async def endQuiz(ctx, *args, **kwargs):
    author = ctx.message.author
    authorRoles = [str(role).lower() for role in author.roles[1:]]
    if 'quizmaster' not in authorRoles and 'admin' not in authorRoles:
        await ctx.send("Only an admin or quizmaster can end this quiz.")
        return

    response = "Warning! This will clear all channels and end the quiz."
    await ctx.send(response)
    global quizOn
    quizOn=False
    #clear everything
    guild =  bot.get_guild(int(guildId))
    for channel in guild.text_channels:
        if channel.name not in whitelistChannels:
            while(True):
                deleted = await channel.purge(limit=1000)
                if not len(deleted):
                    break
    
    response = "The final scores are below (they're also saved in finalscores.txt)\n"
    response += '\n'.join(str(team)+" : "+str(scores[team]) for team in scores)
    await ctx.send(response)
    
    teamDistribution = {}
    for team in teamChannels:
        teamDistribution[team] = []
    for member in guild.members:
        for role in member.roles:
            if role.name.startswith("team") and role.name in teamDistribution:
                teamDistribution[role.name].append(member.display_name)
    response = "The participants were\n"
    response += '\n'.join(str(team)+" : "+str(teamDistribution[team]) for team in teamDistribution)
    await ctx.send(response)

    with open("finalscores.txt","w") as scoresFileObject:
        json.dump([scores, teamDistribution], scoresFileObject)
    if os.path.exists("scores.txt"):
        os.remove("scores.txt")


@bot.command(name="setNumTeams", aliases = ["startQuiz", "newquiz", "newQuiz", "startquiz"], help="Reset everything and start a new quiz with an input number of teams")
async def newQuiz(ctx, *args, **kwargs):
    author = ctx.message.author
    authorRoles = [str(role).lower() for role in author.roles[1:]]
    if 'quizmaster' not in authorRoles and 'admin' not in authorRoles:
        await ctx.send("Only an admin or quizmaster can reset everything and start a quiz.")
        return

    response = "Warning! This will clear all channels and reset all scores."
    await ctx.send(response)

    if not len(args):
        await ctx.send("This command must be issued along with the number of participating teams (example: `!newQuiz 7` for starting a quiz with 7 teams). Existing member roles will not be affected.")
        return
    
    numberOfTeams = int(args[-1])
    response = "Creating a quiz with {} teams. \nClearing all channels. This message and everything above might soon disappear.".format(str(numberOfTeams))
    await ctx.send(response)
    global quizOn
    quizOn = True
    print("Quiz started!")

    # make dicts of all team and common channels
    guild =  bot.get_guild(int(guildId))
    commonChannels.clear()
    teamChannels.clear()
    for channel in guild.text_channels:
        if channel.name.startswith('team') and channel.name.endswith('-chat'): #I don't want to import re
            teamNo = int(''.join(char for char in channel.name if char.isdigit()))
            if teamNo <= numberOfTeams:
                teamChannels[channel.name.replace('-chat','')] = bot.get_channel(channel.id)
        elif channel.name not in whitelistChannels:
            commonChannels[channel.name] = bot.get_channel(channel.id)

    #clear everything
    for channel in list(commonChannels.values())+list(teamChannels.values()):
        while(True):
            deleted = await channel.purge(limit=1000)
            if not len(deleted):
                break
    
    #reset scores
    scores.clear()
    for team in teamChannels:
        scores[team] = 0

    #create score file
    #json.dump(scores, open("scores.txt",'w'))
    with open("scores.txt","w") as scoresFileObject:
        json.dump(scores, scoresFileObject)

    #Welcome texts
    response = "The bot is ready to bring the pounces to you"
    await commonChannels[pounceChannel].send(response)    
    response = "Guesses on bounce you make by with `!bounce` or `!b` command appear here"
    await commonChannels[bounceChannel].send(response)
    response = "Welcome! Below are the commands you can use to set scores. Teams are always abbreviated as t1 t2 etc.\n`!s -10 t3 t4 t8` to add -10 points to teams3,4,5;\n`!s 5 t2` to add 5 points to team2\n`!plus 10 t3 t4 t8` to give 10 points to teams 3,4,8 ;\n`!minus 5 t1 t2` to deduct 5 points from team1 and team2"
    await commonChannels[scoreChannel].send(response)

    await broadcastToAllTeams("Welcome to the quiz! This is your team's private text channel.\nCommands for the bot:\n`!p your guess here` or `!pounce your guess here` to pounce,\n`!b your guess here` or `!bounce your guess here` to answer on bounce,\n`!scores` to see the scores.")
    await broadcastToAllTeams("If you are seeing this message in the middle of a quiz, alert the quizmaster. The scores might need to be checked.")
    await broadcastToAllTeams("\n1)Please have an identifiable nickname by right-clicking on your name on the right column and changing nickname (it won't affect your name in other discord guilds)\n2)Please mute your microphone\n3)Go to user settings -> notifications and turn off notifications for User Joined, User Leave, User Moved, Viewer Join, Viewer Leave")
    
    await ctx.send("All team channels have been cleared, and all scores have been set to 0. You can begin the quiz. \nIf you want to unassign all team roles, make the bot an admin and issue the command `!resetTeams`. Those who wish to participate have to type `!join` to be automatically assigned a ream.")

    return


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')

    if os.path.exists('scores.txt'):
        with open("scores.txt") as scoresFileObject:
            scoresInFile = json.load(scoresFileObject)
        print("The bot has reset and scores are being read from file")
        numberOfTeams = len(scoresInFile)
        guild =  bot.get_guild(int(guildId))
        commonChannels.clear()
        teamChannels.clear()
        for channel in guild.text_channels:
            if channel.name.startswith('team') and channel.name.endswith('-chat'): #I don't want to import re
                teamNo = int(''.join(char for char in channel.name if char.isdigit()))
                if teamNo <= numberOfTeams:
                    teamChannels[channel.name.replace('-chat','')] = bot.get_channel(channel.id)
            elif channel.name not in whitelistChannels:
                commonChannels[channel.name] = bot.get_channel(channel.id)
        scores.clear()
        for team in teamChannels:
            scores[team] = scoresInFile[team]
        global quizOn
        quizOn=True
        await broadcastToAllTeams("The bot had to reset for reasons unknown but the scores must have been retained. Below are the scores after the last update. Please alert the quizmaster if there's a discrepancy.")
        response = '\n'.join(str(team)+" : "+str(scores[team]) for team in scoresInFile)
        await broadcastToAllTeams(response)
        response = "Here are the scores after reset\n"
        response += '\n'.join(str(team)+" : "+str(scores[team]) for team in scoresInFile)
        await commonChannels[scoreChannel].send(response)
    else:
        print("Please !startQuiz")
    

@bot.command(name="p", aliases = ["pounce", "P", "punce", "ponce", "puonce"], 
             help="Pounce: type `!p your guess` or `!pounce your guess` to send \"your guess\" to the quizmaster")
async def pounce(ctx, *args, **kwargs):
    if not quizOn:
        response = "This is the right command to send a pounce. However, the quiz hasn't begun yet. If you are the quizmaster, you must run the `!startQuiz` command."
        await ctx.message.channel.send(response)
        return

    guess = ' '.join([word for word in args])
    author = ctx.message.author
    authorName = str(author.display_name).split("#")[0]
    team = ', '.join([str(role.name.lower()) for role in author.roles[1:] if role.name.startswith('team')])
    response = '\'{}\' pounced by {}\'s {}'.format(guess, team, authorName)
    channel = commonChannels[pounceChannel]
    await channel.send(response)
    response = "Pounce submitted"
    await ctx.message.channel.send(response)


@bot.command(name="b", aliases = ["bounce", "B", "bunce", "bonce", "buonce"], 
             help="Bounce: type `!b your guess` or `!bounce your guess` to send \"your guess\" to the quizmaster and all teams")
async def bounce(ctx, *args, **kwargs):
    if not quizOn:
        response = "This is the right command to send a guess on bounce. However, the quiz hasn't begun yet. If you are the quizmaster, you must run the `!startQuiz` command."
        await ctx.message.channel.send(response)
        return

    guess = ' '.join([word for word in args])
    author = ctx.message.author
    authorName = str(author.display_name).split("#")[0]
    team = ', '.join([str(role.name.lower()) for role in author.roles[1:] if role.name.startswith('team')])
    response = '{}\'s {}: {}'.format(team, authorName, guess)
    channel = commonChannels[bounceChannel]
    await channel.send(response)
    response = 'Guess on the bounce by {}\'s {}: {}'.format(team, authorName, str(guess))
    await broadcastToAllTeams(response)

@bot.command(name="scores", aliases = ["pointstable"], help="Displays the scores")
async def displayScores(ctx, *args, **kwargs):
    if not quizOn:
        response = "This is the right command to see the scores. However, the quiz hasn't begun yet. If you are the quizmaster, you must run the `!startQuiz` command."
        await ctx.message.channel.send(response)
        return

    guild =  bot.get_guild(int(guildId))
    teamDistribution = {}
    for team in scores:
        teamDistribution[team] = []
    for member in guild.members:
        for role in member.roles:
            if role.name.startswith("team"):
                try:
                    assert role.name in teamDistribution
                    teamDistribution[role.name].append(member)
                except:
                    print("Please check that teamnames match roles (no spaces). Someone might have a role of a team that isn't in this quiz.")
    response = '\n\n'.join('{}\t{}\t{}'.format(str(team),str(scores[team]).center(8),(', '.join(member.display_name.split("#")[0] for member in teamDistribution[team]).center(60))) for team in scores)
    await ctx.message.channel.send(response)

@bot.command(name="s", aliases = ["plus"], help="for scorers and quizmasters to update scores")
async def updateScores(ctx, *args, **kwargs):
    if not quizOn:
        response = "This is the right command to update scores. However, the quiz hasn't begun yet. If you are the quizmaster, you must run the `!startQuiz` command."
        await ctx.message.channel.send(response)
        return

    if len(args)<2:
        await ctx.send("example: `!s -5 t2 t8`  to deduct 5 points from team2 and team8")
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
    response = '{}{} to {}. Points table now: \n'.format(sign(points),str(points), ', '.join(team for team in teams)) 
    response += '\n'.join(str(team)+" : "+str(scores[team]) for team in scores)
    channel = commonChannels[scoreChannel]
    await channel.send(response)
    with open("scores.txt","w") as scoresFileObject:
        json.dump(scores, scoresFileObject)

    for team in teams:
        channel=teamChannels[team]
        response = '{}{} to your team. Your score is now {}'.format(sign(points),str(points), scores[team])
        await channel.send(response)

#TODO handle !minus better
@bot.command(name="minus", aliases = ["deduct"], help="for scorers and quizmasters to update scores")
async def minus(ctx, *args, **kwargs):
    if not quizOn:
        response = "This is the right command to update scores. However, the quiz hasn't begun yet. If you are the quizmaster, you must run the `!startQuiz` command."
        await ctx.message.channel.send(response)
        return

    if len(args)<2:
        await ctx.send("example: `!minus 5 t2 t8`  to deduct 5 points from team2 and team8")
        return

    author = ctx.message.author
    authorRoles = [str(role).lower() for role in author.roles[1:]]
    if 'quizmaster' not in authorRoles and 'scorer' not in authorRoles:
        await ctx.send("Only a scorer or quizmaster can update scores.")
        return

    points = int(args[0])
    teams = [team.replace('t','team') for team in args[1:]]
    for team in teams:
        scores[team]-=points
    sign = lambda x: ('+', '')[-x<0]
    response = '{}{} off {}. Points table now: \n'.format(sign(points),str(points), ' '.join(team for team in teams)) 
    response += '\n'.join(str(team)+" : "+str(scores[team]) for team in scores)
    channel = commonChannels[scoreChannel]
    await channel.send(response)
    with open("scores.txt","w") as scoresFileObject:
        json.dump(scores, scoresFileObject)

    for team in teams:
        channel=teamChannels[team]
        response = '{}{} points off your team score. Your score is now {}'.format(sign(points),str(points), scores[team])
        await channel.send(response)

@bot.command(name="clearAllChannels", help="delete all messages in all important channel and resets score to 0")
async def clearAll(ctx, *args, **kwargs):
    author = ctx.message.author
    authorRoles = [str(role).lower() for role in author.roles[1:]]
    if 'quizmaster' not in authorRoles and 'scorer' not in authorRoles and 'admin' not in authorRoles:
        await ctx.send("Only a quizmaster or admin or scorer can purge all channels and reset scores to 0.")
        return

    guild =  bot.get_guild(int(guildId))
    for channel in guild.text_channels:
        if channel.name not in whitelistChannels:
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

@bot.command(name="resetRoles", aliases = ["unassignAll", "resetTeams"], help="remove all team roles")
async def resetRoles(ctx, *args, **kwargs):
    author = ctx.message.author
    authorRoles = [str(role).lower() for role in author.roles[1:]]
    if 'quizmaster' not in authorRoles and 'scorer' not in authorRoles and 'admin' not in authorRoles:
        await ctx.send("Only a quizmaster or admin or scorer can assign or unassign teams.")
        return
    
    guild =  bot.get_guild(int(guildId))
    for member in guild.members:
        for role in member.roles:
            if role.name.startswith("team"):
                try:
                    await member.remove_roles(role)
                    response = 'Removing {} from {}.'.format(str(member.display_name),str(role.name))
                    await ctx.send(str(response))
                except:
                    print("Did not remove",member,"from",role,"because of permissions. Make the bot an admin and run this again.")
    await ctx.send("Removed all team roles. The quizmaster can either manually assign roles or ask participants to `!join` once `!startQuiz` is run")
    return 

@bot.command(name="assignMe", aliases = ["join", "joinTeam"], help="join a team")
async def assignRoles(ctx, *args, **kwargs):
    if not quizOn:
        response = "This is the right command to join a team. However, the number of teams hasn't been set yet. Ask the quizmaster to run the `!startQuiz` command"
        await ctx.message.channel.send(response)
        return

    author = ctx.message.author
    authorRoles = [str(role).lower() for role in author.roles[1:]]
    for role in authorRoles:
        if role.startswith("team"):
            await ctx.send('You are already in {}. Please contact the quizmaster if you need help.'.format(role))
            return
    
    guild =  bot.get_guild(int(guildId))
    teamSizeCount = {}
    for role in guild.roles:
        if role.name in scores:
            teamSizeCount[role] = 0

    for member in guild.members:
        for role in member.roles:
            if role.name.startswith("team") and role in teamSizeCount:
                teamSizeCount[role] += 1

    smallestTeamSize = min(teamSizeCount.values())
    smallestTeams = [role for role, size in teamSizeCount.items() if size==smallestTeamSize]
    roleToAssign = random.choice(smallestTeams)
    print(author.display_name, "assigned to", roleToAssign)

    await author.add_roles(roleToAssign)
    authorName = str(author.display_name).split("#")[0]
    response = 'Assigning {} to {}.'.format(authorName,str(roleToAssign)) 
    await ctx.send(str(response))
    return 


@bot.event
async def on_command_error(ctx, error):
    with open('err.log', 'a') as f:
        f.write(f'Unhandled message: {error}\n')
        await ctx.send("The command could not be run. Please type `!help` for the list of available commands")

bot.run(token)
