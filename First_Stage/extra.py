import dash
import re
import dash.testing
from dash import dcc, html, Input, Output, dash_table
from textblob import TextBlob
import sqlite3
import plotly.graph_objs as go
import base64
import requests
import os
import tweepy
import pandas as pd
from main import dataframe


# Create an instance of your Dashboard class
My_dashboard = Dashboard(app, dataframe)

# Define the values for page_current_value and page_size_value
page_current_value = 0  
page_size_value = 10    

# Call the update_table function
result, fig = My_dashboard.update_table(page_current_value, page_size_value)

# Print the DataFrame and display the histogram using Plotly
print(result)  
fig.show() 

# Create a DashRenderer instance
renderer = DashRenderer()

# Render the app and retrieve the DataTable component
response = renderer.run_app(app)
datatable = response.find_by_id('datatable')

# Retrieve the data from the DataTable component
data = datatable.props['data']

# Check that the data matches the expected data
self.assertEqual(data, expected_data)

# Dashboard Creation
# Create a pie chart of sentiment scores
fig = px.pie(dataframe, values=['Sentiment','Sentiment_Magnitude'], names=['Sentiment','Sentiment_Magnitude'], title='Sentiment Analysis Pie Chart')
fig.show()
