from datetime import datetime
from app import db

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_id = db.Column(db.String(100))  # External payment ID (e.g., PayPal)
    payment_method = db.Column(db.String(50))  # paypal, voucher, etc.
    status = db.Column(db.String(20))  # completed, pending, refunded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    booking = db.relationship('Booking', backref='transaction', uselist=False)
    
    def __repr__(self):
        return f'<Transaction {self.id} - Booking {self.booking_id} - ${self.amount}>'
