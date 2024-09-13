import os
import base64
import re
import sqlite3
from dataclasses import dataclass
import pandas as pd
import requests
from textblob import TextBlob
from textblob.sentiments import PatternAnalyzer
import dash
from dash import Dash, html, dcc, Input, Output, State, dash_table
import plotly.express as px
import dash_bootstrap_components as dbc
from nltk.sentiment.vader import SentimentIntensityAnalyzer

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


@dataclass
class Tweet:
    '''Class for storing a single tweet'''
    text: str
    sentiment: float = 0.0
    sentiment_magnitude: float = 0.0
    sentiment_vader: float = 0.0

    def clean(self):
        self.text = re.sub(
            r'http\S+|@\w+|#\w+|[^\w\s]|(\s+)', ' ', self.text).strip()

    def analyze_sentiment(self):
        blob = TextBlob(self.text, analyzer=PatternAnalyzer())
        self.sentiment, self.sentiment_magnitude = blob.sentiment.polarity, blob.sentiment.subjectivity

    @staticmethod
    def analyze_sentiment_vader(text):
        analyzer = SentimentIntensityAnalyzer()
        return analyzer.polarity_scores(text)['compound']


class TwitterAPI:
    '''Class for interacting with the Twitter API'''

    @staticmethod
    def get_tweet_sentiments(tweets):
        '''Get sentiments of tweets'''
        tweet_objects = [Tweet(tweet) for tweet in tweets]
        for tweet in tweet_objects:
            tweet.clean()
            tweet.analyze_sentiment()
            tweet.sentiment_vader = Tweet.analyze_sentiment_vader(tweet.text)
        tweet_data = [(tweet.text, tweet.sentiment, tweet.sentiment_magnitude, tweet.sentiment_vader)
                      for tweet in tweet_objects]
        return tweet_data

    @staticmethod
    def encode_api_keys(api_key, api_secret):
        '''Encode API keys for use in the Authorization header'''
        api_key_secret = f'{api_key}:{api_secret}'
        return base64.b64encode(api_key_secret.encode('utf-8')).decode('utf-8')

    @staticmethod
    def get_bearer_token(encoded_keys):
        '''Get bearer token from Twitter API'''
        url = 'https://api.twitter.com/oauth2/token'
        headers = {
            'Authorization': f'Basic {encoded_keys}',
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
        }
        data = {'grant_type': 'client_credentials'}
        response = requests.post(url, headers=headers, data=data)
        return response.json().get('access_token') if response.status_code == 200 else None

    @staticmethod
    def search_tweets(bearer_token, query, max_tweets):
        '''Get tweets from Twitter API'''
        url = f'https://api.twitter.com/2/tweets/search/recent?query={query}&max_results={max_tweets}'
        headers = {'Authorization': f'Bearer {bearer_token}'}
        response = requests.get(url, headers=headers)
        return [data_item.get('text', '') for data_item in response.json().get('data', [])] if response.status_code == 200 else []


class Database:
    '''Class for interacting with the database'''

    @staticmethod
    def get_table_data(db_path, table_name):
        '''Get data from the database'''
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f'SELECT * FROM {table_name}')
            rows = cursor.fetchall()
            return rows

    @staticmethod
    def store_in_database(tweet_data):
        '''Store data in the database'''
        with sqlite3.connect('tweets.db') as conn:
            cursor = conn.cursor()
            cursor.executemany(
                'INSERT INTO tweets (Text, Sentiment, Sentiment_Magnitude, Sentiment_VADER) VALUES (?, ?, ?, ?)', tweet_data)

    @staticmethod
    def update_records(column_name, new_value, condition_column, condition_value):
        '''Update records in the database'''
        with sqlite3.connect('tweets.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                f'UPDATE tweets SET {column_name} = ? WHERE {condition_column} = ?', (new_value, condition_value))

    @staticmethod
    def clear_table(table_name):
        '''Clear the table'''
        # with statement is used to ensure that the changes are committed to the database, and it doesn't need closing.
        with sqlite3.connect('tweets.db') as conn:
            cursor = conn.cursor()
            cursor.execute(f'DELETE FROM {table_name};')

    @staticmethod
    def show_all_records(db_path):
        '''Show all records in the database'''
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            for table in tables:
                table_name = table[0]
                print(f"Records from table {table_name}:")
                cursor.execute(f"SELECT * FROM {table_name};")
                records = cursor.fetchall()
                for record in records:
                    print(record)
                print("\n")


@dataclass
class DashboardConfig:
    '''Dataclass for configuring the dashboard'''
    default_column: str
    page_size: int
    max_length: int


def generate_layout(config: DashboardConfig):
    '''Returns the layout for the dashboard'''
    return html.Div(children=[
        html.H1(children='Sentiment Analysis Dashboard'),
        # Add input fields here
        html.Div([
            html.Label("Search Phrase:"),
            dcc.Input(id='input-query', type='text', value='',
                      placeholder='Enter search phrase'),
            html.Label("Number of Tweets (Max 100):"),
            dcc.Input(id='input-max-tweets', type='number',
                      value=10, min=1, max=100),
            dbc.Button("Update Database", id="update-database-button",
                       color="primary", n_clicks=0),
        ], style={'margin-bottom': '20px'}),

        dcc.Dropdown(
            id='column-selector',
            options=[{'label': col, 'value': col}
                     for col in sentiment_df.columns[1:]],
            value=config.default_column,
            multi=False
        ),
        dcc.RangeSlider(
            id='pagination-slider',
            min=0,
            max=config.max_length,
            step=1,
            marks={i: str(i) for i in range(0, config.max_length, 10)},
            value=[0, config.page_size]
        ),
        dcc.Graph(id='sentiment-histogram'),

        dcc.Download(id="download-dataframe-csv"),

        dbc.Button("Export Data", id="export-button",
                   color="primary", className="mr-2"),
        dash_table.DataTable(
            id='sentiment-table',
            style_table={'height': '400px', 'overflowY': 'auto'},
            page_size=config.page_size
        )
    ])


# def generate_table(dataframe, page_size, current_page):
#     start = current_page * page_size
#     end = start + page_size
#     return dash_table.DataTable(
#         id='sentiment-table',
#         columns=[{"name": i, "id": i} for i in dataframe.columns],
#         data=dataframe.iloc[start:end].to_dict('records'),
#         style_table={'height': '400px', 'overflowY': 'auto'},
#         page_size=page_size,
#         page_current=current_page
#     )

# Update Results Callback


@app.callback(
    [Output('sentiment-histogram', 'figure'),
     Output('sentiment-table', 'data'),
     Output('sentiment-table', 'page_size')],
    [Input('update-database-button', 'n_clicks')],
    [State('input-query', 'value'),
     State('input-max-tweets', 'value')]
)

# Define the update results callback function
def update_results(n_clicks, input_query, input_max_tweets):
    '''Returns the histogram and table data based on the user input'''
    print("Update Results - n_clicks value:", n_clicks)
    if n_clicks and n_clicks > 0:
        # Get the Bearer Token inside the callback
        api_key = os.getenv('Key_Twitter')
        api_secret = os.getenv('Secret_Key_Twitter')
        encoded_keys = TwitterAPI.encode_api_keys(api_key, api_secret)
        bearer_token = TwitterAPI.get_bearer_token(encoded_keys)

        if not bearer_token:
            print('Error: Failed to obtain Bearer Token.')
            # Use this to stop the callback if there's an error
            raise dash.exceptions.PreventUpdate

        # Search tweets and process them
        raw_tweets = TwitterAPI.search_tweets(
            bearer_token, input_query, input_max_tweets)
        print("Number of tweets fetched:", len(raw_tweets))

        tweets = [Tweet(text=t) for t in raw_tweets]
        for tweet in tweets:
            tweet.clean()
            tweet.analyze_sentiment()
            tweet.sentiment_vader = Tweet.analyze_sentiment_vader(tweet.text)

        # Extract data for storage and update database
        sentiment_results = [
            (t.text, t.sentiment, t.sentiment_magnitude, t.sentiment_vader) for t in tweets]
        columns = ['Text', 'Sentiment',
                   'Sentiment_Magnitude', 'Sentiment_VADER']
        global sentiment_df
        print(sentiment_df.head())
        sentiment_df = pd.DataFrame(sentiment_results, columns=columns)

        # Store in the database
        Database.clear_table('tweets')
        Database.store_in_database(sentiment_results)

        # Prepare the histogram and table
        start_idx, end_idx = 0, min(10, len(sentiment_df))
        fig = px.histogram(sentiment_df.iloc[start_idx:end_idx], x=sentiment_df.columns[1],
                           nbins=10, title=f"Sentiment Analysis Histogram ({sentiment_df.columns[1]})")
        table_data = sentiment_df.iloc[start_idx:end_idx].to_dict('records')
        return fig, table_data, min(10, len(sentiment_df))
    raise dash.exceptions.PreventUpdate

# Export Data Callback
@app.callback(
    Output("download-dataframe-csv", "data"),
    [Input("export-button", "n_clicks")]
)

# Define the export data callback function
def export_data(n_clicks_export):
    '''Returns the data in the table as a downloadable csv file'''
    if n_clicks_export and n_clicks_export > 0:
        csv_string = sentiment_df.to_csv(index=False, encoding='utf-8')
        return {
            "content": csv_string,
            "filename": "sentiment_data.csv",
            "type": "text/csv"
        }
    return dash.no_update


sentiment_df = pd.DataFrame(columns=['Text', 'Sentiment', 'Sentiment_Magnitude', 'Sentiment_VADER'])
config = DashboardConfig(default_column='Sentiment', page_size=10, max_length=100)
app.layout = generate_layout(config)

if __name__ == '__main__':
    app.run_server(debug=True)