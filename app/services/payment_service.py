import requests
from flask import current_app

def setup_paypal_auth():
    """Get PayPal OAuth token"""
    client_id = current_app.config['PAYPAL_CLIENT_ID']
    client_secret = current_app.config['PAYPAL_CLIENT_SECRET']
    mode = current_app.config['PAYPAL_MODE']
    
    base_url = "https://api.sandbox.paypal.com" if mode == 'sandbox' else "https://api.paypal.com"
    auth_url = f"{base_url}/v1/oauth2/token"
    
    response = requests.post(
        auth_url,
        auth=(client_id, client_secret),
        data={'grant_type': 'client_credentials'},
        headers={'Accept': 'application/json', 'Accept-Language': 'en_US'}
    )
    
    if response.status_code == 200:
        return response.json()['access_token'], base_url
    else:
        raise Exception(f"PayPal authentication failed: {response.text}")

def create_paypal_order(amount, description):
    """Create a PayPal order"""
    token, base_url = setup_paypal_auth()
    
    create_order_url = f"{base_url}/v2/checkout/orders"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {
                "currency_code": "USD",
                "value": str(amount)
            },
            "description": description
        }],
        "application_context": {
            "return_url": "http://localhost:5000/payment/success",
            "cancel_url": "http://localhost:5000/payment/cancel"
        }
    }
    
    response = requests.post(create_order_url, json=payload, headers=headers)
    
    if response.status_code in [200, 201]:
        data = response.json()
        return data['id']  # Return the order ID
    else:
        raise Exception(f"Failed to create PayPal order: {response.text}")

def capture_paypal_payment(order_id):
    """Capture an approved PayPal payment"""
    token, base_url = setup_paypal_auth()
    
    capture_url = f"{base_url}/v2/checkout/orders/{order_id}/capture"
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.post(capture_url, headers=headers)
    
    if response.status_code in [200, 201]:
        data = response.json()
        capture = data['purchase_units'][0]['payments']['captures'][0]
        
        return {
            "id": order_id,
            "status": data['status'],
            "amount": capture['amount']['value'],
            "currency": capture['amount']['currency_code']
        }
    else:
        raise Exception(f"Failed to capture PayPal payment: {response.text}")

def refund_payment(payment_id):
    """Simulate refund for demo purposes"""
    # In a real application, this would call the PayPal refund API
    # For this demo, we'll just return True to simulate successful refund
    return True
