# HeadpatBot

A discord bot for distributing headpats and rating waifus.  
[Add the bot to your server](https://discord.com/api/oauth2/authorize?client_id=807859649621524490&permissions=117824&scope=bot)  
[Join the support server](https://discord.gg/yhQzBYqFZb)

## Features/Commands
### !help command
Help command - gives a list of commands when <command> argument is empty, or describes in more detail the functionality of a command.  
Available to all roles
### !Headpat
Retreives a random headpat from your server's list.  
Available to all roles
##### !Headpat addimage image.link
Stores a new headpat image that can be randomly fetched by !headpat.  
Available to all roles
##### !Headpat removeimage image.link
Removes the specified link from the server's headpats.  
Available to moderator roles
### !Waifu 
Command family for approval voting polls. Does not work without arguments.
##### !Waifu add image.link name
adds a waifu to be voted on in selection polls.  
performs some checking to ensure the link is valid, but does not always succeed.  
Available to all roles
##### !Waifu addcsv
Adds all waifus from a csv file.  
Default CSVs for testing or bootstrapping included in github repository.  
CSV must have columns in following order: `Name | Immunity (default 0) | Probability (default 1) | image.link`  
Available to moderator roles
##### !waifu exportCSV
Exports the server's waifus to a csv file
Available to moderator roles
##### !Waifu remove name
Removes the named waifu from the poll list.  
Not required nor reccomended for eliminated waifus - those are kept by default in order to revent re-addition, but will not appear in future polls.  
Available to moderator roles
##### !waifu list \[exclude eliminated (boolean __yes__/no)]
Responds with a sorted list of the waifus in the server.
Returns names only, no immunity or probability data.
Adding an optional 'false' or 'no' argument wil also include waifus that have been eliminated from polling in the list.
Available to all roles
##### !Waifu startpoll
Selects 10 waifus, then creates and posts image collage.  
Reacts with keypad numbers from 0 to 9, and a flag.  
* The flag is intended as a 'done voting' mark to help moderators keep track of a threshold for ending rounds
* Each Reacted keypad emoji corresponds to a waifu, and user reactions will count as a vote for that waifu

Available to moderator roles
##### !Waifu endpoll
Closes the latest round of voting, and calculates results.  
posts vote distribution graph of round in channel
Available to moderator roles
##### !Waifupoll <round> [deprecated]
Fetches the keypad number reacts from recent pins, excluding its own, and posts them as a text file

## Planned Features
* Configurable Role Control
* Configurable Poll Settings (size, image specifications, etc)
* Random Replacement of headpat images by users
* Auto-polling by time interval and/or completion votes
* Discord image attachment/link support

## Unplanned/Out-of-scope features
* Image fetching from external service by name
* Automated Image Moderation to exclude possibly un-wholesome content
* Competent writing

## Backend
Built using discord.py
designed to run on Heroku, compatible with free Dynos
### Headpats
Stores and retreives from a postgreSQL database using psycopg2.
### Waifupolls
Stores and retreives from a postgreSQL database using psycopg2.  
Fetches Imges using URLLIB.  
Stitches collage with Numpy and openCV2.  
Determines round results with a devation-from-mean method executed with numpy.
* by default, eliminates all selections with 0 votes, or fewer votes than 1 standard devation below the mean.  
* Assigns a future pick weight based on ```1/(pickScale+votes)``` where `pickScale` = 2 by default.  
* Will not select contestants for future rounds until the number of rounds since they last appeared exceeds how many standard deviations above elimination they were.

Creates diagnosic plots with matplotlib.  
