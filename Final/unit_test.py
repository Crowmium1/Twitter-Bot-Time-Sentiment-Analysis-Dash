import unittest
import main  # The name of the file you provided
from unittest.mock import patch, MagicMock

class TestTweet(unittest.TestCase):
    
    def test_clean(self):
        tweet = main.Tweet(text="Hello @user check out http://example.com #cool")
        tweet.clean()
        self.assertEqual(tweet.text, "Hello user check out example com cool")

    def test_analyze_sentiment(self):
        tweet = main.Tweet(text="I love it")
        tweet.analyze_sentiment()
        self.assertGreaterEqual(tweet.sentiment, 0)
    
    def test_analyze_sentiment_vader(self):
        result = main.Tweet.analyze_sentiment_vader("I love it")
        self.assertGreaterEqual(result, 0)
    

class TestTwitterAPI(unittest.TestCase):

    @patch("main.requests.post")
    def test_get_bearer_token(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'access_token': 'token'}
        mock_post.return_value = mock_response

        encoded_keys = "encoded_key"
        result = main.TwitterAPI.get_bearer_token(encoded_keys)
        self.assertEqual(result, 'token')


class TestDatabase(unittest.TestCase):

    @patch("main.sqlite3.connect")
    def test_store_in_database(self, mock_connect):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        tweet_data = [('Text1', 0.5, 0.5, 0.5)]
        main.Database.store_in_database(tweet_data)
        mock_cursor.executemany.assert_called()

# ... You can add more tests for other methods and classes

if __name__ == "__main__":
    unittest.main()
