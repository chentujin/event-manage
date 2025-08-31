"""
数据库初始化工具
包含默认角色、权限、服务等数据的创建
"""
from app import db
from app.models import (
    User, Group, Role, Permission, Service,
    NotificationChannel, NotificationTemplate, ApprovalWorkflow, ApprovalStep
)
from werkzeug.security import generate_password_hash

def init_default_data():
    """初始化默认数据"""
    
    # 创建权限
    permissions_data = [
        # 用户管理权限
        ('user:read', '查看用户信息'),
        ('user:write', '创建和编辑用户'),
        ('user:delete', '删除用户'),
        ('user:activate', '激活/禁用用户'),
        
        # 事件管理权限
        ('incident:read', '查看事件'),
        ('incident:write', '创建和编辑事件'),
        ('incident:assign', '分配事件'),
        ('incident:close', '关闭事件'),
        ('incident:comment', '添加事件评论'),
        
        # 故障管理权限
        ('problem:read', '查看故障'),
        ('problem:write', '创建和编辑故障'),
        ('problem:approve', '审批故障解决方案'),
        
        # 复盘管理权限
        ('postmortem:read', '查看复盘'),
        ('postmortem:write', '创建和编辑复盘'),
        ('postmortem:approve', '审批复盘'),
        ('postmortem:publish', '发布复盘'),
        
        # 行动项管理权限
        ('action_item:read', '查看行动项'),
        ('action_item:write', '创建和编辑行动项'),
        ('action_item:assign', '分配行动项'),
        ('action_item:complete', '完成行动项'),
        
        # 告警管理权限
        ('alert:read', '查看告警'),
        ('alert:write', '创建和编辑告警'),
        
        # 系统管理权限
        ('system:admin', '系统管理'),
        ('system:config', '系统配置'),
        ('notification:admin', '通知管理'),
        ('approval:admin', '审批流程管理'),
        
        # 审批管理权限
        ('approval:read', '查看审批流程'),
        ('approval:write', '创建和编辑审批流程'),
        ('approval:approve', '审批操作'),
        ('approval:admin', '审批流程管理'),
        
        # 报表权限
        ('report:read', '查看报表'),
        ('dashboard:read', '查看仪表盘'),
    ]
    
    for code, description in permissions_data:
        if not Permission.query.filter_by(code=code).first():
            permission = Permission(code=code, description=description)
            db.session.add(permission)
    
    db.session.commit()
    
    # 创建角色
    roles_data = [
        ('Admin', '超级管理员', [
            'user:read', 'user:write', 'user:delete', 'user:activate',
            'incident:read', 'incident:write', 'incident:assign', 'incident:close', 'incident:comment',
            'problem:read', 'problem:write', 'problem:approve',
            'postmortem:read', 'postmortem:write', 'postmortem:approve', 'postmortem:publish',
            'action_item:read', 'action_item:write', 'action_item:assign', 'action_item:complete',
            'alert:read', 'alert:write',  # 添加告警权限
            'approval:read', 'approval:write', 'approval:approve', 'approval:admin',  # 添加审批权限
            'system:admin', 'system:config', 'notification:admin',
            'report:read', 'dashboard:read'
        ]),
        ('Problem Manager', '故障经理', [
            'incident:read', 'incident:write', 'incident:assign', 'incident:close', 'incident:comment',
            'problem:read', 'problem:write', 'problem:approve',
            'alert:read', 'alert:write',  # 添加告警权限
            'report:read', 'dashboard:read'
        ]),
        ('track-management', '质量管理', [
            'incident:read', 'incident:write', 'incident:assign', 'incident:close', 'incident:comment',
            'problem:read', 'problem:write', 'problem:approve',
            'postmortem:read', 'postmortem:write', 'postmortem:approve', 'postmortem:publish',
            'action_item:read', 'action_item:write', 'action_item:assign', 'action_item:complete',
            'alert:read', 'alert:write',
            'report:read', 'dashboard:read'
        ]),
        ('Engineer', '工程师', [
            'incident:read', 'incident:write', 'incident:comment',
            'problem:read', 'problem:write',
            'alert:read', 'alert:write',  # 添加告警权限
            'dashboard:read'
        ]),
        ('Service Desk', '服务台', [
            'incident:read', 'incident:write', 'incident:comment',
            'problem:read',
            'alert:read', 'alert:write',  # 添加告警权限
            'dashboard:read'
        ]),
        ('Viewer', '只读用户', [
            'incident:read',
            'problem:read',
            'alert:read',  # 添加告警权限
            'dashboard:read'
        ])
    ]
    
    for role_name, description, permission_codes in roles_data:
        if not Role.query.filter_by(name=role_name).first():
            role = Role(name=role_name, description=description)
            
            # 添加权限
            for perm_code in permission_codes:
                permission = Permission.query.filter_by(code=perm_code).first()
                if permission:
                    role.permissions.append(permission)
            
            db.session.add(role)
    
    db.session.commit()
    
    # 创建默认admin账号
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123'),
            real_name='系统管理员',
            department='IT管理部',
            is_active=True
        )
        
        # 分配Admin角色
        admin_role = Role.query.filter_by(name='Admin').first()
        if admin_role:
            admin_user.roles.append(admin_role)
        
        db.session.add(admin_user)
        db.session.commit()
        print("默认管理员账号创建完成！")
        print("用户名: admin")
        print("密码: admin123")
    
    # 创建默认服务
    services_data = [
        ('用户登录API', '用户认证和登录服务', '后端团队'),
        ('支付服务', '支付处理服务', '支付团队'),
        ('订单服务', '订单管理服务', '业务团队'),
        ('通知服务', '消息推送服务', '基础架构团队'),
        ('数据库服务', 'MySQL数据库集群', 'DBA团队'),
        ('缓存服务', 'Redis缓存集群', '基础架构团队'),
        ('CDN服务', '内容分发网络', '运维团队'),
        ('监控系统', '系统监控和告警', 'SRE团队'),
    ]
    
    for name, description, owner_team in services_data:
        if not Service.query.filter_by(name=name).first():
            service = Service(
                name=name,
                description=description,
                owner_team=owner_team,
                is_active=True
            )
            db.session.add(service)
    
    db.session.commit()
    
    # 创建默认通知模板
    templates_data = [
        {
            'name': '事件创建通知 - 邮件',
            'description': '新事件创建时的邮件通知模板',
            'trigger_event': 'incident.created',
            'channel_type': 'EMAIL',
            'subject_template': '【事件通知】{{ incident.title }}',
            'body_template': '''<h2>事件详情</h2>
<p><strong>事件ID:</strong> {{ incident.id }}</p>
<p><strong>标题:</strong> {{ incident.title }}</p>
<p><strong>描述:</strong> {{ incident.description }}</p>
<p><strong>优先级:</strong> {{ incident.priority }}</p>
<p><strong>影响度:</strong> {{ incident.impact }}</p>
<p><strong>紧急度:</strong> {{ incident.urgency }}</p>
<p><strong>服务:</strong> {{ incident.service.name if incident.service else '未指定' }}</p>
<p><strong>报告人:</strong> {{ incident.reporter.real_name }}</p>
<p><strong>创建时间:</strong> {{ incident.created_at }}</p>

<p>请登录系统查看详情并处理。</p>'''
        },
        {
            'name': '事件创建通知 - 短信',
            'description': '新事件创建时的短信通知模板',
            'trigger_event': 'incident.created',
            'channel_type': 'SMS',
            'body_template': '【事件通知】{{ incident.title }}，优先级：{{ incident.priority }}，请及时处理。详情查看系统。'
        },
        {
            'name': 'P0级故障语音告警',
            'description': 'P0级别故障的语音电话告警模板',
            'trigger_event': 'incident.created',
            'channel_type': 'VOICE_CALL',
            'body_template': '''（紧急告警音）
您好，这是一条来自【事件管理平台】的紧急告警。
发生P0级故障，事件ID：{{ incident.id }}，标题：{{ incident.title }}。
影响服务：{{ incident.service.name if incident.service else '未知' }}。
请立即登录系统查看处理。重复收听请按1，确认已收到本通知请按2。
（紧急告警音）''',
            'tts_voice': 'xiaoyun',
            'play_times': 3,
            'timeout_sec': 60
        }
    ]
    
    for template_data in templates_data:
        if not NotificationTemplate.query.filter_by(
            name=template_data['name']
        ).first():
            template = NotificationTemplate(**template_data)
            db.session.add(template)
    
    db.session.commit()
    
    # 创建默认审批流程
    if not ApprovalWorkflow.query.filter_by(name='故障解决方案审批').first():
        workflow = ApprovalWorkflow(
            name='故障解决方案审批',
            description='故障根因分析和解决方案的标准审批流程',
            is_active=True
        )
        db.session.add(workflow)
        db.session.flush()  # 获取workflow.id
        
        # 添加审批步骤
        # 第一步：团队负责人审批
        step1 = ApprovalStep(
            workflow_id=workflow.id,
            step_number=1,
            approval_type='GROUP_MANAGER'
        )
        db.session.add(step1)
        
        # 第二步：故障经理审批
        step2 = ApprovalStep(
            workflow_id=workflow.id,
            step_number=2,
            approval_type='ROLE'
        )
        problem_manager_role = Role.query.filter_by(name='Problem Manager').first()
        if problem_manager_role:
            step2.approved_by_role_id = problem_manager_role.id
        db.session.add(step2)
    
    db.session.commit()
    
    print("默认数据初始化完成！")
    print("- 创建了基础权限和角色")
    print("- 创建了默认管理员账号")
    print("- 创建了默认服务目录")
    print("- 创建了通知模板")
    print("- 创建了审批流程")

def create_test_users():
    """创建测试用户"""
    test_users = [
        {
            'username': 'john.doe',
            'email': 'john.doe@example.com',
            'password': 'password123',
            'real_name': '约翰·多伊',
            'department': 'SRE团队',
            'role': 'Engineer'
        },
        {
            'username': 'jane.smith',
            'email': 'jane.smith@example.com',
            'password': 'password123',
            'real_name': '简·史密斯',
            'department': '后端开发',
            'role': 'Problem Manager'
        },
        {
            'username': 'service.desk',
            'email': 'servicedesk@example.com',
            'password': 'password123',
            'real_name': '服务台',
            'department': 'IT支持',
            'role': 'Service Desk'
        }
    ]
    
    for user_data in test_users:
        if not User.query.filter_by(username=user_data['username']).first():
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                password_hash=generate_password_hash(user_data['password']),
                real_name=user_data['real_name'],
                department=user_data['department'],
                is_active=True
            )
            
            # 分配角色
            role = Role.query.filter_by(name=user_data['role']).first()
            if role:
                user.roles.append(role)
            
            db.session.add(user)
    
    db.session.commit()
    print("测试用户创建完成！")

if __name__ == '__main__':
    from app import create_app
    
    app = create_app()
    with app.app_context():
        init_default_data()
        create_test_users()