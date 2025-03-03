from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
import random, string
from datetime import datetime

from app import db
from app.models.voucher import Voucher
from app.models.court import Court
from app.services.booking_service import admin_required

voucher_bp = Blueprint('voucher', __name__, url_prefix='/vouchers')

def generate_voucher_code(length=8):
    """Generate a random voucher code"""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        # Make sure code is unique
        if not Voucher.query.filter_by(code=code).first():
            return code

@voucher_bp.route('/')
@login_required
@admin_required
def list():
    vouchers = Voucher.query.order_by(Voucher.created_at.desc()).all()
    return render_template('admin/voucher/list.html', vouchers=vouchers)

@voucher_bp.route('/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create():
    if request.method == 'POST':
        # Generate a unique code
        code = generate_voucher_code()
        
        # Get form data
        value = float(request.form.get('value'))
        max_uses = int(request.form.get('max_uses', 1))
        court_id = request.form.get('court_id')
        
        # Convert empty string to None
        if court_id == '':
            court_id = None
        
        # Parse dates
        valid_from = None
        valid_until = None
        
        from_date = request.form.get('valid_from')
        if from_date:
            valid_from = datetime.strptime(from_date, '%Y-%m-%d')
            
        until_date = request.form.get('valid_until')
        if until_date:
            valid_until = datetime.strptime(until_date, '%Y-%m-%d')
            valid_until = valid_until.replace(hour=23, minute=59, second=59)
        
        # Create voucher
        voucher = Voucher(
            code=code,
            value=value,
            max_uses=max_uses,
            current_uses=0,
            court_id=court_id,
            valid_from=valid_from,
            valid_until=valid_until,
            creator_id=current_user.id,
            status='active',
            created_at=datetime.utcnow()
        )
        
        db.session.add(voucher)
        db.session.commit()
        
        flash(f'Voucher created successfully with code: {code}', 'success')
        return redirect(url_for('voucher.list'))
    
    # GET request - show form
    courts = Court.query.filter_by(status='active').all()
    return render_template('admin/voucher/create.html', courts=courts)

@voucher_bp.route('/<int:voucher_id>/deactivate', methods=['POST'])
@login_required
@admin_required
def deactivate(voucher_id):
    voucher = Voucher.query.get_or_404(voucher_id)
    voucher.status = 'inactive'
    db.session.commit()
    
    flash('Voucher has been deactivated', 'success')
    return redirect(url_for('voucher.list'))

@voucher_bp.route('/verify', methods=['POST'])
@login_required
def verify():
    code = request.form.get('code').strip().upper()
    court_id = request.form.get('court_id')
    
    if not code:
        return {'valid': False, 'message': 'Please enter a voucher code'}, 400
    
    voucher = Voucher.query.filter_by(code=code).first()
    
    if not voucher:
        return {'valid': False, 'message': 'Invalid voucher code'}, 404
    
    if not voucher.is_valid(court_id):
        if voucher.status != 'active':
            return {'valid': False, 'message': 'This voucher is no longer active'}, 400
        elif voucher.current_uses >= voucher.max_uses:
            return {'valid': False, 'message': 'This voucher has reached its usage limit'}, 400
        elif voucher.valid_until and datetime.utcnow() > voucher.valid_until:
            return {'valid': False, 'message': 'This voucher has expired'}, 400
        elif voucher.valid_from and datetime.utcnow() < voucher.valid_from:
            return {'valid': False, 'message': 'This voucher is not valid yet'}, 400
        elif voucher.court_id and int(court_id) != voucher.court_id:
            return {'valid': False, 'message': 'This voucher is not valid for this court'}, 400
        else:
            return {'valid': False, 'message': 'This voucher is not valid'}, 400
    
    return {
        'valid': True, 
        'value': voucher.value,
        'message': f'Voucher applied: ${voucher.value} discount'
    }, 200
