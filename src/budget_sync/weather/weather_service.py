"""Weather service for handling API calls."""
import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Weather:
    """
    Class that uses an API call to collect weather data based on user input of
    City, State Code, and Country Code (e.g., US, GB, etc.)
    """

    def __init__(self, city_name_param, state_code_param, country_code):
        self._api_key = os.getenv('OPENWEATHER_API_KEY')
        self.base_geocode_url = 'http://api.openweathermap.org/geo/1.0/direct'
        self.base_weather_url = 'https://api.openweathermap.org/data/2.5/weather'
        self.base_radar_url = 'http://api.openweathermap.org/data/3.0/onecall'
        self.city_name = city_name_param
        self.state_code = state_code_param
        self.country_code = country_code

        if not self._api_key:
            raise ValueError("OpenWeather API key not found. Please set the OPENWEATHER_API_KEY in the .env file")

    def get_lat_lon(self):
        """
        Retrieve the latitude and longitude for a specified location.

        Returns:
            tuple: A tuple containing the latitude and longitude as floats,
                e.g., (37.7749, -122.4194).
            None: If the location data is unavailable or an error occurs.
        """
        params = {
            'q': f'{self.city_name},{self.state_code},{self.country_code}',
            'limit': 1,
            'appid': self._api_key
        }

        try:
            response = requests.get(self.base_geocode_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data:
                latitude = float(data[0]['lat'])
                longitude = float(data[0]['lon'])
                return latitude, longitude
            else:
                print("No location data found.")
                return None
        except requests.RequestException as e:
            print(f"Error fetching latitude and longitude data: {e}")
            return None

    def get_weather(self, latitude, longitude):
        """
        Fetch the current weather data for a specified location.

        Args:
            latitude (float): The latitude of the location.
            longitude (float): The longitude of the location.

        Returns:
            dict: A dictionary containing the weather data if successful.
            None: If an error occurs during the API request.
        """
        params = {
            'lat': latitude,
            'lon': longitude,
            'appid': self._api_key,
            'units': 'imperial'
        }

        try:
            response = requests.get(self.base_weather_url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
        except ValueError as val_err:
            print(f"Value error occurred: {val_err}")

        return None

    def get_radar_map(self, latitude, longitude):
        """
        Fetches the radar map URL for the specified latitude and longitude.

        Args:
            latitude (float): Latitude of the location.
            longitude (float): Longitude of the location.

        Returns:
            str: URL of the radar map.
        """
        params = {
            'lat': latitude,
            'lon': longitude,
            'appid': self._api_key,
            'zoom': 10,
            'overlay': 'precipitation_new'
        }

        try:
            radar_response = requests.get(self.base_radar_url, params=params, timeout=10)
            radar_response.raise_for_status()
            radar_data = radar_response.json()
            return radar_data.get('radar_url')
        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred while fetching radar map: {http_err}")
        except requests.exceptions.RequestException as req_err:
            print(f"Request error occurred while fetching radar map: {req_err}")
        except ValueError as val_err:
            print(f"Value error occurred while fetching radar map: {val_err}")

        return None 