# -*- coding: utf-8 -*-
from flask import jsonify
from app.api import api_v1
from app import db
from app.models import Incident, Problem, Service, User
from app.utils.auth import permission_required
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

@api_v1.route('/dashboard/overview', methods=['GET'])
@permission_required('dashboard:read')
def get_overview():
    """获取仪表盘概览数据"""
    try:
        # 事件统计
        total_incidents = Incident.query.count()
        open_incidents = Incident.query.filter(
            Incident.status.in_(['New', 'In Progress', 'On Hold', 'Reopened'])
        ).count()
        
        # 故障统计
        total_problems = Problem.query.count()
        open_problems = Problem.query.filter(
            Problem.status.in_(['New', 'Investigating', 'Known Error'])
        ).count()
        
        # 服务统计
        total_services = Service.query.filter(Service.is_active == True).count()
        
        # 用户统计
        total_users = User.query.filter(User.is_active == True).count()
        
        # 按优先级统计事件
        try:
            incident_by_priority = db.session.query(
                Incident.priority,
                func.count(Incident.id).label('count')
            ).filter(
                Incident.status.in_(['New', 'In Progress', 'On Hold', 'Reopened'])
            ).group_by(Incident.priority).all()
            
            priority_stats = {priority: count for priority, count in incident_by_priority}
        except Exception as e:
            logger.error(f'Priority stats error: {str(e)}')
            priority_stats = {}
        
        return jsonify({
            'incidents': {
                'total': total_incidents,
                'open': open_incidents,
                'by_priority': priority_stats
            },
            'problems': {
                'total': total_problems,
                'open': open_problems
            },
            'services': {
                'total': total_services
            },
            'users': {
                'total': total_users
            }
        }), 200
        
    except Exception as e:
        logger.error(f'Dashboard overview error: {str(e)}')
        return jsonify({'error': 'Failed to get overview data'}), 500

@api_v1.route('/dashboard/recent-incidents', methods=['GET'])
@permission_required('incident:read')
def get_recent_incidents():
    """获取最近的事件"""
    try:
        recent_incidents = Incident.query.order_by(
            Incident.created_at.desc()
        ).limit(10).all()
        
        return jsonify({
            'incidents': [incident.to_dict() for incident in recent_incidents]
        }), 200
        
    except Exception as e:
        logger.error(f'Recent incidents error: {str(e)}')
        return jsonify({'error': 'Failed to get recent incidents'}), 500

@api_v1.route('/dashboard/event-status-distribution', methods=['GET'])
@permission_required('dashboard:read')
def get_event_status_distribution():
    """获取事件状态分布数据"""
    try:
        # 事件状态分布
        incident_status_stats = db.session.query(
            Incident.status,
            func.count(Incident.id).label('count')
        ).group_by(Incident.status).all()
        
        # 故障状态分布
        problem_status_stats = db.session.query(
            Problem.status,
            func.count(Problem.id).label('count')
        ).group_by(Problem.status).all()
        
        # 转换为前端友好的格式
        incident_distribution = []
        status_colors = {
            'New': '#f56c6c',
            'In Progress': '#e6a23c', 
            'On Hold': '#909399',
            'Resolved': '#67c23a',
            'Closed': '#409eff',
            'Reopened': '#f56c6c'
        }
        
        for status, count in incident_status_stats:
            incident_distribution.append({
                'name': status,
                'value': count,
                'color': status_colors.get(status, '#909399')
            })
        
        problem_distribution = []
        problem_colors = {
            'New': '#f56c6c',
            'Investigating': '#e6a23c',
            'Known Error': '#909399', 
            'Resolved': '#67c23a',
            'Closed': '#409eff'
        }
        
        for status, count in problem_status_stats:
            problem_distribution.append({
                'name': status,
                'value': count,
                'color': problem_colors.get(status, '#909399')
            })
        
        return jsonify({
            'incident_distribution': incident_distribution,
            'problem_distribution': problem_distribution
        }), 200
        
    except Exception as e:
        logger.error(f'Event status distribution error: {str(e)}')
        return jsonify({'error': 'Failed to get event status distribution'}), 500