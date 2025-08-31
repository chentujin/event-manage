from flask import request, jsonify
from app.api import api_v1
from app import db
from app.models.incident_new import NewIncident
from app.models.incident import Service
from app.models.user import User
from app.utils.auth import permission_required, get_current_user
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@api_v1.route('/incidents-new', methods=['GET'])
@permission_required('incident:read')
def get_new_incidents():
    """获取新事件列表"""
    try:
        logger.info("开始查询故障列表")
        
        # 暂时不使用分页，直接返回所有故障
        incidents = NewIncident.query.order_by(NewIncident.created_at.desc()).all()
        logger.info(f"查询到 {len(incidents)} 个故障")
        
        # 转换为字典
        incidents_dict = []
        for incident in incidents:
            try:
                incident_dict = incident.to_dict()
                incidents_dict.append(incident_dict)
                logger.info(f"故障 {incident.id} 转换成功")
            except Exception as e:
                logger.error(f"故障 {incident.id} 转换失败: {e}")
                continue
        
        logger.info("故障列表查询成功")
        return jsonify({
            'incidents': incidents_dict,
            'pagination': {
                'page': 1,
                'per_page': len(incidents_dict),
                'total': len(incidents_dict),
                'pages': 1
            }
        })
    except Exception as e:
        logger.error(f"获取新事件列表失败: {e}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return jsonify({'error': '获取事件列表失败'}), 500

@api_v1.route('/incidents-new/statistics', methods=['GET'])
@permission_required('incident:read')
def get_new_incidents_statistics():
    """获取新事件统计信息"""
    try:
        from datetime import datetime, date
        
        # 获取基础统计信息
        total_incidents = NewIncident.query.count()
        new_incidents = NewIncident.query.filter_by(status='Pending').count()
        in_progress = NewIncident.query.filter_by(status='Investigating').count()
        resolved = NewIncident.query.filter_by(status='Recovered').count()
        closed = NewIncident.query.filter_by(status='Closed').count()
        
        # 计算活跃故障（非关闭状态）
        active_incidents = NewIncident.query.filter(
            NewIncident.status.in_(['Pending', 'Investigating', 'Recovering', 'Recovered'])
        ).count()
        
        # 计算今日新增故障
        today = date.today()
        today_incidents = NewIncident.query.filter(
            db.func.date(NewIncident.created_at) == today
        ).count()
        
        # 计算待复盘故障（状态为Post-Mortem或需要复盘的）
        pending_postmortem = NewIncident.query.filter(
            NewIncident.status.in_(['Post-Mortem', 'Recovered'])
        ).count()
        
        # 计算P1故障数量（高严重度）
        p1_incidents = NewIncident.query.filter_by(severity='P1').count()
        
        return jsonify({
            'total_incidents': total_incidents,
            'active_incidents': active_incidents,
            'today_incidents': today_incidents,
            'pending_postmortem': pending_postmortem,
            'p1_incidents': p1_incidents,
            'new_incidents': new_incidents,
            'in_progress': in_progress,
            'resolved': resolved,
            'closed': closed
        })
    except Exception as e:
        logger.error(f"获取新事件统计失败: {e}")
        return jsonify({'error': '获取统计信息失败'}), 500

@api_v1.route('/incidents-new/<int:incident_id>', methods=['GET'])
@permission_required('incident:read')
def get_new_incident(incident_id):
    """获取新事件详情"""
    try:
        incident = NewIncident.query.get_or_404(incident_id)
        return jsonify({'incident': incident.to_dict()})
    except Exception as e:
        logger.error(f"获取新事件详情失败: {e}")
        return jsonify({'error': '获取事件详情失败'}), 500

@api_v1.route('/incidents-new', methods=['POST'])
@permission_required('incident:write')
def create_new_incident():
    """创建新事件"""
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        # 兼容前端字段名称
        title = data.get('title') or data.get('故障标题')
        description = data.get('description') or data.get('故障描述')
        severity = data.get('severity') or data.get('严重度')
        impact_scope = data.get('impact_scope') or data.get('影响范围')
        
        # 验证必填字段
        if not title:
            return jsonify({'error': '故障标题是必填字段'}), 400
        if not description:
            return jsonify({'error': '故障描述是必填字段'}), 400
        if not severity:
            return jsonify({'error': '严重度是必填字段'}), 400
        
        # 验证严重度值
        if severity not in ['P1', 'P2', 'P3', 'P4']:
            return jsonify({'error': '无效的严重度值，请选择P1、P2、P3或P4'}), 400
        
        # 创建事件
        incident = NewIncident(
            title=title,
            description=description,
            severity=severity,
            impact_scope=impact_scope,
            assignee_id=data.get('assignee_id') or current_user.id,
            reporter_id=current_user.id,
            status='Pending'
        )
        
        db.session.add(incident)
        db.session.commit()
        
        return jsonify(incident.to_dict()), 201
        
    except Exception as e:
        logger.error(f"创建新事件失败: {e}")
        db.session.rollback()
        return jsonify({'error': '创建事件失败'}), 500

@api_v1.route('/incidents-new/<int:incident_id>/status', methods=['PUT'])
@permission_required('incident:write')
def update_incident_status(incident_id):
    """更新故障状态"""
    try:
        data = request.get_json()
        new_status = data.get('status')
        comments = data.get('comments', '')
        
        if not new_status:
            return jsonify({'error': '状态是必填字段'}), 400
        
        # 验证状态值
        valid_statuses = ['Pending', 'Investigating', 'Recovering', 'Recovered', 'Post-Mortem', 'Closed']
        if new_status not in valid_statuses:
            return jsonify({'error': '无效的状态值'}), 400
        
        incident = NewIncident.query.get_or_404(incident_id)
        old_status = incident.status
        current_user = get_current_user()
        
        # 更新状态
        incident.status = new_status
        
        # 根据状态更新时间字段
        if new_status == 'Pending':
            incident.acknowledged_at = datetime.utcnow()
        elif new_status == 'Recovered':
            incident.recovered_at = datetime.utcnow()
        elif new_status == 'Closed':
            incident.closed_at = datetime.utcnow()
        
        # 自动创建时间线记录
        from app.models.incident_new import IncidentTimeline
        
        timeline_entry = IncidentTimeline(
            incident_id=incident_id,
            user_id=current_user.id,
            entry_type='status_change',
            title=f'状态变更: {old_status} → {new_status}',
            description=comments or f'故障状态从 {old_status} 变更为 {new_status}',
            timestamp=datetime.utcnow()
        )
        
        db.session.add(timeline_entry)
        db.session.commit()
        
        return jsonify({
            'message': '故障状态更新成功',
            'incident': incident.to_dict()
        })
        
    except Exception as e:
        logger.error(f"更新故障状态失败: {e}")
        db.session.rollback()
        return jsonify({'error': '状态更新失败'}), 500

@api_v1.route('/incidents-new/<int:incident_id>/progress', methods=['POST'])
@permission_required('incident:write')
def add_incident_progress(incident_id):
    """添加故障处理进展"""
    try:
        data = request.get_json()
        title = data.get('title')
        description = data.get('description')
        
        if not title or not description:
            return jsonify({'error': '进展标题和详情是必填字段'}), 400
        
        incident = NewIncident.query.get_or_404(incident_id)
        current_user = get_current_user()
        
        # 创建时间线条目
        from app.models.incident_new import IncidentTimeline
        
        timeline_entry = IncidentTimeline(
            incident_id=incident_id,
            user_id=current_user.id,
            entry_type='action',
            title=title,
            description=description,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(timeline_entry)
        db.session.commit()
        
        return jsonify({
            'message': '进展记录添加成功',
            'timeline_entry': timeline_entry.to_dict()
        })
        
    except Exception as e:
        logger.error(f"添加故障进展记录失败: {e}")
        db.session.rollback()
        return jsonify({'error': '添加进展记录失败'}), 500

@api_v1.route('/incidents-new/<int:incident_id>/timeline', methods=['GET'])
@permission_required('incident:read')
def get_incident_timeline(incident_id):
    """获取故障处理时间线"""
    try:
        incident = NewIncident.query.get_or_404(incident_id)
        
        # 获取时间线记录
        timeline_entries = []
        if incident.timeline_entries:
            timeline_entries = [entry.to_dict() for entry in incident.timeline_entries]
        
        return jsonify({
            'timeline': timeline_entries,
            'incident_id': incident_id
        })
        
    except Exception as e:
        logger.error(f"获取故障时间线失败: {e}")
        return jsonify({'error': '获取时间线失败'}), 500