from datetime import datetime
from app import db
import json

class NotificationChannel(db.Model):
    """通知渠道配置模型"""
    __tablename__ = 'notification_channels'
    
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Enum('EMAIL', 'SMS', 'SLACK', 'TEAMS', 'DINGTALK', 'WEBHOOK', 'VOICE_CALL'), 
                    nullable=False)
    name = db.Column(db.String(100), nullable=False)
    config = db.Column(db.JSON, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'config': self.config,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class UserNotificationPreference(db.Model):
    """用户通知偏好模型"""
    __tablename__ = 'user_notification_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    channel_type = db.Column(db.Enum('EMAIL', 'SMS', 'SLACK', 'TEAMS', 'DINGTALK', 'WEBHOOK', 'VOICE_CALL'), 
                           nullable=False)
    is_enabled = db.Column(db.Boolean, default=True)
    preferences = db.Column(db.JSON)
    
    # 联合唯一约束
    __table_args__ = (db.UniqueConstraint('user_id', 'channel_type', name='_user_channel_uc'),)
    
    # 关系
    user = db.relationship('User', backref='notification_preferences')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'channel_type': self.channel_type,
            'is_enabled': self.is_enabled,
            'preferences': self.preferences
        }

class NotificationRule(db.Model):
    """通知规则模型"""
    __tablename__ = 'notification_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    trigger_event = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    actions = db.relationship('NotificationRuleAction', backref='rule', cascade='all, delete-orphan')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'trigger_event': self.trigger_event,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'actions': [action.to_dict() for action in self.actions]
        }

class NotificationRuleAction(db.Model):
    """通知规则动作模型"""
    __tablename__ = 'notification_rule_actions'
    
    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('notification_rules.id'), nullable=False)
    action_type = db.Column(db.Enum('NOTIFY_USER', 'NOTIFY_GROUP', 'NOTIFY_ROLE', 'WEBHOOK'), 
                          nullable=False)
    target_identifier = db.Column(db.String(100), nullable=False)
    channel_priority = db.Column(db.JSON, nullable=False)  # 渠道优先级配置
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'action_type': self.action_type,
            'target_identifier': self.target_identifier,
            'channel_priority': self.channel_priority
        }

class NotificationTemplate(db.Model):
    """通知模板模型"""
    __tablename__ = 'notification_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    trigger_event = db.Column(db.String(100), nullable=False)
    channel_type = db.Column(db.Enum('EMAIL', 'SMS', 'SLACK', 'TEAMS', 'DINGTALK', 'WEBHOOK', 'VOICE_CALL'), 
                           nullable=False)
    subject_template = db.Column(db.Text)
    body_template = db.Column(db.Text, nullable=False)
    
    # 语音电话特有字段
    tts_voice = db.Column(db.String(50))
    play_times = db.Column(db.Integer, default=2)
    timeout_sec = db.Column(db.Integer, default=30)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'trigger_event': self.trigger_event,
            'channel_type': self.channel_type,
            'subject_template': self.subject_template,
            'body_template': self.body_template,
            'tts_voice': self.tts_voice,
            'play_times': self.play_times,
            'timeout_sec': self.timeout_sec,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class NotificationLog(db.Model):
    """通知发送日志模型"""
    __tablename__ = 'notification_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('notification_rules.id'))
    template_id = db.Column(db.Integer, db.ForeignKey('notification_templates.id'))
    trigger_event = db.Column(db.String(100), nullable=False)
    trigger_record_id = db.Column(db.Integer, nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    channel_type = db.Column(db.Enum('EMAIL', 'SMS', 'SLACK', 'TEAMS', 'DINGTALK', 'WEBHOOK', 'VOICE_CALL'), 
                           nullable=False)
    status = db.Column(db.Enum('SUCCESS', 'FAILED'), nullable=False)
    request_content = db.Column(db.Text)
    response_content = db.Column(db.Text)
    external_id = db.Column(db.String(255))
    
    # 语音电话特有字段
    call_duration = db.Column(db.Integer)
    call_status = db.Column(db.String(50))
    dtmf_input = db.Column(db.String(10))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    rule = db.relationship('NotificationRule', foreign_keys=[rule_id])
    template = db.relationship('NotificationTemplate', foreign_keys=[template_id])
    target_user = db.relationship('User', foreign_keys=[target_user_id])
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'template_id': self.template_id,
            'trigger_event': self.trigger_event,
            'trigger_record_id': self.trigger_record_id,
            'target_user': self.target_user.to_dict() if self.target_user else None,
            'channel_type': self.channel_type,
            'status': self.status,
            'request_content': self.request_content,
            'response_content': self.response_content,
            'external_id': self.external_id,
            'call_duration': self.call_duration,
            'call_status': self.call_status,
            'dtmf_input': self.dtmf_input,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }