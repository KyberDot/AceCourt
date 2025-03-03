from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user

from app import db
from app.models.court import Court
from app.services.booking_service import admin_required, court_manager_required

court_bp = Blueprint('court', __name__, url_prefix='/courts')

@court_bp.route('/')
def list():
    courts = Court.query.filter_by(status='active').all()
    return render_template('court/list.html', courts=courts)

@court_bp.route('/<int:court_id>')
def detail(court_id):
    court = Court.query.get_or_404(court_id)
    return render_template('court/detail.html', court=court)

@court_bp.route('/admin')
@login_required
@admin_required
def admin_list():
    courts = Court.query.all()
    return render_template('admin/court/list.html', courts=courts)

@court_bp.route('/admin/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add():
    if request.method == 'POST':
        name = request.form.get('name')
        court_type = request.form.get('court_type')
        indoor = 'indoor' in request.form
        has_lighting = 'has_lighting' in request.form
        base_price_per_hour = float(request.form.get('base_price_per_hour', 20.0))
        description = request.form.get('description', '')
        
        court = Court(
            name=name,
            court_type=court_type,
            indoor=indoor,
            has_lighting=has_lighting,
            base_price_per_hour=base_price_per_hour,
            description=description,
            status='active'
        )
        
        db.session.add(court)
        db.session.commit()
        
        flash(f'Court "{name}" has been added successfully', 'success')
        return redirect(url_for('court.admin_list'))
    
    return render_template('admin/court/add.html')

@court_bp.route('/admin/<int:court_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit(court_id):
    court = Court.query.get_or_404(court_id)
    
    if request.method == 'POST':
        court.name = request.form.get('name')
        court.court_type = request.form.get('court_type')
        court.indoor = 'indoor' in request.form
        court.has_lighting = 'has_lighting' in request.form
        court.base_price_per_hour = float(request.form.get('base_price_per_hour', 20.0))
        court.description = request.form.get('description', '')
        court.status = request.form.get('status')
        
        db.session.commit()
        
        flash(f'Court "{court.name}" has been updated successfully', 'success')
        return redirect(url_for('court.admin_list'))
    
    return render_template('admin/court/edit.html', court=court)

@court_bp.route('/admin/<int:court_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete(court_id):
    court = Court.query.get_or_404(court_id)
    
    # Instead of deleting, set status to inactive
    court.status = 'inactive'
    db.session.commit()
    
    flash(f'Court "{court.name}" has been deactivated', 'success')
    return redirect(url_for('court.admin_list'))
