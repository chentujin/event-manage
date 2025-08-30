from datetime import datetime
from app import db
from sqlalchemy.ext.hybrid import hybrid_property

# 事件-故障关联表
incident_problem = db.Table('incident_problem',
    db.Column('incident_id', db.Integer, db.ForeignKey('incidents.id'), primary_key=True),
    db.Column('problem_id', db.Integer, db.ForeignKey('problems.id'), primary_key=True)
)

class Service(db.Model):
    """服务目录模型"""
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    owner_team = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    
    # 关系
    incidents = db.relationship('Incident', backref='service')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'owner_team': self.owner_team,
            'is_active': self.is_active
        }

class Incident(db.Model):
    """事件模型"""
    __tablename__ = 'incidents'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum('New', 'In Progress', 'On Hold', 'Resolved', 'Closed', 'Reopened'), 
                      default='New')
    impact = db.Column(db.Enum('High', 'Medium', 'Low'), nullable=False)
    urgency = db.Column(db.Enum('High', 'Medium', 'Low'), nullable=False)
    
    # 外键
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'))
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    closed_at = db.Column(db.DateTime)
    
    # 关系
    comments = db.relationship('IncidentComment', backref='incident', cascade='all, delete-orphan')
    problems = db.relationship('Problem', secondary=incident_problem, backref='incidents')
    
    @hybrid_property
    def priority(self):
        """根据影响度和紧急度自动计算优先级"""
        if self.impact == 'High' and self.urgency == 'High':
            return 'Critical'
        elif (self.impact == 'High' and self.urgency == 'Medium') or \
             (self.impact == 'Medium' and self.urgency == 'High'):
            return 'High'
        elif (self.impact == 'High' and self.urgency == 'Low') or \
             (self.impact == 'Medium' and self.urgency == 'Medium') or \
             (self.impact == 'Low' and self.urgency == 'High'):
            return 'Medium'
        else:
            return 'Low'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'impact': self.impact,
            'urgency': self.urgency,
            'priority': self.priority,
            'service': self.service.to_dict() if self.service else None,
            'assignee': self.assignee.to_dict() if self.assignee else None,
            'reporter': self.reporter.to_dict() if self.reporter else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'comments_count': len(self.comments),
            'problems': [p.id for p in self.problems]
        }

class IncidentComment(db.Model):
    """事件评论模型"""
    __tablename__ = 'incident_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_private = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'user': self.user.to_dict() if self.user else None,
            'content': self.content,
            'is_private': self.is_private,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class IncidentStatusLog(db.Model):
    """事件状态变更日志模型"""
    __tablename__ = 'incident_status_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    old_status = db.Column(db.String(50))
    new_status = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # 描述操作类型
    comments = db.Column(db.Text)  # 操作说明
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    incident = db.relationship('Incident', backref='status_logs')
    user = db.relationship('User')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'user': self.user.to_dict() if self.user else None,
            'old_status': self.old_status,
            'new_status': self.new_status,
            'action': self.action,
            'comments': self.comments,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Problem(db.Model):
    """故障模型"""
    __tablename__ = 'problems'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.Enum('New', 'Investigating', 'Known Error', 'Closed', 'Pending Approval'), 
                      default='New')
    priority = db.Column(db.Enum('High', 'Medium', 'Low'))
    root_cause_analysis = db.Column(db.Text)
    solution = db.Column(db.Text)
    current_approval_id = db.Column(db.Integer, db.ForeignKey('approvals.id'))
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = db.Column(db.DateTime)
    
    # 关系
    current_approval = db.relationship('Approval', foreign_keys=[current_approval_id])
    approvals = db.relationship('Approval', foreign_keys='Approval.problem_id', back_populates='problem')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'root_cause_analysis': self.root_cause_analysis,
            'solution': self.solution,
            'current_approval_id': self.current_approval_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'incidents': [i.id for i in self.incidents]
        }

class ProblemStatusLog(db.Model):
    """故障状态变更日志模型"""
    __tablename__ = 'problem_status_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    old_status = db.Column(db.String(50))
    new_status = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # 描述操作类型
    comments = db.Column(db.Text)  # 操作说明
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    problem = db.relationship('Problem', backref='status_logs')
    user = db.relationship('User')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'problem_id': self.problem_id,
            'user': self.user.to_dict() if self.user else None,
            'old_status': self.old_status,
            'new_status': self.new_status,
            'action': self.action,
            'comments': self.comments,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }