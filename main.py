import os
import pandas as pd
import sqlite3
import base64
import re
import requests
from textblob import TextBlob
from textblob.sentiments import PatternAnalyzer
from dash import Dash, html, dcc, Input, Output, State
import plotly.express as px
from dash import dash_table
import dash_bootstrap_components as dbc
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from dataclasses import dataclass

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

@dataclass
class Tweet:
    text: str
    sentiment: float = 0.0
    sentiment_magnitude: float = 0.0
    sentiment_vader: float = 0.0

    def clean(self):
        self.text = re.sub(r'http\S+|@\w+|#\w+|[^\w\s]|(\s+)', ' ', self.text).strip()

    def analyze_sentiment(self):
        blob = TextBlob(self.text, analyzer=PatternAnalyzer())
        self.sentiment, self.sentiment_magnitude = blob.sentiment.polarity, blob.sentiment.subjectivity

    @staticmethod
    def analyze_sentiment_vader(text):
        analyzer = SentimentIntensityAnalyzer()
        return analyzer.polarity_scores(text)['compound']


class TwitterAPI:

    @staticmethod
    def encode_api_keys(api_key, api_secret):
        api_key_secret = f'{api_key}:{api_secret}'
        return base64.b64encode(api_key_secret.encode('utf-8')).decode('utf-8')

    @staticmethod
    def get_bearer_token(encoded_keys):
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
        url = f'https://api.twitter.com/2/tweets/search/recent?query={query}&max_results={max_tweets}'
        headers = {'Authorization': f'Bearer {bearer_token}'}
        response = requests.get(url, headers=headers)
        return [data_item.get('text', '') for data_item in response.json().get('data', [])] if response.status_code == 200 else []


class Database:  

    @staticmethod
    def store_in_database(tweet_data):
        with sqlite3.connect('tweets.db') as conn:
            cursor = conn.cursor()
            cursor.executemany('INSERT INTO tweets (Text, Sentiment, Sentiment_Magnitude, Sentiment_VADER) VALUES (?, ?, ?, ?)', tweet_data)

    @staticmethod
    def update_records(column_name, new_value, condition_column, condition_value):
        with sqlite3.connect('tweets.db') as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE tweets SET {column_name} = ? WHERE {condition_column} = ?', (new_value, condition_value))

    @staticmethod
    def clear_table(table_name):
        with sqlite3.connect('tweets.db') as conn:  # with statement is used to ensure that the changes are committed to the database, and it doesn't need closing.
            cursor = conn.cursor()
            cursor.execute(f'DELETE FROM {table_name};')

    @staticmethod
    def show_all_records(db_path):
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            for table in tables:
                table_name = table[0]
                print(f"Records from table {table_name}:")
                cursor.execute(f"SELECT * FROM {table_name};")
                records = cursor.fetchall()
                for record in records:
                    print(record)
                print("\n")

# Define a Dataclass for organizing Dashboard configurations
@dataclass
class DashboardConfig:
    default_column: str
    page_size: int
    max_length: int

def generate_layout(config: DashboardConfig):
    return html.Div(children=[
        html.H1(children='Sentiment Analysis Dashboard'),
        dcc.Dropdown(
            id='column-selector',
            options=[{'label': col, 'value': col} for col in sentiment_df.columns[1:]],
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
        dbc.Button("Export Data", id="export-button", color="primary", className="mr-2"),
        dbc.Button("Update Database", id="update-database-button", color="danger"),
        dash_table.DataTable(
            id='sentiment-table',
            style_table={'height': '400px', 'overflowY': 'auto'},
            page_size=config.page_size
        )
    ])


@app.callback(
    [Output('sentiment-histogram', 'figure'), Output('sentiment-table', 'data'), Output('sentiment-table', 'page_size')],
    Input('column-selector', 'value'),
    Input('pagination-slider', 'value'),
    State('sentiment-table', 'page_current')
    )

def update_dashboard(selected_column, slider_value, current_page):
    start_idx, end_idx = slider_value
    paginated_df = sentiment_df.iloc[start_idx:end_idx]
    fig = px.histogram(paginated_df, x=selected_column, nbins=10, title=f"Sentiment Analysis Histogram ({selected_column})")
    table_data = paginated_df.to_dict('records')
    new_page_size = min(10, len(paginated_df))
    return fig, table_data, new_page_size


# Load environment variables
api_key = os.getenv('Key_Twitter')
api_secret = os.getenv('Secret_Key_Twitter')

# Get the Bearer Token
encoded_keys = TwitterAPI.encode_api_keys(api_key, api_secret)
bearer_token = TwitterAPI.get_bearer_token(encoded_keys)

if not bearer_token:
    print('Error: Failed to obtain Bearer Token.')
    exit()

# Query Parameters
query = 'football'
max_tweets = 10

# Search tweets and process them
raw_tweets = TwitterAPI.search_tweets(bearer_token, query, max_tweets)
tweets = [Tweet(text=t) for t in raw_tweets]
for tweet in tweets:
    tweet.clean()
    tweet.analyze_sentiment()
    tweet.sentiment_vader = Tweet.analyze_sentiment_vader(tweet.text)

# Extract data for storage
sentiment_results = [(t.text, t.sentiment, t.sentiment_magnitude, t.sentiment_vader) for t in tweets]
columns = ['Text', 'Sentiment', 'Sentiment_Magnitude', 'Sentiment_VADER']
sentiment_df = pd.DataFrame(sentiment_results, columns=columns) 

# Set up app layout using the correct config
config = DashboardConfig(default_column=sentiment_df.columns[1], page_size=10, max_length=len(sentiment_df))
app.layout = generate_layout(config)

# # Clear and Store in the database
# Database.clear_table('tweets') 
# Database.store_in_database(sentiment_results)
# print(f'Successfully stored {len(sentiment_results)} tweets in the database.')

# # Display records
# Database.show_all_records('tweets.db')

# # Run the server
# app.run_server(debug=True)


# In debug mode, the Flask server runs in a reloader, meaning it essentially starts your app twice: 
# once to run it, and once to monitor for changes to restart the server when any of your files change.

if __name__ == '__main__':
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":  # This ensures the code only runs once and not in reloader mode preventing the duplicate storing.
        Database.clear_table('tweets') 
        Database.store_in_database(sentiment_results)
        print(f'Successfully stored {len(sentiment_results)} tweets in the database.')
    
    app.run_server(debug=True)
