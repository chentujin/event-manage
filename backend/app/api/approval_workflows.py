from flask import request, jsonify
from app.api import api_v1
from app import db
from app.models import ApprovalWorkflow, ApprovalStep, User, Role, Group
from app.utils.auth import permission_required, get_current_user
import logging

logger = logging.getLogger(__name__)

@api_v1.route('/approval-workflows', methods=['GET'])
@permission_required('approval:read')
def get_approval_workflows():
    """获取审批流程列表"""
    try:
        workflows = ApprovalWorkflow.query.all()
        return jsonify({
            'workflows': [workflow.to_dict() for workflow in workflows]
        }), 200
    except Exception as e:
        logger.error(f"获取审批流程列表失败: {str(e)}")
        return jsonify({'error': '获取审批流程列表失败'}), 500

@api_v1.route('/approval-workflows', methods=['POST'])
@permission_required('approval:write')
def create_approval_workflow():
    """创建审批流程"""
    try:
        data = request.get_json()
        current_user = get_current_user()
        
        # 检查流程名称是否已存在
        if ApprovalWorkflow.query.filter_by(name=data['name']).first():
            return jsonify({'error': '流程名称已存在'}), 400
        
        workflow = ApprovalWorkflow(
            name=data['name'],
            description=data.get('description'),
            is_active=data.get('is_active', True),
            created_by_id=current_user.id
        )
        
        db.session.add(workflow)
        db.session.flush()  # 获取workflow的ID
        
        # 创建审批步骤
        if 'steps' in data and data['steps']:
            for step_data in data['steps']:
                step = ApprovalStep(
                    workflow_id=workflow.id,
                    step_number=step_data['step_number'],
                    approval_type=step_data['approval_type'],
                    approved_by_id=step_data.get('approved_by_id'),
                    approved_by_role_id=step_data.get('approved_by_role_id'),
                    approved_by_group_id=step_data.get('approved_by_group_id')
                )
                db.session.add(step)
        
        db.session.commit()
        
        logger.info(f'Approval workflow created: {workflow.name} by {current_user.username}')
        
        return jsonify({
            'message': '审批流程创建成功',
            'workflow': workflow.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"创建审批流程失败: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '创建审批流程失败'}), 500

@api_v1.route('/approval-workflows/<int:workflow_id>', methods=['PUT'])
@permission_required('approval:write')
def update_approval_workflow(workflow_id):
    """更新审批流程"""
    try:
        workflow = ApprovalWorkflow.query.get_or_404(workflow_id)
        data = request.get_json()
        current_user = get_current_user()
        
        # 检查流程名称是否已被其他流程使用
        if 'name' in data and data['name'] != workflow.name:
            if ApprovalWorkflow.query.filter_by(name=data['name']).first():
                return jsonify({'error': '流程名称已存在'}), 400
        
        workflow.name = data.get('name', workflow.name)
        workflow.description = data.get('description', workflow.description)
        workflow.is_active = data.get('is_active', workflow.is_active)
        
        # 更新审批步骤
        if 'steps' in data:
            # 删除现有步骤
            ApprovalStep.query.filter_by(workflow_id=workflow.id).delete()
            
            # 创建新步骤
            for step_data in data['steps']:
                step = ApprovalStep(
                    workflow_id=workflow.id,
                    step_number=step_data['step_number'],
                    approval_type=step_data['approval_type'],
                    approved_by_id=step_data.get('approved_by_id'),
                    approved_by_role_id=step_data.get('approved_by_role_id'),
                    approved_by_group_id=step_data.get('approved_by_group_id')
                )
                db.session.add(step)
        
        db.session.commit()
        
        logger.info(f'Approval workflow updated: {workflow.name} by {current_user.username}')
        
        return jsonify({
            'message': '审批流程更新成功',
            'workflow': workflow.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"更新审批流程失败: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '更新审批流程失败'}), 500

@api_v1.route('/approval-workflows/<int:workflow_id>', methods=['DELETE'])
@permission_required('approval:write')
def delete_approval_workflow(workflow_id):
    """删除审批流程"""
    try:
        workflow = ApprovalWorkflow.query.get_or_404(workflow_id)
        current_user = get_current_user()
        
        # 删除相关的审批步骤
        ApprovalStep.query.filter_by(workflow_id=workflow.id).delete()
        
        db.session.delete(workflow)
        db.session.commit()
        
        logger.info(f'Approval workflow deleted: {workflow.name} by {current_user.username}')
        
        return jsonify({'message': '审批流程删除成功'}), 200
        
    except Exception as e:
        logger.error(f"删除审批流程失败: {str(e)}")
        db.session.rollback()
        return jsonify({'error': '删除审批流程失败'}), 500

@api_v1.route('/approval-workflows/<int:workflow_id>', methods=['GET'])
@permission_required('approval:read')
def get_approval_workflow(workflow_id):
    """获取审批流程详情"""
    try:
        workflow = ApprovalWorkflow.query.get_or_404(workflow_id)
        return jsonify({
            'workflow': workflow.to_dict()
        }), 200
    except Exception as e:
        logger.error(f"获取审批流程详情失败: {str(e)}")
        return jsonify({'error': '获取审批流程详情失败'}), 500