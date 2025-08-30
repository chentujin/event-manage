from flask import request, jsonify
from app.api import api_v1
from app import db
from app.models import Problem, ProblemStatusLog
from app.utils.auth import permission_required, get_current_user
import logging

logger = logging.getLogger(__name__)

@api_v1.route('/problems', methods=['GET'])
@permission_required('problem:read')
def get_problems():
    """获取故障列表"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    # 筛选参数
    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    
    # 构建查询
    query = Problem.query
    
    # 应用筛选条件
    if status_filter:
        query = query.filter(Problem.status == status_filter)
    
    if priority_filter:
        query = query.filter(Problem.priority == priority_filter)
    
    # 排序和分页
    pagination = query.order_by(Problem.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'problems': [problem.to_dict() for problem in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200

@api_v1.route('/problems', methods=['POST'])
@permission_required('problem:write')
def create_problem():
    """创建故障"""
    data = request.get_json()
    current_user = get_current_user()
    
    required_fields = ['title', 'description']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    try:
        problem = Problem(
            title=data['title'],
            description=data['description'],
            priority=data.get('priority', 'Medium')
        )
        
        db.session.add(problem)
        db.session.flush()  # 获取problem.id
        
        # 记录初始状态日志
        initial_log = ProblemStatusLog(
            problem_id=problem.id,
            user_id=current_user.id,
            old_status=None,
            new_status='New',
            action='故障创建',
            comments=f'创建新故障'
        )
        db.session.add(initial_log)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Problem created successfully',
            'problem': problem.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Problem creation error: {str(e)}')
        return jsonify({'error': 'Problem creation failed'}), 500

@api_v1.route('/problems/<int:problem_id>', methods=['GET'])
@permission_required('problem:read')
def get_problem(problem_id):
    """获取故障详情"""
    problem = Problem.query.get_or_404(problem_id)
    return jsonify({
        'problem': problem.to_dict()
    }), 200

@api_v1.route('/problems/<int:problem_id>/logs', methods=['GET'])
@permission_required('problem:read')
def get_problem_logs(problem_id):
    """获取故障状态变更日志"""
    problem = Problem.query.get_or_404(problem_id)
    
    # 获取状态变更日志
    status_logs = ProblemStatusLog.query.filter_by(
        problem_id=problem_id
    ).order_by(ProblemStatusLog.created_at.asc()).all()
    
    return jsonify({
        'logs': [log.to_dict() for log in status_logs]
    }), 200

@api_v1.route('/problems/<int:problem_id>', methods=['PUT'])
@permission_required('problem:write')
def update_problem(problem_id):
    """更新故障"""
    problem = Problem.query.get_or_404(problem_id)
    data = request.get_json()
    current_user = get_current_user()
    
    try:
        # 记录状态变更
        old_status = problem.status
        
        # 更新允许的字段
        allowed_fields = ['title', 'description', 'priority', 'root_cause_analysis', 'solution', 'status']
        for field in allowed_fields:
            if field in data:
                setattr(problem, field, data[field])
        
        # 记录状态变更日志
        if 'status' in data and old_status != data['status']:
            status_log = ProblemStatusLog(
                problem_id=problem.id,
                user_id=current_user.id,
                old_status=old_status,
                new_status=data['status'],
                action=f'状态更新为: {data["status"]}',
                comments=data.get('comments', '')
            )
            db.session.add(status_log)
        
        db.session.commit()
        
        logger.info(f'Problem updated: {problem.title} by {current_user.username}')
        
        return jsonify({
            'message': 'Problem updated successfully',
            'problem': problem.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Problem update error: {str(e)}')
        return jsonify({'error': 'Problem update failed'}), 500
