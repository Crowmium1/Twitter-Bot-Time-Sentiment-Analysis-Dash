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

# Load environment variables
api_key = os.getenv('Key_Twitter')
api_secret = os.getenv('Secret_Key_Twitter')
client_id = os.getenv('Client_ID')
client_secret = os.getenv('Client_Secret')
access_token = os.getenv('Token')
access_secret = os.getenv('Secret_Token')

class MyApp:
    def __init__(self, app):
        self.app = app
        self.layout = html.Div([
            html.Div([
                html.H1('Twitter Sentiment Analysis',
                        style={'text-align': 'center'}),
                html.H5('Analyze the sentiment of tweets about a company',
                        style={'text-align': 'center'}),
                html.Div([
                    html.Div([
                        html.Label('Enter a company name'),
                        dcc.Input(id='company-name', type='text',
                                  value='Apple', style={'width': '100%'})
                    ], style={'width': '48%', 'display': 'inline-block'}),
                    html.Div([
                        html.Label('Enter a date'),
                        dcc.Input(id='date', type='date',
                                  value='2021-01-01', style={'width': '100%'})
                    ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
                ], style={'padding': '20px 0'}),
                html.Div([
                    html.Button('Analyze', id='analyze-button',
                                n_clicks=0, style={'width': '100%'})
                ], style={'padding': '20px 0'})
            ])
        ])


class TwitterAPI:
    def __init__(self, api_key, api_secret, bearer_token, query, max_tweets):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base64_encoded_key = self.encode_api_keys()

        self.bearer_token = bearer_token
        self.query = query
        self.max_tweets = max_tweets
        self.data = self.search_tweets()

    def encode_api_keys(self):
        api_key_secret = f'{self.api_key}:{self.api_secret}'
        return base64.b64encode(api_key_secret.encode('utf-8')).decode('utf-8')

    def get_bearer_token(self):
        url = 'https://api.twitter.com/oauth2/token'
        headers = {
            'Authorization': f'Basic {self.base64_encoded_key}',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
        }
        data = {'grant_type': 'client_credentials'}

        response = requests.post(url, headers=headers, data=data)

        if response.status_code == 200:
            return response.json()['access_token']
        else:
            print(f'Error getting Bearer Token: {response.status_code}')
            return None

    def search_tweets(self, bearer_token, query, max_tweets):
        url = f'https://api.twitter.com/2/tweets/search/recent?query={self.query}&max_results={self.max_tweets}'
        headers = {
            'Authorization': f'Bearer {self.bearer_token}'
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(f'Error searching tweets: {response.status_code}')
            return None


class Actions:
    # Function to clean the text of a single tweet
    def clean_tweet_text(self, text):
        cleaned_text = re.sub(
            r'http\S+|@\w+|#\w+|[^\w\s]|(\s+)', '', text).strip()
        return cleaned_text

    # Function for performing sentiment analysis on dataframe
    def perform_sentiment_analysis(self, cleaned_data):
        sentiment_data = cleaned_data()
        sentiment_data['Sentiment'] = sentiment_data['Text'].apply(
            lambda text: TextBlob(text).sentiment.polarity)
        sentiment_data['Sentiment_Magnitude'] = sentiment_data['Text'].apply(
            lambda text: TextBlob(text).sentiment.subjectivity)
        return sentiment_data


class Database:
    def __init__(self, api, query, max_tweets):
        self.api = api
        self.query = query
        self.max_tweets = max_tweets
        self.search_recent_tweets = self.search_and_store_tweets()

    # Function to search for tweets and store them in a Database
    def search_and_store_tweets(self, api, query, max_tweets=10):

        # Connect to the SQLite database
        conn = sqlite3.connect('tweets.db')
        cursor = conn.cursor()

        # Create a table to store tweet data if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tweets (
                text TEXT,
            )
        ''')

        # Search for tweets and store them in the database
        tweet_count = 0
        for tweet in tweepy.Cursor(api.search_recent_tweets, q=query, max_results=max_tweets).items(max_tweets):
            tweet_data = (
                tweet.text,
            )
            cursor.execute('INSERT INTO tweets VALUES (?)', tweet_data)
            tweet_count += 1

        # Commit changes and close the database connection
        conn.commit()
        conn.close()

        return tweet_count

class Dashboard:
    def __init__(self, app, dataframe):
        self.app = dash.Dash(__name__)
        self.layout = html.Div([
            html.H1('Twitter Sentiment Analysis for Lies of People',
                    style={'text-align': 'center'}),

            # DataTable with pagination
            dash_table.DataTable(
                id='datatable',
                columns=[
                    {'name': 'Text', 'id': 'Text'},
                    {'name': 'Sentiment', 'id': 'Sentiment'},
                    {'name': 'Sentiment_Magnitude', 'id': 'Sentiment_Magnitude'}
                ],
                page_size=10,  # Number of rows per page
            ),

            # Pagination controls
            dcc.Input(id='page-current', type='number',
                      placeholder='Current Page', value=0),
            dcc.Input(id='page-size', type='number',
                      placeholder='Page Size', value=10),

            # Button to show/hide the graph
            html.Button('Show Sentiment Histogram', id='show-graph-button'),

            # Graph to display the sentiment analysis histogram
            dcc.Graph(
                id='sentiment-histogram',
                # Optional: Hide the interactive mode bar
                config={'displayModeBar': False},
                style={'display': 'none'},  # Initially hidden
            ),

            # Export button
            html.A('Export Sentiment Analysis to CSV', id='export-button',
                   href='', download='sentiment_analysis.csv'),

            # Button to update the database
            html.Button('Update Database', id='update-database-button'),
        ])

        self.app.layout = self.layout

    # Function to export data to a CSV file
    @app.callback(
        Output('export-button', 'href'),
        Input('export-button', 'n_clicks')
    )
    # Function to export data to a CSV file
    def export_data_to_csv(self, n_clicks):
        if n_clicks is not None:
            # Connect to the database and retrieve the entire tweet data
            conn = sqlite3.connect('tweets.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tweets')

            data = cursor.fetchall()
            conn.close()

            # Convert the retrieved data to a DataFrame for export
            columns = ['Text']
            df = pd.DataFrame(data, columns=columns)

            # Create a CSV file and return its path for download
            csv_path = 'sentiment_analysis.csv'
            df.to_csv(csv_path, index=False)
            return csv_path

    # Function to toggle the visibility of the graph
    @app.callback(
        Output('sentiment-histogram', 'style'),
        Input('show-graph-button', 'n_clicks')
    )
    def toggle_graph_visibility(self, n_clicks):
        if n_clicks is None:
            return {'display': 'none'}  # Initially hidden
        else:
            return {'display': 'block'}  # Visible on button click

    # Function to update the dashboard with new data based on page and page size
    @app.callback(
        [Output("datatable", "data"), Output("sentiment-histogram", "figure")],
        [Input("datatable", "page_current"), Input('page-size', 'value')]
    )

    # Function to update the dashboard with new data based on page and page size
    def update_table(self, page_current, page_size):
        # Connect to the database and retrieve the tweet data with pagination
        conn = sqlite3.connect('tweets.db')
        cursor = conn.cursor()
        offset = page_current * page_size
        query = f'SELECT * FROM tweets LIMIT {page_size} OFFSET {offset}'
        cursor.execute(query)
        data = cursor.fetchall()
        conn.close()

        # Convert the paginated data to a DataFrame
        columns = ['Text', 'Sentiment', 'Sentiment_Magnitude']
        paginated_data = [dict(zip(columns, row)) for row in data]
        df = pd.DataFrame(paginated_data)

        # Clean the tweet text and perform sentiment analysis on the tweet text
        cleaned_data = Actions.clean_tweet_text(df.to_dict('records'))
        result = Actions.perform_sentiment_analysis(cleaned_data)

        # Create a histogram of the sentiment analysis
        fig = go.Figure(
            data=[go.Histogram(x=result['Sentiment'], y=result['Sentiment_Magnitude'])])
        fig.update_layout(title_text='Sentiment Analysis Histogram')

        # Return the cleaned tweet data and the sentiment analysis histogram
        return result, fig


# Create a Dash instance and set the layout
app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True
app.layout = html.Div([
    MyApp(app).layout
    ])

# Run the server
if __name__ == '__main__':
    app.run_server(debug=True)
