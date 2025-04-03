"""app/forms.py"""

from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField, SubmitField, FormField, FieldList
from wtforms.validators import DataRequired, Optional, NumberRange
from wtforms.fields import SelectMultipleField


class UtilityField(FlaskForm):
    electricity = FloatField('Electricity', validators=[Optional()])
    water = FloatField('Water', validators=[Optional()])
    internet = FloatField('Internet', validators=[Optional()])
    cable = FloatField('Cable', validators=[Optional()])
    streamTV1 = FloatField('StreamTV 1', validators=[Optional()])
    streamTV2 = FloatField('StreamTV 2', validators=[Optional()])
    streamTV3 = FloatField('StreamTV 3', validators=[Optional()])
    streamTV4 = FloatField('StreamTV 4', validators=[Optional()])
    streamTV5 = FloatField('StreamTV 5', validators=[Optional()])
    gas = FloatField('Gas', validators=[Optional()])

class CreditCardField(FlaskForm):
    card1 = FloatField('Credit Card 1', validators=[Optional()])
    card2 = FloatField('Credit Card 2', validators=[Optional()])
    card3 = FloatField('Credit Card 3', validators=[Optional()])
    card4 = FloatField('Credit Card 4', validators=[Optional()])
    card5 = FloatField('Credit Card 5', validators=[Optional()])

class LoanField(FlaskForm):
    vehicle1 = FloatField('Vehicle Loan 1', validators=[Optional()])
    vehicle2 = FloatField('Vehicle Loan 2', validators=[Optional()])
    vehicle3 = FloatField('Vehicle Loan 3', validators=[Optional()])
    boat1 = FloatField('Boat Loan 1', validators=[Optional()])
    boat2 = FloatField('Boat Loan 2', validators=[Optional()])
    boat3 = FloatField('Boat Loan 3', validators=[Optional()])
    school1 = FloatField('School Loan 1', validators=[Optional()])
    school2 = FloatField('School Loan 2', validators=[Optional()])
    school3 = FloatField('School Loan 3', validators=[Optional()])
    school4 = FloatField('School Loan 4', validators=[Optional()])
    medical1 = FloatField('Medical Loan 1', validators=[Optional()])
    medical2 = FloatField('Medical Loan 2', validators=[Optional()])

class BudgetForm(FlaskForm):
    # New field for budget name (required)
    budget_name = StringField('Budget Name', validators=[DataRequired()])
    
    income = FloatField('Gross Annual Income', validators=[Optional()])
    pay_period = SelectField(
        'Pay Period',
        choices=[('weekly', 'Weekly'), ('biweekly', 'Every Two Weeks'), ('semimonthly', 'Twice Per Month'), ('monthly', 'Monthly')],
        validators=[Optional()]
    )
    rent = FloatField('Rent', validators=[Optional()])
    utilities = FormField(UtilityField)
    debts = FormField(CreditCardField)
    loans = FormField(LoanField)
    groceries = FloatField('Groceries', validators=[Optional()])
    transportation_gas = FloatField('Transportation Gas', validators=[Optional()])
    vehicle_insurance = FloatField('Vehicle Insurance', validators=[Optional()])
    cell_phone = FloatField('Cell Phone', validators=[Optional()])
    savings = FloatField('Savings', validators=[Optional()])
    submit = SubmitField('Calculate Budget')


class OtherIncomeField(FlaskForm):
    """Form field for additional income sources."""
    category = SelectField(
        'Income Type',
        choices=[
            ('rental', 'Rental Income'),
            ('investment', 'Investment Dividends'),
            ('business', 'Business Income'),
            ('side_job', 'Secondary Employment'),
            ('royalties', 'Royalties'),
            ('social_security', 'Social Security'),
            ('pension', 'Pension'),
            ('other', 'Other')
        ],
        validators=[DataRequired()]
    )
    name = StringField('Income Source Name', validators=[DataRequired()])
    amount = FloatField('Amount', validators=[DataRequired()])
    frequency = SelectField(
        'Frequency',
        choices=[
            ('weekly', 'Weekly'),
            ('biweekly', 'Biweekly'),
            ('monthly', 'Monthly'),
            ('bimonthly', 'Bimonthly'),
            ('annually', 'Annually')
        ],
        validators=[DataRequired()]
    )


class IncomeForm(FlaskForm):
    """Form for entering gross income and other income sources."""
    gross_income = FloatField('Gross Income', validators=[DataRequired()])
    gross_income_frequency = SelectField(
        'Income Frequency',
        choices=[
            ('weekly', 'Weekly'),
            ('biweekly', 'Biweekly'),
            ('monthly', 'Monthly'),
            ('bimonthly', 'Bimonthly'),
            ('annually', 'Annually')
        ],
        validators=[DataRequired()]
    )

    # Removed the FieldList for other_income_sources because we handle it directly in the template and route
    # other_income_sources = FieldList(FormField(OtherIncomeField), min_entries=1, max_entries=10)

    save = SubmitField('Save Income')
    preview = SubmitField('Next: Budget Preview')


# forms.py (add this at the top)
class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class CategorySelectionForm(FlaskForm):
    categories = MultiCheckboxField('Categories', coerce=str)
    submit = SubmitField('Next: Input Details')
