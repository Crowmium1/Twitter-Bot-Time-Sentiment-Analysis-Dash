import dash
import dash.testing
from dash import html 
import unittest
from flask import Flask
from module import Dashboard
from main import dataframe
import pandas as pd


server = Flask(__name__)
app = dash.Dash(__name__, server=server)
df = pd.DataFrame(dataframe)  # replace with your actual data
dashboard = Dashboard(app, df)  # Create an instance of your Dashboard class


class TestDashboard(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config.suppress_callback_exceptions = True
        self.app.layout = html.Div([dashboard.layout])
        self.client = server.test_client()

    def test_layout(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_datatable(self):
        response = self.client.get('/')
        self.assertIn(b'datatable', response.data)

    def test_pagination_controls(self):
        response = self.client.get('/')
        self.assertIn(b'page-current', response.data)
        self.assertIn(b'page-size', response.data)

    def test_sentiment_histogram(self):
        response = self.client.get('/')
        self.assertIn('sentiment-histogram', response.data.decode('utf-8'))

    def test_export_button(self):
        response = self.client.get('/')
        self.assertIn(b'export-button', response.data)
        
    def test_datatable_data(self):
        # Define the expected data
        expected_data = [
            {'Text': 'Hello world!', 'Sentiment': 'Positive', 'Sentiment_Magnitude': 0.5},
            {'Text': 'Goodbye world!', 'Sentiment': 'Negative', 'Sentiment_Magnitude': -0.5},
            # Add more rows as needed
        ]

if __name__ == '__main__':
    unittest.main()