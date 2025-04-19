from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, SelectField, DateTimeField
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp, Optional, ValidationError
from flask_login import current_user
from entry.models import User, Rider, Admin


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    contact = StringField('Contact Number', validators=[DataRequired(),
                                 Regexp(r'^[0-9]{10}$',
                                 message='Please enter a valid 10-digit phone number')])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class RiderRegistrationForm(FlaskForm):
    username = StringField('Name', validators=[DataRequired(),
		       Length(min=2, max=100)])
    contact = StringField('Contact Number', validators=[DataRequired(),
                                 Regexp(r'^[0-9]{10}$',
                                 message='Please enter a valid 10-digit phone number')])
    email = StringField('Email', validators=[Email()])
    vehicle_type = StringField('Vehicle Type', validators=[DataRequired(),
                               Length(min=2, max=50)])
    vehicle_registration = StringField('Vehicle Registration',
                                       validators=[DataRequired(),
				       Length(min=2, max=50)])
    area_of_operation = StringField('Area of Operation',
				    validators=[DataRequired(),
                                    Length(min=2, max=100)])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class LoginRiderForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    contact = StringField('Contact Number', validators=[DataRequired(),
                                 Regexp(r'^[0-9]{10}$',
                                 message='Please enter a valid 10-digit phone number')])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Username is already taken, please choose another one')
    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('User with this email is exists, please choose another one')


class UpdateRiderForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    contact = StringField('Contact', validators=[DataRequired()])
    vehicle_type = StringField('Vehicle Type', validators=[DataRequired()])
    vehicle_registration = StringField('Vehicle Registration', validators=[DataRequired()])
    area_of_operation = StringField('Area of Operation')
    current_location = StringField('Current Location')
    new_password = PasswordField('New Password')
    confirm_new_password = PasswordField('Confirm New Password',
                                         validators=[EqualTo('new_password')])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')

class ParcelForm(FlaskForm):
    sender_name = StringField('Sender\'s Name', validators=[DataRequired(), Length(max=100)])
    sender_email = StringField('Sender\'s Email', validators=[DataRequired(), Email(), Length(max=100)])
    sender_contact = StringField('Sender\'s Contact', validators=[DataRequired(), Length(max=20)])
    receiver_name = StringField('Receiver\'s Name', validators=[Length(max=100)])
    receiver_contact = StringField('Receiver\'s Contact', validators=[Length(max=20)])
    pickup_location = StringField('Pickup Location', validators=[DataRequired(), Length(max=255)])
    delivery_location = StringField('Delivery Location', validators=[DataRequired(), Length(max=255)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=400)])


class ForgotPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Submit')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')


class AdminLoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class AdminRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        admin = Admin.query.filter_by(email=email.data).first()
        if admin:
            raise ValidationError('That email is taken. Please choose a different one.')

class UpdateAdminForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Update')
