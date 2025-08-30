# -*- coding: utf-8 -*-
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_mail import Mail
import os
import logging
from logging.handlers import RotatingFileHandler

# 扩展实例
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
cors = CORS()
mail = Mail()

def create_app(config_name=None):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    from config import config
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])
    mail.init_app(app)
    
    # 初始化通知服务
    from app.notification.service import init_notification_service
    init_notification_service(mail)
    
    # 注册蓝图
    from app.api import api_v1
    app.register_blueprint(api_v1, url_prefix='/api/v1')
    
    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    # JWT错误处理
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'message': 'Token has expired'}, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'message': 'Invalid token'}, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'message': 'Authorization token is required'}, 401
    
    # 配置日志
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Event Management Platform startup')
    
    return app

def register_cli_commands(app):
    """注册CLI命令"""
    @app.cli.command()
    def init_db():
        """初始化数据库"""
        from app.models import User, Role, Permission
        from app.utils.init_data import init_default_data
        
        db.create_all()
        init_default_data()
        print('Database initialized successfully!')
    
    @app.cli.command()
    def create_admin():
        """创建管理员用户"""
        from app.models import User, Role
        from werkzeug.security import generate_password_hash
        
        admin_role = Role.query.filter_by(name='Admin').first()
        if not admin_role:
            print('Error: Admin role not found. Please run init-db first.')
            return
            
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            real_name='System Administrator',
            department='IT',
            is_active=True
        )
        admin.roles.append(admin_role)
        
        try:
            db.session.add(admin)
            db.session.commit()
            print('Admin user created successfully!')
            print('Username: admin')
            print('Password: admin123')
        except Exception as e:
            db.session.rollback()
            print('Error creating admin user: ' + str(e))