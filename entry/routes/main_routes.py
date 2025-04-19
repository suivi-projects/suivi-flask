from flask import Blueprint, render_template, flash, request, redirect, url_for, jsonify, current_app
from flask_login import login_user, login_required, logout_user, current_user
import json
from entry import mail
from entry.models import User, Rider, Parcel, FAQ, UnansweredQuestion
from sqlalchemy.exc import IntegrityError
from entry import app, db, bcrypt
from flask_mail import Message, Mail
from sqlalchemy import or_
from datetime import datetime

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/home')
def home():
    if current_user.is_authenticated and (current_user.role == 'sender' or current_user.role == 'admin'):
        return redirect(url_for('auth.home_authenticated'))
    elif current_user.is_authenticated and current_user.role == 'rider':
        return redirect(url_for('rider.rider_authenticated'))
    return render_template('home.html', title='Home')

@main.route('/about')
def about():
    return render_template('about.html')

@main.route('/contacts')
def contacts():
    return render_template('contact.html')

@main.route('/logout')
@login_required
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for('main.home'))

@main.route('/support', methods=['GET', 'POST'])
def support():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        comment = request.form.get('comment')

        if not name or not email or not comment:
            flash('Please fill out all fields.', 'error')
        else:
            subject = f"Support Request from {name}"
            sender_email = current_app.config.get('MAIL_USERNAME')
            admin_email = 'suiviadmn@gmail.com'

            if not sender_email:
                 flash('Mail server not configured correctly.', 'error')
                 current_app.logger.error("MAIL_USERNAME not set in config.")
                 return redirect(url_for('main.support'))

            msg = Message(subject=subject,
                          sender=sender_email,
                          recipients=[admin_email])
            msg.body = f"Name: {name}\nEmail: {email}\n\nComment:\n{comment}"

            try:
                mail.send(msg)
                flash('Message sent successfully! Our support team will get back to you shortly.', 'success')
            except Exception as e:
                current_app.logger.error(f"Failed to send support email: {e}")
                flash('Something went wrong while sending your message. Please try again later.', 'error')

        return redirect(url_for('main.support'))

    if request.method == 'GET':
        search_query = request.args.get('search_query', '').strip()

        if search_query:
            search_words = search_query.split()
            filter_conditions = []
            for word in search_words:
                question_condition = FAQ.question.ilike(f'%{word}%')
                answer_condition = FAQ.answer.ilike(f'%{word}%')
                filter_conditions.append(or_(question_condition, answer_condition))
            combined_condition = or_(*filter_conditions)

            existing_faqs = FAQ.query.filter(combined_condition).limit(10).all()

            if not existing_faqs:
                try:
                    user_id_to_log = current_user.id if current_user.is_authenticated else None
                    unanswered = UnansweredQuestion(
                        query_text=search_query,
                        timestamp=datetime.utcnow(),
                        status='new',
                        user_id=user_id_to_log
                    )
                    db.session.add(unanswered)
                    db.session.commit()
                    current_app.logger.info(f"Logged unanswered query: '{search_query}' (User ID: {user_id_to_log or 'Anonymous'})")

                    subject = "Unanswered FAQ Query on Suivi"
                    sender_email = current_app.config.get('MAIL_USERNAME')
                    admin_email = 'suiviadmn@gmail.com'

                    if sender_email:
                        user_info_for_email = f"User ID: {user_id_to_log}" if user_id_to_log else "User: Anonymous"

                        msg_admin = Message(subject=subject,
                                            sender=sender_email,
                                            recipients=[admin_email])
                        msg_admin.body = (
                            f"An unanswered FAQ query was submitted:\n\n"
                            f"Query: \"{search_query}\"\n"
                            f"{user_info_for_email}\n"
                            f"Timestamp: {unanswered.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                            f"Please consider adding this question to the FAQ database or reviewing it."
                        )
                        mail.send(msg_admin)
                        current_app.logger.info(f"Emailed admin about unanswered query: '{search_query}'")
                    else:
                        current_app.logger.warning("MAIL_USERNAME not set. Cannot email admin about unanswered query.")

                except Exception as e:
                    db.session.rollback()
                    current_app.logger.error(f"Error logging/emailing unanswered query '{search_query}': {e}")

            faqs_dict = [{'id': faq.id, 'question': faq.question, 'answer': faq.answer} for faq in existing_faqs]
            return jsonify(faqs_dict)

        return render_template('support.html')

    return render_template('support.html')
