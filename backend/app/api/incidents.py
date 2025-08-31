from flask import request, jsonify
from app.api import api_v1
from app import db
from app.models import Incident, IncidentComment, IncidentStatusLog, Service, User
from app.utils.auth import permission_required, get_current_user
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@api_v1.route('/incidents/assignable-users', methods=['GET'])
@permission_required('incident:read')
def get_assignable_users():
    """获取可分配的用户列表事件分配使用"""
    try:
        # 获取所有激活的用户
        users = User.query.filter_by(is_active=True).all()
        return jsonify({
            'users': [user.to_dict() for user in users]
        })
    except Exception as e:
        logger.error(f"获取可分配用户失败: {e}")
        return jsonify({'error': '获取用户列表失败'}), 500

@api_v1.route('/incidents', methods=['GET'])
@permission_required('incident:read')
def get_incidents():
    """获取事件列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        service_id = request.args.get('service_id', type=int)
        
        # 构建查询
        query = Incident.query
        
        if status:
            query = query.filter(Incident.status == status)
        if service_id:
            query = query.filter(Incident.service_id == service_id)
        
        # 分页
        pagination = query.order_by(Incident.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'incidents': [incident.to_dict() for incident in pagination.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })
    except Exception as e:
        logger.error(f"获取事件列表失败: {e}")
        return jsonify({'error': '获取事件列表失败'}), 500

@api_v1.route('/incidents/<int:incident_id>', methods=['GET'])
@permission_required('incident:read')
def get_incident(incident_id):
    """获取事件详情"""
    try:
        incident = Incident.query.get_or_404(incident_id)
        return jsonify({'incident': incident.to_dict()})
    except Exception as e:
        logger.error(f"获取事件详情失败: {e}")
        return jsonify({'error': '获取事件详情失败'}), 500

@api_v1.route('/incidents/<int:incident_id>/logs', methods=['GET'])
@permission_required('incident:read')
def get_incident_logs(incident_id):
    """获取事件状态变更日志"""
    try:
        logs = IncidentStatusLog.query.filter_by(incident_id=incident_id).order_by(IncidentStatusLog.created_at.desc()).all()
        return jsonify({
            'logs': [log.to_dict() for log in logs]
        })
    except Exception as e:
        logger.error(f"获取事件日志失败: {e}")
        return jsonify({'error': '获取事件日志失败'}), 500

@api_v1.route('/incidents', methods=['POST'])
@permission_required('incident:write')
def create_incident():
    """创建事件"""
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        # 兼容前端字段名称
        title = data.get('title') or data.get('故障标题')
        description = data.get('description') or data.get('故障描述')
        impact = data.get('impact') or data.get('severity') or 'Medium'
        urgency = data.get('urgency') or 'Medium'
        
        # 验证必填字段
        if not title:
            return jsonify({'error': '标题是必填字段'}), 400
        if not description:
            return jsonify({'error': '描述是必填字段'}), 400
        if not impact:
            return jsonify({'error': '影响度是必填字段'}), 400
        if not urgency:
            return jsonify({'error': '紧急度是必填字段'}), 400
        
        # 验证枚举值
        valid_impacts = ['High', 'Medium', 'Low', '高', '中', '低']
        valid_urgencies = ['High', 'Medium', 'Low', '高', '中', '低']
        
        if impact not in valid_impacts:
            return jsonify({'error': '无效的影响度值'}), 400
        if urgency not in valid_urgencies:
            return jsonify({'error': '无效的紧急度值'}), 400
        
        # 将中文值转换为英文
        impact_map = {'高': 'High', '中': 'Medium', '低': 'Low'}
        urgency_map = {'高': 'High', '中': 'Medium', '低': 'Low'}
        
        impact = impact_map.get(impact, impact)
        urgency = urgency_map.get(urgency, urgency)
        
        # 创建事件
        incident = Incident(
            title=title,
            description=description,
            impact=impact,
            urgency=urgency,
            service_id=data.get('service_id') or 1,  # 默认服务ID
            assignee_id=data.get('assignee_id') or current_user.id,
            reporter_id=current_user.id,
            status='New'
        )
        
        db.session.add(incident)
        db.session.commit()
        
        return jsonify(incident.to_dict()), 201
        
    except Exception as e:
        logger.error(f"创建事件失败: {e}")
        db.session.rollback()
        return jsonify({'error': f'创建事件失败: {str(e)}'}), 500

@api_v1.route('/incidents/<int:incident_id>', methods=['PUT'])
@permission_required('incident:write')
def update_incident(incident_id):
    """更新事件信息"""
    incident = Incident.query.get_or_404(incident_id)
    data = request.get_json()
    current_user = get_current_user()
    
    try:
        # 记录状态变更
        old_status = incident.status
        
        # 更新基本字段
        allowed_fields = ['title', 'description', 'impact', 'urgency', 'service_id']
        for field in allowed_fields:
            if field in data:
                # 验证枚举值
                if field in ['impact', 'urgency'] and data[field] not in ['High', 'Medium', 'Low']:
                    return jsonify({'error': f'Invalid {field} value'}), 400
                setattr(incident, field, data[field])
        
        # 状态更新（需要特殊处理）
        if 'status' in data:
            new_status = data['status']
            valid_statuses = ['New', 'In Progress', 'On Hold', 'Resolved', 'Closed', 'Reopened']
            
            if new_status not in valid_statuses:
                return jsonify({'error': 'Invalid status value'}), 400
            
            # 状态流转规则检查
            if not _is_valid_status_transition(old_status, new_status):
                return jsonify({
                    'error': f'Invalid status transition from {old_status} to {new_status}'
                }), 400
            
            incident.status = new_status
            
            # 记录状态变更日志
            if old_status != new_status:
                status_log = IncidentStatusLog(
                    incident_id=incident_id,
                    user_id=current_user.id,
                    old_status=old_status,
                    new_status=new_status,
                    action=f'状态更新为: {new_status}',
                    comments=data.get('comments', '')
                )
                db.session.add(status_log)
            
            # 自动设置时间戳
            if new_status == 'In Progress' and old_status != 'In Progress':
                incident.started_at = incident.started_at or datetime.utcnow()
            elif new_status == 'Resolved' and old_status != 'Resolved':
                incident.resolved_at = datetime.utcnow()
            elif new_status == 'Closed' and old_status != 'Closed':
                incident.closed_at = datetime.utcnow()
            elif new_status == 'Reopened':
                incident.resolved_at = None
                incident.closed_at = None
        
        # 分配人更新（需要权限检查）
        if 'assignee_id' in data:
            if not can_assign_incident(current_user, incident):
                return jsonify({'error': 'Permission denied to assign incident'}), 403
            
            old_assignee_id = incident.assignee_id
            new_assignee_id = data['assignee_id']
            
            if old_assignee_id != new_assignee_id:
                incident.assignee_id = new_assignee_id
                
                # 获取分配人信息
                if new_assignee_id:
                    assignee = User.query.get(new_assignee_id)
                    assignee_name = assignee.real_name or assignee.username if assignee else '未知用户'
                else:
                    assignee_name = '未分配'
                
                # 记录分配状态日志，使用被分配的用户ID
                assign_log = IncidentStatusLog(
                    incident_id=incident_id,
                    user_id=new_assignee_id if new_assignee_id else current_user.id,  # 使用被分配的用户ID
                    old_status=incident.status,
                    new_status=incident.status,
                    action='重新分配' if old_assignee_id else '事件分配',
                    comments=f'事件已分配给 {assignee_name}'
                )
                db.session.add(assign_log)
        
        db.session.commit()
        
        logger.info(f'Incident updated: {incident.id} by {current_user.username}')
        
        # TODO: 触发通知（如果状态或分配人有变化）
        
        return jsonify({
            'message': 'Incident updated successfully',
            'incident': incident.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Incident update error: {str(e)}')
        return jsonify({'error': 'Incident update failed'}), 500

@api_v1.route('/incidents/<int:incident_id>/comments', methods=['POST'])
@permission_required('incident:write')
def add_incident_comment(incident_id):
    """为事件添加评论"""
    incident = Incident.query.get_or_404(incident_id)
    data = request.get_json()
    current_user = get_current_user()
    
    if not data.get('content'):
        return jsonify({'error': 'Comment content is required'}), 400
    
    try:
        comment = IncidentComment(
            incident_id=incident_id,
            user_id=current_user.id,
            content=data['content'],
            is_private=data.get('is_private', False)
        )
        
        db.session.add(comment)
        db.session.commit()
        
        logger.info(f'Comment added to incident {incident_id} by {current_user.username}')
        
        # TODO: 处理@提及用户的通知
        
        return jsonify({
            'message': 'Comment added successfully',
            'comment': comment.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Comment creation error: {str(e)}')
        return jsonify({'error': 'Comment creation failed'}), 500

@api_v1.route('/incidents/<int:incident_id>/assign', methods=['POST'])
@permission_required('incident:assign')
def assign_incident(incident_id):
    """分配事件"""
    incident = Incident.query.get_or_404(incident_id)
    data = request.get_json()
    current_user = get_current_user()
    
    if not can_assign_incident(current_user, incident):
        return jsonify({'error': 'Permission denied to assign incident'}), 403
    
    assignee_id = data.get('assignee_id')
    if assignee_id:
        assignee = User.query.get(assignee_id)
        if not assignee:
            return jsonify({'error': 'Assignee not found'}), 404
        if not assignee.is_active:
            return jsonify({'error': 'Cannot assign to inactive user'}), 400
    
    try:
        old_assignee_id = incident.assignee_id
        old_status = incident.status
        incident.assignee_id = assignee_id
        
        # 如果状态是New，自动更新为In Progress
        if incident.status == 'New' and assignee_id:
            incident.status = 'In Progress'
            
            # 记录状态变更日志
            status_log = IncidentStatusLog(
                incident_id=incident_id,
                user_id=current_user.id,
                old_status=old_status,
                new_status='In Progress',
                action='分配事件并开始处理',
                comments=f'事件已分配给 {assignee.real_name or assignee.username}'
            )
            db.session.add(status_log)
        elif assignee_id and old_assignee_id != assignee_id:
            # 记录分配变更日志（状态不变）
            assign_log = IncidentStatusLog(
                incident_id=incident_id,
                user_id=current_user.id,
                old_status=incident.status,
                new_status=incident.status,
                action='重新分配事件',
                comments=f'事件重新分配给 {assignee.real_name or assignee.username}'
            )
            db.session.add(assign_log)
        
        db.session.commit()
        
        logger.info(f'Incident {incident_id} assigned to {assignee_id} by {current_user.username}')
        
        # TODO: 通知新的分配人
        
        return jsonify({
            'message': 'Incident assigned successfully',
            'incident': incident.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Incident assignment error: {str(e)}')
        return jsonify({'error': 'Incident assignment failed'}), 500

@api_v1.route('/incidents/<int:incident_id>/close', methods=['POST'])
def close_incident(incident_id):
    """关闭事件"""
    incident = Incident.query.get_or_404(incident_id)
    data = request.get_json()
    current_user = get_current_user()
    
    if not can_close_incident(current_user, incident):
        return jsonify({'error': 'Permission denied to close incident'}), 403
    
    if incident.status in ['Closed']:
        return jsonify({'error': 'Incident is already closed'}), 400
    
    try:
        old_status = incident.status
        
        # 如果还没有resolved，先设为resolved
        if incident.status != 'Resolved':
            incident.status = 'Resolved'
            incident.resolved_at = datetime.utcnow()
            
            # 记录resolved状态日志
            resolved_log = IncidentStatusLog(
                incident_id=incident_id,
                user_id=current_user.id,
                old_status=old_status,
                new_status='Resolved',
                action='事件已解决',
                comments='事件问题已解决'
            )
            db.session.add(resolved_log)
        
        # 然后关闭
        incident.status = 'Closed'
        incident.closed_at = datetime.utcnow()
        
        # 记录关闭状态日志
        close_reason = data.get('close_reason', 'Incident closed')
        close_log = IncidentStatusLog(
            incident_id=incident_id,
            user_id=current_user.id,
            old_status='Resolved',
            new_status='Closed',
            action='事件已关闭',
            comments=f'关闭原因: {close_reason}'
        )
        db.session.add(close_log)
        
        # 添加关闭评论
        comment = IncidentComment(
            incident_id=incident_id,
            user_id=current_user.id,
            content=f'Incident closed. Reason: {close_reason}',
            is_private=False
        )
        db.session.add(comment)
        
        db.session.commit()
        
        logger.info(f'Incident {incident_id} closed by {current_user.username}')
        
        return jsonify({
            'message': 'Incident closed successfully',
            'incident': incident.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Incident closure error: {str(e)}')
        return jsonify({'error': 'Incident closure failed'}), 500



@api_v1.route('/incidents/<int:incident_id>/reopen', methods=['POST'])
@permission_required('incident:write')
def reopen_incident(incident_id):
    """重新打开事件"""
    incident = Incident.query.get_or_404(incident_id)
    data = request.get_json()
    current_user = get_current_user()
    
    if incident.status not in ['Resolved', 'Closed']:
        return jsonify({'error': 'Only resolved or closed incidents can be reopened'}), 400
    
    reopen_reason = data.get('reopen_reason')
    if not reopen_reason:
        return jsonify({'error': 'Reopen reason is required'}), 400
    
    try:
        old_status = incident.status
        incident.status = 'Reopened'
        incident.resolved_at = None
        incident.closed_at = None
        
        # 记录重新打开状态日志
        reopen_log = IncidentStatusLog(
            incident_id=incident_id,
            user_id=current_user.id,
            old_status=old_status,
            new_status='Reopened',
            action='事件重新打开',
            comments=f'重新打开原因: {reopen_reason}'
        )
        db.session.add(reopen_log)
        
        # 添加重新打开评论
        comment = IncidentComment(
            incident_id=incident_id,
            user_id=current_user.id,
            content=f'Incident reopened. Reason: {reopen_reason}',
            is_private=False
        )
        db.session.add(comment)
        
        db.session.commit()
        
        logger.info(f'Incident {incident_id} reopened by {current_user.username}')
        
        return jsonify({
            'message': 'Incident reopened successfully',
            'incident': incident.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Incident reopen error: {str(e)}')
        return jsonify({'error': 'Incident reopen failed'}), 500

def _is_valid_status_transition(from_status, to_status):
    """检查状态流转是否有效"""
    valid_transitions = {
        'New': ['In Progress', 'On Hold', 'Resolved', 'Closed'],
        'In Progress': ['On Hold', 'Resolved', 'Closed'],
        'On Hold': ['In Progress', 'Resolved', 'Closed'],
        'Resolved': ['Closed', 'Reopened'],
        'Closed': ['Reopened'],
        'Reopened': ['In Progress', 'On Hold', 'Resolved', 'Closed']
    }
    
    return to_status in valid_transitions.get(from_status, [])

def can_assign_incident(user, incident):
    """检查用户是否可以分配事件"""
    # TODO: 实现权限检查逻辑
    return True

def can_close_incident(user, incident):
    """检查用户是否可以关闭事件"""
    # TODO: 实现权限检查逻辑
    return True
