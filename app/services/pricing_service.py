from datetime import datetime

from app import db
from app.models.court import Court
from app.models.pricing_rule import PricingRule

def calculate_price(court_id, start_time, end_time):
    """Calculate price for a booking including dynamic pricing rules"""
    court = Court.query.get(court_id)
    
    if not court:
        raise ValueError("Court not found")
    
    # Calculate duration in hours
    duration = (end_time - start_time).total_seconds() / 3600
    
    # Base price calculation
    base_price = court.base_price_per_hour * duration
    
    # Get applicable pricing rules
    rules = PricingRule.query.filter(
        PricingRule.court_id == court_id,
        PricingRule.status == 'active'
    ).order_by(PricingRule.specificity.desc()).all()
    
    # Apply pricing rules
    final_price = base_price
    
    for rule in rules:
        if rule.applies_to(start_time, end_time):
            if rule.modifier_type == 'percentage':
                final_price = final_price * (1 + rule.modifier_value / 100)
            elif rule.modifier_type == 'fixed':
                final_price = final_price + rule.modifier_value
            
            # If rule is final, stop applying further rules
            if rule.is_final:
                break
    
    return round(final_price, 2)
