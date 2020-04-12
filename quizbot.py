"""
For more information, please see the repo README https://github.com/harishkrishnav/PounceScoreBounceBot/blob/master/README.md 
The guild must have the following with appropriate permissions
- roles: quizmaster, scorer, team1, team2, ...
- text channels: bounce-guesses, pounce-guesses, scores
- text channels: team1, team2, ...

Summary of commands

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
sender's channel sees "<team>:<score>" one team per line

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

"""

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
    print("Setting up the bot for your server For details, refer to \
            \nhttps://github.com/harishkrishnav/PounceScoreBounceBot\#running-the-bot-the-first-time")

    token = input("Enter bot developer token: ") 
    # You can find this in https://discordapp.com/developers/applications 
    # and in the Bot menu of the settings

    guildId = input("Enter Guild (Server) ID: ") # You get this by 
    # right-clicking on the server icon if you have enabled developer appearance

    with open('.env', 'w+') as envfile:
        envfile.write('TOKEN='+token+'\n')
        envfile.write('GUILD='+guildId+'\n')
except:
    print("An unknown exception occured. There might be a problem with the .env file or its contents. Try deleting it and running this script again")
    raise

numberOfTeams = 8
bounceChannel = 'bounce-guesses'
pounceChannel = 'pounce-guesses'
scoreChannel  = 'scores'
whitelistChannels = ['general','discord-and-bot-help'] #these channels are not touched by the bot and hence not cleared during reset
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

    await broadcastToAllTeams("Welcome to the quiz! Commands: \n`!p your guess here` or `!pounce your guess here` to pounce,\n\
        `!b your guess here` or `!bounce your guess here` to answer on bounce, `!scores` to see the scoretable.")
    
    response = "The bot is ready to bring the pounces to you"
    await commonChannels[pounceChannel].send(response)
    
    response = "Guesses on bounce you make by with `!bounce` or `!b` command \
appear here"
    await commonChannels[bounceChannel].send(response)
    
    response = "The scores have been reset. If this has happened while a quiz was in progress, there was a connection issue."
    await commonChannels[scoreChannel].send(response)


@bot.command(name="p", aliases = ["pounce", "P", "punce", "ponce", "puonce"], 
             help="Pounce: type `!p your guess` or `!pounce your guess` to send \"your guess\" to the quizmaster")
async def pounce(ctx, *args, **kwargs):
    guess = ' '.join([word for word in args])
    author = ctx.message.author
    authorName = author.split("#")[0]
    team = ', '.join([str(role.name.lower()) for role in author.roles[1:] if role.name.startswith('team')])
    response = '\'{}\' pounced by {}\'s {}'.format(guess, team, authorName)
    channel = commonChannels[pounceChannel]
    await channel.send(response)
    response = "Pounce submitted"
    await ctx.message.channel.send(response)


@bot.command(name="b", aliases = ["bounce", "B", "bunce", "bonce", "buonce"], 
             help="Bounce: type `!b your guess` or `!bounce your guess` to send \"your guess\" to the quizmaster and all teams")
async def bounce(ctx, *args, **kwargs):
    guess = ' '.join([word for word in args])
    author = ctx.message.author
    authorName = author.split("#")[0]
    team = str([role.name.lower() for role in author.roles[1:] if role.name.startswith('team')])
    response = '{}\'s {}: {}'.format(team, authorName, guess)
    channel = commonChannels[bounceChannel]
    await channel.send(response)
    response = 'Guess on the bounce by {}\'s {}: {}'.format(team, authorName, str(guess))
    await broadcastToAllTeams(response)

@bot.command(name="scores", aliases = ["pointstable"], help="Displays the scores")
async def displayScores(ctx, *args, **kwargs):
    response = '\n'.join(str(team)+" : "+str(scores[team]) for team in scores)
    await ctx.message.channel.send(response)

@bot.command(name="s", aliases = ["plus"], help="for scorers and quizmasters to update scores")
async def updateScores(ctx, *args, **kwargs):
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
    response = '{}{} to {}. Points table now: \n'.format(sign(points),str(points), ' '.join(team for team in teams)) 
    response += '\n'.join(str(team)+" : "+str(scores[team]) for team in scores)
    channel = commonChannels[scoreChannel]
    await channel.send(response)

    for team in teams:
        channel=teamChannels[team]
        response = '{}{} to your team. Your score is now {}'.format(sign(points),str(points), scores[team])
        await channel.send(response)

#TODO handle !minus better
@bot.command(name="minus", aliases = ["deduct"], help="for scorers and quizmasters to update scores")
async def minus(ctx, *args, **kwargs):
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

    for team in teams:
        channel=teamChannels[team]
        response = '{}{} points off your team score. Your score is now {}'.format(sign(points),str(points), scores[team])
        await channel.send(response)

@bot.command(name="clearAllChannels", help="delete all messages in all important channel and resets score to 0")
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
