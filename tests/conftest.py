"""Test configuration and fixtures."""
import pytest
from app import create_app, db
from app.models import User, Profile, Budget, ExpenseCategory, ExpenseTemplate, BudgetItem
from flask_login import current_user, login_user

@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['LOGIN_DISABLED'] = False  # Ensure login is required
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture
def test_user(app):
    """Create a test user."""
    user = User(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def test_profile(app, test_user):
    """Create a test profile."""
    profile = Profile(
        user_id=test_user.id,
        first_name='Test',
        last_name='User',
        state='CA',
        filing_status='single',
        income_type='Salary',
        pay_cycle='monthly',  # Added pay_cycle
        retirement_contribution_type='pretax',  # Added retirement_contribution_type
        num_dependents=0
    )
    db.session.add(profile)
    db.session.commit()
    return profile

@pytest.fixture
def test_budget(app, test_user, test_profile):  # Added test_profile dependency
    """Create a test budget."""
    budget = Budget(
        name='Test Budget',
        user_id=test_user.id,
        profile_id=test_profile.id  # Added profile_id reference
    )
    db.session.add(budget)
    db.session.commit()
    return budget

@pytest.fixture
def auth_client(client, test_user, app):
    """Create an authenticated test client."""
    # Login via Flask-Login
    with app.test_request_context():
        login_user(test_user)
        
    # Login via the client session
    with client.session_transaction() as session:
        session['user_id'] = test_user.id
        session['_fresh'] = True  # Mark the session as fresh
        
    # Perform an actual login request
    client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'testpass123',
        'remember_me': False
    })
    
    return client

@pytest.fixture
def test_expense_category(app):
    """Create a test expense category."""
    category = ExpenseCategory(
        name='Housing',
        description='Housing related expenses',
        priority=1
    )
    db.session.add(category)
    db.session.commit()
    return category

@pytest.fixture
def test_expense_template(app, test_expense_category):
    """Create a test expense template."""
    template = ExpenseTemplate(
        category_id=test_expense_category.id,
        name='Rent',
        description='Monthly rent payment',
        is_default=False,
        priority=1
    )
    db.session.add(template)
    db.session.commit()
    return template

@pytest.fixture
def test_budget_with_items(app, test_user, test_profile):
    """Create a test budget with budget items."""
    budget = Budget(
        name='Test Budget with Items',
        user_id=test_user.id,
        profile_id=test_profile.id,
        gross_income=5000.0,
        status='draft'
    )
    db.session.add(budget)
    db.session.flush()
    
    # Add some budget items
    items = [
        BudgetItem(
            budget_id=budget.id,
            category='Housing',
            name='Rent',
            minimum_payment=1000.0,
            preferred_payment=1200.0
        ),
        BudgetItem(
            budget_id=budget.id,
            category='Utilities',
            name='Electricity',
            minimum_payment=100.0,
            preferred_payment=120.0
        )
    ]
    for item in items:
        db.session.add(item)
    
    db.session.commit()
    return budget

@pytest.fixture
def test_db(app):
    """Set up a clean database for each test."""
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all() 