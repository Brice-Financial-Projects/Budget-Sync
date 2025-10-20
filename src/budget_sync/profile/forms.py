"""budget_sync/profile/forms.py"""

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FloatField, IntegerField, BooleanField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

# A complete list of states (50 states)
states = [
    ('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'),
    ('AR', 'Arkansas'), ('CA', 'California'), ('CO', 'Colorado'),
    ('CT', 'Connecticut'), ('DE', 'Delaware'), ('FL', 'Florida'),
    ('GA', 'Georgia'), ('HI', 'Hawaii'), ('ID', 'Idaho'),
    ('IL', 'Illinois'), ('IN', 'Indiana'), ('IA', 'Iowa'),
    ('KS', 'Kansas'), ('KY', 'Kentucky'), ('LA', 'Louisiana'),
    ('ME', 'Maine'), ('MD', 'Maryland'), ('MA', 'Massachusetts'),
    ('MI', 'Michigan'), ('MN', 'Minnesota'), ('MS', 'Mississippi'),
    ('MO', 'Missouri'), ('MT', 'Montana'), ('NE', 'Nebraska'),
    ('NV', 'Nevada'), ('NH', 'New Hampshire'), ('NJ', 'New Jersey'),
    ('NM', 'New Mexico'), ('NY', 'New York'), ('NC', 'North Carolina'),
    ('ND', 'North Dakota'), ('OH', 'Ohio'), ('OK', 'Oklahoma'),
    ('OR', 'Oregon'), ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'),
    ('SC', 'South Carolina'), ('SD', 'South Dakota'), ('TN', 'Tennessee'),
    ('TX', 'Texas'), ('UT', 'Utah'), ('VT', 'Vermont'),
    ('VA', 'Virginia'), ('WA', 'Washington'), ('WV', 'West Virginia'),
    ('WI', 'Wisconsin'), ('WY', 'Wyoming')
]

class ProfileForm(FlaskForm):
    # Personal Information
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=50)])
    date_of_birth = DateField('Date of Birth', validators=[Optional()])
    is_blind = BooleanField('Are you legally blind?')
    is_student = BooleanField('Are you a full-time student?')

    # Location and Filing Information
    state = SelectField('State', choices=[
        ('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'), ('AR', 'Arkansas'),
        ('CA', 'California'), ('CO', 'Colorado'), ('CT', 'Connecticut'), ('DE', 'Delaware'),
        ('FL', 'Florida'), ('GA', 'Georgia'), ('HI', 'Hawaii'), ('ID', 'Idaho'),
        ('IL', 'Illinois'), ('IN', 'Indiana'), ('IA', 'Iowa'), ('KS', 'Kansas'),
        ('KY', 'Kentucky'), ('LA', 'Louisiana'), ('ME', 'Maine'), ('MD', 'Maryland'),
        ('MA', 'Massachusetts'), ('MI', 'Michigan'), ('MN', 'Minnesota'), ('MS', 'Mississippi'),
        ('MO', 'Missouri'), ('MT', 'Montana'), ('NE', 'Nebraska'), ('NV', 'Nevada'),
        ('NH', 'New Hampshire'), ('NJ', 'New Jersey'), ('NM', 'New Mexico'), ('NY', 'New York'),
        ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('OH', 'Ohio'), ('OK', 'Oklahoma'),
        ('OR', 'Oregon'), ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'), ('SC', 'South Carolina'),
        ('SD', 'South Dakota'), ('TN', 'Tennessee'), ('TX', 'Texas'), ('UT', 'Utah'),
        ('VT', 'Vermont'), ('VA', 'Virginia'), ('WA', 'Washington'), ('WV', 'West Virginia'),
        ('WI', 'Wisconsin'), ('WY', 'Wyoming')
    ], validators=[DataRequired()])

    filing_status = SelectField('Filing Status', choices=[
        ('single', 'Single'),
        ('married_joint', 'Married Filing Jointly'),
        ('married_separate', 'Married Filing Separately'),
        ('head_household', 'Head of Household'),
        ('qualifying_widow', 'Qualifying Widow(er)')
    ], validators=[DataRequired()])

    num_dependents = IntegerField('Number of Dependents', 
                                validators=[NumberRange(min=0, max=99)],
                                default=0)

    # Employment Information
    income_type = SelectField('Income Type', choices=[
        ('Salary', 'Salary'),
        ('Hourly', 'Hourly'),
        ('Commission', 'Commission'),
        ('Contract', 'Contract')
    ], validators=[DataRequired()])

    pay_cycle = SelectField('Pay Cycle', choices=[
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-Weekly'),
        ('semimonthly', 'Semi-Monthly'),
        ('monthly', 'Monthly')
    ], validators=[DataRequired()])

    # Tax Withholdings
    federal_additional_withholding = FloatField('Additional Federal Tax Withholding',
                                              validators=[Optional(), NumberRange(min=0)],
                                              default=0.0)
    state_additional_withholding = FloatField('Additional State Tax Withholding',
                                            validators=[Optional(), NumberRange(min=0)],
                                            default=0.0)

    # Retirement Contributions
    retirement_contribution_type = SelectField('Retirement Contribution Type', choices=[
        ('pretax', 'Pre-tax (Traditional)'),
        ('posttax', 'Post-tax (Roth)'),
        ('none', 'None')
    ], validators=[DataRequired()])

    retirement_contribution = FloatField('Retirement Contribution (%)',
                                       validators=[Optional(), NumberRange(min=0, max=100)],
                                       default=0.0)

    # Pre-tax Benefits
    health_insurance_premium = FloatField('Health Insurance Premium',
                                        validators=[Optional(), NumberRange(min=0)],
                                        default=0.0)
    hsa_contribution = FloatField('HSA Contribution',
                                validators=[Optional(), NumberRange(min=0)],
                                default=0.0)
    fsa_contribution = FloatField('FSA Contribution',
                                validators=[Optional(), NumberRange(min=0)],
                                default=0.0)
    other_pretax_benefits = FloatField('Other Pre-tax Benefits',
                                     validators=[Optional(), NumberRange(min=0)],
                                     default=0.0)

    submit = SubmitField('Save Profile')
