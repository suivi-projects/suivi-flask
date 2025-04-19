# payment.py

import os
import requests
import base64
from datetime import datetime
import json
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from flask import current_app

load_dotenv()

MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE")
MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")
MPESA_CALLBACK_URL = os.getenv("MPESA_CALLBACK_URL")
MPESA_ACCOUNT_REFERENCE_PREFIX = os.getenv("MPESA_ACCOUNT_REFERENCE_PREFIX", "SUIVI")
MPESA_TRANSACTION_DESC = os.getenv("MPESA_TRANSACTION_DESC", "Payment for Suivi Delivery")

MPESA_ENV = os.getenv("MPESA_ENV", "sandbox").lower()
MPESA_API_BASE_URL = "https://api.safaricom.co.ke" if MPESA_ENV == "production" else "https://sandbox.safaricom.co.ke"

if not all([MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET, MPESA_SHORTCODE, MPESA_PASSKEY, MPESA_CALLBACK_URL]):
    print("⚠️ WARNING: M-Pesa environment variables not fully configured.")


def get_access_token():
    auth_url = f"{MPESA_API_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    try:
        response = requests.get(
            auth_url,
            auth=HTTPBasicAuth(MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET),
            timeout=10
        )
        response.raise_for_status()
        token_data = response.json()
        logger = current_app.logger if current_app else print
        logger.debug("Access Token Response: %s", token_data)
        return token_data.get("access_token")
    except requests.exceptions.RequestException as e:
        logger = current_app.logger if current_app else print
        logger.error(f"Error getting access token: {e}")
        if 'response' in locals():
            logger.error(f"Response status: {response.status_code}, Response text: {response.text}")
        return None
    except json.JSONDecodeError as e:
        logger = current_app.logger if current_app else print
        logger.error(f"Error decoding token response JSON: {e}")
        if 'response' in locals():
            logger.error(f"Response text: {response.text}")
        return None

def format_phone_number(phone):
    phone = str(phone).strip().replace(" ", "")
    if phone.startswith('+'):
        phone = phone[1:]
    if phone.startswith('0'):
        phone = '254' + phone[1:]
    if not phone.startswith('254') or len(phone) != 12 or not phone.isdigit():
        logger = current_app.logger if current_app else print
        logger.warning(f"Invalid phone number format provided: {phone}")
        return None
    return phone

def initiate_stk_push(phone_number, amount, parcel_id, description=MPESA_TRANSACTION_DESC):
    logger = current_app.logger if current_app else print
    access_token = get_access_token()
    if not access_token:
        logger.error("Failed to get access token. Cannot initiate STK push.")
        return None

    formatted_phone = format_phone_number(phone_number)
    if not formatted_phone:
        return None
    try:
        amount = int(amount)
        if amount < 1:
            logger.error("Amount must be at least 1.")
            return None
    except ValueError:
        logger.error("Invalid amount provided.")
        return None

    stk_push_url = f"{MPESA_API_BASE_URL}/mpesa/stkpush/v1/processrequest"
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password_str = f"{MPESA_SHORTCODE}{MPESA_PASSKEY}{timestamp}"
    password = base64.b64encode(password_str.encode('utf-8')).decode('utf-8')

    account_ref = f"{MPESA_ACCOUNT_REFERENCE_PREFIX}{parcel_id}"

    payload = {
        "BusinessShortCode": MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline" if len(str(MPESA_SHORTCODE)) >= 5 else "CustomerBuyGoodsOnline",
        "Amount": amount,
        "PartyA": formatted_phone,
        "PartyB": MPESA_SHORTCODE,
        "PhoneNumber": formatted_phone,
        "CallBackURL": MPESA_CALLBACK_URL,
        "AccountReference": account_ref,
        "TransactionDesc": description
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    try:
        logger.info(f"Initiating STK Push to {formatted_phone} for KES {amount} (Parcel ID: {parcel_id})")
        logger.debug(f"STK Push Payload: {json.dumps(payload)}")
        response = requests.post(stk_push_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        response_data = response.json()
        logger.info("STK Push Initiation Response: %s", response_data)
        return response_data
    except requests.exceptions.Timeout:
        logger.error("STK Push request timed out.")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error initiating STK push: {e}")
        if 'response' in locals():
            logger.error(f"Response status: {response.status_code}, Response text: {response.text}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding STK push response JSON: {e}")
        if 'response' in locals():
            logger.error(f"Response text: {response.text}")
        return None

def process_mpesa_callback(callback_data, db, Parcel):
    logger = current_app.logger if current_app else print
    logger.info("Processing M-Pesa callback data...")
    logger.debug("Callback Raw Data: %s", json.dumps(callback_data))

    try:
        stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
        merchant_request_id = stk_callback.get('MerchantRequestID')
        checkout_request_id = stk_callback.get('CheckoutRequestID')
        result_code = stk_callback.get('ResultCode')
        result_desc = stk_callback.get('ResultDesc')

        if not checkout_request_id:
            logger.error("Callback data missing CheckoutRequestID.")
            return False, None

        logger.info(f"Processing callback for CheckoutRequestID: {checkout_request_id}, ResultCode: {result_code}")

        parcel = Parcel.query.filter_by(checkout_request_id=checkout_request_id).first()

        if not parcel:
            logger.warning(f"No Parcel found matching CheckoutRequestID: {checkout_request_id}. Ignoring callback.")
            return False, None

        if result_code == 0:
            logger.info(f"Payment successful for Parcel ID: {parcel.id} (CheckoutRequestID: {checkout_request_id})")
            callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            mpesa_receipt = None
            paid_amount = None
            for item in callback_metadata:
                if item.get("Name") == "MpesaReceiptNumber":
                    mpesa_receipt = item.get("Value")
                elif item.get("Name") == "Amount":
                    paid_amount = item.get("Value")

            logger.info(f"Callback Success Details - Amount: {paid_amount}, Receipt: {mpesa_receipt}")

            try:
                parcel.payment_status = 'paid'
                parcel.mpesa_receipt = mpesa_receipt
                db.session.commit()
                logger.info(f"Parcel {parcel.id} updated to 'paid' with receipt {mpesa_receipt}.")
                return True, parcel
            except Exception as e:
                db.session.rollback()
                logger.error(f"DB Error updating Parcel {parcel.id} after successful payment: {e}", exc_info=True)
                return False, parcel

        else:
            logger.warning(f"Payment failed/cancelled for Parcel ID: {parcel.id} (CheckoutRequestID: {checkout_request_id}). Reason: {result_desc} (Code: {result_code})")
            try:
                parcel.payment_status = 'payment_failed'
                db.session.commit()
                logger.info(f"Parcel {parcel.id} updated to 'payment_failed'.")
                return False, parcel
            except Exception as e:
                db.session.rollback()
                logger.error(f"DB Error updating Parcel {parcel.id} after failed payment: {e}", exc_info=True)
                return False, parcel

    except Exception as e:
        logger.error(f"Generic error processing M-Pesa callback: {e}", exc_info=True)
        return False, None
