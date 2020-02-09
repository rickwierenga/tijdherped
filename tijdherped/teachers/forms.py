from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, IntegerField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, NumberRange, Email


class NewGroup(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    excel_file = FileField(validators=[FileAllowed(['xlsx'], 'xlsx (MS Excel)')])
    submit = SubmitField('Create')


class NewStudent(FlaskForm):
    first_name = StringField('First name', validators=[DataRequired()])
    last_name  = StringField('Last name', validators=[DataRequired()])
    submit     = SubmitField('Create')


class NewTeamForm(FlaskForm):
    name   = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Create')


class NewProjectForm(FlaskForm):
    name       = StringField('Name', validators=[DataRequired()])
    start_week = IntegerField('Start week (number)', validators=[DataRequired(), NumberRange(1, 53, 'Not a week number')])
    end_week   = IntegerField('End week (number)', validators=[DataRequired(), NumberRange(1, 53, 'Not a week number')])
    excluded   = IntegerField('Excluded', validators=[DataRequired(), NumberRange(0, None, 'Value must be positive.')])
    submit     = SubmitField('Create')


class UpdateRFIDForm(FlaskForm):
    rfid   = StringField('RFID', validators=[DataRequired()])
    submit = SubmitField('Submit')


class NewSessionForm(FlaskForm):
    minutes = IntegerField('minutes', validators=[DataRequired()])
    submit  = SubmitField('Create')