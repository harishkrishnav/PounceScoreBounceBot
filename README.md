# PounceScoreBounceBot for quizzes

## What is it?

Discord + this bot eliminates the need for paid p2p subscriptions, time limits, screenshotting, frequent switching between channels, spreadsheets to keep scores, WhatsApp groups specifically for a quiz, and all those frustrations of quizzing online. In this, if a participant tabs the screenshare window, they can go through the entire quiz without needing a mouse or switching out of the channel. 

This is a discord bot to handle pounces, bounces, scoring, and cleaning up in a quiz. This repo is currently under development and all feature suggestions, bug reports, pull requests are welcome.

### Pouncing

To pounce, a participant simply types
`!p their pounce answer` or `!pounce some guess`
This message is displayed as a popup to the quizmaster and appears in a separate channel for pounce answers that only the
quizmaster has access to. For example, if a quizzer named harish in team3 wants to submit "mahatma gandhi" as a pounce answer,
he simply types `!p mahatma gandhi` in team3's channel. The quizmaster would see the message `mahatma gandhi pounced by team3's harish`.


Quizmaster sees pounces at one place: 
![pounce](https://i.imgur.com/YBUh06N.png "quizmaster view of pounces channel")
quizmaster's view


### Bounce

Similarly, for bounce, a team types in their team's private chat 
`!b their bounce answer` or `!bounce some guess`
The bot sends this message to the private chats of all teams. So, if harish of team 3 were to answer mahatma gandhi" on bounce,
he would type `!b mahatma gandhi` and all teams would see `Guess on the bounce by team3's harish : mahatma gandhi`. This will also appear in a separate bounces channel. 


Bounce answers are broadcast: 
![bounce](https://i.imgur.com/3ShWRlm.png "team1 submit an answer on bounce")
team1's view. The stream can be popped out and pinned to the top.


### Scoring

The 'quizmaster' or someone else who is assigned with the role of 'scorer' can simply type `!s 10 t4 t6` to add 10 points to the scores 
of team4 and team6. Likewise, `!s -15 t1 t8` subtracts 15 points from the scores of team1 and team8. All score updates will be visible on the dedicated scores channel and a message will be sent to every team that has an update. The score channel will also have the full table of points of every team after every update.
The bot can also handle commands of the type `!plus 10 t4 t1 t2` and `!minus 5 t2 t9` for adding 10 points and subtracting 5 points respectively. 




Scoring is through one command. This can be done by a scorer too: 
![scoring](https://i.imgur.com/H5qfg2k.png "scores are given")
scorer's view


Typing `!scores` at any time from any channel will display all the scores. 

If there are connectivity issues, the bot may reload and the scores may reset to zero. A warning will be displayed and the scores will have to be entered again. Pounce/bounce should not be affected. 


Teams are notified of score updates: 
![scores](https://i.imgur.com/mp9L1i5.png "points table at any time during the quiz")
team2's view



### Cleanup

This command deletes all messages in all channels with IDs defined in the code:
`!clearAllChannels` 
This command deletes all messages in the specific channel it is called
`!clearThis`
This may be better than cloning/deleting channels or servers and then retyping channel IDs 


## Running the bot (the first time)
1. Create a discord server with this [template](https://discord.new/ZSrQHC4tTF6T) 
1. [Create a bot with 'administrator' permissions on the discord developer portal](https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token). When replacing the client id in the URL, use permissions=8 i.e. `https://discordapp.com/oauth2/authorize?&client_id=CLIENTID&scope=bot&permissions=8` and not `permissions=0` 
1. You probably already have [python](https://www.python.org/downloads/) installed. Clone or zip and download this repository. 
1. Install the required packages in a virtual environment (warnings are okay) on a terminal
```
pip install -r requirements.txt
```
6. Run:
```
python quizbot.py
```
7. The command window will prompt for the token. You would have noticed this when performing step 2 above. You can find this in https://discordapp.com/developers/applications and in the Bot menu in the settings tab. Copy-paste this long token here and hit enter.
8. The prompt will not ask for a guild ID. Right click on the guild icon in the bar on the left and click on copy ID ([may need to toggle an appearance switch](https://discordia.me/en/developer-mode)). Paste this in the prompt and hit enter.
9. You will notice that the folder now has a `.env` file with the credentials. You do not need to confront the prompts for this again.


## Starting the bot (subsequently)
- Run `python quizbot.py`. That's it.

## Some tips and tricks when running a quiz
 - Running Discord on thr browser may not allow for many features. It is recommended that everyone run Discord on the [desktop or mobile application](https://discordapp.com/download) and not on the browser. 
 
 - It needn't be the quizmaster running the bot. In fact, the bot can be running on a server machine in the background for weeks and this machine need not have the discord app. (I'm currently figuring out how to set it up on Azure) 
 
#### Assigning teams
- Team assignment of a participant to say `team1` is by assigning them the role `team1`. 
- The owner of the discord server can assign roles to the participants who are displayed in the member list column on the right. Clicking on a user will open up a window where there's a plus button to add a role. Right clicking on a user will give many other options as well. 
- Someone who has been assigned as a quizmaster can assign roles to other users.
- The quizmaster will not be able to see non-bounce-pounce team channel chat messages unless the quizmaster is also assigned a team role. 

#### Screenshare
- Only those connected from the desktop app (not the browser, not the mobile app) can [screenshare](https://support.discordapp.com/hc/en-us/articles/360040816151-Share-your-screen-with-Go-Live-Screen-Share).
- Quizmasters can go to the voice channel named `the quiz` and find the option to "go live" in the bottom left
- There is currently a limit of 50 people being connected to this live streaming. The limit may reduce in the future. However, there is no limit on the number of people being connected to the voice channel when there's no streaming, nor in other channels. In such a scenario, using screenshots may be the best way to hold quizzes. By the time discord announces a reduction in the number of people who can connect to a live stream, this bot should have features that make it very easy to send images of slides.
- In Windows, it's possible for the quiz master to dock the discord app and the slideshow like this:
![both discord and powerpoint slideshow open](https://i.imgur.com/oYjP2Fm.png "the quizmaster can have both discord and powerpoint slideshow open side-by-side")

Because of this, a quizmaster need not keep keying `alt-tab` to switch between different applications. If there's a scorer, a quizmaster can go through an entire quiz only without needing to switch tabs - using the left and right arrow kets for the slideshow, while observing pounces through the channel and bounces through the notifications. The quizmaster can save themselves a lot of hassle by assigning someone as a scorer who will handle the scoring commands while the quizmaster simply announces the points per question.
![powerpoint slideshow as window](https://i.imgur.com/TbfLXNo.png "how to get powerpoint to open in a window that can be rescaled")
This slideshow window can be resized.

- How to dock both the Powerpoint slideshow and discord windows side-by-side to avoid tab switching:
   1. Click on the Slideshow ribbon tab and then set up slideshow
   1. In the window that pops up, under 'Show Type', click 'Browsed by an individual (window)' and click OK
   1. Present the slideshow
   1. Double click on the title bar at the very top of the slideshow window or click on the 'Restore down' button that's between 'minimize' and 'close' on the top right
   1. Move the mouse curser to the edges of the window to resize it. 
   1. Repeat the above two steps for the discord app window. Place the two windows side-by-side, neither of them maximised. Look at the image above for inspiration.
   1. Advancing slides on the slideshow is by clicking on the arrows at the bottom of the window. No need for alt-tabs.

- I hear that in Macbooks, go live only mirrors the screen. The quizmaster will then have to turn off push notifications and download the discord app on their mobile to see the bounce and pounce channels while the laptop runs the slideshow in full-screen.

#### Mute notifications
 - The server owner might want to mute themselves from the team and pounce channels to not see the answers  
 and guesses 
 - Users can also mute the bot (right click and mute) 
 

## Credits
This is largely based on [this repo](https://github.com/zubairabid/QuizPounceBot) by Zubair Abid. Many thanks to him, Athreya, Shyam, and others in the IIIT Hyderabad quiz club for figuring all this out. 


## Feature backlog
- Scorers can add some keywords from the question while sending score updates. Teams can then get a history of which questions they got right and wrong. This will also allow for other features such as figuring out which team was the most recent to get points on bounce which would help figure out whose question it is now
- Check if every team that pounced got a score update. Also keep track of the number of negative pounces by a team and allow the option of disallowing teams that have more incorrect pounces than a certain threshold.
- If the entire quiz is saved as a folder of images (each image being a slide), allowing for the quizmaster to send the image of the next slide to all teams through one command. This will be helpful if there's no AV content and many participants don't have a good internet connection.


Any idea to make this bot powerful and easy-to-understand is welcome.
