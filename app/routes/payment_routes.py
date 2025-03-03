from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user

from app import db
from app.models.booking import Booking
from app.models.transaction import Transaction
from app.services.pricing_service import calculate_price
from app.services.payment_service import create_paypal_order, capture_paypal_payment
from app.services.email_service import send_booking_confirmation

payment_bp = Blueprint('payment', __name__, url_prefix='/payment')

@payment_bp.route('/checkout/<int:booking_id>')
@login_required
def checkout(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if user owns the booking
    if booking.user_id != current_user.id:
        flash('You do not have permission to view this booking', 'danger')
        return redirect(url_for('booking.my_bookings'))
    
    # Check if booking is already paid
    if booking.is_paid:
        flash('This booking has already been paid for', 'info')
        return redirect(url_for('booking.my_bookings'))
    
    # Calculate price
    price = calculate_price(booking.court_id, booking.start_time, booking.end_time)
    
    return render_template(
        'payment/checkout.html', 
        booking=booking, 
        price=price,
        paypal_client_id=current_app.config['PAYPAL_CLIENT_ID']
    )

@payment_bp.route('/success/<int:booking_id>')
@login_required
def success(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if user owns the booking
    if booking.user_id != current_user.id:
        flash('You do not have permission to view this booking', 'danger')
        return redirect(url_for('booking.my_bookings'))
    
    return render_template('payment/success.html', booking=booking)

@payment_bp.route('/cancel/<int:booking_id>')
@login_required
def cancel(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if user owns the booking
    if booking.user_id != current_user.id:
        flash('You do not have permission to view this booking', 'danger')
        return redirect(url_for('booking.my_bookings'))
    
    return render_template('payment/cancel.html', booking=booking)

@payment_bp.route('/api/create-paypal-order', methods=['POST'])
@login_required
def api_create_order():
    data = request.json
    booking_id = data.get('booking_id')
    
    if not booking_id:
        return jsonify({'error': 'Booking ID is required'}), 400
    
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if user owns the booking
    if booking.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Calculate price
    try:
        price = calculate_price(booking.court_id, booking.start_time, booking.end_time)
        order_id = create_paypal_order(price, f"AceCourt booking #{booking.id}")
        
        return jsonify({'orderId': order_id}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/api/capture-paypal-order', methods=['POST'])
@login_required
def api_capture_order():
    data = request.json
    order_id = data.get('orderID')
    booking_id = data.get('bookingId')
    
    if not order_id or not booking_id:
        return jsonify({'error': 'Order ID and Booking ID are required'}), 400
    
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if user owns the booking
    if booking.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        # Capture the payment
        payment_details = capture_paypal_payment(order_id)
        
        # Create transaction record
        transaction = Transaction(
            booking_id=booking.id,
            amount=float(payment_details['amount']),
            payment_id=payment_details['id'],
            payment_method='paypal',
            status='completed'
        )
        
        db.session.add(transaction)
        
        # Update booking status to confirmed
        booking.status = 'confirmed'
        db.session.commit()
        
        # Send confirmation email
        send_booking_confirmation(booking)
        
        return jsonify({
            'success': True,
            'transactionId': transaction.id,
            'redirectUrl': url_for('payment.success', booking_id=booking.id)
        }), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
