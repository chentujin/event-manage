from flask import request, jsonify
from app.api import api_v1
from app.models import NotificationTemplate, NotificationLog
from app.utils.auth import permission_required
import logging

logger = logging.getLogger(__name__)

@api_v1.route('/notification/templates', methods=['GET'])
@permission_required('notification:admin')
def get_notification_templates():
    """获取通知模板列表"""
    templates = NotificationTemplate.query.filter(
        NotificationTemplate.is_active == True
    ).all()
    return jsonify({
        'templates': [template.to_dict() for template in templates]
    }), 200

@api_v1.route('/notification/logs', methods=['GET'])
@permission_required('notification:admin')
def get_notification_logs():
    """获取通知发送日志"""
    logs = NotificationLog.query.order_by(
        NotificationLog.created_at.desc()
    ).limit(100).all()
    return jsonify({
        'logs': [log.to_dict() for log in logs]
    }), 200
