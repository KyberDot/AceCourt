from datetime import datetime
from app import db

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    court_id = db.Column(db.Integer, db.ForeignKey('court.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)
    
    # Relationships
    user = db.relationship('User', backref='bookings')
    
    @property
    def duration_hours(self):
        """Calculate booking duration in hours"""
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 3600
    
    @property
    def is_paid(self):
        """Check if booking has been paid"""
        return self.transaction is not None and self.transaction.status == 'completed'
    
    @property
    def is_past(self):
        """Check if booking is in the past"""
        return self.end_time < datetime.utcnow()
    
    @property
    def can_cancel(self):
        """Check if booking can be cancelled"""
        return self.status != 'cancelled' and not self.is_past
    
    def __repr__(self):
        return f'<Booking {self.id} - Court {self.court_id} - {self.start_time.strftime("%Y-%m-%d %H:%M")}>'
