'''Methodology which can be used in the next project for simplicity'''
# # Filename: functional_helpers.py
# import base64
# import os
# import requests

# # Load environment variables
# api_key = os.getenv('Key_Twitter')
# api_secret = os.getenv('Secret_Key_Twitter')

# # Creating functional helpers
# def functional_helpers():
#     """Returns a tuple of functions that can be used to encode API keys, get the bearer token, 
#     and search tweets."""

#     def _encode_api_keys(_api_key, _api_secret):
#         api_key_secret = f'{_api_key}:{_api_secret}'
#         return base64.b64encode(api_key_secret.encode('utf-8')).decode('utf-8')

#     def _get_bearer_token(_encoded_keys):
#         url = 'https://api.twitter.com/oauth2/token'
#         headers = {
#             'Authorization': f'Basic {_encoded_keys}',
#             'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
#         }
#         data = {'grant_type': 'client_credentials'}
#         response = requests.post(url, headers=headers, data=data, timeout=10)
#         return response.json().get('access_token') if response.status_code == 200 else None

#     def _search_tweets(_bearer_token, query, max_tweets):
#         url = f'https://api.twitter.com/2/tweets/search/recent?query={query}&max_results={max_tweets}'
#         headers = {'Authorization': f'Bearer {_bearer_token}'}
#         response = requests.get(url, headers=headers, timeout=10)
#         return [data_item.get('text', '') for data_item in response.json().get('data', [])] if response.status_code == 200 else []

#     return _encode_api_keys, _get_bearer_token, _search_tweets

# # Use them like this when you need them:
# encode, bearer, search = functional_helpers()
# encoded_keys = encode(api_key, api_secret)
# bearer_token = bearer(encoded_keys)
# raw_tweets = search(bearer_token, 'covid', 10)


'''Code which was used during the development stages'''
# # Load environment variables
# api_key = os.getenv('Key_Twitter')
# api_secret = os.getenv('Secret_Key_Twitter')

# # Get the Bearer Token
# encoded_keys = TwitterAPI.encode_api_keys(api_key, api_secret)
# bearer_token = TwitterAPI.get_bearer_token(encoded_keys)

# if not bearer_token:
#     print('Error: Failed to obtain Bearer Token.')
#     exit()

# # Query Parameters
# query = 'football'
# max_tweets = 10

# # Search tweets and process them
# raw_tweets = TwitterAPI.search_tweets(bearer_token, query, max_tweets)
# tweets = [Tweet(text=t) for t in raw_tweets]
# for tweet in tweets:
#     tweet.clean()
#     tweet.analyze_sentiment()
#     tweet.sentiment_vader = Tweet.analyze_sentiment_vader(tweet.text)

# # Extract data for storage
# sentiment_results = [
#     (t.text, t.sentiment, t.sentiment_magnitude, t.sentiment_vader) for t in tweets]
# columns = ['Text', 'Sentiment', 'Sentiment_Magnitude', 'Sentiment_VADER']
# sentiment_df = pd.DataFrame(sentiment_results, columns=columns)

# # Set up app layout using the correct config
# config = DashboardConfig(default_column=sentiment_df.columns[1], page_size=10, max_length=len(sentiment_df))
# app.layout = generate_layout(config)

# # Display records
# Database.show_all_records('tweets.db')

# In debug mode, the Flask server runs in a reloader, meaning it essentially starts your app twice:
# once to run it, and once to monitor for changes to restart the server when any of your files change.

# if __name__ == '__main__':
#     # This ensures the code only runs once and not in reloader mode preventing the duplicate storing.
#     if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
#         Database.clear_table('tweets')
#         Database.store_in_database(sentiment_results)
#         print(
#             f'Successfully stored {len(sentiment_results)} tweets in the database.')

#     app.run_server(debug=True)
