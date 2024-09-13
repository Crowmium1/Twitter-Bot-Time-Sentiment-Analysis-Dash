import os
import sqlite3
import base64
import requests
from textblob import TextBlob
from dash import Dash
from module import Dashboard
import pandas as pd

# Initialize the Dash app
app = Dash(__name__)

# Load environment variables
api_key = os.getenv('Key_Twitter')

api_secret = os.getenv('Secret_Key_Twitter')

# Encode the API key and API secret key in base64 format
api_key_secret = f'{api_key}:{api_secret}'
base64_encoded_key = base64.b64encode(api_key_secret.encode('utf-8')).decode('utf-8')

# Define the URL to get the Bearer Token
url = 'https://api.twitter.com/oauth2/token'

# Define the headers with Authorization
headers = {
    'Authorization': f'Basic {base64_encoded_key}',
    'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
}

# Define the data for the POST request
data = {'grant_type': 'client_credentials'}

# Make the POST request to get the Bearer Token
response = requests.post(url, headers=headers, data=data)

# Parse the JSON response and extract the access token
bearer_token = response.json().get('access_token')

# Check if the Bearer Token was obtained successfully
if not bearer_token:
    print('Error: Failed to obtain Bearer Token.')
    exit()

# # DELETE
# conn = sqlite3.connect('tweets.db')
# # conn.close()
# db_file_path = 'tweets.db'

# if os.path.exists(db_file_path):
#     os.remove(db_file_path)
#     print(f'Database file has been deleted.')
# else:
#     print(f'Database file does not exist.')

# CREATE
conn = sqlite3.connect('tweets.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS tweets (
        Text TEXT,
        Sentiment REAL,
        Sentiment_Magnitude REAL
    )
''')
conn.commit()

# Query Parameters
query = 'data analysis'
max_tweets = 10

# Parameters
query = 'data analysis'
max_tweets = 10
url = f'https://api.twitter.com/2/tweets/search/recent?query={query}&max_results={max_tweets}'
headers = {
    'Authorization': f'Bearer {bearer_token}'
}

# # Create an instance of the TwitterSearch class with the required arguments
# search = TwitterSearch(bearer_token, query, max_tweets)

# Make the GET request
response = requests.get(url, headers=headers)

# Parse and print the response
if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f'Error: {response.status_code}')

# Parse the response JSON
if response.status_code == 200:
    data = response.json()
    tweets = [data_item.get('text', '') for data_item in data.get('data', [])]
else:
    print(f'Error: {response.status_code}')

# Create a DataFrame from the extracted tweets with Sentiment and Sentiment_Magnitude columns
df = pd.DataFrame({'text': tweets, 'Sentiment': 0.0, 'Sentiment_Magnitude': 0.0})

print(df)

# Store, clean, and analyze tweets to the dataframe and the database
tweet_count = 0
for data, row in df.iterrows():
    
    # Clean tweet text
    blob = TextBlob(row['text'])
    cleaned_text = blob.correct().string

    # Perform sentiment analysis
    blob = TextBlob(cleaned_text)
    sentiment = blob.sentiment.polarity
    sentiment_magnitude = blob.sentiment.subjectivity

    # Update DataFrame with sentiment scores
    df.at[data, 'Sentiment'] = sentiment
    df.at[data, 'Sentiment_Magnitude'] = sentiment_magnitude

    # Update the database
    tweet_data = (cleaned_text, sentiment, sentiment_magnitude)
    cursor.execute('INSERT INTO tweets (Text, Sentiment, Sentiment_Magnitude) VALUES (?, ?, ?)', tweet_data)
    tweet_count += 1

    if tweet_count >= max_tweets:
        break

# Commit and close the database connection
conn.commit()
conn.close()

if tweet_count > 0:
    print(f'Successfully stored {tweet_count} tweets in the database.')
else:
    print('No tweets found or stored.')

# Display the DataFrame containing the stored tweets
dataframe = df
print(dataframe)

# Statistics about the dataframe
dataframe.head()
dataframe.info()
dataframe.describe()
dataframe['Sentiment'].value_counts()
dataframe['Sentiment_Magnitude'].value_counts()

# # Run the Dash app
if __name__ == '__main__':
    dashboard = Dashboard(app, dataframe)
    app.run_server(debug=True)