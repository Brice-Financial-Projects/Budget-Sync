"""Weather routes."""
from flask import Blueprint, render_template, request, flash
from flask_login import login_required
from ..weather.weather_service import Weather
from ..weather.forms import WeatherForm

weather_bp = Blueprint('weather', __name__, template_folder='templates')

@weather_bp.route('/weather', methods=['GET', 'POST'])
@login_required
def weather_form():
    """Renders the weather form and displays weather results if available."""
    form = WeatherForm()
    
    if form.validate_on_submit():
        city = form.city.data.lower()
        state = form.state.data.upper() if form.state.data else ''
        country = form.country.data.upper()

        try:
            # Create a Weather object
            weather = Weather(city, state, country)

            # Get the latitude and longitude
            lat_lon = weather.get_lat_lon()

            if lat_lon:
                lat, lon = lat_lon
                # Fetch weather data
                weather_data = weather.get_weather(lat, lon)

                if weather_data:
                    # Get radar map URL if available
                    radar_url = weather.get_radar_map(lat, lon)
                    
                    # Pass weather data to the template
                    return render_template('weather/../templates/weather/weather_form.html',
                                           form=form,
                                           weather_data=weather_data,
                                           city=city,
                                           state=state,
                                           country=country,
                                           radar_url=radar_url)
                else:
                    flash("Weather data not found.", "error")
            else:
                flash("Location not found.", "error")
        except ValueError as e:
            flash(str(e), "error")
        except (ConnectionError, TimeoutError) as e:
            flash(f"Network error: {str(e)}", "error")

    # For GET requests or if form validation fails, render the form
    return render_template('weather/../templates/weather/weather_form.html', form=form)