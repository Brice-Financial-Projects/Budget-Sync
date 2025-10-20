"""Weather forms."""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp

class WeatherForm(FlaskForm):
    """Form for weather search."""
    city = StringField('City', 
                      validators=[DataRequired(), Length(min=1, max=100)],
                      description='Enter city name')
    
    state = StringField('State Code',
                       validators=[Length(max=2), Regexp(r'^[A-Za-z]{2}$', message='State code must be exactly 2 letters')],
                       description='Enter 2-letter state code (optional)')
    
    country = StringField('Country Code',
                         validators=[Length(max=2), Regexp(r'^[A-Za-z]{2}$', message='Country code must be exactly 2 letters')],
                         default='US',
                         description='Enter 2-letter country code')
    
    submit = SubmitField('Get Weather') 