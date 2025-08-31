from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property

# 关联表定义
user_group = db.Table('user_group',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True)
)

role_permission = db.Table('role_permission',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)

user_role = db.Table('user_role',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

group_role = db.Table('group_role',
    db.Column('group_id', db.Integer, db.ForeignKey('groups.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(50))
    real_name = db.Column(db.String(100))
    department = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    groups = db.relationship('Group', secondary=user_group)
    roles = db.relationship('Role', secondary=user_role, backref='users')
    
    # 暂时注释掉与Incident模型的外键关系，避免模型冲突
    # incidents_reported = db.relationship('Incident', foreign_keys='Incident.reporter_id', backref='reporter')
    # incidents_assigned = db.relationship('Incident', foreign_keys='Incident.assignee_id', backref='assignee')
    # incident_comments = db.relationship('IncidentComment', backref='user')
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission_code):
        """检查用户是否有指定权限"""
        # 直接分配给用户的权限
        for role in self.roles:
            if role.has_permission(permission_code):
                return True
        
        # 通过组获得的权限
        for group in self.groups:
            for role in group.roles:
                if role.has_permission(permission_code):
                    return True
        
        return False
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone_number': self.phone_number,
            'real_name': self.real_name,
            'department': self.department,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'groups': [group.name for group in self.groups],
            'roles': [role.name for role in self.roles]
        }

class Group(db.Model):
    """组模型"""
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    manager = db.relationship('User', foreign_keys=[manager_id])
    roles = db.relationship('Role', secondary=group_role, backref='groups')
    members = db.relationship('User', secondary=user_group)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'manager': self.manager.real_name if self.manager else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'member_count': len(self.members),
            'roles': [role.name for role in self.roles]
        }

class Role(db.Model):
    """角色模型"""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # 关系
    permissions = db.relationship('Permission', secondary=role_permission, backref='roles')
    
    def has_permission(self, permission_code):
        """检查角色是否有指定权限"""
        return any(perm.code == permission_code for perm in self.permissions)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'permissions': [perm.code for perm in self.permissions]
        }

class Permission(db.Model):
    """权限模型"""
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'code': self.code,
            'description': self.description
        }