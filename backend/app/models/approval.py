from datetime import datetime
from app import db

class ApprovalWorkflow(db.Model):
    """审批流程定义模型"""
    __tablename__ = 'approval_workflows'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    # 关系
    steps = db.relationship('ApprovalStep', backref='workflow', cascade='all, delete-orphan')
    approvals = db.relationship('Approval', backref='workflow')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'steps': [step.to_dict() for step in self.steps]
        }

class ApprovalStep(db.Model):
    """审批节点定义模型"""
    __tablename__ = 'approval_steps'
    
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('approval_workflows.id'), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    approval_type = db.Column(db.Enum('USER', 'ROLE', 'GROUP_MANAGER'), nullable=False)
    
    # 审批人配置
    approved_by_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    approved_by_role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    approved_by_group_id = db.Column(db.Integer, db.ForeignKey('groups.id'))
    
    # 关系
    approved_by_user = db.relationship('User', foreign_keys=[approved_by_id])
    approved_by_role = db.relationship('Role', foreign_keys=[approved_by_role_id])
    approved_by_group = db.relationship('Group', foreign_keys=[approved_by_group_id])
    
    def get_approvers(self):
        """获取该步骤的所有审批人"""
        approvers = []
        
        if self.approval_type == 'USER' and self.approved_by_user:
            approvers.append(self.approved_by_user)
        elif self.approval_type == 'ROLE' and self.approved_by_role:
            approvers.extend(self.approved_by_role.users)
        elif self.approval_type == 'GROUP_MANAGER' and self.approved_by_group:
            if self.approved_by_group.manager:
                approvers.append(self.approved_by_group.manager)
        
        return approvers
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'step_number': self.step_number,
            'approval_type': self.approval_type,
            'approved_by_user': self.approved_by_user.to_dict() if self.approved_by_user else None,
            'approved_by_role': self.approved_by_role.to_dict() if self.approved_by_role else None,
            'approved_by_group': self.approved_by_group.to_dict() if self.approved_by_group else None,
            'approvers': [user.to_dict() for user in self.get_approvers()]
        }

class Approval(db.Model):
    """审批实例模型"""
    __tablename__ = 'approvals'
    
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('approval_workflows.id'), nullable=False)
    problem_id = db.Column(db.Integer, db.ForeignKey('problems.id'), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.Enum('PENDING', 'APPROVED', 'REJECTED'), default='PENDING')
    current_step = db.Column(db.Integer, default=1)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    problem = db.relationship('Problem', foreign_keys=[problem_id], back_populates='approvals')
    requester = db.relationship('User', foreign_keys=[requester_id])
    logs = db.relationship('ApprovalLog', backref='approval', cascade='all, delete-orphan')
    
    def get_current_approvers(self):
        """获取当前步骤的审批人"""
        if self.status != 'PENDING':
            return []
        
        current_step = self.workflow.steps.filter_by(step_number=self.current_step).first()
        if not current_step:
            return []
        
        return current_step.get_approvers()
    
    def is_user_current_approver(self, user):
        """检查用户是否为当前步骤的审批人"""
        return user in self.get_current_approvers()
    
    def approve_step(self, approver, comments=None):
        """批准当前步骤"""
        if not self.is_user_current_approver(approver):
            raise ValueError("User is not authorized to approve this step")
        
        # 记录审批日志
        current_step = self.workflow.steps.filter_by(step_number=self.current_step).first()
        log = ApprovalLog(
            approval_id=self.id,
            step_id=current_step.id,
            approver_id=approver.id,
            decision='APPROVED',
            comments=comments
        )
        db.session.add(log)
        
        # 检查是否还有下一步
        next_step = self.workflow.steps.filter_by(step_number=self.current_step + 1).first()
        if next_step:
            # 进入下一步
            self.current_step += 1
        else:
            # 所有步骤都已批准
            self.status = 'APPROVED'
        
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def reject(self, approver, comments=None):
        """拒绝审批"""
        if not self.is_user_current_approver(approver):
            raise ValueError("User is not authorized to reject this step")
        
        # 记录审批日志
        current_step = self.workflow.steps.filter_by(step_number=self.current_step).first()
        log = ApprovalLog(
            approval_id=self.id,
            step_id=current_step.id,
            approver_id=approver.id,
            decision='REJECTED',
            comments=comments
        )
        db.session.add(log)
        
        self.status = 'REJECTED'
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'workflow': self.workflow.to_dict() if self.workflow else None,
            'problem': self.problem.to_dict() if self.problem else None,
            'requester': self.requester.to_dict() if self.requester else None,
            'status': self.status,
            'current_step': self.current_step,
            'current_approvers': [user.to_dict() for user in self.get_current_approvers()],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'logs': [log.to_dict() for log in self.logs]
        }

class ApprovalLog(db.Model):
    """审批日志模型"""
    __tablename__ = 'approval_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    approval_id = db.Column(db.Integer, db.ForeignKey('approvals.id'), nullable=False)
    step_id = db.Column(db.Integer, db.ForeignKey('approval_steps.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    decision = db.Column(db.Enum('APPROVED', 'REJECTED'), nullable=False)
    comments = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    step = db.relationship('ApprovalStep', foreign_keys=[step_id])
    approver = db.relationship('User', foreign_keys=[approver_id])
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'approval_id': self.approval_id,
            'step': self.step.to_dict() if self.step else None,
            'approver': self.approver.to_dict() if self.approver else None,
            'decision': self.decision,
            'comments': self.comments,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }