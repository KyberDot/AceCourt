from datetime import datetime
from app import db

class Voucher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    value = db.Column(db.Float, nullable=False)
    valid_from = db.Column(db.DateTime)
    valid_until = db.Column(db.DateTime)
    max_uses = db.Column(db.Integer, default=1)
    current_uses = db.Column(db.Integer, default=0)
    court_id = db.Column(db.Integer, db.ForeignKey('court.id'))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='active')  # active, expired, depleted
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User')
    court = db.relationship('Court')
    
    def is_valid(self, court_id=None):
        """Check if voucher is valid for use"""
        now = datetime.utcnow()
        
        # Check status
        if self.status != 'active':
            return False
            
        # Check usage limit
        if self.current_uses >= self.max_uses:
            return False
            
        # Check validity period
        if self.valid_from and now < self.valid_from:
            return False
            
        if self.valid_until and now > self.valid_until:
            return False
            
        # Check court restriction
        if self.court_id and court_id and self.court_id != court_id:
            return False
            
        return True
    
    def use(self, booking_id, user_id):
        """Use voucher for a booking"""
        if not self.is_valid():
            return False
            
        # Record usage
        usage = VoucherUsage(
            voucher_id=self.id,
            booking_id=booking_id,
            user_id=user_id
        )
        
        db.session.add(usage)
        
        # Update usage count
        self.current_uses += 1
        if self.current_uses >= self.max_uses:
            self.status = 'depleted'
            
        db.session.commit()
        return True
    
    def __repr__(self):
        return f'<Voucher {self.code} - ${self.value}>'


class VoucherUsage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voucher_id = db.Column(db.Integer, db.ForeignKey('voucher.id'), nullable=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    used_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    voucher = db.relationship('Voucher')
    booking = db.relationship('Booking')
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<VoucherUsage {self.id} - Voucher {self.voucher_id} - Booking {self.booking_id}>'
