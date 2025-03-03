from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from .config import config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
mail = Mail()

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Register blueprints
    from .routes import all_blueprints
    for bp in all_blueprints:
        app.register_blueprint(bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        # Import models to ensure they're registered with SQLAlchemy
        from .models import user, court, booking, transaction, voucher, pricing_rule
        
        # Create admin user if doesn't exist
        from .models.user import User
        admin = User.query.filter_by(email='admin@acecourt.com').first()
        if not admin:
            admin = User(
                email='admin@acecourt.com',
                first_name='Admin',
                last_name='User',
                role='admin'
            )
            admin.password = 'adminpass'  # Set a default password
            db.session.add(admin)
            db.session.commit()
            print('Admin user created with email: admin@acecourt.com and password: adminpass')
    
    return app
