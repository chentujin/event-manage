from flask import request, jsonify
from app.api import api_v1
from app import db
from app.models import User, Role, Group
from app.utils.auth import permission_required, admin_required, get_current_user
import bcrypt
import logging

logger = logging.getLogger(__name__)

@api_v1.route('/users', methods=['GET'])
@permission_required('user:read')
def get_users():
    """获取用户列表"""
    users = User.query.filter(User.is_active == True).all()
    return jsonify({
        'users': [user.to_dict() for user in users]
    }), 200

@api_v1.route('/roles', methods=['GET'])
@permission_required('user:read')
def get_roles():
    """获取角色列表"""
    roles = Role.query.all()
    return jsonify({
        'roles': [role.to_dict() for role in roles]
    }), 200

@api_v1.route('/groups', methods=['GET'])
@permission_required('user:read')
def get_groups():
    """获取组列表"""
    groups = Group.query.all()
    return jsonify({
        'groups': [group.to_dict() for group in groups]
    }), 200

@api_v1.route('/users', methods=['POST'])
@permission_required('user:write')
def create_user():
    """创建新用户"""
    data = request.get_json()
    current_user = get_current_user()
    
    # 验证必填字段
    required_fields = ['username', 'email', 'password', 'real_name', 'department']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # 检查用户名和邮箱是否已存在
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
        
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    try:
        # 创建用户
        password_bytes = data['password'].encode('utf-8')
        password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')
        
        user = User(
            username=data['username'],
            email=data['email'],
            password_hash=password_hash,
            real_name=data['real_name'],
            department=data['department'],
            phone_number=data.get('phone_number'),
            is_active=True
        )
        
        # 分配角色
        if 'roles' in data and data['roles']:
            roles = Role.query.filter(Role.id.in_(data['roles'])).all()
            user.roles.extend(roles)
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f'User created: {user.username} by {current_user.username}')
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'User creation error: {str(e)}')
        return jsonify({'error': 'User creation failed'}), 500

@api_v1.route('/users/<int:user_id>', methods=['PUT'])
@permission_required('user:write')
def update_user(user_id):
    """更新用户信息"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    current_user = get_current_user()
    
    try:
        # 检查邮箱是否已存在（排除当前用户）
        if 'email' in data and data['email'] != user.email:
            if User.query.filter_by(email=data['email']).first():
                return jsonify({'error': 'Email already exists'}), 400
        
        # 更新用户信息
        allowed_fields = ['real_name', 'email', 'department', 'phone_number']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        # 更新角色
        if 'roles' in data:
            user.roles.clear()
            if data['roles']:
                roles = Role.query.filter(Role.id.in_(data['roles'])).all()
                user.roles.extend(roles)
        
        db.session.commit()
        
        logger.info(f'User updated: {user.username} by {current_user.username}')
        
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'User update error: {str(e)}')
        return jsonify({'error': 'User update failed'}), 500

@api_v1.route('/users/<int:user_id>/status', methods=['PUT'])
@permission_required('user:write')
def toggle_user_status(user_id):
    """切换用户状态"""
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    current_user = get_current_user()
    
    try:
        user.is_active = data.get('is_active', not user.is_active)
        db.session.commit()
        
        action = '启用' if user.is_active else '禁用'
        logger.info(f'User {action}: {user.username} by {current_user.username}')
        
        return jsonify({
            'message': f'User {action} successfully',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'User status toggle error: {str(e)}')
        return jsonify({'error': 'Status toggle failed'}), 500

@api_v1.route('/groups', methods=['POST'])
@permission_required('user:write')
def create_group():
    """创建用户组"""
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        # 检查组名是否已存在
        if Group.query.filter_by(name=data['name']).first():
            return jsonify({'error': '组名已存在'}), 400
        
        group = Group(
            name=data['name'],
            description=data.get('description'),
            manager_id=data.get('manager_id')
        )
        
        db.session.add(group)
        db.session.commit()
        
        logger.info(f'Group created: {group.name} by {current_user.username}')
        
        return jsonify({
            'message': '用户组创建成功',
            'group': group.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"创建用户组失败: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '创建用户组失败'}), 500

@api_v1.route('/groups/<int:group_id>', methods=['PUT'])
@permission_required('user:write')
def update_group(group_id):
    """更新用户组"""
    try:
        group = Group.query.get_or_404(group_id)
        data = request.get_json()
        current_user = get_current_user()
        
        # 检查组名是否已被其他组使用
        if 'name' in data and data['name'] != group.name:
            if Group.query.filter_by(name=data['name']).first():
                return jsonify({'error': '组名已存在'}), 400
        
        group.name = data.get('name', group.name)
        group.description = data.get('description', group.description)
        group.manager_id = data.get('manager_id', group.manager_id)
        
        db.session.commit()
        
        logger.info(f'Group updated: {group.name} by {current_user.username}')
        
        return jsonify({
            'message': '用户组更新成功',
            'group': group.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"更新用户组失败: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '更新用户组失败'}), 500

@api_v1.route('/groups/<int:group_id>', methods=['DELETE'])
@permission_required('user:write')
def delete_group(group_id):
    """删除用户组"""
    try:
        group = Group.query.get_or_404(group_id)
        current_user = get_current_user()
        
        # 清除组成员关系
        group.members.clear()
        
        db.session.delete(group)
        db.session.commit()
        
        logger.info(f'Group deleted: {group.name} by {current_user.username}')
        
        return jsonify({'message': '用户组删除成功'}), 200
        
    except Exception as e:
        logger.error(f"删除用户组失败: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '删除用户组失败'}), 500

@api_v1.route('/groups/<int:group_id>/members', methods=['GET'])
@permission_required('user:read')
def get_group_members(group_id):
    """获取用户组成员"""
    try:
        group = Group.query.get_or_404(group_id)
        members = [user.to_dict() for user in group.members]
        
        return jsonify({
            'members': members
        }), 200
        
    except Exception as e:
        logger.error(f"获取用户组成员失败: {str(e)}")
        return jsonify({'error': '获取用户组成员失败'}), 500

@api_v1.route('/groups/<int:group_id>/members', methods=['POST'])
@permission_required('user:write')
def add_group_member(group_id):
    """添加用户组成员"""
    try:
        group = Group.query.get_or_404(group_id)
        data = request.get_json()
        user_id = data.get('user_id')
        current_user = get_current_user()
        
        user = User.query.get_or_404(user_id)
        
        # 检查用户是否已在组中
        if user in group.members:
            return jsonify({'error': '用户已在该组中'}), 400
        
        group.members.append(user)
        db.session.commit()
        
        logger.info(f'User {user.username} added to group {group.name} by {current_user.username}')
        
        return jsonify({
            'message': '成员添加成功',
            'group': group.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"添加用户组成员失败: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '添加用户组成员失败'}), 500

@api_v1.route('/groups/<int:group_id>/members/<int:user_id>', methods=['DELETE'])
@permission_required('user:write')
def remove_group_member(group_id, user_id):
    """移除用户组成员"""
    try:
        group = Group.query.get_or_404(group_id)
        user = User.query.get_or_404(user_id)
        current_user = get_current_user()
        
        if user in group.members:
            group.members.remove(user)
            db.session.commit()
            
            logger.info(f'User {user.username} removed from group {group.name} by {current_user.username}')
            
            return jsonify({
                'message': '成员移除成功',
                'group': group.to_dict()
            }), 200
        else:
            return jsonify({'error': '用户不在该组中'}), 400
            
    except Exception as e:
        logger.error(f"移除用户组成员失败: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '移除用户组成员失败'}), 500
