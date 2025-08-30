from flask import request, jsonify
from app.api import api_v1
from app import db
from app.models import Service
from app.utils.auth import permission_required
import logging

logger = logging.getLogger(__name__)

@api_v1.route('/services', methods=['GET'])
def get_services():
    """获取服务列表"""
    # 检查是否有分页参数，如果有则使用分页模式
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', type=int)
    
    if page is not None:
        # 分页模式，支持筛选
        per_page = min(per_page or 20, 100)
        
        # 筛选参数
        name_filter = request.args.get('name')
        is_active_filter = request.args.get('is_active')
        owner_team_filter = request.args.get('owner_team')
        
        # 构建查询
        query = Service.query
        
        # 应用筛选条件
        if name_filter:
            query = query.filter(Service.name.contains(name_filter))
        
        if is_active_filter is not None:
            # 处理布尔值筛选
            if is_active_filter.lower() in ['true', '1']:
                query = query.filter(Service.is_active == True)
            elif is_active_filter.lower() in ['false', '0']:
                query = query.filter(Service.is_active == False)
        
        if owner_team_filter:
            query = query.filter(Service.owner_team.contains(owner_team_filter))
        
        # 排序和分页
        pagination = query.order_by(Service.id.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'services': [service.to_dict() for service in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }), 200
    else:
        # 非分页模式，保持原有的逻辑（只返回活跃的服务）
        services = Service.query.filter(Service.is_active == True).all()
        return jsonify({
            'services': [service.to_dict() for service in services]
        }), 200

@api_v1.route('/services/<int:service_id>', methods=['GET'])
def get_service(service_id):
    """获取服务详情"""
    service = Service.query.get_or_404(service_id)
    return jsonify({'service': service.to_dict()}), 200

@api_v1.route('/services', methods=['POST'])
@permission_required('system:admin')
def create_service():
    """创建服务"""
    data = request.get_json()
    
    # 验证必填字段
    if not data.get('name'):
        return jsonify({'error': 'Service name is required'}), 400
    
    # 检查服务名是否已存在
    if Service.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Service name already exists'}), 400
    
    try:
        service = Service(
            name=data['name'],
            description=data.get('description', ''),
            owner_team=data.get('owner_team', ''),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(service)
        db.session.commit()
        
        logger.info(f'Service created: {service.name}')
        
        return jsonify({
            'message': 'Service created successfully',
            'service': service.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Service creation error: {str(e)}')
        return jsonify({'error': 'Service creation failed'}), 500

@api_v1.route('/services/<int:service_id>', methods=['PUT'])
@permission_required('system:admin')
def update_service(service_id):
    """更新服务信息"""
    service = Service.query.get_or_404(service_id)
    data = request.get_json()
    
    try:
        # 检查服务名是否重复
        if 'name' in data and data['name'] != service.name:
            if Service.query.filter_by(name=data['name']).first():
                return jsonify({'error': 'Service name already exists'}), 400
        
        # 更新字段
        allowed_fields = ['name', 'description', 'owner_team', 'is_active']
        for field in allowed_fields:
            if field in data:
                setattr(service, field, data[field])
        
        db.session.commit()
        
        logger.info(f'Service updated: {service.name}')
        
        return jsonify({
            'message': 'Service updated successfully',
            'service': service.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Service update error: {str(e)}')
        return jsonify({'error': 'Service update failed'}), 500

@api_v1.route('/services/<int:service_id>', methods=['DELETE'])
@permission_required('system:admin')
def delete_service(service_id):
    """删除服务（软删除）"""
    service = Service.query.get_or_404(service_id)
    
    try:
        # 检查是否有关联的事件
        if service.incidents:
            return jsonify({
                'error': 'Cannot delete service with associated incidents',
                'incident_count': len(service.incidents)
            }), 400
        
        # 软删除：设置为非激活状态
        service.is_active = False
        db.session.commit()
        
        logger.info(f'Service deleted (deactivated): {service.name}')
        
        return jsonify({'message': 'Service deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Service deletion error: {str(e)}')
        return jsonify({'error': 'Service deletion failed'}), 500

@api_v1.route('/services/teams', methods=['GET'])
def get_service_teams():
    """获取所有服务团队列表"""
    teams = db.session.query(Service.owner_team).filter(
        Service.owner_team.isnot(None),
        Service.owner_team != '',
        Service.is_active == True
    ).distinct().all()
    
    team_list = [team[0] for team in teams if team[0]]
    
    return jsonify({'teams': sorted(team_list)}), 200
