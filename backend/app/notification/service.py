"""
通知引擎核心服务
负责处理各种通知渠道的消息发送
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from flask import current_app
from flask_mail import Message, Mail
from jinja2 import Template
import requests
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationChannel(ABC):
    """通知渠道抽象基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    def send(self, to: str, subject: str, content: str, **kwargs) -> Dict[str, Any]:
        """发送通知"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """验证配置是否有效"""
        pass

class EmailChannel(NotificationChannel):
    """邮件通知渠道"""
    
    def __init__(self, config: Dict[str, Any], mail: Mail):
        super().__init__(config)
        self.mail = mail
    
    def send(self, to: str, subject: str, content: str, **kwargs) -> Dict[str, Any]:
        try:
            msg = Message(
                subject=subject,
                recipients=[to],
                html=content,
                sender=current_app.config.get('MAIL_DEFAULT_SENDER')
            )
            
            self.mail.send(msg)
            
            return {
                'status': 'SUCCESS',
                'message': 'Email sent successfully',
                'external_id': None
            }
        except Exception as e:
            logger.error(f'Email sending failed: {str(e)}')
            return {
                'status': 'FAILED',
                'message': str(e),
                'external_id': None
            }
    
    def validate_config(self) -> bool:
        required_keys = ['smtp_server', 'smtp_port', 'username', 'password']
        return all(key in self.config for key in required_keys)

class SMSChannel(NotificationChannel):
    """短信通知渠道"""
    
    def send(self, to: str, subject: str, content: str, **kwargs) -> Dict[str, Any]:
        try:
            # 模拟短信发送（实际需要根据服务商API实现）
            logger.info(f'SMS would be sent to {to}: {content}')
            
            return {
                'status': 'SUCCESS',
                'message': 'SMS sent successfully (simulated)',
                'external_id': 'sms_' + str(int(datetime.utcnow().timestamp()))
            }
        except Exception as e:
            logger.error(f'SMS sending failed: {str(e)}')
            return {
                'status': 'FAILED',
                'message': str(e),
                'external_id': None
            }
    
    def validate_config(self) -> bool:
        required_keys = ['api_url', 'access_key', 'access_secret', 'sign_name']
        return all(key in self.config for key in required_keys)

class WebhookChannel(NotificationChannel):
    """Webhook通知渠道（支持钉钉、企业微信等）"""
    
    def send(self, to: str, subject: str, content: str, **kwargs) -> Dict[str, Any]:
        try:
            webhook_url = self.config.get('webhook_url')
            webhook_type = self.config.get('webhook_type', 'dingtalk')
            
            if webhook_type == 'dingtalk':
                payload = {
                    'msgtype': 'text',
                    'text': {
                        'content': f'{subject}\n{content}'
                    }
                }
            else:  # generic webhook
                payload = {
                    'text': f'{subject}\n{content}'
                }
            
            response = requests.post(webhook_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                return {
                    'status': 'SUCCESS',
                    'message': 'Webhook sent successfully',
                    'external_id': f'webhook_{int(datetime.utcnow().timestamp())}',
                    'response': response.text
                }
            else:
                return {
                    'status': 'FAILED',
                    'message': f'Webhook failed with status {response.status_code}',
                    'external_id': None,
                    'response': response.text
                }
                
        except Exception as e:
            logger.error(f'Webhook sending failed: {str(e)}')
            return {
                'status': 'FAILED',
                'message': str(e),
                'external_id': None
            }
    
    def validate_config(self) -> bool:
        return 'webhook_url' in self.config

class VoiceCallChannel(NotificationChannel):
    """语音电话通知渠道"""
    
    def send(self, to: str, subject: str, content: str, **kwargs) -> Dict[str, Any]:
        try:
            # 模拟语音电话（实际需要调用语音服务API）
            logger.info(f'Voice call would be made to {to}: {content}')
            
            return {
                'status': 'SUCCESS',
                'message': 'Voice call initiated successfully (simulated)',
                'external_id': f'voice_{int(datetime.utcnow().timestamp())}',
                'call_duration': 0,
                'call_status': 'initiated'
            }
            
        except Exception as e:
            logger.error(f'Voice call failed: {str(e)}')
            return {
                'status': 'FAILED',
                'message': str(e),
                'external_id': None
            }
    
    def validate_config(self) -> bool:
        required_keys = ['api_url', 'api_key', 'from_number']
        return all(key in self.config for key in required_keys)

class NotificationService:
    """通知服务核心类"""
    
    def __init__(self, mail: Mail):
        self.mail = mail
        self.channels = {}
    
    def register_channel(self, channel_type: str, config: Dict[str, Any]):
        """注册通知渠道"""
        if channel_type == 'EMAIL':
            self.channels[channel_type] = EmailChannel(config, self.mail)
        elif channel_type == 'SMS':
            self.channels[channel_type] = SMSChannel(config)
        elif channel_type in ['DINGTALK', 'WECHAT', 'SLACK', 'WEBHOOK']:
            self.channels[channel_type] = WebhookChannel(config)
        elif channel_type == 'VOICE_CALL':
            self.channels[channel_type] = VoiceCallChannel(config)
        else:
            raise ValueError(f'Unsupported channel type: {channel_type}')
    
    def send_notification(
        self,
        channel_type: str,
        to: str,
        subject: str,
        content: str,
        **kwargs
    ) -> Dict[str, Any]:
        """发送通知"""
        if channel_type not in self.channels:
            return {
                'status': 'FAILED',
                'message': f'Channel {channel_type} not configured'
            }
        
        channel = self.channels[channel_type]
        return channel.send(to, subject, content, **kwargs)
    
    def render_template(self, template_content: str, context: Dict[str, Any]) -> str:
        """渲染模板"""
        try:
            template = Template(template_content)
            return template.render(**context)
        except Exception as e:
            logger.error(f'Template rendering failed: {str(e)}')
            return template_content  # 返回原始内容
    
    def validate_channel(self, channel_type: str) -> bool:
        """验证渠道配置"""
        if channel_type not in self.channels:
            return False
        return self.channels[channel_type].validate_config()

# 全局通知服务实例
notification_service = None

def init_notification_service(mail: Mail):
    """初始化通知服务"""
    global notification_service
    notification_service = NotificationService(mail)
    return notification_service

def get_notification_service() -> NotificationService:
    """获取通知服务实例"""
    return notification_service