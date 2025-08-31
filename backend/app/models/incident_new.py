from datetime import datetime
from app import db
import uuid

class NewIncident(db.Model):
    """
    故障模型 - 代表已确认的、对业务产生影响的故障
    区别于Alert（告警），Incident是经过确认的业务影响事件
    一个故障可以关联多个告警
    """
    __tablename__ = 'incidents_new'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 故障标识信息  
    incident_id = db.Column(db.String(50), unique=True, nullable=False, comment='故障ID，格式如F-20240520-001')
    title = db.Column(db.String(255), nullable=False, comment='故障标题')
    description = db.Column(db.Text, comment='故障详细描述')
    
    # 故障状态和等级
    status = db.Column(db.Enum('Pending', 'Investigating', 'Recovering', 'Recovered', 'Post-Mortem', 'Closed'), 
                      default='Pending', comment='故障状态：待确认->处理中->恢复中->已恢复->待复盘->已关闭')
    severity = db.Column(db.Enum('P1', 'P2', 'P3', 'P4'), nullable=False, comment='故障等级')
    
    # 影响范围
    impact_scope = db.Column(db.Text, comment='影响范围描述')
    affected_services = db.Column(db.Text, comment='受影响的服务列表，JSON格式')
    business_impact = db.Column(db.Text, comment='业务影响描述')
    
    # 人员分配
    incident_commander = db.Column(db.Integer, db.ForeignKey('users.id'), comment='故障指挥官')
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='主要处理人')
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='报告人')
    
    # 时间信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    detected_at = db.Column(db.DateTime, comment='检测到故障的时间')
    acknowledged_at = db.Column(db.DateTime, comment='确认时间')
    recovered_at = db.Column(db.DateTime, comment='恢复时间')
    closed_at = db.Column(db.DateTime, comment='关闭时间')
    
    # 应急响应信息
    emergency_chat_url = db.Column(db.String(500), comment='应急群聊链接')
    notification_sent = db.Column(db.Boolean, default=False, comment='是否已发送通知')
    external_status_page = db.Column(db.Boolean, default=False, comment='是否在状态页显示')
    
    # 复盘相关
    postmortem_required = db.Column(db.Boolean, default=True, comment='是否需要复盘')
    postmortem_id = db.Column(db.Integer, db.ForeignKey('post_mortems.id'), comment='关联的复盘ID')
    
    # 关系
    commander = db.relationship('User', foreign_keys=[incident_commander], backref='commanded_new_incidents')
    assignee = db.relationship('User', foreign_keys=[assignee_id], backref='assigned_new_incidents')
    reporter = db.relationship('User', foreign_keys=[reporter_id], backref='reported_new_incidents')
    postmortem = db.relationship('PostMortem', foreign_keys='PostMortem.incident_id', back_populates='incident', uselist=False)

    # 添加关联告警和时间线关系
    alerts = db.relationship('Alert', foreign_keys='Alert.incident_id')
    timeline_entries = db.relationship('IncidentTimeline', foreign_keys='IncidentTimeline.incident_id', back_populates='incident', order_by='IncidentTimeline.timestamp.desc()')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.incident_id:
            self.incident_id = self.generate_incident_id()
    
    @staticmethod
    def generate_incident_id():
        """生成故障ID，格式：F-YYYYMMDD-NNN"""
        today = datetime.now().strftime('%Y%m%d')
        
        # 查询今天已有的故障数量
        today_count = NewIncident.query.filter(
            NewIncident.incident_id.like(f'F-{today}-%')
        ).count()
        
        return f'F-{today}-{today_count + 1:03d}'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'severity': self.severity,
            'impact_scope': self.impact_scope,
            'affected_services': self.affected_services,
            'business_impact': self.business_impact,
            'commander': self.commander.to_dict() if self.commander else None,
            'assignee': self.assignee.to_dict() if self.assignee else None,
            'reporter': self.reporter.to_dict() if self.reporter else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'detected_at': self.detected_at.isoformat() if self.detected_at else None,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'recovered_at': self.recovered_at.isoformat() if self.recovered_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'emergency_chat_url': self.emergency_chat_url,
            'notification_sent': self.notification_sent,
            'external_status_page': self.external_status_page,
            'postmortem_required': self.postmortem_required,
            'postmortem_id': self.postmortem_id,
            'alerts_count': len(self.alerts) if self.alerts else 0,
            'timeline_count': len(self.timeline_entries) if self.timeline_entries else 0,
            'alerts': [alert.to_dict() for alert in self.alerts] if self.alerts else [],
            'timeline': [entry.to_dict() for entry in self.timeline_entries] if self.timeline_entries else []
        }
    
    def change_status(self, new_status, user_id, comments=None):
        """变更故障状态"""
        old_status = self.status
        
        # 验证状态转换的合法性
        valid_transitions = {
            'Pending': ['Investigating', 'Closed'],
            'Investigating': ['Recovering', 'Closed'],
            'Recovering': ['Recovered', 'Investigating'],
            'Recovered': ['Post-Mortem', 'Investigating'],
            'Post-Mortem': ['Closed'],
            'Closed': []  # 关闭状态不能再转换
        }
        
        if new_status not in valid_transitions.get(old_status, []):
            raise ValueError(f'Invalid status transition from {old_status} to {new_status}')
        
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        # 更新相关时间戳
        if new_status == 'Investigating':
            self.acknowledged_at = datetime.utcnow()
        elif new_status == 'Recovered':
            self.recovered_at = datetime.utcnow()
        elif new_status == 'Closed':
            self.closed_at = datetime.utcnow()
        
        # 创建时间线记录
        timeline_entry = IncidentTimeline(
            incident_id=self.id,
            user_id=user_id,
            entry_type='status_change',
            title=f'状态变更: {old_status} → {new_status}',
            description=comments or f'故障状态从 {old_status} 变更为 {new_status}',
            timestamp=datetime.utcnow()
        )
        db.session.add(timeline_entry)
    
    def trigger_emergency_response(self, user_id):
        """触发应急响应"""
        # 这里可以集成实际的通讯工具API
        # 目前只是记录操作
        timeline_entry = IncidentTimeline(
            incident_id=self.id,
            user_id=user_id,
            entry_type='emergency_response',
            title='触发应急响应',
            description='已启动应急响应流程，创建应急群聊并通知相关人员',
            timestamp=datetime.utcnow()
        )
        db.session.add(timeline_entry)
        
        self.notification_sent = True
        self.updated_at = datetime.utcnow()


class IncidentTimeline(db.Model):
    """故障处理时间线模型"""
    __tablename__ = 'incident_timelines'
    
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents_new.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 时间线条目信息
    entry_type = db.Column(db.Enum('status_change', 'comment', 'action', 'emergency_response', 'alert_linked'), 
                          nullable=False, comment='条目类型')
    title = db.Column(db.String(255), nullable=False, comment='标题')
    description = db.Column(db.Text, comment='详细描述')
    timestamp = db.Column(db.DateTime, nullable=False, comment='时间戳')
    
    # 关联数据
    related_alert_id = db.Column(db.Integer, db.ForeignKey('alerts.id'), comment='关联的告警ID')
    attachments = db.Column(db.Text, comment='附件信息，JSON格式')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    incident = db.relationship('NewIncident', back_populates='timeline_entries')
    user = db.relationship('User', foreign_keys=[user_id])
    related_alert = db.relationship('Alert')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'user': self.user.to_dict() if self.user else None,
            'entry_type': self.entry_type,
            'title': self.title,
            'description': self.description,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'related_alert_id': self.related_alert_id,
            'related_alert': self.related_alert.to_dict() if self.related_alert else None,
            'attachments': self.attachments,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class PostMortem(db.Model):
    """复盘模型"""
    __tablename__ = 'post_mortems'
    
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey('incidents_new.id'), comment='关联的故障ID')
    
    # 复盘基本信息
    title = db.Column(db.String(255), nullable=False, comment='复盘标题')
    status = db.Column(db.Enum('Draft', 'In Review', 'Approved', 'Published'), 
                      default='Draft', comment='复盘状态')
    
    # 复盘内容
    incident_summary = db.Column(db.Text, comment='故障概述')
    timeline_analysis = db.Column(db.Text, comment='时间线分析')
    root_cause_analysis = db.Column(db.Text, comment='根因分析')
    lessons_learned = db.Column(db.Text, comment='经验教训')
    
    # 复盘会议信息
    meeting_date = db.Column(db.DateTime, comment='复盘会议时间')
    attendees = db.Column(db.Text, comment='参会人员，JSON格式')
    
    # 人员信息
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='编写人')
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='审核人')
    
    # 时间信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = db.Column(db.DateTime, comment='发布时间')
    
    # 关系
    incident = db.relationship('NewIncident', foreign_keys=[incident_id], back_populates='postmortem')
    author = db.relationship('User', foreign_keys=[author_id])
    reviewer = db.relationship('User', foreign_keys=[reviewer_id])
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'incident_id': self.incident_id,
            'incident': self.incident.to_dict() if self.incident else None,
            'title': self.title,
            'status': self.status,
            'incident_summary': self.incident_summary,
            'timeline_analysis': self.timeline_analysis,
            'root_cause_analysis': self.root_cause_analysis,
            'lessons_learned': self.lessons_learned,
            'meeting_date': self.meeting_date.isoformat() if self.meeting_date else None,
            'attendees': self.attendees,
            'author': self.author.to_dict() if self.author else None,
            'reviewer': self.reviewer.to_dict() if self.reviewer else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'action_items_count': len(self.action_items) if hasattr(self, 'action_items') else 0
        }


class ActionItem(db.Model):
    """改进措施模型"""
    __tablename__ = 'action_items'
    
    id = db.Column(db.Integer, primary_key=True)
    postmortem_id = db.Column(db.Integer, db.ForeignKey('post_mortems.id'), nullable=False)
    incident_id = db.Column(db.String(100), comment='关联的故障ID（F-格式）')  # 添加故障ID字段
    
    # 改进措施信息
    title = db.Column(db.String(255), nullable=False, comment='改进措施标题')
    description = db.Column(db.Text, comment='详细描述')
    category = db.Column(db.Enum('Technical', 'Process', 'Documentation', 'Training', 'Monitoring'), 
                        comment='措施类别')
    priority = db.Column(db.Enum('High', 'Medium', 'Low'), default='Medium', comment='优先级')
    status = db.Column(db.Enum('Open', 'In Progress', 'Completed', 'Cancelled'), 
                      default='Open', comment='状态')
    
    # 责任人和时间
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), comment='负责人')
    due_date = db.Column(db.DateTime, comment='截止时间')
    completed_at = db.Column(db.DateTime, comment='完成时间')
    
    # 外部链接
    external_link = db.Column(db.String(500), comment='外部链接（如Jira等）')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    postmortem = db.relationship('PostMortem', backref='action_items')
    assignee = db.relationship('User')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'postmortem_id': self.postmortem_id,
            'incident_id': self.incident_id,  # 返回故障ID
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'priority': self.priority,
            'status': self.status,
            'assignee': self.assignee.to_dict() if self.assignee else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'external_link': self.external_link,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ActionItemStatusLog(db.Model):
    """改进措施状态变更日志模型"""
    __tablename__ = 'action_item_status_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    action_item_id = db.Column(db.Integer, db.ForeignKey('action_items.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # 状态变更信息
    old_status = db.Column(db.String(50), comment='原状态')
    new_status = db.Column(db.String(50), nullable=False, comment='新状态')
    action = db.Column(db.String(100), nullable=False, comment='操作类型')
    comments = db.Column(db.Text, comment='操作说明')
    
    # 时间信息
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    action_item = db.relationship('ActionItem', backref='status_logs')
    user = db.relationship('User')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'action_item_id': self.action_item_id,
            'user': self.user.to_dict() if self.user else None,
            'old_status': self.old_status,
            'new_status': self.new_status,
            'action': self.action,
            'comments': self.comments,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }