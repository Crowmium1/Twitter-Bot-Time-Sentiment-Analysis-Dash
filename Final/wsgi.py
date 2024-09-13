import sys

# add your project directory to the sys.path
project_home = u'C:\Users\ljfit\Desktop\Coding Projects\Time Sentiment Analysis of social media for Brand Monitoring\Project Folder\Fourth Attempt (running code output on update button)'
if project_home not in sys.path:
    sys.path = [project_home] + sys.path

# need to pass the flask app as "application" for WSGI to work
# for a dash app, that is at app.server
# see https://plot.ly/dash/deployment
from main import app
application = app.server