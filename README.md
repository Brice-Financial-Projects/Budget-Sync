# Finance Budget Application

A comprehensive budgeting application that helps users manage their finances, track income sources, and plan expenses while considering tax implications.

## 📊 Project Status

| Branch | CI Status | Coverage | Python | Last Commit | License |
|--------|-----------|----------|--------|-------------|----------|
| **main** | [![CI/CD](https://github.com/Brice-Financial-Projects/Budget-Sync/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Brice-Financial-Projects/Budget-Sync/actions/workflows/ci.yml) | ![Coverage](https://img.shields.io/badge/Coverage-Auto--Generated-blue) | ![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python) | ![Last Commit](https://img.shields.io/github/last-commit/Brice-Financial-Projects/Budget-Sync/main) | ![License](https://img.shields.io/github/license/Brice-Financial-Projects/Budget-Sync) |
| **dev**  | [![CI/CD](https://github.com/Brice-Financial-Projects/Budget-Sync/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/Brice-Financial-Projects/Budget-Sync/actions/workflows/ci.yml) | ![Coverage](https://img.shields.io/badge/Coverage-Auto--Generated-blue) | ![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python) | ![Last Commit](https://img.shields.io/github/last-commit/Brice-Financial-Projects/Budget-Sync/dev) | ![License](https://img.shields.io/github/license/Brice-Financial-Projects/Budget-Sync) |

## Features

- **User Management**
  - Secure user registration and authentication
  - Profile management with personal and financial information
  - Role-based access control

- **Profile Management**
  - Personal information tracking
  - Tax-related details (filing status, dependents)
  - Employment information
  - Pre-tax benefits and deductions

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
cd finance-budget-budget_sync
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

```
finance-budget-app/
├── app/
│   ├── auth/          # Authentication routes and forms
│   ├── budget/        # Budget management functionality
│   ├── config/        # Configuration settings
│   ├── docs/          # Documentation files
│   ├── models/        # Database models
│   ├── profile/       # Profile management
│   ├── static/        # Static files (CSS, JS)
│   ├── templates/     # HTML templates
│   └── weather/       # Weather integration
├── docs/             # Project documentation
├── migrations/       # Database migrations
├── tests/           # Test files
├── .env             # Environment variables
├── .gitignore       # Git ignore file
├── requirements.txt  # Python dependencies
└── run.py           # Application entry point
```

## Database Schema

The application uses a relational database with the following main models:
- Users
- Profiles
- Budgets
- Budget Items
- Gross Income
- Other Income

For detailed schema information, see [Database Schema Documentation](docs/database_schema.md).

## Testing

Run the test suite:
```bash
pytest
```

## API Documentation

### Weather API
- Endpoint: `/weather/weather`
- Method: POST
- Parameters:
  - city: City name
  - state: State code (US)
  - country: Country code

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 👥 Contributors

Thanks to the following contributors for improving this project:

- **[Randall LaPoint Jr. ](https://github.com/Lokie-ree)** — Documentation improvements & project structure guidance

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenWeather API for weather data
- Bootstrap for UI components
- Flask community for excellent documentation
