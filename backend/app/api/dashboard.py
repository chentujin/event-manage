# -*- coding: utf-8 -*-
from flask import jsonify
from app.api import api_v1
from app import db
from app.models import Problem, Service, User, Incident
from app.utils.auth import permission_required
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

@api_v1.route('/dashboard', methods=['GET'])
@permission_required('dashboard:read')
def get_dashboard():
    """获取仪表盘数据"""
    try:
        # 获取基础统计信息
        total_users = User.query.filter_by(is_active=True).count()
        total_services = Service.query.filter_by(is_active=True).count()
        total_problems = Problem.query.count()
        total_incidents = Incident.query.count()
        
        # 获取问题状态分布
        problem_status_stats = db.session.query(
            Problem.status, func.count(Problem.id)
        ).group_by(Problem.status).all()
        
        # 获取事件状态分布
        incident_status_stats = db.session.query(
            Incident.status, func.count(Incident.id)
        ).group_by(Incident.status).all()
        
        return jsonify({
            'overview': {
                'total_users': total_users,
                'total_services': total_services,
                'total_problems': total_problems,
                'total_incidents': total_incidents
            },
            'problem_status_distribution': dict(problem_status_stats),
            'incident_status_distribution': dict(incident_status_stats)
        })
    except Exception as e:
        logger.error(f"获取仪表盘数据失败: {e}")
        return jsonify({'error': '获取仪表盘数据失败'}), 500

@api_v1.route('/dashboard/overview', methods=['GET'])
@permission_required('dashboard:read')
def get_overview():
    """获取仪表盘概览数据"""
    try:
        # 获取基础统计信息
        total_users = User.query.filter_by(is_active=True).count()
        total_services = Service.query.filter_by(is_active=True).count()
        total_problems = Problem.query.count()
        total_incidents = Incident.query.count()
        
        return jsonify({
            'total_users': total_users,
            'total_services': total_services,
            'total_problems': total_problems,
            'total_incidents': total_incidents
        })
    except Exception as e:
        logger.error(f"获取仪表盘概览失败: {e}")
        return jsonify({'error': '获取仪表盘概览失败'}), 500

@api_v1.route('/dashboard/recent-incidents', methods=['GET'])
@permission_required('incident:read')
def get_recent_incidents():
    """获取最近的事件"""
    try:
        # 获取最近的事件
        recent_incidents = Incident.query.order_by(
            Incident.created_at.desc()
        ).limit(10).all()
        
        return jsonify({
            'recent_incidents': [incident.to_dict() for incident in recent_incidents]
        })
    except Exception as e:
        logger.error(f"获取最近事件失败: {e}")
        return jsonify({'error': '获取最近事件失败'}), 500

@api_v1.route('/dashboard/event-status-distribution', methods=['GET'])
@permission_required('dashboard:read')
def get_event_status_distribution():
    """获取事件状态分布数据"""
    try:
        # 获取事件状态分布
        incident_status_stats = db.session.query(
            Incident.status, func.count(Incident.id)
        ).group_by(Incident.status).all()
        
        return jsonify({
            'incident_status_distribution': dict(incident_status_stats)
        })
    except Exception as e:
        logger.error(f"获取事件状态分布失败: {e}")
        return jsonify({'error': '获取事件状态分布失败'}), 500
