from flask import current_app, render_template
from flask_mail import Message
from threading import Thread

from app import mail

def send_async_email(app, msg):
    """Send email asynchronously"""
    with app.app_context():
        mail.send(msg)

def send_email(subject, recipients, html_body, text_body=None):
    """Send email with the given parameters"""
    app = current_app._get_current_object()
    msg = Message(subject, recipients=recipients)
    msg.html = html_body
    if text_body:
        msg.body = text_body
    
    # Send email asynchronously
    Thread(target=send_async_email, args=(app, msg)).start()

def send_booking_confirmation(booking):
    """Send booking confirmation email"""
    subject = f"Tennis Court Booking Confirmation - #{booking.id}"
    recipients = [booking.user.email]
    
    html_body = render_template(
        'email/booking_confirmation.html',
        user=booking.user,
        booking=booking,
        court=booking.court
    )
    
    text_body = f"""
    Booking Confirmation #{booking.id}
    
    Thank you for booking with AceCourt!
    
    Court: {booking.court.name}
    Date: {booking.start_time.strftime('%A, %B %d, %Y')}
    Time: {booking.start_time.strftime('%I:%M %p')} - {booking.end_time.strftime('%I:%M %p')}
    
    Your booking is now confirmed.
    
    The AceCourt Team
    """
    
    # For demo purposes, just print to console instead of sending email
    print(f"Email would be sent to {recipients}: {subject}")
    print(text_body)
    
    # Uncomment to actually send emails
    # send_email(subject, recipients, html_body, text_body)

def send_password_reset_email(user):
    """Send password reset email"""
    token = user.generate_reset_token()
    subject = "Reset Your Password"
    recipients = [user.email]
    
    html_body = render_template(
        'email/reset_password.html',
        user=user,
        token=token
    )
    
    text_body = f"""
    Hello {user.get_full_name()},
    
    To reset your password, please visit the following link:
    
    http://localhost:5000/auth/reset-password/{token}
    
    This link will expire in 1 hour.
    
    The AceCourt Team
    """
    
    # For demo purposes, just print to console instead of sending email
    print(f"Email would be sent to {recipients}: {subject}")
    print(text_body)
    print(f"Reset token: {token}")
    
    # Uncomment to actually send emails
    # send_email(subject, recipients, html_body, text_body)
