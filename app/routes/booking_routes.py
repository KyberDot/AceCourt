from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user

from app import db
from app.models.booking import Booking
from app.models.court import Court
from app.models.transaction import Transaction
from app.services.booking_service import create_booking, cancel_booking, admin_required
from app.services.pricing_service import calculate_price

booking_bp = Blueprint('booking', __name__, url_prefix='/bookings')

@booking_bp.route('/calendar')
def calendar():
    courts = Court.query.filter_by(status='active').all()
    return render_template('booking/calendar.html', courts=courts)

@booking_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'GET':
        court_id = request.args.get('court_id')
        date_str = request.args.get('date')
        start_time_str = request.args.get('start_time')
        end_time_str = request.args.get('end_time')
        
        if not all([court_id, date_str, start_time_str, end_time_str]):
            flash('Missing booking parameters', 'danger')
            return redirect(url_for('booking.calendar'))
        
        try:
            court = Court.query.get_or_404(court_id)
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(f"{date_str} {start_time_str}", '%Y-%m-%d %H:%M')
            end_time = datetime.strptime(f"{date_str} {end_time_str}", '%Y-%m-%d %H:%M')
            
            price = calculate_price(court.id, start_time, end_time)
            
            return render_template(
                'booking/create.html',
                court=court,
                date=date,
                start_time=start_time,
                end_time=end_time,
                price=price
            )
        
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            return redirect(url_for('booking.calendar'))
    
    elif request.method == 'POST':
        court_id = request.form.get('court_id')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        notes = request.form.get('notes')
        
        try:
            start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
            end_time = datetime.strptime(end_time_str, '%Y-%m-%d %H:%M:%S')
            
            booking, error = create_booking(
                current_user.id, 
                int(court_id), 
                start_time, 
                end_time,
                notes
            )
            
            if error:
                flash(error, 'danger')
                return redirect(url_for('booking.calendar'))
            
            # Redirect to payment page
            return redirect(url_for('payment.checkout', booking_id=booking.id))
        
        except Exception as e:
            flash(f'Error creating booking: {str(e)}', 'danger')
            return redirect(url_for('booking.calendar'))

@booking_bp.route('/my-bookings')
@login_required
def my_bookings():
    # Get upcoming bookings
    upcoming_bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.end_time > datetime.utcnow(),
        Booking.status != 'cancelled'
    ).order_by(Booking.start_time).all()
    
    # Get past bookings
    past_bookings = Booking.query.filter(
        Booking.user_id == current_user.id,
        Booking.end_time <= datetime.utcnow()
    ).order_by(Booking.start_time.desc()).all()
    
    return render_template(
        'booking/my_bookings.html', 
        upcoming_bookings=upcoming_bookings, 
        past_bookings=past_bookings
    )

@booking_bp.route('/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    
    # Check if user owns the booking or is admin
    if booking.user_id != current_user.id and not current_user.is_admin():
        flash('You do not have permission to cancel this booking', 'danger')
        return redirect(url_for('booking.my_bookings'))
    
    success, message = cancel_booking(booking_id)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'danger')
    
    return redirect(url_for('booking.my_bookings'))

@booking_bp.route('/admin')
@login_required
@admin_required
def admin_list():
    # Get all bookings for admin view
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_template('admin/booking/list.html', bookings=bookings)

@booking_bp.route('/admin/<int:booking_id>')
@login_required
@admin_required
def admin_detail(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    return render_template('admin/booking/detail.html', booking=booking)
