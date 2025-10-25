"""backend/budget_sync/models.py"""

from budget_sync import bcrypt, db
from sqlalchemy.sql import func
from datetime import datetime, timedelta
import secrets


# -------------------- User Model --------------------
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    # Relationships
    profile = db.relationship("Profile", back_populates="user", uselist=False)
    budgets = db.relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    password_reset_tokens = db.relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan")

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        # Hash the password using bcrypt
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    # Flask-Login required properties:
    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"<User {self.username}, {self.email}>"


# -------------------- Password Reset Token Model --------------------
class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)

    # Relationships
    user = db.relationship("User", back_populates="password_reset_tokens")

    def __init__(self, user_id, expiration_hours=1):
        self.user_id = user_id
        self.token = secrets.token_urlsafe(32)
        self.expires_at = datetime.utcnow() + timedelta(hours=expiration_hours)

    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    def __repr__(self):
        return f"<PasswordResetToken {self.token[:8]}... for user {self.user_id}>"


# -------------------- Profile Model --------------------
class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    
    # Personal Information
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date)
    is_blind = db.Column(db.Boolean, default=False)
    is_student = db.Column(db.Boolean, default=False)
    
    # Location and Filing Information
    state = db.Column(db.String(2), nullable=False)
    filing_status = db.Column(db.String(20), nullable=False, default="single")
    num_dependents = db.Column(db.Integer, default=0)
    
    # Employment Information
    income_type = db.Column(db.String(20), nullable=False, default="Salary")
    pay_cycle = db.Column(db.String(20), nullable=False)
    
    # Tax Withholdings
    federal_additional_withholding = db.Column(db.Float, default=0.0)
    state_additional_withholding = db.Column(db.Float, default=0.0)
    
    # Retirement Contributions
    retirement_contribution_type = db.Column(db.String(10), nullable=False)
    retirement_contribution = db.Column(db.Float, default=0.0)
    
    # Pre-tax Benefits
    health_insurance_premium = db.Column(db.Float, default=0.0)
    hsa_contribution = db.Column(db.Float, default=0.0)
    fsa_contribution = db.Column(db.Float, default=0.0)
    other_pretax_benefits = db.Column(db.Float, default=0.0)
    benefit_deductions = db.Column(db.Float, default=0.0)  # Total of all benefits

    # Relationships
    user = db.relationship("User", back_populates="profile")
    budgets = db.relationship("Budget", back_populates="profile")

    def __repr__(self):
        return f"<Profile {self.first_name} {self.last_name}, State: {self.state}>"
    
    @property
    def total_pretax_deductions(self):
        """Calculate total pre-tax deductions."""
        return (
            self.health_insurance_premium +
            self.hsa_contribution +
            self.fsa_contribution +
            self.other_pretax_benefits +
            (self.retirement_contribution if self.retirement_contribution_type == "pretax" else 0.0)
        )
    
    @property
    def age(self):
        """Calculate age based on date of birth."""
        if not self.date_of_birth:
            return None
        today = datetime.now()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )




# -------------------- Budget Model --------------------
class Budget(db.Model):
    __tablename__ = "budgets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)

    # Ensuring unique budget names per user
    __table_args__ = (db.UniqueConstraint('user_id', 'name', name='unique_user_budget_name'),)

    # Salary details
    gross_income = db.Column(db.Float, nullable=False, default=0.0)
    retirement_contribution = db.Column(db.Float, default=0)
    benefit_deductions = db.Column(db.Float, default=0)

    # Budget status (draft, finalized, archived)
    status = db.Column(db.String(20), nullable=False, default="draft")

    # Timestamps
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = db.relationship("User", back_populates="budgets")
    profile = db.relationship("Profile", back_populates="budgets")
    budget_items = db.relationship("BudgetItem", back_populates="budget", cascade="all, delete-orphan")
    gross_income_sources = db.relationship("GrossIncome", back_populates="budget", cascade="all, delete-orphan")
    other_income_sources = db.relationship("OtherIncome", back_populates="budget", cascade="all, delete-orphan")

    # Properties for dynamic calculations
    @property
    def salary_type(self):
        return self.user.profile.salary_type if self.user and self.user.profile else "Salary"

    @property
    def state(self):
        return self.user.profile.state if self.user and self.user.profile else "CA"

    @property
    def tax_withholding(self):
        """Pull tax withholding from Profile instead of duplicating."""
        return self.user.profile.tax_withholding if self.user and self.user.profile else 0

    # New Helper Methods
    def calculate_total_income(self):
        """Calculate total income from all sources linked to this budget."""
        return sum(income.gross_income for income in self.gross_income_sources)

    def get_budget_summary(self):
        """Return a dictionary summarizing budget details."""
        return {
            "name": self.name,
            "status": self.status,
            "total_income": self.calculate_total_income(),
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "updated_at": self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

    @property
    def primary_income(self):
        """Get the primary income source for this budget"""
        # Get the first gross income source from the list
        return self.gross_income_sources[0] if self.gross_income_sources else None

    def __repr__(self):
        return f"<Budget {self.name} (Status: {self.status})>"


# -------------------- Expense Category Model --------------------
class ExpenseCategory(db.Model):
    __tablename__ = "expense_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    priority = db.Column(db.Integer, default=0)  # For ordering categories (lower = higher priority)
    
    # Relationships
    expense_templates = db.relationship("ExpenseTemplate", back_populates="category", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ExpenseCategory {self.name}>"


# -------------------- Expense Template Model --------------------
class ExpenseTemplate(db.Model):
    __tablename__ = "expense_templates"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(200))
    is_default = db.Column(db.Boolean, default=False)  # Whether this expense is included by default
    priority = db.Column(db.Integer, default=0)  # For ordering within a category
    
    # Relationships
    category = db.relationship("ExpenseCategory", back_populates="expense_templates")
    
    def __repr__(self):
        return f"<ExpenseTemplate {self.name} (Category: {self.category.name})>"


# -------------------- BudgetItem Model --------------------
class BudgetItem(db.Model):
    __tablename__ = "budget_items"

    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budgets.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    minimum_payment = db.Column(db.Float, nullable=False, default=0.0)
    preferred_payment = db.Column(db.Float, nullable=False, default=0.0)
    # Link to the template if this item was created from a template
    template_id = db.Column(db.Integer, db.ForeignKey('expense_templates.id'), nullable=True)

    # Relationship
    budget = db.relationship("Budget", back_populates="budget_items")
    template = db.relationship("ExpenseTemplate", foreign_keys=[template_id])

    def __repr__(self):
        return f"<BudgetItem {self.category} - {self.name}>"


# -------------------- Gross Income Model ------------------------------
class GrossIncome(db.Model):
    __tablename__ = "gross_income"

    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budgets.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # e.g., "W2 Job", "Rental", "Freelance"
    source = db.Column(db.String(100), nullable=False)  # e.g., "Uber", "Book Royalties"
    gross_income = db.Column(db.Float, nullable=False)  # 💰 Clearly labeled as "Gross"
    frequency = db.Column(db.String(20), nullable=False, default="monthly")  # e.g., "weekly", "monthly"

    # ✅ Reference tax rules dynamically
    tax_type = db.Column(db.String(50), nullable=False)  # "W2", "Self-Employed", "Capital Gains", "Rental"
    state_tax_ref = db.Column(db.String(2), nullable=True)  # Used for API calls based on Profile.state

    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    # Relationship
    budget = db.relationship("Budget", back_populates="gross_income_sources")

    def __repr__(self):
        return f"<GrossIncome {self.source} - ${self.gross_income} ({self.frequency}) - Tax: {self.tax_type}, State Tax: {self.state_tax_ref}>"


# ---------------------- Other Income Model --------------------------------
class OtherIncome(db.Model):
    """Model for additional income sources."""
    __tablename__ = "other_income"

    id = db.Column(db.Integer, primary_key=True)
    budget_id = db.Column(db.Integer, db.ForeignKey('budgets.id'), nullable=False)  # Note: 'budgets' not 'budget'
    category = db.Column(db.String(50), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.String(20), nullable=False, default="monthly")
    created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)

    # Relationship
    budget = db.relationship("Budget", back_populates="other_income_sources")

    def __repr__(self):
        return f"<OtherIncome {self.source} - ${self.amount} ({self.frequency})>"

