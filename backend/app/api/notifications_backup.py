from flask import request, jsonify, current_app
from app.api import api_v1
from app.models import NotificationTemplate, NotificationLog, NotificationChannel, NotificationRule
from app.utils.auth import permission_required
from app import db
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@api_v1.route('/notifications', methods=['GET'])
@permission_required('notification:admin')
def get_notifications():
    """获取通知概览"""
    try:
        # 获取基础统计信息
        total_templates = NotificationTemplate.query.filter_by(is_active=True).count()
        total_channels = NotificationChannel.query.filter_by(is_active=True).count()
        total_rules = NotificationRule.query.filter_by(is_active=True).count()
        total_logs = NotificationLog.query.count()
        
        return jsonify({
            'overview': {
                'total_templates': total_templates,
                'total_channels': total_channels,
                'total_rules': total_rules,
                'total_logs': total_logs
            }
        })
    except Exception as e:
        logger.error(f"获取通知概览失败: {e}")
        return jsonify({'error': '获取通知概览失败'}), 500

@api_v1.route('/notification/templates', methods=['GET'])
@permission_required('notification:admin')
def get_notification_templates():
    """获取通知模板列表"""
    try:
        templates = NotificationTemplate.query.filter_by(is_active=True).all()
        return jsonify({
            'templates': [template.to_dict() for template in templates]
        })
    except Exception as e:
        logger.error(f"获取通知模板失败: {e}")
        return jsonify({'error': '获取通知模板失败'}), 500

@api_v1.route('/notification/channels', methods=['GET'])
@permission_required('notification:admin')
def get_notification_channels():
    """获取通知渠道列表"""
    try:
        channels = NotificationChannel.query.filter_by(is_active=True).all()
        return jsonify({
            'channels': [channel.to_dict() for channel in channels]
        })
    except Exception as e:
        logger.error(f"获取通知渠道失败: {e}")
        return jsonify({'error': '获取通知渠道失败'}), 500

@api_v1.route('/notification/rules', methods=['GET'])
@permission_required('notification:admin')
def get_notification_rules():
    """获取通知规则列表"""
    try:
        rules = NotificationRule.query.filter_by(is_active=True).all()
        return jsonify({
            'rules': [rule.to_dict() for rule in rules]
        })
    except Exception as e:
        logger.error(f"获取通知规则失败: {e}")
        return jsonify({'error': '获取通知规则失败'}), 500

@api_v1.route('/notification/logs', methods=['GET'])
@permission_required('notification:admin')
def get_notification_logs():
    """获取通知发送日志"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        
        pagination = NotificationLog.query.order_by(
            NotificationLog.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'logs': [log.to_dict() for log in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })
    except Exception as e:
        logger.error(f"获取通知日志失败: {e}")
        return jsonify({'error': '获取通知日志失败'}), 500

@api_v1.route('/notification/logs/<int:log_id>', methods=['GET'])
@permission_required('notification:admin')
def get_notification_log_detail(log_id):
    """获取通知日志详情"""
    try:
        # 查找日志
        log = NotificationLog.query.get(log_id)
        if not log:
            return jsonify({'error': '通知日志不存在'}), 404
        
        # 获取关联的用户信息
        user_info = None
        if log.target_user_id:
            from app.models.user import User
            user = User.query.get(log.target_user_id)
            if user:
                user_info = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'real_name': user.real_name
                }
        
        # 构建详细的日志信息
        log_detail = {
            'id': log.id,
            'trigger_event': log.trigger_event,
            'trigger_record_id': log.trigger_record_id,
            'target_user': user_info,
            'channel_type': log.channel_type,
            'status': log.status,
            'request_content': log.request_content,
            'response_content': log.response_content,
            'external_id': log.external_id,
            'call_duration': log.call_duration,
            'call_status': log.call_status,
            'dtmf_input': log.dtmf_input,
            'created_at': log.created_at.isoformat() if log.created_at else None
        }
        
        # 添加渠道类型的中文描述
        channel_type_names = {
            'EMAIL': '邮件',
            'SMS': '短信',
            'WEBHOOK': 'Webhook',
            'VOICE_CALL': '语音服务',
            'SLACK': 'Slack',
            'TEAMS': 'Teams',
            'DINGTALK': '钉钉'
        }
        log_detail['channel_type_name'] = channel_type_names.get(log.channel_type, log.channel_type)
        
        # 添加状态的中文描述
        status_names = {
            'SUCCESS': '成功',
            'FAILED': '失败'
        }
        log_detail['status_name'] = status_names.get(log.status, log.status)
        
        # 添加触发事件的中文描述
        event_names = {
            'manual_notification': '手动通知',
            'incident_created': '故障创建',
            'incident_updated': '故障更新',
            'incident_resolved': '故障解决',
            'test': '测试'
        }
        log_detail['trigger_event_name'] = event_names.get(log.trigger_event, log.trigger_event)
        
        return jsonify({
            'log': log_detail
        }), 200
        
    except Exception as e:
        logger.error(f"获取通知日志详情失败: {e}")
        return jsonify({'error': '获取通知日志详情失败'}), 500

@api_v1.route('/notification/send', methods=['POST'])
@permission_required('notification:admin')
def send_notification():
    """发送通知"""
    try:
        data = request.get_json()
        
        # 检查是否是批量通知格式
        if 'channel_ids' in data:
            # 批量通知格式
            return send_batch_notification(data)
        else:
            # 单个通知格式
            return send_single_notification(data)
            
    except Exception as e:
        logger.error(f"发送通知失败: {e}")
        return jsonify({'error': '发送通知失败'}), 500

def send_batch_notification(data):
    """发送批量通知"""
    try:
        # 验证必填字段
        required_fields = ['channel_ids', 'message']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必填字段: {field}'}), 400
        
        channel_ids = data['channel_ids']
        message = data['message']
        incident_id = data.get('incident_id')
        group_ids = data.get('group_ids', [])
        
        if not channel_ids:
            return jsonify({'error': '请选择至少一个通知渠道'}), 400
        
        # 获取选中的通知渠道
        channels = NotificationChannel.query.filter(
            NotificationChannel.id.in_(channel_ids),
            NotificationChannel.is_active == True
        ).all()
        
        if not channels:
            return jsonify({'error': '未找到有效的通知渠道'}), 400
        
        # 获取用户组中的用户
        users = []
        if group_ids:
            from app.models.user import User, Group
            groups = Group.query.filter(Group.id.in_(group_ids)).all()
            for group in groups:
                users.extend(group.members)
        
        if not users:
            return jsonify({'error': '请选择至少一个用户组'}), 400
        
        # 发送通知到每个渠道
        results = []
        for channel in channels:
            for user in users:
                try:
                    # 根据渠道类型发送通知
                    if channel.type == 'EMAIL':
                        result = send_email_notification(user.email, message, user.id, incident_id)
                    elif channel.type == 'SMS':
                        result = send_sms_notification(user.phone, message, user.id, incident_id)
                    elif channel.type == 'WEBHOOK':
                        result = send_webhook_notification(channel, message, user.id, incident_id)
                    else:
                        result = {'status': 'FAILED', 'message': f'不支持的通知渠道类型: {channel.type}'}
                    
                    results.append({
                        'channel': channel.name,
                        'user': user.real_name or user.username,
                        'result': result
                    })
                    
                except Exception as e:
                    results.append({
                        'channel': channel.name,
                        'user': user.real_name or user.username,
                        'result': {'status': 'FAILED', 'message': str(e)}
                    })
        
        # 统计结果
        success_count = sum(1 for r in results if r['result']['status'] == 'SUCCESS')
        total_count = len(results)
        
        return jsonify({
            'message': f'批量通知发送完成，成功: {success_count}/{total_count}',
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"批量通知发送失败: {e}")
        return jsonify({'error': f'批量通知发送失败: {str(e)}'}), 500

def send_single_notification(data):
    """发送单个通知"""
    # 验证必填字段
    required_fields = ['channel_type', 'to', 'subject', 'content']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'缺少必填字段: {field}'}), 400
    
    # 根据渠道类型发送通知
    channel_type = data['channel_type']
    
    if channel_type == 'EMAIL':
            # 发送邮件通知
            from app.notification.service import EmailChannel
            from flask_mail import Mail
            
            # 获取邮件配置
            mail = Mail()
            mail.init_app(current_app)
            
            # 从数据库获取邮件渠道配置
            email_channel_db = NotificationChannel.query.filter_by(type='EMAIL', is_active=True).first()
            if not email_channel_db:
                return jsonify({'error': '未找到启用的邮件渠道配置'}), 500
            
            email_config = email_channel_db.config
            if not email_config:
                return jsonify({'error': '邮件渠道配置为空'}), 500
            
            # 创建邮件配置
            mail_config = {
                'smtp_server': email_config['smtp_host'],
                'smtp_port': email_config['smtp_port'],
                'username': email_config['smtp_username'],
                'password': email_config['smtp_password'],
                'use_tls': email_config.get('use_tls', True)
            }
            
            email_channel = EmailChannel(mail_config, mail)
            
            # 发送邮件
            result = email_channel.send(
                to=data['to'],
                subject=data['subject'],
                content=data['content']
            )
            
            # 记录发送日志
            from app.models import NotificationLog
            log = NotificationLog(
                channel_type='EMAIL',
                target_user_id=data.get('user_id'),
                trigger_event=data.get('trigger_event', 'manual'),
                trigger_record_id=data.get('trigger_record_id', 0),  # 使用传入的值或默认值
                status=result['status'],
                request_content=f'发送邮件到: {data["to"]}',
                response_content=result.get('message', ''),
                external_id=result.get('external_id')
            )
            db.session.add(log)
            db.session.commit()
            
            if result['status'] == 'SUCCESS':
                return jsonify({'message': '通知发送成功', 'result': result}), 200
            else:
                return jsonify({'error': f'通知发送失败: {result["message"]}'}), 500
        
        elif channel_type == 'SMS':
            # 发送短信通知
            from app.notification.service import SMSChannel
            
            sms_config = {
                'api_url': current_app.config.get('SMS_API_URL'),
                'access_key': current_app.config.get('SMS_ACCESS_KEY_ID'),
                'access_secret': current_app.config.get('SMS_ACCESS_KEY_SECRET'),
                'sign_name': current_app.config.get('SMS_SIGN_NAME')
            }
            
            sms_channel = SMSChannel(sms_config)
            result = sms_channel.send(
                to=data['to'],
                subject=data['subject'],
                content=data['content']
            )
            
            # 记录发送日志
            from app.models import NotificationLog
            log = NotificationLog(
                channel_type='SMS',
                target_user_id=data.get('user_id'),
                trigger_event=data.get('trigger_event', 'manual'),
                trigger_record_id=data.get('trigger_record_id', 0),  # 使用传入的值或默认值
                status=result['status'],
                request_content=f'发送短信到: {data["to"]}',
                response_content=result.get('message', ''),
                external_id=result.get('external_id')
            )
            db.session.add(log)
            db.session.commit()
            
            if result['status'] == 'SUCCESS':
                return jsonify({'message': '通知发送成功', 'result': result}), 200
            else:
                return jsonify({'error': f'通知发送失败: {result["message"]}'}), 500
        
        else:
            return jsonify({'error': f'不支持的通知渠道类型: {channel_type}'}), 400
            
    except Exception as e:
        logger.error(f"发送通知失败: {e}")
        return jsonify({'error': '发送通知失败'}), 500

@api_v1.route('/notification/test', methods=['POST'])
@permission_required('notification:admin')
def test_notification():
    """测试通知渠道"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['channel_type', 'to']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必填字段: {field}'}), 400
        
        channel_type = data['channel_type']
        test_to = data['to']
        
        if channel_type == 'EMAIL':
            # 测试邮件发送
            from app.notification.service import EmailChannel
            from flask_mail import Mail
            
            # 从数据库获取邮件渠道配置
            email_channel_db = NotificationChannel.query.filter_by(type='EMAIL', is_active=True).first()
            if not email_channel_db:
                return jsonify({'error': '未找到启用的邮件渠道配置'}), 400
            
            # 验证邮件配置
            email_config = email_channel_db.config
            if not email_config:
                return jsonify({'error': '邮件渠道配置为空'}), 400
            
            # 检查必要的配置字段
            required_fields = ['smtp_host', 'smtp_port', 'from_email', 'smtp_username', 'smtp_password']
            missing_fields = [field for field in required_fields if not email_config.get(field)]
            if missing_fields:
                return jsonify({'error': f'邮件配置不完整，缺少字段: {", ".join(missing_fields)}'}), 400
            
            # 创建邮件配置
            mail_config = {
                'smtp_server': email_config['smtp_host'],
                'smtp_port': email_config['smtp_port'],
                'username': email_config['smtp_username'],
                'password': email_config['smtp_password'],
                'use_tls': email_config.get('use_tls', True)
            }
            
            # 初始化Flask-Mail
            mail = Mail()
            mail.init_app(current_app)
            
            email_channel = EmailChannel(mail_config, mail)
            
            # 发送测试邮件
            test_subject = '事件管理平台 - 邮件测试'
            test_content = f'''
            <html>
            <body>
                <h2>邮件测试通知</h2>
                <p>这是一封测试邮件，用于验证邮件配置是否正确。</p>
                <p>发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>如果您收到这封邮件，说明邮件配置正确。</p>
                <hr>
                <p style="color: #666; font-size: 12px;">
                    此邮件由事件管理平台自动发送，请勿回复。
                </p>
            </body>
            </html>
            '''
            
            try:
                result = email_channel.send(
                    to=test_to,
                    subject=test_subject,
                    content=test_content
                )
            except Exception as e:
                # 捕获邮件发送异常，提供更详细的错误信息
                error_msg = f'邮件发送异常: {str(e)}'
                if 'Connection unexpectedly closed' in str(e):
                    error_msg = 'SMTP连接被意外关闭，请检查SMTP服务器配置和网络连接'
                elif 'Authentication failed' in str(e):
                    error_msg = 'SMTP认证失败，请检查用户名和密码'
                elif 'Connection refused' in str(e):
                    error_msg = '无法连接到SMTP服务器，请检查服务器地址和端口'
                
                return jsonify({'error': error_msg}), 500
            
            # 记录测试日志
            from app.models import NotificationLog
            log = NotificationLog(
                channel_type='EMAIL',
                target_user_id=data.get('user_id'),
                trigger_event='test',
                trigger_record_id=0,  # 测试时使用默认值
                status=result['status'],
                request_content=f'测试邮件发送到: {test_to}',
                response_content=result.get('message', ''),
                external_id=result.get('external_id')
            )
            db.session.add(log)
            db.session.commit()
            
            if result['status'] == 'SUCCESS':
                return jsonify({
                    'message': '邮件测试发送成功',
                    'result': result,
                                    'details': {
                    'smtp_server': mail_config['smtp_server'],
                    'smtp_port': mail_config['smtp_port'],
                    'username': mail_config['username'],
                    'test_to': test_to
                }
                }), 200
            else:
                return jsonify({'error': f'邮件测试发送失败: {result["message"]}'}), 500
        
        elif channel_type == 'SMS':
            # 测试短信发送
            from app.notification.service import SMSChannel
            
            sms_config = {
                'api_url': current_app.config.get('SMS_API_URL'),
                'access_key': current_app.config.get('SMS_ACCESS_KEY_ID'),
                'access_secret': current_app.config.get('SMS_ACCESS_KEY_SECRET'),
                'sign_name': current_app.config.get('SMS_SIGN_NAME')
            }
            
            sms_channel = SMSChannel(sms_config)
            
            test_content = f'事件管理平台测试短信 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            
            result = sms_channel.send(
                to=test_to,
                subject='SMS Test',
                content=test_content
            )
            
            # 记录测试日志
            from app.models import NotificationLog
            log = NotificationLog(
                channel_type='SMS',
                target_user_id=data.get('user_id'),
                trigger_event='test',
                trigger_record_id=0,  # 测试时使用默认值
                status=result['status'],
                request_content=f'测试短信发送到: {test_to}',
                response_content=result.get('message', ''),
                external_id=result.get('external_id')
            )
            db.session.add(log)
            db.session.commit()
            
            if result['status'] == 'SUCCESS':
                return jsonify({
                    'message': '短信测试发送成功',
                    'result': result
                }), 200
            else:
                return jsonify({'error': f'短信测试发送失败: {result["message"]}'}), 500
        
        elif channel_type == 'WEBHOOK':
            # 测试Webhook发送
            from app.notification.service import WebhookChannel
            
            # 验证webhook URL
            if not test_to or test_to.strip() == '':
                return jsonify({'error': 'Webhook URL不能为空，请先配置Webhook URL'}), 400
            
            if not test_to.startswith(('http://', 'https://')):
                return jsonify({'error': 'Webhook URL必须以http://或https://开头'}), 400
            
            # 自动检测Webhook类型
            webhook_type = 'generic'
            if 'weixin' in test_to.lower() or 'wechat' in test_to.lower():
                webhook_type = 'wechat'
            elif 'dingtalk' in test_to.lower():
                webhook_type = 'dingtalk'
            
            webhook_config = {
                'webhook_url': test_to,
                'webhook_type': webhook_type,
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'timeout': 30
            }
            
            webhook_channel = WebhookChannel(webhook_config)
            
            test_content = f'事件管理平台测试Webhook - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            
            try:
                result = webhook_channel.send(
                    to=test_to,
                    subject='Webhook Test',
                    content=test_content
                )
            except Exception as e:
                error_msg = f'Webhook发送异常: {str(e)}'
                if 'Invalid URL' in str(e):
                    error_msg = f'无效的Webhook URL: {test_to}，请检查URL格式'
                elif 'Connection refused' in str(e):
                    error_msg = '无法连接到Webhook服务器，请检查URL和网络连接'
                elif 'timeout' in str(e).lower():
                    error_msg = 'Webhook请求超时，请检查服务器响应时间'
                
                return jsonify({'error': error_msg}), 500
            
            # 记录测试日志
            from app.models import NotificationLog
            log = NotificationLog(
                channel_type='WEBHOOK',
                target_user_id=data.get('user_id'),
                trigger_event='test',
                trigger_record_id=0,  # 测试时使用默认值
                status=result['status'],
                request_content=f'测试Webhook发送到: {test_to}',
                response_content=result.get('message', ''),
                external_id=result.get('external_id')
            )
            db.session.add(log)
            db.session.commit()
            
            if result['status'] == 'SUCCESS':
                return jsonify({
                    'message': 'Webhook测试发送成功',
                    'result': result
                }), 200
            else:
                return jsonify({'error': f'Webhook测试发送失败: {result["message"]}'}), 500
        
        elif channel_type == 'VOICE_CALL':
            # 测试语音电话
            from app.notification.service import VoiceCallChannel
            
            voice_config = {
                'api_url': current_app.config.get('VOICE_CALL_API_URL'),
                'api_key': current_app.config.get('VOICE_CALL_API_KEY'),
                'from_number': current_app.config.get('VOICE_CALL_FROM_NUMBER')
            }
            
            voice_channel = VoiceCallChannel(voice_config)
            
            test_content = f'事件管理平台测试语音电话 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            
            result = voice_channel.send(
                to=test_to,
                subject='Voice Call Test',
                content=test_content
            )
            
            # 记录测试日志
            from app.models import NotificationLog
            log = NotificationLog(
                channel_type='VOICE_CALL',
                target_user_id=data.get('user_id'),
                trigger_event='test',
                trigger_record_id=0,  # 测试时使用默认值
                status=result['status'],
                request_content=f'测试语音电话发送到: {test_to}',
                response_content=result.get('message', ''),
                external_id=result.get('external_id')
            )
            db.session.add(log)
            db.session.commit()
            
            if result['status'] == 'SUCCESS':
                return jsonify({
                    'message': '语音电话测试发送成功',
                    'result': result
                }), 200
            else:
                return jsonify({'error': f'语音电话测试发送失败: {result["message"]}'}), 500
        
        else:
            return jsonify({'error': f'不支持的通知渠道类型: {channel_type}'}), 400
            
    except Exception as e:
        logger.error(f"测试通知失败: {e}")
        return jsonify({'error': f'测试通知失败: {str(e)}'}), 500

@api_v1.route('/notification/channels/<int:channel_id>', methods=['PUT'])
@permission_required('notification:admin')
def update_notification_channel(channel_id):
    """更新通知渠道配置"""
    try:
        data = request.get_json()
        
        # 查找渠道
        channel = NotificationChannel.query.get(channel_id)
        if not channel:
            return jsonify({'error': '通知渠道不存在'}), 404
        
        # 更新渠道信息
        if 'name' in data:
            channel.name = data['name']
        if 'is_active' in data:
            channel.is_active = data['is_active']
        if 'config' in data:
            channel.config = data['config']
        
        db.session.commit()
        
        return jsonify({
            'message': '通知渠道配置更新成功',
            'channel': channel.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"更新通知渠道失败: {e}")
        db.session.rollback()
        return jsonify({'error': '更新通知渠道失败'}), 500

@api_v1.route('/notification/channels', methods=['POST'])
@permission_required('notification:admin')
def create_notification_channel():
    """创建新的通知渠道"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['type', 'name', 'config']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'缺少必填字段: {field}'}), 400
        
        # 创建新渠道
        channel = NotificationChannel(
            type=data['type'],
            name=data['name'],
            config=data['config'],
            is_active=data.get('is_active', True)
        )
        
        db.session.add(channel)
        db.session.commit()
        
        return jsonify({
            'message': '通知渠道创建成功',
            'channel': channel.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"创建通知渠道失败: {e}")
        db.session.rollback()
        return jsonify({'error': '创建通知渠道失败'}), 500
