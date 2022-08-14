# whatdayisit_JP
#### Video Demo:  <URL https://youtu.be/e3YPM1rvRDY>
#### Description:
People associate special meanings to many days in a year like our birthdays, valentine’s day, Halloween, and many more.

There are generally accepted special meanings to a day, while there are also some newly arising special meanings to many days in a year. Like the Ramen’s day in Japan is the 11th of July because we need a pair of chopsticks and a spoon to eat it, and the number 11 looks like chopsticks and the number 7 looks like a spoon. So just because of that, some people claimed that the 11th of July is Ramen’s day.

Where did all those meanings come from? Apart from individual's creativity, promotion also plays an important role in convincing other people that the legitmacy of the association of meaning with a specific day.

This project allows people to (1) know what today could be, and (2) claim what meanings should be associated with a specific day in year. The ultimate goal is to make every day a special day such that people can continuously discover and experience new things.

#### Purpose
##### For fun
##### For business ideas
##### For people to promote special meaning association with any day in year

#### Requirement
##### Twitter API 2.0 Bearer Token (Essential)
##### Python 3.8
##### Sqlite3 3.38.0
##### Flask 2.1.0

#### Usage
Check the index page everyday to see what are something new to you. If you find any day that has a specific meaning in your community, add that meaning to the day.db database such that other people may share the joy of the day.

#### Author
Chris LAM

#### Files description
/static/styles.css - Set font family that looks cool for Japanese characters, Set margins for different sections of the web app, Set black theme with white fonts

/templates/layout.html - Set header banner and footer banner that move along with the viewport, set a colorful div showing whatdayisit example (content changes every 500 miliseconds implemented via JavaScript), include bootstrap 5.0.2 css and JavaScript.

/templates/index.html - Show a list of special meanings of today (data extracted from Twitter recent tweets via regex matching against the Twitter search API response, sorted by tweet count in descending order), allow user to save their version of special meaning of today to the days.db database via a form

/templates/database.html - Show a list (up to top 3 items) of user-voted special meaning of a specific day, allow user to browse through each day of a year via a form to check the top 3 meanings associated with that day.

/templates/poll.html - Allow user to save their version of special meaning of any day (vs today only in index.html) to the days.db database via a form

/templates/invalidinput - Show error message when any of the inputs in forms in index.html, database.html, and poll.html is invalid, allow user to go to the index.html or poll.html via a tag

/app.py - Check if Twitter API Bearer token is in place, set up flask, link user submitted web-form to days.db database, get today datetime (in Japan Standard Time) for querying twitter the special meanings of today, using regex to extract the exact whatdayisit phrase (〇〇の日/デー), and then query the number of tweets of each exact phrase and sort the number along with the phrase by number in descending order, pass the data to index.html

/days.db - Consist of 1 table which has columns(month, day, dayName, count) to store user's votes of what special meanings are associated with which days

/requirements.txt - list of python libraries imported in app.py

/READMEmd - this document