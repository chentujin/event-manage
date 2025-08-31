from datetime import datetime
from app import db

class Alert(db.Model):
    """
    告警模型 - 代表来自监控系统的单个告警/事件
    这是故障管理流程的起点，多个告警可以关联到一个故障
    """
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 基本信息
    title = db.Column(db.String(255), nullable=False, comment='告警标题')
    description = db.Column(db.Text, comment='告警描述')
    alert_source = db.Column(db.String(100), comment='告警来源（如：Prometheus, Zabbix等）')
    alert_rule = db.Column(db.String(255), comment='触发的告警规则')
    
    # 告警级别和状态
    level = db.Column(db.Enum('Critical', 'Warning', 'Info'), nullable=False, comment='告警级别')
    status = db.Column(db.Enum('New', 'Acknowledged', 'Linked', 'Ignored'), 
                      default='New', comment='告警状态')
    
    # 告警指标和阈值
    metric_name = db.Column(db.String(255), comment='指标名称')
    metric_value = db.Column(db.String(100), comment='指标值')
    threshold = db.Column(db.String(100), comment='阈值')
    
    # 影响范围
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), comment='关联服务')
    host = db.Column(db.String(255), comment='主机地址')
    environment = db.Column(db.Enum('Production', 'Staging', 'Development'), comment='环境')
    
    # 关联信息
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents_new.id'), comment='关联的故障ID')
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='确认人')
    
    # 时间信息
    fired_at = db.Column(db.DateTime, nullable=False, comment='告警触发时间')
    resolved_at = db.Column(db.DateTime, comment='告警解决时间')
    acknowledged_at = db.Column(db.DateTime, comment='确认时间')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    service = db.relationship('Service', backref='alerts')
    incident = db.relationship('NewIncident', foreign_keys=[incident_id])
    acknowledged_user = db.relationship('User', foreign_keys=[acknowledged_by])
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'alert_source': self.alert_source,
            'alert_rule': self.alert_rule,
            'level': self.level,
            'status': self.status,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'threshold': self.threshold,
            'service': self.service.to_dict() if self.service else None,
            'incident_id': self.incident_id,
            'host': self.host,
            'environment': self.environment,
            'acknowledged_by': self.acknowledged_user.to_dict() if self.acknowledged_user else None,
            'fired_at': self.fired_at.isoformat() if self.fired_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def acknowledge(self, user_id):
        """确认告警"""
        self.status = 'Acknowledged'
        self.acknowledged_by = user_id
        self.acknowledged_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def link_to_incident(self, incident_id):
        """关联到故障"""
        self.status = 'Linked'
        self.incident_id = incident_id
        self.updated_at = datetime.utcnow()
    
    def ignore(self):
        """忽略告警"""
        self.status = 'Ignored'
        self.updated_at = datetime.utcnow()
    
    def resolve(self):
        """解决告警"""
        self.resolved_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

class AlertComment(db.Model):
    """告警评论模型"""
    __tablename__ = 'alert_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_id = db.Column(db.Integer, db.ForeignKey('alerts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False, comment='评论内容')
    is_private = db.Column(db.Boolean, default=False, comment='是否私有评论')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    alert = db.relationship('Alert', backref='comments')
    user = db.relationship('User')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'user': self.user.to_dict() if self.user else None,
            'content': self.content,
            'is_private': self.is_private,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }