from datetime import datetime, timedelta
from app import db

class Court(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    court_type = db.Column(db.String(20))  # clay, hard, grass
    indoor = db.Column(db.Boolean, default=False)
    has_lighting = db.Column(db.Boolean, default=False)
    base_price_per_hour = db.Column(db.Float, nullable=False, default=20.0)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')  # active, maintenance, inactive
    
    # Relationships
    bookings = db.relationship('Booking', backref='court', lazy='dynamic')
    
    def is_available(self, start_time, end_time):
        """Check if court is available for the specified time period"""
        from .booking import Booking
        
        # Check if court is active
        if self.status != 'active':
            return False
            
        # Check for overlapping bookings
        overlap = Booking.query.filter(
            Booking.court_id == self.id,
            Booking.status != 'cancelled',
            Booking.start_time < end_time,
            Booking.end_time > start_time
        ).first()
        
        return overlap is None
    
    def get_available_slots(self, date, slot_duration=60):
        """Get available time slots for a specific date"""
        from .booking import Booking
        
        # Define operating hours (e.g., 8 AM to 10 PM)
        opening_hour = 8
        closing_hour = 22
        
        # Create datetime objects for start and end of day
        start_of_day = datetime.combine(date, datetime.min.time().replace(hour=opening_hour))
        end_of_day = datetime.combine(date, datetime.min.time().replace(hour=closing_hour))
        
        # Get all bookings for this court on the specified date
        bookings = Booking.query.filter(
            Booking.court_id == self.id,
            Booking.status != 'cancelled',
            Booking.start_time >= start_of_day,
            Booking.start_time < end_of_day
        ).order_by(Booking.start_time).all()
        
        # Generate all possible slots
        all_slots = []
        current_time = start_of_day
        while current_time < end_of_day:
            slot_end = current_time + timedelta(minutes=slot_duration)
            all_slots.append((current_time, slot_end))
            current_time = slot_end
        
        # Filter out booked slots
        available_slots = []
        for slot_start, slot_end in all_slots:
            is_available = True
            
            for booking in bookings:
                if (booking.start_time < slot_end and booking.end_time > slot_start):
                    is_available = False
                    break
                    
            if is_available and self.status == 'active':
                available_slots.append((slot_start, slot_end))
        
        return available_slots
    
    def __repr__(self):
        return f'<Court {self.name}>'
