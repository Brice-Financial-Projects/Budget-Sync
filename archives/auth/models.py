"""backend/budget_sync/auth/models.py"""

# from budget_sync import db, bcrypt
# from sqlalchemy.sql import func

# class User(db.Model):
#     """A model for managing users."""
#     __tablename__ = "users"
    
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(20), unique=True, nullable=False)
#     email = db.Column(db.String(120), unique=True, nullable=False)
#     password_hash = db.Column(db.String(128), nullable=False)
#     created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
#     is_admin = db.Column(db.Boolean, default=False)

#     budgets = db.relationship('Budget', back_populates='user', cascade="all, delete-orphan")

#     def __init__(self, username, email, password):
#         self.username = username
#         self.email = email
#         self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

#     def check_password(self, password):
#         return bcrypt.check_password_hash(self.password_hash, password)

#     @property
#     def is_active(self):  # ✅ Required for Flask-Login
#         return True

#     @property
#     def is_authenticated(self):  # ✅ Ensures user is considered "logged in"
#         return True

#     def get_id(self):
#         return str(self.id)

#     def __repr__(self):
#         return f"User('{self.username}', '{self.email}')"




# class Budget(db.Model):
#     """Stores user budgets, referencing profiles for shared user data."""
#     __tablename__ = "budgets"

#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
#     name = db.Column(db.String(100), nullable=False)

#     # Link to profile for shared information
#     profile_id = db.Column(db.Integer, db.ForeignKey('profiles.id'), nullable=False)  # NEW: Link budget to profile

#     # Other income details
#     gross_income = db.Column(db.Float, nullable=False, default=0.0)
#     gross_income_frequency = db.Column(db.String(10), nullable=False, default="annually")  # 'monthly' or 'annually'
#     other_income_sources = db.Column(JSON, nullable=True)  # JSON field for various income sources

#     # Timestamp fields
#     created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
#     updated_at = db.Column(db.DateTime, onupdate=func.now())

#     # Relationships
#     user = db.relationship('User', back_populates='budgets')
#     profile = db.relationship('Profile', back_populates='budgets')  # NEW: Direct reference to Profile
#     budget_items = db.relationship('BudgetItem', back_populates='budget', cascade="all, delete-orphan")

#     @property
#     def state(self):
#         """Get state from the user's profile instead of storing it in budgets."""
#         return self.profile.state if self.profile else "Unknown"

#     @property
#     def income_type(self):
#         """Get income type from the user's profile."""
#         return self.profile.income_type if self.profile else "Unknown"

#     @property
#     def tax_withholding(self):
#         """Get tax withholding from the user's profile."""
#         return self.profile.tax_withholding if self.profile else 0

#     @property
#     def retirement_contribution(self):
#         """Get retirement contributions from the user's profile."""
#         return self.profile.retirement_contribution if self.profile else 0

#     @property
#     def benefit_deductions(self):
#         """Get benefit deductions from the user's profile."""
#         return self.profile.benefit_deductions if self.profile else 0

#     def __repr__(self):
#         return (f"<Budget id={self.id}, name={self.name}, profile_id={self.profile_id}, "
#                 f"gross_income={self.gross_income}, gross_income_frequency={self.gross_income_frequency}, "
#                 f"other_income_sources={self.other_income_sources}>")



# class BudgetItem(db.Model):
#     """Stores budget items as subcategories under categories."""
#     __tablename__ = "budget_items"

#     id = db.Column(db.Integer, primary_key=True)
#     budget_id = db.Column(db.Integer, db.ForeignKey('budgets.id'), nullable=False)
#     category = db.Column(db.String(50), nullable=False)  # Example: "Utilities"
#     name = db.Column(db.String(50), nullable=False)  # e.g., "Water" under "Utilities"
#     minimum_payment = db.Column(db.Float, nullable=False, default=0.0)
#     preferred_payment = db.Column(db.Float, nullable=False, default=0.0)

#     # Relationship to Budget
#     budget = db.relationship('Budget', back_populates='budget_items')

#     def __repr__(self):
#         return (f"<BudgetItem id={self.id}, category={self.category}, "
#                 f"name={self.name}, min={self.minimum_payment}, "
#                 f"pref={self.preferred_payment}>")

# class User(db.Model):
#     """A model for managing users."""
#     __tablename__ = "users"
    
#     id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(20), unique=True, nullable=False)
#     email = db.Column(db.String(120), unique=True, nullable=False)
#     password_hash = db.Column(db.String(128), nullable=False)
#     created_at = db.Column(db.DateTime, server_default=func.now(), nullable=False)
#     is_admin = db.Column(db.Boolean, default=False)

#     budgets = db.relationship('Budget', back_populates='user', cascade="all, delete-orphan")
#     # One-to-one relationship with Profile.
#     profile = db.relationship('Profile', back_populates='user', uselist=False, cascade="all, delete-orphan")

#     def __init__(self, username, email, password):
#         self.username = username
#         self.email = email
#         self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

#     def check_password(self, password):
#         return bcrypt.check_password_hash(self.password_hash, password)

#     @property
#     def is_active(self):  # Required for Flask-Login
#         return True

#     @property
#     def is_authenticated(self):  # Ensures user is considered "logged in"
#         return True

#     def get_id(self):
#         return str(self.id)

#     def __repr__(self):
#         return f"User('{self.username}', '{self.email}')"

# class Profile(db.Model):
#     """Stores user profile details, referenced by budgets."""
#     __tablename__ = "profiles"

#     id = db.Column(db.Integer, primary_key=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
#     first_name = db.Column(db.String(50), nullable=False)
#     last_name = db.Column(db.String(50), nullable=False)
#     state = db.Column(db.String(2), nullable=False)
#     income_type = db.Column(db.String(20), nullable=False)
#     tax_withholding = db.Column(db.Float, default=0)  # We'll compute this via API later
#     retirement_contribution_type = db.Column(db.String(10), nullable=False)  # e.g., 'percent' or 'fixed'
#     retirement_contribution = db.Column(db.Float, default=0)
#     pay_cycle = db.Column(db.String(20), nullable=False)  # e.g., 'weekly', 'biweekly', etc.
#     benefit_deductions = db.Column(db.Float, default=0)

#     # Relationships
#     user = db.relationship('User', back_populates='profile')
#     budgets = db.relationship('Budget', back_populates='profile')

#     def __repr__(self):
#         return f"<Profile id={self.id}, user_id={self.user_id}, first_name={self.first_name}, last_name={self.last_name}, state={self.state}>"

