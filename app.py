from flask import Flask, render_template, request, redirect, url_for
import requests
import json
import os

app = Flask(__name__)

# Constants (you can make these environment variables in a real app or configure in Coolify)
TEST_SERVER_URL = "http://pay.threeg.asia/"
API_KEY_EXAMPLE = "XnUgH1PyIZ8p1iF2IbKUiOBzdrLPNnWq" # Replace with your actual test API key
SALT_EXAMPLE = "FOLzaoJSdbgaNiVVA73vGiIR7yovZury4OdOalPFoWTdKmDVxfoJCJYTs4nhUFS2" # Replace with your actual test salt

@app.route('/', methods=['GET', 'POST'])
def index():
    order_id = request.form.get('order_id') # Persist order_id if it's passed back
    hashed_data = None
    payment_url = None
    qr_data = None
    hash_response = None
    create_response = None
    error_message = None
    success_message = None

    # Default values for form fields (from API examples)
    api_key_val = request.form.get('api_key', API_KEY_EXAMPLE)
    salt_val = request.form.get('salt', SALT_EXAMPLE)
    subamount_1_val = request.form.get('subamount_1', 100)
    subamount_1_label_val = request.form.get('subamount_1_label', 'Test Order')
    order_info_val = request.form.get('order_info', 'Payment for test transaction.')
    order_desc_val = request.form.get('order_desc', 'Description')
    return_url_val = request.form.get('return_url', 'https://www.threegmedia.com/')
    callback_url_val = request.form.get('callback_url', 'http://pocket-api.threeg.asia/callbase')
    discount_val = request.form.get('discount', 0)

    if request.method == 'POST':
        action = request.form.get('action') # Determine which button was clicked

        # Get common parameters from the form
        api_key = request.form['api_key']
        salt = request.form['salt']
        
        try:
            # Step 1: Get New Order ID
            if action == 'get_new_order_id' or action == 'process_payment_flow':
                payload = {
                    "api_key": api_key,
                    "salt": salt
                }
                response = requests.post(f"{TEST_SERVER_URL}payments/getNewOrderId", json=payload)
                response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
                order_id_response = response.json()

                if 'new_id' in order_id_response:
                    order_id = order_id_response['new_id']
                    success_message = f"Successfully obtained Order ID: {order_id}"
                else:
                    raise Exception(f"Failed to get new order ID: {order_id_response.get('message', 'Unknown error')}")

            # Step 2: Generate Hash Data (only if we have an order_id or processing full flow)
            if order_id and (action == 'process_payment_flow'):
                subamount_1 = int(request.form['subamount_1'])
                subamount_1_label = request.form['subamount_1_label']
                order_info = request.form['order_info']
                order_desc = request.form['order_desc']
                return_url = request.form['return_url']
                callback_url = request.form['callback_url']
                discount = int(request.form['discount'])

                hash_payload = {
                    "api_key": api_key,
                    "salt": salt,
                    "subamount_1": subamount_1,
                    "subamount_1_label": subamount_1_label,
                    "subamount_2": 0, "subamount_3": 0, "subamount_4": 0, "subamount_5": 0, # Default to 0
                    "order_id": order_id,
                    "order_info": order_info,
                    "order_desc": order_desc,
                    "return_url": return_url,
                    "callback_url": callback_url,
                    "discount": discount
                }
                response = requests.post(f"{TEST_SERVER_URL}payments/hash", json=hash_payload)
                response.raise_for_status()
                hash_response = response.json()
                
                if 'hashed_data' in hash_response:
                    hashed_data = hash_response['hashed_data']
                    success_message += f"\nSuccessfully generated Hash Data."
                else:
                    raise Exception(f"Failed to get hash data: {hash_response.get('message', 'Unknown error')}")

            # Step 3: Create Payment Link (only if we have hashed_data and processing full flow)
            if hashed_data and (action == 'process_payment_flow'):
                create_payload = {
                    "api_key": api_key,
                    "salt": salt,
                    "hashed_data": hashed_data,
                    "subamount_1": subamount_1,
                    "subamount_1_label": subamount_1_label,
                    "subamount_2": 0, "subamount_3": 0, "subamount_4": 0, "subamount_5": 0, # Default
                    "order_id": order_id,
                    "order_info": order_info,
                    "order_desc": order_desc,
                    "return_url": return_url,
                    "callback_url": callback_url,
                    "discount": discount,
                    "promo": "", "promo_code": "" # Optional fields
                }
                response = requests.post(f"{TEST_SERVER_URL}payments/create", json=create_payload)
                response.raise_for_status()
                create_response = response.json()

                if 'payment_url' in create_response:
                    payment_url = create_response['payment_url']
                    qr_data = create_response.get('qr')
                    success_message += f"\nSuccessfully created Payment Link."
                    # For a seamless test experience, you might want to redirect
                    # to the payment_url directly. For this tester, we'll display it.
                    # return redirect(payment_url_actual)
                else:
                    raise Exception(f"Failed to create payment link: {create_response.get('message', 'Unknown error')}")

        except requests.exceptions.RequestException as e:
            # Catch HTTP errors from requests library
            error_message = f"API Request Error: {e}"
            if e.response:
                try:
                    error_details = e.response.json()
                    error_message += f"\nDetails: {json.dumps(error_details, indent=2)}"
                except json.JSONDecodeError:
                    error_message += f"\nResponse: {e.response.text}"
        except Exception as e:
            # Catch other potential errors in the logic
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
        success_message=success_message
    )

if __name__ == '__main__':
    # Use environment variable for port, or default to 8000
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True) # debug=True for development, turn off for production
