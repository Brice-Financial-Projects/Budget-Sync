# Financial Budget Application

A comprehensive budgeting application that helps users manage their finances, track income sources, and plan expenses while considering tax implications.

## Features

- **User Management**
  - Secure user registration and authentication
  - Profile management with personal and financial information
  - Role-based access control

- **Profile Management**
  - Personal information tracking
  - Tax-related details (filing status, dependents)
  - Employment information
  - Pre-tax benefits and deductions tracking

- **Budget Management**
  - Create and manage multiple budgets
  - Track different income sources
  - Categorize and manage expenses
  - Calculate tax implications
  - View budget summaries and reports

- **Weather Integration**
  - Check weather conditions by location
  - Plan outdoor activities accordingly

## Technology Stack

- **Backend**
  - Python 3.10+
  - Flask (Web Framework)
  - SQLAlchemy (ORM)
  - PostgreSQL (Database)
  - Redis (Session Management)
  - Flask-Login (Authentication)
  - Flask-WTF (Forms and CSRF Protection)

- **Frontend**
  - HTML5
  - CSS3
  - Bootstrap 5
  - JavaScript

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd financial-budget_sync
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables in `.env`:
```env
FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=your_secret_key
DATABASE_URL=postgresql+psycopg2://username:password@localhost:5432/budget_db
REDIS_URL=redis://localhost:6379/0
OPENWEATHER_API_KEY=your_api_key
```

5. Initialize the database:
```bash
flask db upgrade
```

6. Run the application:
```bash
flask run
```

## Project Structure

The application follows a modular structure based on Flask blueprints:

- **app/** - Main application package
  - **auth/** - Authentication functionality
  - **budget/** - Budget management features
  - **profile/** - User profile management
  - **weather/** - Weather integration
  - **static/** - Static assets (CSS, JS)
  - **templates/** - HTML templates
  - **models.py** - Database models
  - **forms.py** - Form definitions
  - **utils.py** - Utility functions

## Usage Guide

### Registration and Profile Setup

1. Register for an account using email and password
2. Create your profile with personal and tax information
3. Add employment details and pre-tax benefits

### Creating a Budget

1. Navigate to the dashboard and select "Create Budget"
2. Name your budget and select expense categories
3. Input minimum and preferred payment amounts for each category
4. Add income sources with amounts and frequencies
5. View your budget summary with tax implications

### Managing Budgets

1. View all budgets from the dashboard
2. Edit budgets to update information as needed
3. Delete budgets you no longer need
4. Compare budget details and track spending

### Weather Integration

1. Navigate to the Weather section
2. Enter city, state, and country information
3. View current weather conditions and radar maps

## Development Status

The application is currently in active development. Key components that have been implemented:

- ✅ User authentication system
- ✅ Profile management with tax information
- ✅ Budget creation and management
- ✅ Income tracking with multiple sources
- ✅ Tax calculation integration
- ✅ Weather API integration
- ✅ Responsive UI with Bootstrap

Upcoming features include:

- Data visualization enhancements
- Budget comparison tools
- Tax optimization recommendations
- Expanded weather forecasting
- Mobile application support

## API Documentation

The application includes internal APIs for accessing tax and budget information:

### Tax API Endpoints

1. Get Federal Tax Brackets
   ```
   GET /api/v1/tax/federal/<year>
   ```

2. Get State Tax Brackets
   ```
   GET /api/v1/tax/state/<state>/<year>
   ```

3. Get FICA Rates
   ```
   GET /api/v1/tax/fica/<year>
   ```

4. Calculate Taxes
   ```
   POST /api/v1/tax/calculate
   ```

5. Get Available Tax Years
   ```
   GET /api/v1/tax/years
   ```

### Weather API

The application integrates with OpenWeather API for weather data:

```
POST /weather/weather
```
Parameters:
- city: City name
- state: State code (US)
- country: Country code

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

Please ensure your code follows the project's coding standards and includes appropriate tests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenWeather API for weather data
- Bootstrap for UI components
- Flask community for excellent documentation
