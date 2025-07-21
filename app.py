from flask import Flask, render_template, request, redirect, url_for
import requests
import json
import os

app = Flask(__name__)

# Use environment variables for sensitive data
TEST_SERVER_URL = os.environ.get("TEST_SERVER_URL", "http://pay.threeg.asia/")
API_KEY_EXAMPLE = os.environ.get("API_KEY_EXAMPLE", "XnUgH1PyIZ8p1iF2IbKUiOBzdrLPNnWq")
SALT_EXAMPLE = os.environ.get("SALT_EXAMPLE", "FOLzaoJSdbgaNiVVA73vGiIR7yovZury4OdOalPFoWTdKmDVxfoJCJYTs4nhUFS2")

def safe_int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default

def post_api(endpoint, payload):
    url = f"{TEST_SERVER_URL}{endpoint}"
    response = requests.post(url, json=payload)
    response.raise_for_status()
    return response.json()

@app.route('/', methods=['GET', 'POST'])
def index():
    order_id = request.form.get('order_id')
    hashed_data = None
    payment_url = None
    qr_data = None
    hash_response = None
    create_response = None
    error_message = None
    success_message = None

    # Default values for form fields
    api_key_val = request.form.get('api_key', API_KEY_EXAMPLE)
    salt_val = request.form.get('salt', SALT_EXAMPLE)
    subamount_1_val = safe_int(request.form.get('subamount_1', 100), 100)
    subamount_1_label_val = request.form.get('subamount_1_label', 'Test Order')
    order_info_val = request.form.get('order_info', 'Payment for test transaction.')
    order_desc_val = request.form.get('order_desc', 'Description')
    return_url_val = request.form.get('return_url', 'https://www.threegmedia.com/')
    callback_url_val = request.form.get('callback_url', 'http://pocket-api.threeg.asia/callbase')
    discount_val = safe_int(request.form.get('discount', 0), 0)

    if request.method == 'POST':
        action = request.form.get('action')
        api_key = request.form.get('api_key', API_KEY_EXAMPLE)
        salt = request.form.get('salt', SALT_EXAMPLE)
        try:
            # Step 1: Get New Order ID
            if action in ['get_new_order_id', 'process_payment_flow']:
                payload = {"api_key": api_key, "salt": salt}
                order_id_response = post_api("payments/getNewOrderId", payload)
                order_id = order_id_response.get('new_id')
                if order_id:
                    success_message = f"Successfully obtained Order ID: {order_id}"
                else:
                    raise Exception(f"Failed to get new order ID: {order_id_response.get('message', 'Unknown error')}")

            # Step 2: Generate Hash Data
            if order_id and action == 'process_payment_flow':
                subamount_1 = safe_int(request.form.get('subamount_1'), 100)
                subamount_1_label = request.form.get('subamount_1_label', 'Test Order')
                order_info = request.form.get('order_info', 'Payment for test transaction.')
                order_desc = request.form.get('order_desc', 'Description')
                return_url = request.form.get('return_url', 'https://www.threegmedia.com/')
                callback_url = request.form.get('callback_url', 'http://pocket-api.threeg.asia/callbase')
                discount = safe_int(request.form.get('discount'), 0)

                hash_payload = {
                    "api_key": api_key,
                    "salt": salt,
                    "subamount_1": subamount_1,
                    "subamount_1_label": subamount_1_label,
                    "subamount_2": 0, "subamount_3": 0, "subamount_4": 0, "subamount_5": 0,
                    "order_id": order_id,
                    "order_info": order_info,
                    "order_desc": order_desc,
                    "return_url": return_url,
                    "callback_url": callback_url,
                    "discount": discount
                }
                hash_response = post_api("payments/hash", hash_payload)
                hashed_data = hash_response.get('hashed_data')
                if hashed_data:
                    success_message = (success_message or "") + "\nSuccessfully generated Hash Data."
                else:
                    raise Exception(f"Failed to get hash data: {hash_response.get('message', 'Unknown error')}")

            # Step 3: Create Payment Link
            if hashed_data and action == 'process_payment_flow':
                create_payload = {
                    "api_key": api_key,
                    "salt": salt,
                    "hashed_data": hashed_data,
                    "subamount_1": subamount_1,
                    "subamount_1_label": subamount_1_label,
                    "subamount_2": 0, "subamount_3": 0, "subamount_4": 0, "subamount_5": 0,
                    "order_id": order_id,
                    "order_info": order_info,
                    "order_desc": order_desc,
                    "return_url": return_url,
                    "callback_url": callback_url,
                    "discount": discount,
                    "promo": "", "promo_code": ""
                }
                create_response = post_api("payments/create", create_payload)
                payment_url = create_response.get('payment_url')
                qr_data = create_response.get('qr')
                if payment_url:
                    success_message = (success_message or "") + "\nSuccessfully created Payment Link."
                else:
                    raise Exception(f"Failed to create payment link: {create_response.get('message', 'Unknown error')}")

        except requests.exceptions.RequestException as e:
            error_message = f"API Request Error: {e}"
            if hasattr(e, 'response') and e.response:
                try:
                    error_details = e.response.json()
                    error_message += f"\nDetails: {json.dumps(error_details, indent=2)}"
                except Exception:
                    error_message += f"\nResponse: {getattr(e.response, 'text', '')}"
        except Exception as e:
            error_message = f"An error occurred: {e}"

    return render_template(
        'index.html',
        api_key=api_key_val,
        salt=salt_val,
        subamount_1=subamount_1_val,
        subamount_1_label=subamount_1_label_val,
        order_info=order_info_val,
        order_desc=order_desc_val,
        return_url=return_url_val,
        callback_url=callback_url_val,
        discount=discount_val,
        order_id=order_id,
        hashed_data=hashed_data,
        payment_url=payment_url,
        qr_data=qr_data,
        hash_response=hash_response,
        create_response=create_response,
        error_message=error_message,
        success_message=