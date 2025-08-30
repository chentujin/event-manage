"""
权限管理工具
包含权限检查装饰器和相关工具函数
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import User

def permission_required(permission_code):
    """权限检查装饰器"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            if not user.has_permission(permission_code):
                return jsonify({
                    'error': 'Permission denied',
                    'required_permission': permission_code
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def role_required(*role_names):
    """角色检查装饰器"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 404
            
            user_roles = [role.name for role in user.roles]
            if not any(role in user_roles for role in role_names):
                return jsonify({
                    'error': 'Role access denied',
                    'required_roles': list(role_names),
                    'user_roles': user_roles
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    """获取当前登录用户对象"""
    current_user_id = get_jwt_identity()
    if current_user_id:
        return User.query.get(current_user_id)
    return None

def admin_required(f):
    """管理员权限装饰器"""
    return role_required('Admin')(f)

def check_user_permission(user, permission_code):
    """检查用户是否有指定权限"""
    if not user:
        return False
    return user.has_permission(permission_code)

def check_user_role(user, role_name):
    """检查用户是否有指定角色"""
    if not user:
        return False
    return any(role.name == role_name for role in user.roles)