from flask import request, jsonify
from app.api import api_v1
from app import db
from app.models.alert import Alert, AlertComment
from app.models.user import User
from app.models.incident import Service
from app.utils.auth import permission_required, get_current_user
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@api_v1.route('/alerts', methods=['GET'])
@permission_required('alert:read')
def get_alerts():
    """获取告警列表"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    # 筛选参数
    status_filter = request.args.get('status')
    level_filter = request.args.get('level')
    service_id_filter = request.args.get('service_id', type=int)
    source_filter = request.args.get('source')
    environment_filter = request.args.get('environment')
    unlinked_only = request.args.get('unlinked', type=bool)
    
    # 构建查询
    query = Alert.query
    
    # 应用筛选条件
    if status_filter:
        query = query.filter(Alert.status == status_filter)
    
    if level_filter:
        query = query.filter(Alert.level == level_filter)
    
    if service_id_filter:
        query = query.filter(Alert.service_id == service_id_filter)
    
    if source_filter:
        query = query.filter(Alert.alert_source == source_filter)
    
    if environment_filter:
        query = query.filter(Alert.environment == environment_filter)
    
    if unlinked_only:
        query = query.filter(Alert.incident_id.is_(None))
    
    # 排序和分页
    pagination = query.order_by(Alert.fired_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'alerts': [alert.to_dict() for alert in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200

@api_v1.route('/alerts/<int:alert_id>', methods=['GET'])
@permission_required('alert:read')
def get_alert(alert_id):
    """获取告警详情"""
    alert = Alert.query.get_or_404(alert_id)
    
    # 获取评论
    comments = AlertComment.query.filter_by(
        alert_id=alert_id
    ).order_by(AlertComment.created_at.asc()).all()
    
    result = alert.to_dict()
    result['comments'] = [comment.to_dict() for comment in comments]
    
    return jsonify({'alert': result}), 200

@api_v1.route('/alerts', methods=['POST'])
@permission_required('alert:write')
def create_alert():
    """创建告警（通常由监控系统调用）"""
    data = request.get_json()
    
    required_fields = ['title', 'level', 'fired_at']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    try:
        # 解析fired_at时间
        fired_at = datetime.fromisoformat(data['fired_at'].replace('Z', '+00:00'))
        
        alert = Alert(
            title=data['title'],
            description=data.get('description'),
            alert_source=data.get('alert_source'),
            alert_rule=data.get('alert_rule'),
            level=data['level'],
            metric_name=data.get('metric_name'),
            metric_value=data.get('metric_value'),
            threshold=data.get('threshold'),
            service_id=data.get('service_id'),
            host=data.get('host'),
            environment=data.get('environment'),
            fired_at=fired_at
        )
        
        db.session.add(alert)
        db.session.commit()
        
        return jsonify({
            'message': 'Alert created successfully',
            'alert': alert.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Alert creation error: {str(e)}')
        return jsonify({'error': 'Alert creation failed'}), 500

@api_v1.route('/alerts/<int:alert_id>/acknowledge', methods=['PUT'])
@permission_required('alert:write')
def acknowledge_alert(alert_id):
    """确认告警"""
    alert = Alert.query.get_or_404(alert_id)
    current_user = get_current_user()
    
    if alert.status != 'New':
        return jsonify({'error': 'Alert is already acknowledged or processed'}), 400
    
    try:
        alert.acknowledge(current_user.id)
        db.session.commit()
        
        return jsonify({
            'message': 'Alert acknowledged successfully',
            'alert': alert.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Alert acknowledgment error: {str(e)}')
        return jsonify({'error': 'Alert acknowledgment failed'}), 500

@api_v1.route('/alerts/<int:alert_id>/ignore', methods=['PUT'])
@permission_required('alert:write')
def ignore_alert(alert_id):
    """忽略告警"""
    alert = Alert.query.get_or_404(alert_id)
    
    if alert.status in ['Linked', 'Ignored']:
        return jsonify({'error': 'Alert is already processed'}), 400
    
    try:
        alert.ignore()
        db.session.commit()
        
        return jsonify({
            'message': 'Alert ignored successfully',
            'alert': alert.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Alert ignore error: {str(e)}')
        return jsonify({'error': 'Alert ignore failed'}), 500

@api_v1.route('/alerts/<int:alert_id>/resolve', methods=['PUT'])
@permission_required('alert:write')
def resolve_alert(alert_id):
    """解决告警"""
    alert = Alert.query.get_or_404(alert_id)
    
    try:
        alert.resolve()
        db.session.commit()
        
        return jsonify({
            'message': 'Alert resolved successfully',
            'alert': alert.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Alert resolve error: {str(e)}')
        return jsonify({'error': 'Alert resolve failed'}), 500

@api_v1.route('/alerts/<int:alert_id>/link', methods=['PUT'])
@permission_required('alert:write')
def link_alert_to_incident(alert_id):
    """关联告警到故障"""
    data = request.get_json()
    incident_id = data.get('incident_id')
    
    if not incident_id:
        return jsonify({'error': 'incident_id is required'}), 400
    
    alert = Alert.query.get_or_404(alert_id)
    
    # 验证故障是否存在
    from app.models.incident_new import NewIncident
    incident = NewIncident.query.get(incident_id)
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404
    try:
        alert.link_to_incident(incident_id)
        db.session.commit()
        
        return jsonify({
            'message': 'Alert linked to incident successfully',
            'alert': alert.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Alert link error: {str(e)}')
        return jsonify({'error': 'Alert link failed'}), 500

@api_v1.route('/alerts/<int:alert_id>/comments', methods=['GET'])
@permission_required('alert:read')
def get_alert_comments(alert_id):
    """获取告警评论"""
    alert = Alert.query.get_or_404(alert_id)
    
    comments = AlertComment.query.filter_by(
        alert_id=alert_id
    ).order_by(AlertComment.created_at.asc()).all()
    
    return jsonify({
        'comments': [comment.to_dict() for comment in comments]
    }), 200

@api_v1.route('/alerts/<int:alert_id>/comments', methods=['POST'])
@permission_required('alert:write')
def create_alert_comment(alert_id):
    """创建告警评论"""
    data = request.get_json()
    current_user = get_current_user()
    
    if not data.get('content'):
        return jsonify({'error': 'content is required'}), 400
    
    alert = Alert.query.get_or_404(alert_id)
    
    try:
        comment = AlertComment(
            alert_id=alert_id,
            user_id=current_user.id,
            content=data['content'],
            is_private=data.get('is_private', False)
        )
        
        db.session.add(comment)
        db.session.commit()
        
        return jsonify({
            'message': 'Comment created successfully',
            'comment': comment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Comment creation error: {str(e)}')
        return jsonify({'error': 'Comment creation failed'}), 500

@api_v1.route('/alerts/batch', methods=['PUT'])
@permission_required('alert:write')
def batch_update_alerts():
    """批量更新告警"""
    data = request.get_json()
    alert_ids = data.get('alert_ids', [])
    action = data.get('action')
    
    if not alert_ids or not action:
        return jsonify({'error': 'alert_ids and action are required'}), 400
    
    if action not in ['acknowledge', 'ignore', 'resolve']:
        return jsonify({'error': 'Invalid action'}), 400
    
    current_user = get_current_user()
    
    try:
        alerts = Alert.query.filter(Alert.id.in_(alert_ids)).all()
        
        if len(alerts) != len(alert_ids):
            return jsonify({'error': 'Some alerts not found'}), 404
        
        updated_count = 0
        for alert in alerts:
            if action == 'acknowledge' and alert.status == 'New':
                alert.acknowledge(current_user.id)
                updated_count += 1
            elif action == 'ignore' and alert.status not in ['Linked', 'Ignored']:
                alert.ignore()
                updated_count += 1
            elif action == 'resolve':
                alert.resolve()
                updated_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'Batch {action} completed',
            'updated_count': updated_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Batch update error: {str(e)}')
        return jsonify({'error': 'Batch update failed'}), 500

@api_v1.route('/alerts/statistics', methods=['GET'])
@permission_required('alert:read')
def get_alert_statistics():
    """获取告警统计信息"""
    try:
        # 按状态统计
        status_stats = db.session.query(
            Alert.status, db.func.count(Alert.id)
        ).group_by(Alert.status).all()
        
        # 按级别统计
        level_stats = db.session.query(
            Alert.level, db.func.count(Alert.id)
        ).group_by(Alert.level).all()
        
        # 按来源统计
        source_stats = db.session.query(
            Alert.alert_source, db.func.count(Alert.id)
        ).group_by(Alert.alert_source).all()
        
        # 今日新增告警
        today = datetime.now().date()
        today_alerts = Alert.query.filter(
            db.func.date(Alert.created_at) == today
        ).count()
        
        return jsonify({
            'status_distribution': dict(status_stats),
            'level_distribution': dict(level_stats),
            'source_distribution': dict(source_stats),
            'today_alerts': today_alerts
        }), 200
        
    except Exception as e:
        logger.error(f'Statistics error: {str(e)}')
        return jsonify({'error': 'Failed to get statistics'}), 500