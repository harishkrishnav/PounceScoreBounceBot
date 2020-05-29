"""
For more information, please see the repo README 
https://github.com/harishkrishnav/PounceScoreBounceBot/blob/master/README.md 

The guild must have the following with appropriate permissions
- roles: quizmaster, scorer, team1, team2, ...
- text channels: quiz-questions, qm-panel, scores
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
qm-panel channel sees "Guess on pounce by <teams>'s <sender's name>: mahatma gandhi"
sender's channel gets the message "Pounce submitted"

- !b or !bounce
example: !b mahatma gandhi
qm-panel channel sees "<team>'s <sender's name> : mahatma gandhi"
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

- !resetScores
example: !resetscores
all scores set to 0 and file updated
channel sender sees "scores reset" 

- !minus or !deduct
example: !minus 5 t2 t4 t6
5 subtracted from score of team2, team4, team6
scores-channel sees "<points> to <list of teams>. Points table now: <pointstable>"
channels of teams with update see "<points> off your team score. Your score is now <total points>"
action only when sender has role quizmaster, scorer

- !loadfile
example: !loadfile
File loaded from channel file-upload into the quiz. !n and !prev can now be used.

- !n or !next
example: !n
slideNumber updated and state of slide saved to file
channels of teams, qm-panel, quiz-questions, and scores get a copy of the next image in the slideshow
calling channel gets a confirmation message at the end

- !prev
example: !prev
slideNumber updated and state of slide saved to file
channels of teams, qm-panel, quiz-questions, and scores get a copy of the previous image in the slideshow
calling channel gets a confirmation message at the end

- !clearAllChannels
example: !clearAllChannels
all messages from all non-whitelisted channels deleted
all scores reset to 0
action only when sender has role quizmaster, scorer

- !clearThis
example !clearThis 
all messages in that caller's channel are deleted
action on channels quiz-questions, qm-panel, scores  when sender has role quizmaster, scorer

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
import asyncio

from botutils import (getTeam, getAuthorAndName, getTeamDistribution, 
        getTeamMembers, getAuthorized, deleteAllMessages, getCommonChannels,
        getTeamChannels, unassignTeams, deleteFiles, convertToImages,
        updateSlides, saveSlideState, recoverSlideState, getAuthorizedServer, getAuthorizedUser)

from discord.ext import commands
import discord

#################################
# Bot initialisation for server #
#################################

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
    print("Setting up the bot for your server. For details, refer to \
\nhttps://github.com/harishkrishnav/PounceScoreBounceBot/\#running-the-bot-the-first-time")
    print("You will need to enter these credentials only the first time you \
run on a guild")
    token = input("Enter bot developer token from the bot menu in\
https://discordapp.com/developers/applications : ") 
    guildId = input("Enter Guild (Server) ID (right click on the server\
icon if you have enabled developer appearance): ") 
    with open('.env', 'w+') as envfile:
        envfile.write('TOKEN='+token+'\n')
        envfile.write('GUILD='+guildId+'\n')
except:
    print("An unknown exception occured. There might be a problem with the \
.env file or its contents. Try deleting the file and running \
this script again")
    raise

#################################################################
# Variable setup; global variables that keep track of channels, #
# teams, scores, slides, and the like. Some error messages too. #
#################################################################

### Setting up variables to be used for running a Quiz ###
numberOfTeams = 8
questionChannel = 'slides-and-media'
qmChannel = 'qm-control-panel'
scoreChannel  = 'scores'
fileChannel = 'file-upload'
#whitelistChannels = ['general','discord-and-bot-help'] 
whitelistChannels = [
        'general',                                                              
        'bot-help',                                                 
        'test-channel',                                                         
        ] #these channels are not cleared during reset, do not include slides-and-media here
# whitelistChannels are not cleared during reset
# It is assumed that every team has a name like `teamX-chat`

commonChannels = {}
teamChannels = {}
scores = {}
quizOn = False

sco_command_messages = []

presentationDirPath = os.path.join(os.curdir,'slide_images')
presentationFileName = ''
presentationLoaded = False
slideNumber = 0
slides = []

### Prewriting some common error messages ###
messageQuizNotOn = "This is the right command. However, \
the quiz hasn't begun yet. If you are the quizmaster, you must run \
the `!startQuiz` command."

############################################################################
# Participant commands. Joining, pouncing, bouncing, clear channel, scores #
############################################################################

@bot.command(
    name="assignMe",
    aliases = ["join", "joinTeam"],
    help="join a team"
    )
async def assignRoles(ctx, *args, **kwargs):
    # Authorisation
    if not getAuthorizedServer(bot, guildId, ctx):
        return 
    if not quizOn:
        response = messageQuizNotOn
        await ctx.message.channel.send(response)
        return
    auth, response = getAuthorized(
            ctx,
            'You are already in ',
            '. Please contact the quizmaster if you need help',
            *[team for team in teamChannels])
    if auth:
        await ctx.send(response)
        return
    
    # Initialising team sizes to 0 and counting them
    guild =  bot.get_guild(int(guildId))
    teamSizeCount = {}
    for role in guild.roles:
        if role.name in scores:
            teamSizeCount[role] = 0

    for member in guild.members:
        for role in member.roles:
            if role.name.startswith("team") and role in teamSizeCount:
                teamSizeCount[role] += 1

    author = ctx.message.author

    # Picking a random team from the smallest ones to assign author to
    smallestTeamSize = min(teamSizeCount.values())
    smallestTeams = [role for role, size in teamSizeCount.items() if size==smallestTeamSize]
    roleToAssign = random.choice(smallestTeams)
    print(author.display_name, "assigned to", roleToAssign)

    # Assign the author to selected team
    await author.add_roles(roleToAssign)
    authorName = str(author.display_name).split("#")[0]
    response = 'Assigning {} to {}.'.format(authorName,str(roleToAssign)) 
    await ctx.send(str(response))
    return 


@bot.command(
    name="b",
    aliases = ["bounce", "B", "bunce", "bonce", "buonce"], 
    help="Bounce: type `!b your guess` or `!bounce your guess` to \
send \"your guess\" to the quizmaster and all teams"
    )
async def bounce(ctx, *args, **kwargs):
    # Authorisation
    if not getAuthorizedServer(bot, guildId, ctx):
        return 
    if not quizOn:
        response = messageQuizNotOn
        await ctx.message.channel.send(response)
        return
    # Read the guess and send to all channels
    guess = ' '.join([word for word in args])
    author, authorName = getAuthorAndName(ctx)
    team = getTeam(author)
    response = 'ON BOUNCE {}\'s {}: {}'.format(team, authorName, guess)
    channel = commonChannels[qmChannel]
    await channel.send(response)
    response = 'Guess on the bounce by {}\'s {}: {}'.format(team, authorName, str(guess))
    await broadcastToAllTeams(response)



@bot.command(name="clearThis", help="delete all messages in a channel")
async def clearThis(ctx, *args, **kwargs):
    # Authorisation
    if not getAuthorizedServer(bot, guildId, ctx):
        return 
    channel = ctx.message.channel
    offlimitChannels = [
            commonChannels[qmChannel],
            commonChannels[questionChannel],
            commonChannels[scoreChannel]
            ]
    auth, response = getAuthorized(
            ctx,
            "Only ", 
            " can clear this channel",
            'quizmaster', 'scorer', 'admin'
            )
    if channel in offlimitChannels and not auth:
        await ctx.send(response)
        return
    # Clear messages. TODO port over to botutils.py, in a more general function
    # than deleteAllMessages(bot, guild, whitelistChannels)
    while(True):
        deleted = await channel.purge(limit=1000)
        if not len(deleted):
            break
    return 



@bot.command(
    name="scores",
    aliases = ["pointstable"],
    help="Displays the scores"
    )
async def displayScores(ctx, *args, **kwargs):
    # Authorisation
    if not getAuthorizedServer(bot, guildId, ctx):
        return 
    if not quizOn:
        response = messageQuizNotOn
        await ctx.message.channel.send(response)
        return
    # Get team members, scores, generate a response and send
    teamDistribution = getTeamDistribution(bot, guildId, scores)
    response = '\n\n'.join('{}\t{}\t{}'.format(
        str(team),
        str(scores[team]).center(8),
        ', '.join(getTeamMembers(teamDistribution, team)).center(60)) for team in scores
        )
    await ctx.message.channel.send(response)



@bot.command(
    name="p",
    aliases = ["pounce", "P", "punce", "ponce", "puonce"],
    help="Pounce: type `!p your guess` or `!pounce your guess` to send \
\"your guess\" to the quizmaster"
    )
async def pounce(ctx, *args, **kwargs):
    # Authorisation
    if not getAuthorizedServer(bot, guildId, ctx):
        return 
    if not quizOn:
        response = messageQuizNotOn
        await ctx.message.channel.send(response)
        return
    # Read the guessed pounce and send it
    guess = ' '.join([word for word in args])
    author, authorName = getAuthorAndName(ctx)
    team = getTeam(author)
    response = 'Guess on pounce by **{}\'**s {}: \'{}\''.format(team, authorName, guess)
    channel = commonChannels[qmChannel]
    await channel.send(response)
    response = "Pounce submitted"
    await ctx.message.channel.send(response)


#############################################
# QM Slide operations: load, next, previous #
#############################################

@bot.command(
    name="loadfile",
    aliases=["loadFile",],
    help="Load a PDF presentation uploaded to the files channel"
    )
async def loadfile(ctx, *args, **kwargs):
    # Authorisation
    global presentationLoaded
    if not getAuthorizedServer(bot, guildId, ctx):
        return 
    auth, response = getAuthorized(
            ctx,
            'Only ',
            ' can load the presentation file',
            'quizmaster','admin'
            )
    if not auth:
        await ctx.message.channel.send(response)
        return
    if not quizOn:
        response = messageQuizNotOn
        await ctx.message.channel.send(response)
        return
    if presentationLoaded:
        response = 'A presentation is already loaded'
        print(response)
        ctx.message.channel.send(response)
        return
    # Clear the directory
    if not os.path.isdir(presentationDirPath):
        os.mkdir(presentationDirPath)
    deleteFiles(presentationDirPath, 'jpg', 'pdf')
    # Load file from most recent message sent on fileChannel
    message = await commonChannels[fileChannel].history(limit=1).flatten()
    if len(message) > 0:
        message = message[0]
        if len(message.attachments) > 0: 
            print(message.attachments[0])
            print(message.attachments[0].filename)
            global presentationFileName
            presentationFileName = message.attachments[0].filename
            presentationPath = os.path.join(presentationDirPath,presentationFileName)
            print(presentationPath)
            await message.attachments[0].save(presentationPath)
        else:
            response = "The last message sent to the channel needs the file attached"
            await ctx.message.channel.send(response)
            return
    else:
        response = "Send the file attached to the files channel"
        await ctx.message.channel.send(response)
        return
    # if the file does not exist in the message, return error
    # if file exists in the message, download file into presentationDirPath
    # and generate slide images
    global slides
    slides = convertToImages(presentationDirPath, presentationFileName)
    print(slides)
    presentationLoaded = True
    global slideNumber
    slideNumber = -1
    response = "Presentation loaded"
    await ctx.message.channel.send(response)

@bot.command(
    name="n",
    aliases=["next",],
    help="Move forward one slide"
    )
async def nextSlide(ctx, *args, **kwargs):
    # Authorisation
    global presentationLoaded
    global slideNumber
    global slides
    if not getAuthorizedServer(bot, guildId, ctx):
        return 
    auth, response = getAuthorized(
            ctx,
            'Only ',
            ' can change slides',
            'quizmaster', 'scorer'
            )
    if not auth:
        await ctx.message.channel.send(response)
        return
    if not quizOn:
        response = messageQuizNotOn
        await ctx.message.channel.send(response)
        return
    if not presentationLoaded:
        response = "Please load the presentation by uploading a file to the \
files channel and then run `!loadfile`"
        await ctx.message.channel.send(response)
        return
    # Check for edge cases, then call the appropriate functions
    if slideNumber == len(slides) - 1:
        response = "The presentation is over. End Quiz?"
        await ctx.message.channel.send(response)
        return
    while slideNumber < -1:
        slideNumber += 1
    slideNumber += 1
    slideName = slides[slideNumber]
    filename = os.path.join(presentationDirPath, slideName)

    await updateSlides(ctx, filename, commonChannels, teamChannels, questionChannel, qmChannel, scoreChannel)
    save()


@bot.command(
    name="prev",
    aliases=["previous",],
    help="Move back one slide"
    )
async def prevSlide(ctx, *args, **kwargs):
    # Authorisation
    global presentationLoaded
    global slideNumber
    global slides
    if not getAuthorizedServer(bot, guildId, ctx):
        return 
    auth, response = getAuthorized(
            ctx,
            'Only ',
            ' can change slides',
            'quizmaster', 'scorer'
            )
    if not auth:
        await ctx.message.channel.send(response)
        return
    if not quizOn:
        response = messageQuizNotOn
        await ctx.message.channel.send(response)
        return
    if not presentationLoaded:
        response = "Please load the presentation by uploading a file to the \
files channel and then run `!loadfile`"
        await ctx.message.channel.send(response)
        return
    # Check for edge cases, then call the appropriate functions
    if slideNumber == 0:
        response = "First slide of the presentation, cannot go back further"
        await ctx.message.channel.send(response)
        return
    while slideNumber > len(slides):
        slideNumber -= 1
    slideNumber -= 1
    slideName = slides[slideNumber]
    filename = os.path.join(presentationDirPath, slideName)

    await updateSlides(ctx, filename, commonChannels, teamChannels, questionChannel, qmChannel, scoreChannel)
    save()


############################################################################
# QM Quiz start, stop, restore (on_ready), role reset, clearAll operations #
############################################################################


@bot.command(
    name="stopQuiz",
    aliases = ["stopquiz", "endQuiz", "endquiz"],
    help="Stop the quiz and clear channels"
    )
async def endQuiz(ctx, *args, **kwargs):
    # Authorisation
    if not getAuthorizedServer(bot, guildId, ctx):
        return 
    auth, response = getAuthorized(ctx,'Only ', ' can end this quiz','quizmaster', 'admin')
    if not auth:
        await ctx.send(response)
        return
    # Unset variables, clear channels, remove score and slide states, make
    # finalscores, send final result on calling channel
    response = "Warning! This will clear all channels and end the quiz."
    await ctx.send(response)
    global quizOn
    quizOn=False
    global presentationLoaded
    presentationLoaded = False
    if os.path.exists(presentationDirPath):
        deleteFiles(presentationDirPath, 'jpg', 'pdf')
    #clear everything
    await deleteAllMessages(bot, guildId, whitelistChannels)
    response = "The final scores are below (they're also saved in finalscores.txt)\n"
    response += '\n'.join(str(team)+" : "+str(scores[team]) for team in scores)
    await ctx.send(response)
    teamDistribution = getTeamDistribution(bot, guildId, scores, names=True)
    response = "The participants were\n"
    response += '\n'.join(str(team)+" : "+str(teamDistribution[team]) for team in teamDistribution)
    await ctx.send(response)
    with open("finalscores.txt","w") as scoresFileObject:
        json.dump([scores, teamDistribution], scoresFileObject)
    if os.path.exists("scores.txt"):
        os.remove("scores.txt")
    if os.path.exists("slides.pkl"):
        os.remove("slides.pkl")
    print("Quiz ended")



@bot.command(
    name="newquiz",
    aliases = ["startQuiz", "setNumTeams", "newQuiz", "startquiz"],
    help="Reset everything and start a new quiz with an input number of teams"
    )
async def newQuiz(ctx, *args, **kwargs):
    # Authorisation
    if not getAuthorizedServer(bot, guildId, ctx):
        return 
    auth, response = getAuthorized(ctx,'Only ', ' can end this quiz','quizmaster', 'admin')
    if not auth:
        await ctx.send(response)
        return
    response = "Warning! This will clear all channels and reset all scores."
    await ctx.send(response)
    if not len(args):
        await ctx.send("This command must be issued along with the number of \
participating teams (example: `!newQuiz 7` for starting a quiz \
with 7 teams). Existing member roles will not be affected.")
        return

    # Read number of teams, clear messages, set flags, reset scores, send
    # the welcome texts
    numberOfTeams = int(args[-1])
    response = "Creating a quiz with {} teams. \
\nClearing all channels. This message and everything above might \
soon disappear.".format(str(numberOfTeams))
    await ctx.send(response)
    
    try:
        await endQuiz(ctx=ctx)
    except:
        response = "Could not find a quiz to end. Starting a new one..."
    await ctx.send(response)

    global quizOn
    quizOn = True
    print("Quiz started!")

    # make dicts of all team and common channels
    # This has been done to avoid issues with dictionary.clear()
    global commonChannels
    global teamChannels
    commonChannels = {}
    teamChannels = {}

    teamChannels = getTeamChannels(bot, guildId, numberOfTeams)
    commonChannels = getCommonChannels(bot, guildId, whitelistChannels)

    #clear everything
    await deleteAllMessages(bot, guildId, whitelistChannels)

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
    await commonChannels[qmChannel].send(response)    

    response = "Guesses on bounce you make by with `!bounce` or \
`!b` command appear here"
    await commonChannels[qmChannel].send(response)

    response = "Welcome! Below are the commands you can use to set scores. \
Teams are always abbreviated as t1 t2 etc.\
\n`!s -10 t3 t4 t8` to add -10 points to teams3,4,5;\
\n`!s 5 t2` to add 5 points to team2\
\n`!plus 10 t3 t4 t8` to give 10 points to teams 3,4,8 ;\
\n`!minus 5 t1 t2` to deduct 5 points from team1 and team2"
    await commonChannels[scoreChannel].send(response)

    await broadcastToAllTeams("Welcome to the quiz! This is your \
team's private text channel.\
\nCommands for the bot:\
\n`!p your guess here` or `!pounce your guess here` to pounce,\
\n`!b your guess here` or `!bounce your guess here` to answer on bounce,\
\n`!scores` to see the scores.")

    await broadcastToAllTeams("If you are seeing this message in the middle \
of a quiz, alert the quizmaster. The scores might need to be checked.")

    await broadcastToAllTeams("\n1)Please have an identifiable nickname by \
right-clicking on your name on the right column and changing \
nickname (it won't affect your name in other discord guilds)\
\n2)Please mute your microphone\
\n3)Go to user settings -> notifications and turn off \
notifications for User Joined, User Leave, User Moved, Viewer \
Join, Viewer Leave")
    
    await ctx.send("All team channels have been cleared, and all scores have \
been set to 0. You can begin the quiz. \
\nIf you want to use a PDF for the quiz please upload a file to \
the #file-upload channel and run `!loadfile`. To show the next\
slide enter `!n` or `!next`. to show the previous slide (this does not\
delete the last slide sent) enter `!prev`\
\nIf you want to unassign all team roles, make the bot an admin \
and issue the command `!resetTeams`. Those who wish to participate \
have to type `!join` to be automatically assigned a team.")

    return



@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    # In case there was a running quiz, restore everything
    if os.path.exists('scores.txt'):
        with open("scores.txt") as scoresFileObject:
            scoresInFile = json.load(scoresFileObject)
        print("The bot has reset and scores are being read from file")

        if os.path.exists('slides.pkl'):
            print("loading")
            load()

        numberOfTeams = len(scoresInFile)
        global commonChannels
        global teamChannels
        teamChannels = {}
        commonChannels = {}
        teamChannels = getTeamChannels(bot, guildId, numberOfTeams)
        commonChannels = getCommonChannels(bot, guildId, whitelistChannels)

        for key in teamChannels.keys():
            print(key, teamChannels[key])
        for key in commonChannels.keys():
            print(key, commonChannels[key])
        
        scores.clear()
        for team in teamChannels:
            scores[team] = scoresInFile[team]

        global quizOn
        quizOn=True

        await commonChannels[qmChannel].send('Bot was restarted, scores restored')
        await broadcastToAllTeams("The bot had to reset for reasons unknown \
but the scores must have been retained. Below are the scores \
after the last update. Please alert the quizmaster if \
there's a discrepancy.")
        response = '\n'.join(str(team)+" : "+str(scores[team]) for team in scoresInFile)
        await broadcastToAllTeams(response)

        response = "Here are the scores after reset\n"
        response += '\n'.join(str(team)+" : "+str(scores[team]) for team in scoresInFile)
        await commonChannels[scoreChannel].send(response)
    else:
        print("Please !startQuiz")


@bot.command(
    name="clearAllChannels",
    help="delete all messages in all important channel and resets score to 0"
    )
async def clearAll(ctx, *args, **kwargs):
    # Authorisation
    if not getAuthorizedServer(bot, guildId, ctx):
        return 
    auth, response = getAuthorized(
            ctx,
            "Only ",
            " can purge all channels and reset scores to 0.",
            'quizmaster', 'scorer', 'admin'
            )
    if not auth:
        await ctx.send(response)
        return
    # clear messages, scores 
    await deleteAllMessages(bot, guildId, whitelistChannels)
    for team in teamChannels:
        scores[team]=0
    response = "All channels cleared and scores set to 0"
    await ctx.message.channel.send(response)


@bot.command(
    name="resetRoles",
    aliases = ["unassignAll", "resetTeams"],
    help="remove all team roles"
    )
async def resetRoles(ctx, *args, **kwargs):
    # Authorisation
    if not getAuthorizedServer(bot, guildId, ctx):
        return 
    auth, response = getAuthorized(
            ctx,
            "Only ",
            " can assign or unassign teams",
            'quizmaster', 'scorer', 'admin'
            )
    if not auth:
        await ctx.send(response)
        return
    # Clear team roles 
    await unassignTeams(bot, guildId, ctx)
    await ctx.send("Removed all team roles. The quizmaster can either manually \
assign roles or ask participants to `!join` once `!startQuiz` is run")
    return 


###################################
# QM Scoring options: plus, minus #
###################################

@bot.command(
    name="s",
    aliases = ["plus","sco","sc","score"],
    help="for scorers and quizmasters to update scores"
    )
async def updateScores(ctx, *args, **kwargs):
    # Authorisation
    if not getAuthorizedServer(bot, guildId, ctx):
        return 
    if not quizOn:
        response = messageQuizNotOn 
        await ctx.message.channel.send(response)
        return

    if len(args) <2:
        if len(args) == 1:
            positive_points, negative_points = abs(int(args[0])), -1*abs(int(args[0]))
        else:
             positive_points, negative_points = 10, -5

        teamDistribution = getTeamDistribution(bot, guildId, scores)
        arr_of_messages = []
        arr_of_msg_ids = []
        for team in scores:
            # Get team members, scores, generate a response and send
            response = '{}\t{}\t{}'.format(
                str(team),
                str(scores[team]).center(8),
                ', '.join(getTeamMembers(teamDistribution, team)).center(60))

            mesg = await ctx.message.channel.send(response)
            await mesg.add_reaction('\U00002795')
            await mesg.add_reaction('\U00002796')
            arr_of_messages.append(mesg)
            arr_of_msg_ids.append(mesg.id)

        global sco_command_messages
        for msg in sco_command_messages:
            await msg.delete()

        sco_command_messages = arr_of_messages
        wait_time = 1

        def check(reaction, user):
            auth, _ = getAuthorizedUser(user, "Only ", " can update scores", 'quizmaster', 'scorer')
            return (auth and bot.user != user and
                    reaction.message.id in arr_of_msg_ids and
                    reaction.emoji in ['\U00002795', '\U00002796'])

        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', timeout=wait_time, check=check)
                await reaction.remove(user)
                
                ind = arr_of_msg_ids.index(reaction.message.id)
                team = "team"+str(ind+1)

                points = 0
                # If plus add 10 to teams score
                if reaction.emoji == '\U00002795':
                    points = positive_points
                # If minus remove 5 from teams score
                if reaction.emoji == '\U00002796':
                    points = negative_points
            
                scores[team] += points
                sign = lambda x: ('+', '')[x<0]
                response = '{}{} to {}. '.format(sign(points),str(points), team) 
                channel = commonChannels[scoreChannel]

                response = '{}\t{}\t{}'.format(
                    str(team),
                    str(scores[team]).center(8),
                    ', '.join(getTeamMembers(teamDistribution, team)).center(60))
                
                await arr_of_messages[ind].edit(content= response)
                response = '{}{} to {}. '.format(sign(points),str(points), team) 
                await channel.send("Logged "+response)
                await ctx.send(response)

                with open("scores.txt","w") as scoresFileObject:
                    json.dump(scores, scoresFileObject)
        
                channel=teamChannels[team]
                response = '{}{} to your team. Your score is now {}'.format(sign(points),str(points), scores[team])
                await channel.send(response)

            except asyncio.TimeoutError:
                # await self.message.clear_reactions()
                # break
                pass

    if len(args)>=2:
        auth, response = getAuthorized(ctx,"Only ", " can update scores", 'quizmaster', 'scorer')
        if not auth:
            await ctx.send(response)
            return
        # Get updated scores, save to file, and send updates to teams
        points = int(args[0])
        teams = [team.replace('t','team') for team in args[1:]]
        for team in teams:
            print("Updating score for ", team)
            scores[team]+=points

        sign = lambda x: ('+', '')[x<0]
        response = '{}{} to {}. '.format(sign(points),str(points), ', '.join(team for team in teams)) 
        channel = commonChannels[scoreChannel]
        await channel.send(response)

        with open("scores.txt","w") as scoresFileObject:
            json.dump(scores, scoresFileObject)

        for team in teams:
            channel=teamChannels[team]
            response = '{}{} to your team. Your score is now {}'.format(sign(points),str(points), scores[team])
            await channel.send(response)


#TODO handle !minus better
@bot.command(
    name="minus",
    aliases = ["deduct"],
    help="for scorers and quizmasters to update scores"
    )
async def minus(ctx, *args, **kwargs):
    # Authorisation
    if not getAuthorizedServer(bot, guildId, ctx):
        return 
    if not quizOn:
        response = messageQuizNotOn
        await ctx.message.channel.send(response)
        return
    if len(args)<2:
        await ctx.send("example: `!minus 5 t2 t8`  to deduct 5 points from team2 and team8")
        return
    auth, response = getAuthorized(ctx,"Only ", " can update scores", 'quizmaster', 'scorer')
    if not auth:
        await ctx.send(response)
        return
    # Get updated scores, save to file, and send updates to teams
    points = int(args[0])
    teams = [team.replace('t','team') for team in args[1:]]
    for team in teams:
        scores[team]-=points

    sign = lambda x: ('+', '')[-x<0]
    response = '{}{} off {}. Points table now: \
            \n'.format(sign(points),str(points), ' '.join(team for team in teams)) 
    response += '\n'.join(str(team)+" : "+str(scores[team]) for team in scores)
    channel = commonChannels[scoreChannel]
    await channel.send(response)

    with open("scores.txt","w") as scoresFileObject:
        json.dump(scores, scoresFileObject)

    for team in teams:
        channel=teamChannels[team]
        response = '{}{} points off your team score. Your score is now \
                {}'.format(sign(points),str(points), scores[team])
        await channel.send(response)

@bot.command(
    name="resetScores",
    aliases = ["resetscores","clearscores","clearScores"],
    help="makes all scores 0"
    )
async def resetscores(ctx, *args, **kwargs):
    # Authorisation
    if not getAuthorizedServer(bot, guildId, ctx):
        return 
    if not quizOn:
        response = messageQuizNotOn
        await ctx.message.channel.send(response)
        return
    auth, response = getAuthorized(ctx,"Only ", " can update scores", 'quizmaster', 'scorer')
    if not auth:
        await ctx.send(response)
        return
    #reset scores
    scores.clear()
    for team in teamChannels:
        scores[team] = 0
    with open("scores.txt","w") as scoresFileObject:
        json.dump(scores, scoresFileObject)
    response = "Scores reset to 0"
    await ctx.message.channel.send(response)


####################
#  Error Handling  #
####################

@bot.event
async def on_command_error(ctx, error):
    if not getAuthorizedServer(bot, guildId, ctx):
        return 
    with open('err.log', 'a') as f:
        f.write(f'Unhandled message: {error}\n')
        await ctx.send("The command could not be run. Please type `!help` for the list of available commands")

############################################################
#  Helper functions that need more context than botutils.  #
############################################################

@bot.command(name="broadcast", help="")
async def broadcastToAllTeams(message):
    # Doesn't actually need to be here, TODO port to botutils
    for team in teamChannels:
        await teamChannels[team].send(message)


def load():
    state = recoverSlideState('slides.pkl')
    print("Loading:")
    for key in state:
        print(key, state[key])
    global presentationLoaded
    global slides
    global slideNumber
    presentationLoaded = state['presentationLoaded']
    slides = state['slides']
    slideNumber = state['slideNumber']

def save():
    state = {}
    state['presentationLoaded'] = presentationLoaded
    state['slides'] = slides
    state['slideNumber'] = slideNumber
    saveSlideState('slides.pkl', state)
    print("Saving:")
    for key in state:
        print(key, state[key])

bot.run(token)
