# PounceScoreBounceBot for quizzes

## What is it?

Discord + this bot eliminates the need for paid p2p subscriptions, participation limits, screenshotting, frequent switching between channels, spreadsheets to keep scores, WhatsApp groups specifically for a quiz, and all those frustrations of quizzing online. In this, if a participant tabs the screenshare window, they can go through the entire quiz without needing a mouse or switching out of the channel. 

This is a discord bot to handle pounces, bounces and scoring in a quiz. A participant is assigned their team as a role (e.g. 'team1', 'team2') and has access only to the chat and voice channels of that team, and a general channel for clarifications. The bot also handles cleaning up after the quiz.


### Pouncing

To pounce, a participant simply types
`!p their pounce answer`
This message is displayed as a popup to the quizmaster and appears in a separate channel for pounce answers that only the
quizmaster has access to. For example, if a quizzer named harish in team3 wants to submit "mahatma gandhi" as a pounce answer,
he simply types `!p mahatma gandhi` in team3's channel. The quizmaster would see the message `mahatma gandhi pounced by team3's harish`.

Quizmaster sees pounces at one place: 
![pounce](https://i.imgur.com/YBUh06N.png "quizmaster view of pounces channel")
quizmaster's view


### Bounce

Similarly, for bounce, a team types in their team's private chat 
`!b their bounce answer`
The bot sends this message to the private chats of all teams. So, if harish of team 3 were to answer mahatma gandhi" on bounce,
he would type `!b mahatma gandhi` and all teams would see `Guess on the bounce by team3's harish : mahatma gandhi`. This will also appear in a separate bounces channel. 


Bounce answers are broadcast: 
![bounce](https://i.imgur.com/3ShWRlm.png "team1 submit an answer on bounce")
team1's view


### Scoring

The 'quizmaster' or someone else who is assigned with the role of 'scorer' can simply type `!s 10 t4 t6` to add 10 points to the scores 
of team4 and team6. Likewise, `!s -15 t1 t8` subtracts 15 points from the scores of team1 and team8. All score updates will be visible on 
the dedicated scores channel and a message will be sent to every team that has an update. The score channel will also have the full table 
of points of every team after every update.


Scoring is one simple command. This can be done by a scorer too: 
![scoring](https://i.imgur.com/H5qfg2k.png "scores are given")
scorer's view

Typing `!scores` at any time from any channel will display all the scores. 

If there are connectivity issues, the bot may reload and the scores may reset to zero. A warning will be displayed and the scores will have 
to be entered again. Pounce/bounce should not be affected. 


Teams are notified of score updates: 
![scores](https://i.imgur.com/mp9L1i5.png "points table at any time during the quiz")
team2's view


### Cleanup

This command deletes all messages in all channels with IDs defined in the code:
`!clearAllChannels` 
This command deletes all messages in the specific channel it is called
`!clearThis`


## Running the bot (the first time)
- Create a discord server with this template: https://discord.new/ZSrQHC4tTF6T 
- [Create a bot with admin privileges on the discord developer portal](https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token) 
- Right click on the channels in discord and copy paste the channel IDs in the python script ([may need to toggle an appearance switch](https://discordia.me/en/developer-mode))
- This assumes you have [python3](https://www.python.org/downloads/). Install required packages in a virtual environment (warnings are okay)
```
pip install -r requirements.txt
```
- Run:
```
python quizbot.py
```


## Running the bot (subsequently)
- Run `python quizbot.py`. That's it.

## Credits
This is based on [this repo](https://github.com/zubairabid/QuizPounceBot) by Zubair. Many thanks to him, Athreya, Shyam, and others in the IIIT Hyderabad quiz club for figuring all this out.  
