"""Integration tests for weather API interactions."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import pytest
from unittest.mock import patch, MagicMock
from budget_sync.weather.weather_service import Weather

@pytest.fixture
def weather_service():
    """Create a weather service instance for testing."""
    return Weather(city_name_param="Orlando", state_code_param="FL", country_code="US")


def test_get_weather_for_location(weather_service):
    """
    GIVEN a Weather service
    WHEN requesting weather data for a valid location
    THEN check that the API calls are made correctly and data is returned
    """
    with patch('budget_sync.weather.weather_service.requests.get') as mock_get:
        # Mock the geocoding API response
        geo_response = MagicMock()
        geo_response.status_code = 200
        geo_response.json.return_value = [{
            'lat': 40.7128,
            'lon': -74.0060,
            'name': 'New York',
            'state': 'NY',
            'country': 'US'
        }]

        # Mock the weather API response
        weather_response = MagicMock()
        weather_response.status_code = 200
        weather_response.json.return_value = {
            'weather': [{'description': 'clear sky'}],
            'main': {'temp': 293.15},  # 20°C
            'wind': {'speed': 5}
        }

        # Configure mock to return different responses for each API call
        mock_get.side_effect = [geo_response, weather_response]

        # Test the complete API flow
        weather_data = weather_service.get_weather_for_location('New York', 'NY', 'US')
        
        # Verify the API was called correctly
        assert mock_get.call_count == 2
        assert 'geo' in mock_get.call_args_list[0][0][0]  # First call should be to geocoding API
        assert 'weather' in mock_get.call_args_list[1][0][0]  # Second call should be to weather API
        assert weather_data == weather_response.json.return_value

def test_api_error_handling(weather_service):
    """
    GIVEN a Weather service
    WHEN the API returns an error
    THEN check that errors are handled gracefully
    """
    with patch('budget_sync.weather.weather_service.requests.get') as mock_get:
        # Mock API error response
        error_response = MagicMock()
        error_response.status_code = 404
        mock_get.return_value = error_response

        # Test error handling
        result = weather_service.get_weather_for_location('Invalid City', 'XX', 'US')
        assert result is None

def test_api_timeout_handling(weather_service):
    """
    GIVEN a Weather service
    WHEN the API request times out
    THEN check that the timeout is handled gracefully
    """
    with patch('budget_sync.weather.weather_service.requests.get') as mock_get:
        # Mock timeout exception
        mock_get.side_effect = TimeoutError()

        # Test timeout handling
        result = weather_service.get_weather_for_location('New York', 'NY', 'US')
        assert result is None 
