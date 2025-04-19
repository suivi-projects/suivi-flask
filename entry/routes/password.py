from flask import Blueprint, render_template, flash, request, redirect, url_for, jsonify
from flask_login import login_user, login_required, logout_user, current_user
import json
from entry.forms import LoginRiderForm, RegistrationForm, LoginForm, UpdateAccountForm, RiderRegistrationForm, ParcelForm, UpdateRiderForm, ForgotPasswordForm, ResetPasswordForm
from entry import mail
from entry.models import User, Sender, Rider, Parcel, FAQ
from sqlalchemy.exc import IntegrityError
from entry import app, db, bcrypt
from flask_mail import Message, Mail
from sqlalchemy import or_
import secrets


password = Blueprint('password', __name__)


@password.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        sender = Sender.query.filter_by(email=email).first()
        rider = Rider.query.filter_by(email=email).first()
        if sender:
            token = secrets.token_urlsafe(32)
            sender.reset_password_token = token
            db.session.commit()

            reset_url = url_for('password.reset_password', token=token, _external=True)
            message = f"Click the link to reset your password: {reset_url}"
            send_email(sender.email, "Password Reset Request", message)

            flash("Instructions to reset your password have been sent to your email.", "success")
            return redirect(url_for('auth.login'))
        elif rider:
            token = secrets.token_urlsafe(32)
            rider.reset_password_token = token
            db.session.commit()

            reset_url = url_for('password.reset_password', token=token, _external=True)
            message = f"Click the link to reset your password: {reset_url}"
            send_email(rider.email, "Password Reset Request", message)

            flash("Instructions to reset your password have been sent to your email.", "success")
            return redirect(url_for('rider.login_rider'))
        else:
            flash("Email address not found.", 'danger')
    return render_template('forgot_password.html', form=form)


@password.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_password_token=token).first()
    if user:
        form = ResetPasswordForm()
        if form.validate_on_submit():
            new_password = form.password.data
            user.password = bcrypt.generate_password_hash(new_password).decode('utf-8')

            user.reset_password_token = None
            db.session.commit()

            flash("Your password has been successfully reset. You can now log in with your new password.", 'success')
            return redirect(url_for('main.logout'))
        return render_template('reset_password.html', form=form)

    flash("Invalid or expired token.", 'danger')
    return redirect(url_for('password.forgot_password'))

def send_email(recipient, subject, html_body):
    msg = Message(subject, recipients=[recipient])
    msg.html = html_body
    mail.send(msg)
