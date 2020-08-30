# PounceScoreBounceBot for quizzes

## Update: now can send slides and scoring can be done through buttons - all thanks to [Athreya](https://github.com/cathreya) and [Zubair](https://github.com/zubairabid) 

If you want to do this the easy way, just follow [this wiki](https://github.com/harishkrishnav/PounceScoreBounceBot/wiki/Bot-setup,-the-easy-way)

#### Setting up the environment
If you starting afresh, create a server by clicking [this link](https://discord.new/7hjs36KQ52tr) and a bot following [this link](https://imgur.com/jEgQEsC). You can skip the changes to the server section below.
If you are already using the bot and have an existing server, follow the following instructions
1. The updated code is in the branch `sendslides`. If you used the command `git pull` earlier, you should be able to run `git pull` again and use the command `git checkout sendslides`.    
    * If there are uncommited changes that prevent you from switching branch, commit your changes using   
    `git commit -a -m "my changes"`
2. You will now need to install Poppler. If you are using Windows, download the latest binary from [this link](http://blog.alivate.com.au/poppler-windows/). At time of writing this, the latest binary was poppler-0.68.0_x86.
3. Extract the downloaded the archive file. It should have a directory called bin.
4. Add the path of this bin folder to PATH environment variable: for example, if the bin directory is at the location `C:\Program Files\poppler-0.68.0_x86\bin`, add this to the environment variable. To do this, click on the Windows start button, search for `Edit the system environment variables`, click on Environment Variables..., under System variables, look for and double-click on PATH, click on New, then add `C:\Program Files\poppler-0.68.0_x86\bin`, click OK.
5. Run `pip install -r requirements.txt` in the home directory of the bot codebase.

#### Changes to the server
1. You will need to rename channel `pounce-guesses` to `qm-control-panel`
1. Rename channel `bounce-channel` to `slides-and-media`
1. Create a new channel called `file-upload` and edit its permissions so that everyone can not read messages
1. If you do not like these names, you can edit quizbot.py and look for the commented line `### Setting up variables to be used for running a Quiz ###` under which the variable names with the channels are defined. Remember that the names of the channels have to match exactly with what's in the code.

#### During a quiz
1. Run `python quizbot.py` 
2. On the discord server, run `!startQuiz <number of teams>` where `<number of teams>` is replaced with a number (you should not include the angular brackets). For example, `!startQuiz 6` for 6 teams.
3. Upload a PDF of the quiz to the channel `file-upload`. Note that the PDF must be smaller than 8MB in size (use online PDF compression services if needed). You currently can not use multiple PDFs per quiz.
4. **There should be nothing else on the `file-upload` channel except one lone message with the attached PDF**
5. In any other channel, run the command `!loadFile`
6. You should now be able to send next slides using the `!n` command. This can be run by a quizmaster/scorer from any channel. 
7. Most likely error: there's a mismatch in channel names.  

Any idea to make this bot powerful and easy-to-understand is welcome.
