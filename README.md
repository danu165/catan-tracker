# Catan Tracker

A fun little project that helps my wife and I keep track of our Catan record. 

Built with:
* AWS
* Google Sheets
  * To authenticate to Google Sheets from AWS, Google's new feature of workload identity pools is used.
    * This means there are no long term credentials stored anywhere :raised_hands:


We text a phone number our results and then we get a response of our current record for the overall game, the specific game type we played, and the conditions of the environment we were in.

## Local Development
Note: not currently working
```
cd flask
flask run
```