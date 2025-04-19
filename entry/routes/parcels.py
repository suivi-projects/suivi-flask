from entry.forms import LoginRiderForm, RegistrationForm, LoginForm, UpdateAccountForm, RiderRegistrationForm, ParcelForm, UpdateRiderForm, ForgotPasswordForm, ResetPasswordForm
from flask import Blueprint, session, render_template, flash, request, redirect, url_for, jsonify, current_app
from flask_login import login_user, login_required, logout_user, current_user
from apscheduler.schedulers.background import BackgroundScheduler
from ..payment import initiate_stk_push, process_mpesa_callback
from apscheduler.triggers.interval import IntervalTrigger
from entry.models import User, Rider, Parcel, FAQ, Sender
from entry.sms_service import send_bulk_sms
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim
from flask_mail import Message, Mail
from geopy.distance import geodesic
from entry import app, db, bcrypt
from sqlalchemy import or_
from flask import session
from entry import mail
import geopy.exc
import retrying
import requests
import secrets
import stripe
import atexit
import json
import os

scheduler = BackgroundScheduler()

parcel = Blueprint('parcel', __name__)

secret_key = os.getenv('STRIPE_SECRET_KEY')
publishable_key = os.getenv('STRIPE_PUBLISHABLE_KEY')
stripe.api_key = secret_key

@parcel.route('/request_pickup', methods=['GET'])
@login_required
def request_pickup():
    form = ParcelForm()
    return render_template('request_pickup.html', form=form, key=publishable_key)

@parcel.route('/submit_pickup_request', methods=['POST'])
@login_required
def submit_pickup_request():
    form = ParcelForm()

    pickup_loc = request.form.get('pickup_location_final')
    delivery_loc = request.form.get('delivery_location_final')
    receiver_name = request.form.get('receiver_name_final')
    receiver_contact = request.form.get('receiver_contact_final')
    pickup_lat = request.form.get('pickup_lat')
    pickup_lng = request.form.get('pickup_lng')
    delivery_lat = request.form.get('delivery_lat')
    delivery_lng = request.form.get('delivery_lng')
    payment_method = request.form.get('payment_method')

    if not all([pickup_loc, delivery_loc, receiver_name, receiver_contact, pickup_lat, pickup_lng, delivery_lat, delivery_lng, payment_method]):
        flash('Incomplete form data received. Please try again.', 'danger')
        return redirect(url_for('parcel.request_pickup'))

    if payment_method == 'stripe':
        stripe_token = request.form.get('stripeToken')
        if not stripe_token:
            flash('Stripe payment token missing. Please try again.', 'danger')
            return redirect(url_for('parcel.request_pickup'))

        try:
            charge = stripe.Charge.create(
                amount=100,
                currency="kes",
                description=f"Suivi Delivery for {current_user.username} to {receiver_name}",
                source=stripe_token,
                receipt_email=current_user.email
            )
            current_app.logger.info(f"Stripe charge successful: {charge.id}")

            try:
                parcel = Parcel(
                    sender_id=current_user.id,
                    receiver_name=receiver_name,
                    receiver_contact=receiver_contact,
                    pickup_location=pickup_loc,
                    delivery_location=delivery_loc,
                    pickup_lat=float(pickup_lat) if pickup_lat else None,
                    pickup_lng=float(pickup_lng) if pickup_lng else None,
                    delivery_lat=float(delivery_lat) if delivery_lat else None,
                    delivery_lng=float(delivery_lng) if delivery_lng else None,
                    payment_status='paid',
                    status='pending',
                    stripe_charge_id=charge.id
                )
                db.session.add(parcel)
                db.session.commit()
                current_app.logger.info(f"Parcel {parcel.id} created successfully after Stripe payment.")

                closest_rider = allocate_parcel(parcel)
                if closest_rider:
                    flash(f'Payment successful! Rider {closest_rider.username} allocated.', 'success')
                else:
                    start_scheduler()
                    flash('Payment successful! Searching for a nearby rider.', 'info')

                return redirect(url_for('main.home'))

            except Exception as db_e:
                db.session.rollback()
                current_app.logger.error(f"Error creating parcel after successful Stripe payment {charge.id}: {db_e}", exc_info=True)
                flash('Payment succeeded, but there was an error submitting your request. Please contact support.', 'danger')
                return redirect(url_for('parcel.request_pickup'))

        except stripe.error.CardError as e:
            body = e.json_body
            err = body.get('error', {})
            flash(f"Payment failed: {err.get('message')}", 'danger')
            current_app.logger.error(f"Stripe CardError: {e}")
            return redirect(url_for('parcel.request_pickup'))
        except stripe.error.StripeError as e:
            flash("An unexpected payment error occurred. Please try again or contact support.", 'danger')
            current_app.logger.error(f"Stripe Generic Error: {e}", exc_info=True)
            return redirect(url_for('parcel.request_pickup'))
        except Exception as e:
            flash("An unexpected error occurred during payment processing.", 'danger')
            current_app.logger.error(f"Non-Stripe Error during payment: {e}", exc_info=True)
            return redirect(url_for('parcel.request_pickup'))

    elif payment_method == 'mpesa':
        payer_phone = request.form.get('mpesa_phone')
        amount_kes = 1

        if not payer_phone:
             flash('M-Pesa phone number is required.', 'danger')
             return redirect(url_for('parcel.request_pickup'))

        parcel = None
        try:
            parcel = Parcel(
                sender_id=current_user.id,
                receiver_name=receiver_name,
                receiver_contact=receiver_contact,
                pickup_location=pickup_loc,
                delivery_location=delivery_loc,
                pickup_lat=float(pickup_lat) if pickup_lat else None,
                pickup_lng=float(pickup_lng) if pickup_lng else None,
                delivery_lat=float(delivery_lat) if delivery_lat else None,
                delivery_lng=float(delivery_lng) if delivery_lng else None,
                payment_status='pending',
                status='pending'
            )
            db.session.add(parcel)
            db.session.commit()
            current_app.logger.info(f"Pending Parcel {parcel.id} created for M-Pesa payment.")

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating initial pending parcel for M-Pesa: {e}", exc_info=True)
            flash('An error occurred while preparing your request. Please try again.', 'danger')
            return redirect(url_for('parcel.request_pickup'))

        mpesa_response = None
        if parcel and parcel.id:
            try:
                mpesa_response = initiate_stk_push(
                    phone_number=payer_phone,
                    amount=amount_kes,
                    parcel_id=parcel.id,
                    description=f"Suivi Delivery Pcl#{parcel.id}"
                )
            except Exception as e:
                 current_app.logger.error(f"Unexpected error calling initiate_stk_push for Parcel {parcel.id}: {e}", exc_info=True)
                 flash('An error occurred while initiating M-Pesa payment.', 'danger')
                 return redirect(url_for('parcel.request_pickup'))

        if mpesa_response and mpesa_response.get('ResponseCode') == '0':
            checkout_request_id = mpesa_response.get('CheckoutRequestID')
            current_app.logger.info(f"M-Pesa STK Push initiated for Parcel {parcel.id}. CheckoutRequestID: {checkout_request_id}")
            try:
                parcel.checkout_request_id = checkout_request_id
                db.session.commit()
                current_app.logger.info(f"Stored CheckoutRequestID on Parcel {parcel.id}.")
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error storing CheckoutRequestID for Parcel {parcel.id}: {e}", exc_info=True)
                flash('M-Pesa payment initiated, but a linking error occurred. Please contact support.', 'warning')
                return redirect(url_for('parcel.request_pickup'))

            try:
                closest_rider = allocate_parcel(parcel)
                if closest_rider:
                    current_app.logger.info(f"Rider {closest_rider.username} tentatively allocated to Parcel {parcel.id} (pending M-Pesa payment).")
                else:
                    start_scheduler()
                    current_app.logger.info(f"No immediate rider for Parcel {parcel.id}. Scheduler started (pending M-Pesa payment).")
            except Exception as e:
                 current_app.logger.error(f"Error during tentative allocation for Parcel {parcel.id}: {e}", exc_info=True)

            flash(f'Please check your phone ({payer_phone}) and enter your M-Pesa PIN to authorize KES {amount_kes}.', 'info')
            return redirect(url_for('main.home'))

        else:
            error_desc = "Unknown error"
            if mpesa_response:
                error_desc = mpesa_response.get('ResponseDescription', error_desc)
                error_code = mpesa_response.get('ResponseCode', 'N/A')
                current_app.logger.error(f"M-Pesa STK Push initiation failed by API for Parcel {parcel.id if parcel else 'N/A'}: {error_desc} (Code: {error_code})")
            else:
                 current_app.logger.error(f"M-Pesa STK Push initiation failed for Parcel {parcel.id if parcel else 'N/A'} (No response from initiate_stk_push).")

            flash(f'Could not initiate M-Pesa payment: {error_desc}. Please try again.', 'danger')
            return redirect(url_for('parcel.request_pickup'))

    else:
        flash('Invalid payment method selected.', 'danger')
        return redirect(url_for('parcel.request_pickup'))


@parcel.route('/mpesa_callback', methods=['POST'])
def mpesa_callback():
    current_app.logger.info("Received M-Pesa callback request.")
    callback_data = request.get_json()
    if not callback_data:
        current_app.logger.error("M-Pesa callback received no JSON data.")
        return jsonify({"ResultCode": 1, "ResultDesc": "Failed - No JSON Data"}), 400

    success, processed_parcel = process_mpesa_callback(callback_data, db, Parcel) # Removed payment. prefix

    if success:
        current_app.logger.info(f"M-Pesa callback processed successfully for Parcel ID: {processed_parcel.id if processed_parcel else 'N/A'}")
        if processed_parcel and processed_parcel.payment_status == 'paid':
             if not processed_parcel.rider_id:
                 current_app.logger.info(f"Attempting rider allocation for paid Parcel {processed_parcel.id}")
                 try:
                     closest_rider = allocate_parcel(processed_parcel)
                     if closest_rider:
                         current_app.logger.info(f"Rider {closest_rider.username} allocated to paid Parcel {processed_parcel.id}.")
                     else:
                         start_scheduler()
                         current_app.logger.info(f"No immediate rider for paid Parcel {processed_parcel.id}. Scheduler started.")
                 except Exception as alloc_e:
                     current_app.logger.error(f"Error during post-payment allocation for Parcel {processed_parcel.id}: {alloc_e}")
             else:
                 current_app.logger.info(f"Parcel {processed_parcel.id} was already allocated to rider {processed_parcel.rider_id}. Payment confirmed.")

    else:
        current_app.logger.warning(f"M-Pesa callback processing failed or payment was unsuccessful for parcel: {processed_parcel.id if processed_parcel else 'N/A'}")

    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200


@parcel.route('/track_parcel')
def track_parcel():
    return render_template('track_parcel.html')


@parcel.route('/get_parcel_status')
def get_parcel_status():
    tracking_number = request.args.get('tracking_number')
    if tracking_number:
        parcel = Parcel.query.filter_by(tracking_number=tracking_number).first()
        if parcel:
            pickup_lat, pickup_lng = get_lat_lng(parcel.pickup_location)
            delivery_lat, delivery_lng = get_lat_lng(parcel.delivery_location)

            return jsonify({
                'status': parcel.status,
                'expected_arrival': parcel.expected_arrival,
                'pickup_location': parcel.pickup_location,
                'delivery_location': parcel.delivery_location,
                'pickup_coords': {'lat': pickup_lat, 'lng': pickup_lng},
                'delivery_coords': {'lat': delivery_lat, 'lng': delivery_lng},
            }), 200
        else:
            return jsonify({'error': 'Parcel not found'}), 404
    else:
        return jsonify({'error': 'Tracking number not provided'}), 400

@parcel.route('/get_coordinates', methods=['POST'])
def get_coordinates():
    data = request.get_json()
    pickup_location = data.get('pickup_location')
    delivery_location = data.get('delivery_location')

    pickup_lat, pickup_lng = get_lat_lng(pickup_location)
    delivery_lat, delivery_lng = get_lat_lng(delivery_location)

    if None in (pickup_lat, pickup_lng, delivery_lat, delivery_lng):
        return jsonify({"error": "Could not fetch coordinates for one or both locations"}), 400
    return jsonify({
        "pickup_lat": pickup_lat,
        "pickup_lng": pickup_lng,
        "delivery_lat": delivery_lat,
        "delivery_lng": delivery_lng
        })


def get_lat_lng(location):
    user_agent = 'SuiviApp/1.0 (victorcyrus01@gmail.com)'
    geolocator = Nominatim(user_agent=user_agent)
    location = geolocator.geocode(location)
    return location.latitude, location.longitude

@retrying.retry(wait_exponential_multiplier=1000, wait_exponential_max=10000)
def geocode_with_retry(geolocator, location):
    """
    retrying decorator incase the nominatim encouters challenges while loading
    """
    return geolocator.geocode(location)


def calculate_distance(location1, location2):
    """
    Implements distance calculation logic
    It uses the location format: (latitude, longitude)
    """
    current = get_lat_lng(location1)
    pickup_location = get_lat_lng(location2)

    distance = geodesic(pickup_location, current).kilometers
    return distance

def allocate_parcel(parcel):
    """
    Allocates a specific parcel delivery to the closest available rider.
    Uses parcel.sender_id to fetch sender details.
    """
    if not parcel or not parcel.sender_id:
        current_app.logger.error("allocate_parcel called with invalid parcel or missing sender_id.")
        return None

    sender = Sender.query.get(parcel.sender_id)
    if not sender:
        current_app.logger.error(f"Could not find sender with ID {parcel.sender_id} for Parcel {parcel.id}.")
        return None

    available_riders = Rider.query.filter_by(status='available').all()
    if not available_riders:
        current_app.logger.info(f"No available riders found for Parcel {parcel.id}.")
        return None

    pickup_location = parcel.pickup_location
    closest_rider = None
    min_distance = float('inf')

    # Exclude rider previously assigned if parcel status is 'pending' (meaning it was rejected)
    # Note: This assumes parcel.rider_id holds the *last* assigned rider if rejected.
    # Consider a separate 'rejected_by' list if multiple rejections are possible.
    rejected_rider_id = parcel.rider_id if parcel.status == 'pending' else None

    for rider in available_riders:
        if rider.id == rejected_rider_id:
            continue

        if not rider.current_location:
            current_app.logger.warning(f"Rider {rider.id} has no current_location set, skipping.")
            continue

        distance = calculate_distance(pickup_location, rider.current_location)
        current_app.logger.debug(f"Distance from {pickup_location} to Rider {rider.id} ({rider.current_location}): {distance} km")
        if distance < min_distance:
            closest_rider = rider
            min_distance = distance

    if closest_rider:
        try:
            parcel.status = 'allocated'
            parcel.rider_id = closest_rider.id
            closest_rider.status = 'unavailable'
            db.session.commit()
            current_app.logger.info(f"Parcel {parcel.id} allocated to Rider {closest_rider.id} (Distance: {min_distance:.2f} km)")

            notify_rider_new_assignment(closest_rider.email, parcel, closest_rider)

            send_rider_details_email(sender.email, closest_rider, parcel.tracking_number)

            sender_name = getattr(sender, 'username', 'Customer')
            sender_contact = getattr(sender, 'contact_number', None)
            rider_contact = getattr(closest_rider, 'contact_number', None)

            if sender_contact:
                sender_message = f"Your Suivi parcel {parcel.tracking_number} is allocated to rider {closest_rider.username} ({closest_rider.contact_number}). Track online."
                send_bulk_sms(sender_contact, sender_message)
            else:
                 current_app.logger.warning(f"Sender {sender.id} has no contact_number for SMS notification (Parcel {parcel.id}).")

            if rider_contact:
                rider_message = f"New Suivi assignment {parcel.tracking_number}: Pickup '{parcel.pickup_location}', Deliver to '{parcel.delivery_location}'. Receiver: {parcel.receiver_name} ({parcel.receiver_contact})."
                send_bulk_sms(rider_contact, rider_message)
            else:
                 current_app.logger.warning(f"Rider {closest_rider.id} has no contact_number for SMS notification (Parcel {parcel.id}).")

            return closest_rider

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error during parcel allocation commit/notification for Parcel {parcel.id}: {e}")
            parcel.status = 'pending'
            parcel.rider_id = None
            if closest_rider:
                closest_rider.status = 'available'
            db.session.commit()
            return None
    else:
        current_app.logger.info(f"No suitable rider found within proximity for Parcel {parcel.id}.")
        return None


def notify_sender_parcel_pending(parcel):
    """Notifies sender if allocation is delayed."""
    if not parcel or not parcel.sender_id:
        current_app.logger.error("notify_sender_parcel_pending called with invalid parcel or missing sender_id.")
        return

    sender = Sender.query.get(parcel.sender_id)
    if not sender:
        current_app.logger.error(f"Could not find sender with ID {parcel.sender_id} for pending notification (Parcel {parcel.id}).")
        return

    sender_email = getattr(sender, 'email', None)
    sender_name = getattr(sender, 'username', 'Customer')

    if not sender_email:
         current_app.logger.warning(f"Sender {sender.id} has no email for pending notification (Parcel {parcel.id}).")
         return

    subject = f"Update on Your Suivi Parcel {parcel.tracking_number}"
    body = (
        f"Dear {sender_name},\n\n"
        f"We're still working on assigning a rider for your parcel pickup from '{parcel.pickup_location}'. "
        f"We apologize for the delay and appreciate your patience.\n\n"
        f"You can track updates using your tracking number: {parcel.tracking_number}\n\n"
        f"Thank you,\nThe Suivi Team"
    )
    msg = Message(subject=subject, recipients=[sender_email], body=body)

    try:
        mail.send(msg)
        current_app.logger.info(f"Pending allocation notification sent to {sender_email} for Parcel {parcel.id}")
    except Exception as e:
        current_app.logger.error(f"Failed to send pending allocation email to {sender_email} for Parcel {parcel.id}: {e}")


def notify_rider_new_assignment(rider_email, parcel, rider):
    """Sends email notification to rider about new assignment."""
    if not rider_email:
        current_app.logger.warning(f"Cannot notify rider {rider.id} for parcel {parcel.id}: Email missing.")
        return

    subject = f'New Suivi Delivery Assignment: {parcel.tracking_number}'
    try:
        html_content = render_template('./new_assignment_email.html', parcel=parcel, rider=rider)
        msg = Message(subject=subject, recipients=[rider_email], html=html_content)
        mail.send(msg)
        current_app.logger.info(f"New assignment email sent to rider {rider.id} ({rider_email}) for parcel {parcel.id}")
    except Exception as e:
        current_app.logger.error(f"Failed to send new assignment email to rider {rider.id} ({rider_email}): {e}")


def send_rider_details_email(recipient_email, assigned_rider, tracking_number):
    """Sends email to sender with assigned rider details."""
    if not recipient_email:
        current_app.logger.warning(f"Cannot send rider details for parcel {tracking_number}: Recipient email missing.")
        return

    subject = f'Rider Assigned for Your Suivi Parcel {tracking_number}'
    try:
        html_content = render_template('emails/rider_details_email.html', rider=assigned_rider, tracking_number=tracking_number)
        msg = Message(subject=subject, recipients=[recipient_email], html=html_content)
        mail.send(msg)
        current_app.logger.info(f"Rider details email sent to {recipient_email} for parcel {tracking_number}")
    except Exception as e:
        current_app.logger.error(f"Failed to send rider details email to {recipient_email} for parcel {tracking_number}: {e}")


def notify_sender_rejected(parcel):
    """Notifies sender if no rider was found."""
    if not parcel or not parcel.sender_id:
        current_app.logger.error("notify_sender_rejected called with invalid parcel or missing sender_id.")
        return

    sender = Sender.query.get(parcel.sender_id)
    if not sender:
        current_app.logger.error(f"Could not find sender with ID {parcel.sender_id} for pending notification (Parcel {parcel.id}).")
        return

    sender_email = getattr(sender, 'email', None)
    sender_name = getattr(sender, 'username', 'Customer')

    if not sender_email:
         current_app.logger.warning(f"Sender {sender.id} has no email for pending notification (Parcel {parcel.id}).")
         return

    subject = f"Update on Your Suivi Parcel {parcel.tracking_number}"
    body = (
        f"Dear {sender_name},\n\n"
        f"We're sorry to inform that all riders are currently unavailable for your parcel pickup from '{parcel.pickup_location}'. "
        f"We apologize for the inconveniences and appreciate your patience.\n\n"
        f"You can try again in 1 hour while we also check for the next available rider.\n\n"
        f"Thank you,\nThe Suivi Team"
    )
    msg = Message(subject=subject, recipients=[sender_email], body=body)

    try:
        mail.send(msg)
        current_app.logger.info(f"Rejected allocation notification sent to {sender_email} for Parcel {parcel.id}")
    except Exception as e:
        current_app.logger.error(f"Failed to send rejected allocation email to {sender_email} for Parcel {parcel.id}: {e}")


def start_scheduler():
    if not scheduler.running:
        scheduler.start()

    if not scheduler.get_job('check_pending_parcels_job'):
        scheduler.add_job(
            func=check_pending_parcels,
            trigger=IntervalTrigger(minutes=5),
            id='check_pending_parcels_job',
            name='Check pending parcels every 5 minutes',
            replace_existing=True
        )

    atexit.register(lambda: scheduler.shutdown())


def check_pending_parcels():
    with app.app_context():
        now = datetime.utcnow()

        pending_parcels_exist = Parcel.query.filter_by(status='pending').first()
        if not pending_parcels_exist:
            print(f"No pending parcels found at {datetime.now()}. Skipping the check.")
            scheduler.remove_job('check_pending_parcels_job')
            return

        pending_parcels = Parcel.query.filter_by(status='pending').all()

        for parcel in pending_parcels:
            time_since_last_update = now - parcel.updated_at

            if time_since_last_update > timedelta(minutes=60):
                notify_sender_rejected(parcel)
                db.session.delete(parcel)
                db.session.commit()
                return
            if time_since_last_update > timedelta(minutes=30):
                notify_sender_parcel_pending(parcel)
            try:
                closest_rider = allocate_parcel(parcel)
                if closest_rider:
                    parcel.status = 'allocated'
                    db.session.commit()
            except Exception as e:
                print(f"Error allocating parcel {parcel.id}: {e}")

            print(f"Attempted to allocate parcel {parcel.id} at {datetime.now()}")

        remaining_pending_parcels = Parcel.query.filter_by(status='pending').count()
        if remaining_pending_parcels == 0:
            print(f"All pending parcels processed. Removing the job at {datetime.now()}.")
            scheduler.remove_job('check_pending_parcels_job')



@parcel.route('/update_assignment', methods=['POST'])
@login_required
def update_assignment():
    data = request.json
    if not data:
        return jsonify({'error': 'Invalid request body'}), 400

    parcel_id = data.get('parcel_id')
    action = data.get('action')

    if not parcel_id or not action:
        return jsonify({'error': 'Missing parcel_id or action'}), 400

    valid_statuses = ['allocated', 'in_progress', 'shipped']
    assignment = Parcel.query.filter(
        Parcel.id == parcel_id,
        Parcel.rider_id == current_user.id,
        Parcel.status.in_(valid_statuses)
    ).first()

    if not assignment:
        exists = Parcel.query.get(parcel_id)
        if not exists:
             return jsonify({'error': 'Assignment not found'}), 404
        elif exists.rider_id != current_user.id:
             return jsonify({'error': 'Forbidden: You are not assigned to this parcel'}), 403
        else:
             return jsonify({'error': f'Assignment status ({exists.status}) does not allow this action'}), 400

    try:
        if action == 'accept':
            if assignment.status != 'allocated':
                 return jsonify({'error': 'Cannot accept: Assignment not in allocated state'}), 400
            assignment.status = 'in_progress'
            db.session.commit()
            flash("Assignment accepted!", 'success')
            return jsonify({'success': True, 'message': 'Assignment accepted.'})

        elif action == 'reject':
            if assignment.status != 'allocated':
                 return jsonify({'error': 'Cannot reject: Assignment not in allocated state'}), 400

            rider = Rider.query.get(assignment.rider_id)
            if rider:
                rider.status = 'available'

            assignment.status = 'pending'
            assignment.rider_id = None
            db.session.commit()
            flash("Assignment rejected.", 'info')

            try:
                allocate_parcel(assignment)
            except Exception as alloc_e:
                current_app.logger.error(f"Error during reallocation attempt after rejection for parcel {parcel_id}: {alloc_e}")

            return jsonify({'success': True, 'message': 'Assignment rejected.'})

        elif action == 'shipped':
            if assignment.status != 'in_progress':
                 return jsonify({'error': 'Cannot mark as shipped: Assignment not in progress'}), 400
            assignment.status = 'shipped'
            db.session.commit()
            flash("Parcel marked as picked up!", 'success')
            return jsonify({'success': True, 'message': 'Parcel marked as shipped.'})

        elif action == 'arrived':
            if assignment.status != 'shipped':
                 return jsonify({'error': 'Cannot mark as arrived: Assignment not shipped'}), 400
            assignment.status = 'arrived'
            rider = Rider.query.get(assignment.rider_id)
            if rider:
                rider.status = 'available'
            db.session.commit()
            flash("Parcel marked as delivered!", 'success')
            return jsonify({'success': True, 'message': 'Parcel marked as delivered.'})

        else:
            return jsonify({'error': f'Invalid action: {action}'}), 400

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error updating assignment {parcel_id} for action {action}: {e}")
        return jsonify({'error': 'An internal error occurred. Please try again.'}), 500


@parcel.route('/view_parcel_history', methods=['GET', 'POST'])
@login_required
def view_parcel_history():
    if current_user.is_authenticated:
        parcels = Parcel.query.filter_by(sender_id=current_user.id).all()

        open_statuses = ['pending', 'allocated', 'in_progress', 'shipped']
        closed_statuses = ['arrived']

        open_parcels = [parcel for parcel in parcels if parcel.status in open_statuses]
        closed_parcels = [parcel for parcel in parcels if parcel.status in closed_statuses]


        return render_template('view_parcel_history.html', 
                               open_parcels=open_parcels,
                               closed_parcels=closed_parcels,
                               all_parcels=parcels)
    else:
        flash('Log in to view your parcel history!', 'danger')
        return redirect(url_for('auth.login'))





@parcel.route('/view_rider_history', methods=['GET', 'POST'])
@login_required
def view_rider_history():
    if current_user.is_authenticated:
        parcels = Parcel.query.filter_by(rider_id=current_user.id).all()

        open_orders = [parcel for parcel in parcels if parcel.status in ['in_progress', 'shipped']]
        closed_orders = [parcel for parcel in parcels if parcel.status == 'arrived']

        return render_template('view_rider_history.html',
                               open_orders=open_orders,
                               closed_orders=closed_orders,
                               all_parcels=parcels)
    else:
        flash('Log in to view your parcel history!', 'danger')
        return redirect(url_for('auth.login_rider'))

