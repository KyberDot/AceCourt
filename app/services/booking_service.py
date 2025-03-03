from datetime import datetime
from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

from app import db
from app.models.booking import Booking
from app.models.court import Court
from app.models.transaction import Transaction

def admin_required(f):
    """Decorator to check if current user is an admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def court_manager_required(f):
    """Decorator to check if current user is a court manager or admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not (current_user.is_admin() or current_user.is_court_manager()):
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def create_booking(user_id, court_id, start_time, end_time, notes=None):
    """Create a new booking"""
    # Validate parameters
    if not all([user_id, court_id, start_time, end_time]):
        return None, "Missing required parameters"
    
    # Check if court exists
    court = Court.query.get(court_id)
    if not court:
        return None, "Court not found"
    
    # Check if court is available
    if not court.is_available(start_time, end_time):
        return None, "Court is not available for this time period"
    
    # Create booking
    booking = Booking(
        user_id=user_id,
        court_id=court_id,
        start_time=start_time,
        end_time=end_time,
        status='pending',
        notes=notes
    )
    
    db.session.add(booking)
    db.session.commit()
    
    return booking, None

def cancel_booking(booking_id):
    """Cancel a booking and process refund if needed"""
    booking = Booking.query.get(booking_id)
    
    if not booking:
        return False, "Booking not found"
    
    if booking.status == 'cancelled':
        return False, "Booking is already cancelled"
    
    if booking.is_past:
        return False, "Cannot cancel past bookings"
    
    # Update booking status
    booking.status = 'cancelled'
    
    # Process refund if booking was paid
    if booking.is_paid and booking.transaction:
        from app.services.payment_service import refund_payment
        
        # Attempt to refund payment
        if refund_payment(booking.transaction.payment_id):
            booking.transaction.status = 'refunded'
            db.session.commit()
            return True, "Booking cancelled and payment refunded"
        else:
            # If refund fails, still cancel but notify
            db.session.commit()
            return True, "Booking cancelled but payment refund failed. Please contact support."
    
    db.session.commit()
    return True, "Booking cancelled successfully"
