from flask import request, jsonify
from app.api import api_v1
from app import db
from app.models import Approval, ApprovalWorkflow, ApprovalStep
from app.utils.auth import permission_required, get_current_user
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@api_v1.route('/approvals', methods=['GET'])
@permission_required('problem:read')
def get_approvals():
    """获取审批列表"""
    approvals = Approval.query.order_by(Approval.created_at.desc()).all()
    return jsonify({
        'approvals': [approval.to_dict() for approval in approvals]
    }), 200

@api_v1.route('/approvals/<int:approval_id>', methods=['GET'])
@permission_required('problem:read')
def get_approval(approval_id):
    """获取审批详情"""
    approval = Approval.query.get_or_404(approval_id)
    current_user = get_current_user()
    
    # 权限检查：只有相关人员可以查看
    if not _can_access_approval(current_user, approval):
        return jsonify({'error': 'Permission denied'}), 403
    
    return jsonify({'approval': approval.to_dict()}), 200

@api_v1.route('/approvals/<int:approval_id>/approve', methods=['POST'])
def approve_approval(approval_id):
    """批准审批"""
    approval = Approval.query.get_or_404(approval_id)
    data = request.get_json()
    current_user = get_current_user()
    
    if approval.status != 'PENDING':
        return jsonify({'error': 'Approval is not pending'}), 400
    
    if not approval.is_user_current_approver(current_user):
        return jsonify({'error': 'You are not authorized to approve this step'}), 403
    
    comments = data.get('comments', '')
    
    try:
        approval.approve_step(current_user, comments)
        
        # 如果所有步骤都已批准，更新关联的故障状态
        if approval.status == 'APPROVED':
            problem = approval.problem
            if problem:
                problem.status = 'Closed'
                problem.current_approval_id = None
                problem.closed_at = datetime.utcnow()
        
        logger.info(f'Approval {approval_id} step approved by {current_user.username}')
        
        # TODO: 通知下一步审批人或申请人
        
        return jsonify({
            'message': 'Approval step approved successfully',
            'approval': approval.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        logger.error(f'Approval error: {str(e)}')
        return jsonify({'error': 'Approval failed'}), 500

@api_v1.route('/approvals/<int:approval_id>/reject', methods=['POST'])
def reject_approval(approval_id):
    """拒绝审批"""
    approval = Approval.query.get_or_404(approval_id)
    data = request.get_json()
    current_user = get_current_user()
    
    if approval.status != 'PENDING':
        return jsonify({'error': 'Approval is not pending'}), 400
    
    if not approval.is_user_current_approver(current_user):
        return jsonify({'error': 'You are not authorized to reject this step'}), 403
    
    comments = data.get('comments', '')
    if not comments:
        return jsonify({'error': 'Comments are required when rejecting'}), 400
    
    try:
        approval.reject(current_user, comments)
        
        # 更新关联的故障状态
        problem = approval.problem
        if problem:
            problem.status = 'Investigating'
            problem.current_approval_id = None
        
        logger.info(f'Approval {approval_id} rejected by {current_user.username}')
        
        # TODO: 通知申请人
        
        return jsonify({
            'message': 'Approval rejected successfully',
            'approval': approval.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 403
    except Exception as e:
        logger.error(f'Approval rejection error: {str(e)}')
        return jsonify({'error': 'Approval rejection failed'}), 500

@api_v1.route('/my-approvals', methods=['GET'])
@permission_required('problem:read')
def get_my_pending_approvals():
    """获取当前用户的待审批列表"""
    current_user = get_current_user()
    
    # 查找当前用户作为审批人的待审批项目
    pending_approvals = []
    
    # 获取所有待审批的项目
    all_pending = Approval.query.filter(Approval.status == 'PENDING').all()
    
    for approval in all_pending:
        if approval.is_user_current_approver(current_user):
            pending_approvals.append(approval)
    
    return jsonify({
        'pending_approvals': [approval.to_dict() for approval in pending_approvals]
    }), 200

@api_v1.route('/approvals/workflows', methods=['GET'])
@permission_required('approval:read')
def get_approvals_workflows():
    """获取审批流程列表（兼容前端路由）"""
    try:
        workflows = ApprovalWorkflow.query.filter(
            ApprovalWorkflow.is_active == True
        ).all()
        
        return jsonify({
            'workflows': [workflow.to_dict() for workflow in workflows]
        })
    except Exception as e:
        logger.error(f"获取审批流程失败: {e}")
        return jsonify({'error': '获取审批流程失败'}), 500

@api_v1.route('/approval-workflows', methods=['GET'])
@permission_required('approval:admin')
def get_approval_workflows():
    """获取审批流程列表"""
    workflows = ApprovalWorkflow.query.filter(
        ApprovalWorkflow.is_active == True
    ).all()
    
    return jsonify({
        'workflows': [workflow.to_dict() for workflow in workflows]
    }), 200

@api_v1.route('/approval-workflows', methods=['POST'])
@permission_required('approval:admin')
def create_approval_workflow():
    """创建审批流程"""
    data = request.get_json()
    current_user = get_current_user()
    
    if not data.get('name'):
        return jsonify({'error': 'Workflow name is required'}), 400
    
    if not data.get('steps') or len(data['steps']) == 0:
        return jsonify({'error': 'At least one approval step is required'}), 400
    
    try:
        workflow = ApprovalWorkflow(
            name=data['name'],
            description=data.get('description', ''),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(workflow)
        db.session.flush()  # 获取workflow.id
        
        # 创建审批步骤
        for i, step_data in enumerate(data['steps'], 1):
            step = ApprovalStep(
                workflow_id=workflow.id,
                step_number=i,
                approval_type=step_data['approval_type']
            )
            
            # 设置审批人
            if step_data['approval_type'] == 'USER':
                step.approved_by_id = step_data.get('approved_by_id')
            elif step_data['approval_type'] == 'ROLE':
                step.approved_by_role_id = step_data.get('approved_by_role_id')
            elif step_data['approval_type'] == 'GROUP_MANAGER':
                step.approved_by_group_id = step_data.get('approved_by_group_id')
            
            db.session.add(step)
        
        db.session.commit()
        
        logger.info(f'Approval workflow created: {workflow.name} by {current_user.username}')
        
        return jsonify({
            'message': 'Approval workflow created successfully',
            'workflow': workflow.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Workflow creation error: {str(e)}')
        return jsonify({'error': 'Workflow creation failed'}), 500

@api_v1.route('/approval-workflows/<int:workflow_id>', methods=['PUT'])
@permission_required('approval:admin')
def update_approval_workflow(workflow_id):
    """更新审批流程"""
    workflow = ApprovalWorkflow.query.get_or_404(workflow_id)
    data = request.get_json()
    current_user = get_current_user()
    
    try:
        # 更新基本信息
        if 'name' in data:
            workflow.name = data['name']
        if 'description' in data:
            workflow.description = data['description']
        if 'is_active' in data:
            workflow.is_active = data['is_active']
        
        # 如果提供了新的步骤，重新创建所有步骤
        if 'steps' in data:
            # 删除现有步骤
            ApprovalStep.query.filter_by(workflow_id=workflow_id).delete()
            
            # 创建新步骤
            for i, step_data in enumerate(data['steps'], 1):
                step = ApprovalStep(
                    workflow_id=workflow_id,
                    step_number=i,
                    approval_type=step_data['approval_type']
                )
                
                if step_data['approval_type'] == 'USER':
                    step.approved_by_id = step_data.get('approved_by_id')
                elif step_data['approval_type'] == 'ROLE':
                    step.approved_by_role_id = step_data.get('approved_by_role_id')
                elif step_data['approval_type'] == 'GROUP_MANAGER':
                    step.approved_by_group_id = step_data.get('approved_by_group_id')
                
                db.session.add(step)
        
        db.session.commit()
        
        logger.info(f'Approval workflow updated: {workflow.name} by {current_user.username}')
        
        return jsonify({
            'message': 'Approval workflow updated successfully',
            'workflow': workflow.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Workflow update error: {str(e)}')
        return jsonify({'error': 'Workflow update failed'}), 500

@api_v1.route('/approval-workflows/<int:workflow_id>', methods=['DELETE'])
@permission_required('approval:admin')
def delete_approval_workflow(workflow_id):
    """删除审批流程（软删除）"""
    workflow = ApprovalWorkflow.query.get_or_404(workflow_id)
    current_user = get_current_user()
    
    # 检查是否有正在进行的审批
    active_approvals = Approval.query.filter(
        Approval.workflow_id == workflow_id,
        Approval.status == 'PENDING'
    ).count()
    
    if active_approvals > 0:
        return jsonify({
            'error': 'Cannot delete workflow with active approvals',
            'active_approvals_count': active_approvals
        }), 400
    
    try:
        workflow.is_active = False
        db.session.commit()
        
        logger.info(f'Approval workflow deleted: {workflow.name} by {current_user.username}')
        
        return jsonify({'message': 'Approval workflow deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'Workflow deletion error: {str(e)}')
        return jsonify({'error': 'Workflow deletion failed'}), 500

def _can_access_approval(user, approval):
    """检查用户是否可以访问审批"""
    # 管理员可以访问所有审批
    if user.has_permission('system:admin'):
        return True
    
    # 申请人可以访问自己的审批
    if approval.requester_id == user.id:
        return True
    
    # 当前步骤的审批人可以访问
    if approval.is_user_current_approver(user):
        return True
    
    # 已经参与过审批的用户可以访问
    for log in approval.logs:
        if log.approver_id == user.id:
            return True
    
    return False
