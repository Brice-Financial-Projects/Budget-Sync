"""Test weather routes and functionality."""
import pytest
from unittest.mock import patch, MagicMock

def test_weather_page(auth_client):
    """Test weather page loads."""
    response = auth_client.get('/weather')
    assert response.status_code == 200
    assert b'Weather Information' in response.data

@patch('budget_sync.weather.weather_service.Weather')
def test_weather_search_success(mock_weather, auth_client):
    """Test successful weather search."""
    # Mock the weather service
    mock_instance = MagicMock()
    mock_instance.get_lat_lon.return_value = (37.7749, -122.4194)
    mock_instance.get_weather.return_value = {
        'main': {
            'temp': 72,
            'feels_like': 75,
            'humidity': 60,
            'pressure': 1015
        },
        'weather': [{'description': 'clear sky'}],
        'wind': {'speed': 5}
    }
    mock_weather.return_value = mock_instance

    response = auth_client.post('/weather', data={
        'city': 'San Francisco',
        'state': 'CA',
        'country': 'US'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'San Francisco' in response.data
    assert b'72' in response.data
    assert b'clear sky' in response.data

@patch('budget_sync.weather.weather_service.Weather')
def test_weather_search_error(mock_weather, auth_client):
    """Test weather search with invalid location."""
    # Mock the weather service to return None for location
    mock_instance = MagicMock()
    mock_instance.get_lat_lon.return_value = None
    mock_weather.return_value = mock_instance

    response = auth_client.post('/weather', data={
        'city': 'Invalid City',
        'state': 'XX',
        'country': 'US'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Location not found' in response.data

def test_weather_form_validation(auth_client):
    """Test weather form validation."""
    response = auth_client.post('/weather', data={
        'city': '',  # Empty city should fail validation
        'state': 'CAA',  # Invalid state code
        'country': 'USA'  # Invalid country code
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'City' in response.data
    assert b'State Code' in response.data
    assert b'Country Code' in response.data 