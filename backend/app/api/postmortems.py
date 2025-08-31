from flask import request, jsonify
from app.api import api_v1
from app import db
from app.models.user import User
from app.utils.auth import permission_required, get_current_user
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@api_v1.route('/postmortems', methods=['GET'])
@permission_required('postmortem:read')
def get_postmortems():
    """获取复盘列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        
        # 查询PostMortem模型
        from app.models.incident_new import PostMortem
        
        query = PostMortem.query
        
        # 应用状态过滤
        if status:
            query = query.filter(PostMortem.status == status)
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        offset = (page - 1) * per_page
        postmortems = query.offset(offset).limit(per_page).all()
        
        # 转换为字典，包含关联数据
        postmortems_dict = []
        for pm in postmortems:
            pm_data = pm.to_dict()
            
            # 添加改进措施数量
            pm_data['action_items_count'] = len(pm.action_items) if hasattr(pm, 'action_items') else 0
            
            # 添加关联的故障信息
            if pm.incident_id:
                from app.models.incident_new import NewIncident
                incident = NewIncident.query.get(pm.incident_id)
                if incident:
                    pm_data['incident'] = {
                        'id': incident.id,
                        'incident_id': incident.incident_id,
                        'title': incident.title
                    }
            
            postmortems_dict.append(pm_data)
        
        # 计算总页数
        pages = (total + per_page - 1) // per_page
        
        return jsonify({
            'postmortems': postmortems_dict,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': pages
            }
        })
    except Exception as e:
        logger.error(f"获取复盘列表失败: {e}")
        return jsonify({'error': '获取复盘列表失败'}), 500

@api_v1.route('/postmortems/statistics', methods=['GET'])
@permission_required('postmortem:read')
def get_postmortems_statistics():
    """获取复盘统计信息"""
    try:
        from app.models.incident_new import PostMortem, ActionItem
        
        # 查询真实数据
        total_postmortems = PostMortem.query.count()
        
        # 统计不同状态的复盘数量
        pending_publish = PostMortem.query.filter(PostMortem.status.in_(['Draft', 'In Review'])).count()
        
        # 统计改进措施数量
        total_actions = ActionItem.query.count()
        completed_actions = ActionItem.query.filter(ActionItem.status == 'Completed').count()
        
        # 统计过期的改进措施（截止时间已过且未完成）
        from datetime import datetime
        overdue_action_items = ActionItem.query.filter(
            ActionItem.due_date < datetime.utcnow(),
            ActionItem.status.in_(['Open', 'In Progress'])
        ).count()
        
        return jsonify({
            'total_postmortems': total_postmortems,
            'pending_publish': pending_publish,
            'overdue_action_items': overdue_action_items,
            'total_actions': total_actions,
            'completed_actions': completed_actions
        })
    except Exception as e:
        logger.error(f"获取复盘统计失败: {e}")
        return jsonify({'error': '获取统计信息失败'}), 500

@api_v1.route('/action-items', methods=['GET'])
@permission_required('postmortem:read')
def get_action_items():
    """获取改进措施列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 获取改进措施列表
        from app.models.incident_new import ActionItem
        
        # 计算总数
        total = ActionItem.query.count()
        
        # 分页查询
        offset = (page - 1) * per_page
        action_items = ActionItem.query.offset(offset).limit(per_page).all()
        
        # 转换为字典
        action_items_dict = [item.to_dict() for item in action_items]
        
        # 计算总页数
        pages = (total + per_page - 1) // per_page
        
        return jsonify({
            'action_items': action_items_dict,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': pages
        })
    except Exception as e:
        logger.error(f"获取改进措施列表失败: {e}")
        return jsonify({'error': '获取改进措施列表失败'}), 500

@api_v1.route('/action-items', methods=['POST'])
@permission_required('postmortem:write')
def create_action_item():
    """创建改进措施"""
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        # 验证必填字段
        title = data.get('title')
        description = data.get('description')
        
        if not title:
            return jsonify({'error': '改进措施标题是必填字段'}), 400
        if not description:
            return jsonify({'error': '改进措施描述是必填字段'}), 400
        
        # 创建改进措施
        from app.models.incident_new import ActionItem
        
        # 处理日期字段
        due_date = None
        if data.get('due_date'):
            try:
                from datetime import datetime
                due_date = datetime.fromisoformat(data.get('due_date').replace('Z', '+00:00'))
            except:
                # 如果日期格式不正确，忽略该字段
                pass
        
        action_item = ActionItem(
            title=title,
            description=description,
            category=data.get('category', 'Technical'),
            priority=data.get('priority', 'Medium'),
            status=data.get('status', 'Open'),
            assignee_id=data.get('assignee_id'),
            due_date=due_date,
            external_link=data.get('external_link'),
            incident_id=data.get('incident_id')  # 设置故障ID字段
        )
        
        # 如果有故障ID，尝试创建或关联复盘
        incident_id = data.get('incident_id')
        if incident_id:
            # 检查是否已有复盘，如果没有则创建一个
            from app.models.incident_new import PostMortem
            
            existing_postmortem = PostMortem.query.filter_by(incident_id=incident_id).first()
            if not existing_postmortem:
                # 创建新的复盘记录
                postmortem = PostMortem(
                    incident_id=incident_id,
                    title=f'故障复盘 - {incident_id}',
                    status='Draft',
                    author_id=current_user.id
                )
                db.session.add(postmortem)
                db.session.flush()  # 获取postmortem.id
                action_item.postmortem_id = postmortem.id
            else:
                action_item.postmortem_id = existing_postmortem.id
        else:
            # 如果没有故障ID，检查是否有复盘ID
            postmortem_id = data.get('postmortem_id')
            if postmortem_id:
                action_item.postmortem_id = postmortem_id
            else:
                # 创建一个独立的复盘记录来关联这个改进措施
                from app.models.incident_new import PostMortem
                
                postmortem = PostMortem(
                    title='独立复盘记录',
                    status='Draft',
                    author_id=current_user.id
                )
                db.session.add(postmortem)
                db.session.flush()  # 获取postmortem.id
                action_item.postmortem_id = postmortem.id
        
        db.session.add(action_item)
        db.session.flush()  # 获取action_item.id
        
        # 记录初始状态日志
        from app.models.incident_new import ActionItemStatusLog
        initial_log = ActionItemStatusLog(
            action_item_id=action_item.id,
            user_id=current_user.id,
            old_status=None,
            new_status='Open',
            action='改进措施创建',
            comments=f'创建新改进措施: {title}'
        )
        db.session.add(initial_log)
        
        db.session.commit()
        
        return jsonify({
            'message': '改进措施创建成功',
            'action_item': action_item.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"创建改进措施失败: {e}")
        db.session.rollback()
        return jsonify({'error': '创建改进措施失败'}), 500

@api_v1.route('/postmortems/<int:postmortem_id>', methods=['GET'])
@permission_required('postmortem:read')
def get_postmortem(postmortem_id):
    """获取复盘详情"""
    try:
        # 暂时返回404，因为模型未完全实现
        return jsonify({'error': '复盘功能暂未完全实现'}), 404
    except Exception as e:
        logger.error(f"获取复盘详情失败: {e}")
        return jsonify({'error': '获取复盘详情失败'}), 500

@api_v1.route('/action-items/<int:action_item_id>', methods=['GET'])
@permission_required('postmortem:read')
def get_action_item(action_item_id):
    """获取改进措施详情"""
    try:
        from app.models.incident_new import ActionItem
        
        action_item = ActionItem.query.get_or_404(action_item_id)
        
        return jsonify({
            'action_item': action_item.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"获取改进措施详情失败: {e}")
        return jsonify({'error': '获取改进措施详情失败'}), 500

@api_v1.route('/action-items/<int:action_item_id>/logs', methods=['GET'])
@permission_required('postmortem:read')
def get_action_item_logs(action_item_id):
    """获取改进措施状态记录"""
    try:
        from app.models.incident_new import ActionItem, ActionItemStatusLog
        action_item = ActionItem.query.get_or_404(action_item_id)
        status_logs = ActionItemStatusLog.query.filter_by(
            action_item_id=action_item_id
        ).order_by(ActionItemStatusLog.created_at.asc()).all()
        return jsonify({'logs': [log.to_dict() for log in status_logs]}), 200
    except Exception as e:
        logger.error(f"获取改进措施状态记录失败: {e}")
        return jsonify({'error': '获取改进措施状态记录失败'}), 500

@api_v1.route('/action-items/<int:action_item_id>', methods=['PUT'])
@permission_required('postmortem:write')
def update_action_item(action_item_id):
    """更新改进措施"""
    try:
        from app.models.incident_new import ActionItem, ActionItemStatusLog
        current_user = get_current_user()
        
        action_item = ActionItem.query.get_or_404(action_item_id)
        data = request.get_json()
        
        # 记录原始状态用于日志
        old_status = action_item.status
        old_assignee_id = action_item.assignee_id
        old_due_date = action_item.due_date
        
        # 更新基本信息
        if 'title' in data:
            action_item.title = data['title']
        if 'description' in data:
            action_item.description = data['description']
        if 'category' in data:
            action_item.category = data['category']
        if 'priority' in data:
            action_item.priority = data['priority']
        if 'external_link' in data:
            action_item.external_link = data['external_link']
        
        # 更新状态
        if 'status' in data and data['status'] != old_status:
            action_item.status = data['status']
            
            # 记录状态变更日志
            status_log = ActionItemStatusLog(
                action_item_id=action_item.id,
                user_id=current_user.id,
                old_status=old_status,
                new_status=data['status'],
                action='状态变更',
                comments=data.get('comments', '状态已变更')
            )
            db.session.add(status_log)
        
        # 更新负责人
        if 'assignee_id' in data and data['assignee_id'] != old_assignee_id:
            action_item.assignee_id = data['assignee_id']
            
            # 记录负责人变更日志
            assignee_log = ActionItemStatusLog(
                action_item_id=action_item.id,
                user_id=current_user.id,
                old_status=old_status,
                new_status=action_item.status,
                action='分配负责人',
                comments=data.get('comments', '负责人已分配')
            )
            db.session.add(assignee_log)
        
        # 更新截止时间
        if 'due_date' in data:
            try:
                if data['due_date']:
                    action_item.due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
                else:
                    action_item.due_date = None
                    
                # 记录截止时间变更日志
                due_date_log = ActionItemStatusLog(
                    action_item_id=action_item.id,
                    user_id=current_user.id,
                    old_status=old_status,
                    new_status=action_item.status,
                    action='设置截止时间',
                    comments=data.get('comments', '截止时间已设置')
                )
                db.session.add(due_date_log)
            except Exception as e:
                logger.warning(f"日期解析失败: {e}")
        
        db.session.commit()
        
        return jsonify({
            'message': '改进措施更新成功',
            'action_item': action_item.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"更新改进措施失败: {e}")
        db.session.rollback()
        return jsonify({'error': '更新改进措施失败'}), 500

@api_v1.route('/action-items/<int:action_item_id>/status', methods=['PUT'])
@permission_required('postmortem:write')
def update_action_item_status(action_item_id):
    """更新改进措施状态"""
    try:
        from app.models.incident_new import ActionItem, ActionItemStatusLog
        current_user = get_current_user()
        
        action_item = ActionItem.query.get_or_404(action_item_id)
        data = request.get_json()
        
        old_status = action_item.status
        new_status = data.get('new_status')
        comments = data.get('comments', '')
        
        if not new_status:
            return jsonify({'error': '新状态不能为空'}), 400
        
        if new_status == old_status:
            return jsonify({'error': '新状态不能与当前状态相同'}), 400
        
        # 更新状态
        action_item.status = new_status
        
        # 记录状态变更日志
        status_log = ActionItemStatusLog(
            action_item_id=action_item.id,
            user_id=current_user.id,
            old_status=old_status,
            new_status=new_status,
            action='状态变更',
            comments=comments
        )
        db.session.add(status_log)
        
        db.session.commit()
        
        return jsonify({
            'message': '状态更新成功',
            'action_item': action_item.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"更新改进措施状态失败: {e}")
        db.session.rollback()
        return jsonify({'error': '更新改进措施状态失败'}), 500

@api_v1.route('/action-items/<int:action_item_id>/assignee', methods=['PUT'])
@permission_required('postmortem:write')
def update_action_item_assignee(action_item_id):
    """更新改进措施负责人"""
    try:
        from app.models.incident_new import ActionItem, ActionItemStatusLog
        current_user = get_current_user()
        
        action_item = ActionItem.query.get_or_404(action_item_id)
        data = request.get_json()
        
        old_assignee_id = action_item.assignee_id
        new_assignee_id = data.get('assignee_id')
        comments = data.get('comments', '')
        
        if not new_assignee_id:
            return jsonify({'error': '负责人ID不能为空'}), 400
        
        if new_assignee_id == old_assignee_id:
            return jsonify({'error': '新负责人不能与当前负责人相同'}), 400
        
        # 验证用户是否存在
        user = User.query.get(new_assignee_id)
        if not user:
            return jsonify({'error': '指定的用户不存在'}), 400
        
        # 更新负责人
        action_item.assignee_id = new_assignee_id
        
        # 记录负责人变更日志
        assignee_log = ActionItemStatusLog(
            action_item_id=action_item.id,
            user_id=current_user.id,
            old_status=action_item.status,
            new_status=action_item.status,
            action='分配负责人',
            comments=comments
        )
        db.session.add(assignee_log)
        
        db.session.commit()
        
        return jsonify({
            'message': '负责人分配成功',
            'action_item': action_item.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"分配改进措施负责人失败: {e}")
        db.session.rollback()
        return jsonify({'error': '分配负责人失败'}), 500

@api_v1.route('/action-items/<int:action_item_id>/due-date', methods=['PUT'])
@permission_required('postmortem:write')
def update_action_item_due_date(action_item_id):
    """更新改进措施截止时间"""
    try:
        from app.models.incident_new import ActionItem, ActionItemStatusLog
        current_user = get_current_user()
        
        action_item = ActionItem.query.get_or_404(action_item_id)
        data = request.get_json()
        
        old_due_date = action_item.due_date
        new_due_date = data.get('due_date')
        comments = data.get('comments', '')
        
        if not new_due_date:
            return jsonify({'error': '截止时间不能为空'}), 400
        
        try:
            parsed_due_date = datetime.fromisoformat(new_due_date.replace('Z', '+00:00'))
        except Exception as e:
            return jsonify({'error': '日期格式不正确'}), 400
        
        if old_due_date and parsed_due_date == old_due_date:
            return jsonify({'error': '新截止时间不能与当前截止时间相同'}), 400
        
        # 更新截止时间
        action_item.due_date = parsed_due_date
        
        # 记录截止时间变更日志
        due_date_log = ActionItemStatusLog(
            action_item_id=action_item.id,
            user_id=current_user.id,
            old_status=action_item.status,
            new_status=action_item.status,
            action='设置截止时间',
            comments=comments
        )
        db.session.add(due_date_log)
        
        db.session.commit()
        
        return jsonify({
            'message': '截止时间设置成功',
            'action_item': action_item.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"设置改进措施截止时间失败: {e}")
        db.session.rollback()
        return jsonify({'error': '设置截止时间失败'}), 500