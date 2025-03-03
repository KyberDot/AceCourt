from app import db

class PricingRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    court_id = db.Column(db.Integer, db.ForeignKey('court.id'))
    day_of_week = db.Column(db.String(20))  # Monday, Tuesday, etc., or comma-separated list
    start_hour = db.Column(db.Integer)
    end_hour = db.Column(db.Integer)
    modifier_type = db.Column(db.String(20), nullable=False)  # percentage, fixed
    modifier_value = db.Column(db.Float, nullable=False)
    specificity = db.Column(db.Integer, default=1)  # Higher means more specific rule
    is_final = db.Column(db.Boolean, default=False)  # If true, stop applying rules after this one
    valid_from = db.Column(db.Date)
    valid_until = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')  # active, inactive
    
    # Relationships
    court = db.relationship('Court')
    
    def applies_to(self, start_time, end_time):
        """Check if rule applies to the given time period"""
        # Check status
        if self.status != 'active':
            return False
            
        # Check validity period
        if self.valid_from and start_time.date() < self.valid_from:
            return False
            
        if self.valid_until and start_time.date() > self.valid_until:
            return False
        
        # Check day of week
        if self.day_of_week:
            day_name = start_time.strftime('%A')
            if day_name not in self.day_of_week.split(','):
                return False
        
        # Check hour range
        if self.start_hour is not None and self.end_hour is not None:
            hour = start_time.hour
            if not (self.start_hour <= hour < self.end_hour):
                return False
                
        return True
    
    def __repr__(self):
        return f'<PricingRule {self.name}>'
