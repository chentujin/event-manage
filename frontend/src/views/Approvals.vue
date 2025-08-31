<template>
  <div class="approvals">
    <div class="page-header">
      <h1>审批管理</h1>
      <el-button type="primary" @click="showWorkflowDialog">
        <el-icon><Plus /></el-icon>
        新建审批流程
      </el-button>
    </div>
    
    <el-tabs v-model="activeTab" class="approval-tabs">
      <el-tab-pane label="审批列表" name="approvals">
        <el-card>
          <el-table v-loading="loading" :data="approvalsList" stripe>
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column label="故障标题" min-width="200">
              <template #default="scope">
                {{ scope.row.problem?.title || '-' }}
              </template>
            </el-table-column>
            <el-table-column label="申请人" width="120">
              <template #default="scope">
                {{ scope.row.requester?.real_name || scope.row.requester?.username }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="120">
              <template #default="scope">
                <el-tag :type="getStatusType(scope.row.status)" size="small">
                  {{ getStatusText(scope.row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="160">
              <template #default="scope">
                {{ formatDate(scope.row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="scope">
                <el-button type="text" size="small" @click="viewApproval(scope.row)">查看</el-button>
                <el-button 
                  v-if="scope.row.status === 'PENDING'"
                  type="text" 
                  size="small" 
                  class="success"
                  @click="approveItem(scope.row)"
                >批准</el-button>
                <el-button 
                  v-if="scope.row.status === 'PENDING'"
                  type="text" 
                  size="small" 
                  class="danger"
                  @click="rejectItem(scope.row)"
                >拒绝</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
      
      <el-tab-pane label="审批流程" name="workflows">
        <el-card>
          <el-table v-loading="workflowLoading" :data="workflowsList" stripe>
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="name" label="流程名称" min-width="200" />
            <el-table-column prop="description" label="描述" min-width="250" />
            <el-table-column prop="is_active" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.is_active ? 'success' : 'danger'" size="small">
                  {{ scope.row.is_active ? '激活' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="scope">
                <el-button type="text" size="small" @click="editWorkflow(scope.row)">编辑</el-button>
                <el-button type="text" size="small" class="danger" @click="deleteWorkflow(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>
    
    <!-- 审批流程对话框 -->
    <el-dialog v-model="workflowDialogVisible" :title="workflowDialogTitle" width="800px">
      <el-form ref="workflowFormRef" :model="workflowForm" :rules="workflowRules" label-width="120px">
        <el-form-item label="流程名称" prop="name">
          <el-input v-model="workflowForm.name" placeholder="请输入流程名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="workflowForm.description" type="textarea" placeholder="请输入流程描述" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="workflowForm.is_active" active-text="激活" inactive-text="禁用" />
        </el-form-item>
        
        <el-divider>审批步骤配置</el-divider>
        
        <div class="approval-steps">
          <div v-for="(step, index) in workflowForm.steps" :key="index" class="step-item">
            <div class="step-header">
              <span>步骤 {{ index + 1 }}</span>
              <el-button type="text" size="small" class="danger" @click="removeStep(index)">删除</el-button>
            </div>
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="审批类型">
                  <el-select v-model="step.approval_type" placeholder="请选择">
                    <el-option label="指定用户" value="USER" />
                    <el-option label="指定角色" value="ROLE" />
                    <el-option label="组管理员" value="GROUP_MANAGER" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="16">
                <el-form-item label="审批人">
                  <el-select 
                    v-if="step.approval_type === 'USER'"
                    v-model="step.approved_by_id" 
                    placeholder="请选择用户"
                    filterable
                  >
                    <el-option 
                      v-for="user in usersList" 
                      :key="user.id" 
                      :label="user.real_name || user.username" 
                      :value="user.id" 
                    />
                  </el-select>
                  <el-select 
                    v-else-if="step.approval_type === 'ROLE'"
                    v-model="step.approved_by_role_id" 
                    placeholder="请选择角色"
                  >
                    <el-option 
                      v-for="role in rolesList" 
                      :key="role.id" 
                      :label="getRoleText(role.name)" 
                      :value="role.id" 
                    />
                  </el-select>
                  <el-select 
                    v-else-if="step.approval_type === 'GROUP_MANAGER'"
                    v-model="step.approved_by_group_id" 
                    placeholder="请选择组"
                  >
                    <el-option 
                      v-for="group in groupsList" 
                      :key="group.id" 
                      :label="group.name" 
                      :value="group.id" 
                    />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
          </div>
          
          <el-button @click="addStep" type="dashed" style="width: 100%; margin-top: 16px;">
            <el-icon><Plus /></el-icon>
            添加审批步骤
          </el-button>
        </div>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="workflowDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleWorkflowSubmit" :loading="workflowSubmitting">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import request from '@/utils/request'
import dayjs from 'dayjs'

export default {
  name: 'Approvals',
  components: { Plus },
  setup() {
    const loading = ref(false)
    const workflowLoading = ref(false)
    const workflowSubmitting = ref(false)
    const approvalsList = ref([])
    const workflowsList = ref([])
    const usersList = ref([])
    const rolesList = ref([])
    const groupsList = ref([])
    const activeTab = ref('approvals')
    const workflowDialogVisible = ref(false)
    const workflowFormRef = ref(null)
    const isEditWorkflow = ref(false)
    
    const workflowForm = reactive({
      id: null,
      name: '',
      description: '',
      is_active: true,
      steps: []
    })
    
    const workflowRules = {
      name: [
        { required: true, message: '请输入流程名称', trigger: 'blur' }
      ],
      description: [
        { required: true, message: '请输入流程描述', trigger: 'blur' }
      ]
    }
    
    const workflowDialogTitle = computed(() => {
      return isEditWorkflow.value ? '编辑审批流程' : '新建审批流程'
    })
    
    const loadApprovals = async () => {
      try {
        loading.value = true
        const data = await request.get('/approvals')
        approvalsList.value = data.approvals || []
      } catch (error) {
        ElMessage.error('获取审批列表失败')
      } finally {
        loading.value = false
      }
    }
    
    const loadWorkflows = async () => {
      try {
        workflowLoading.value = true
        const data = await request.get('/approvals/workflows')
        workflowsList.value = data.workflows || []
      } catch (error) {
        ElMessage.error('获取审批流程失败')
      } finally {
        workflowLoading.value = false
      }
    }
    
    const loadBasicData = async () => {
      try {
        const [usersData, rolesData, groupsData] = await Promise.all([
          request.get('/users'),
          request.get('/users/roles'),
          request.get('/users/groups')
        ])
        usersList.value = usersData.users || []
        rolesList.value = rolesData.roles || []
        groupsList.value = groupsData.groups || []
      } catch (error) {
        console.error('获取基础数据失败:', error)
      }
    }
    
    const showWorkflowDialog = () => {
      isEditWorkflow.value = false
      resetWorkflowForm()
      workflowDialogVisible.value = true
      loadBasicData()
    }
    
    const editWorkflow = (workflow) => {
      isEditWorkflow.value = true
      Object.assign(workflowForm, {
        id: workflow.id,
        name: workflow.name,
        description: workflow.description,
        is_active: workflow.is_active,
        steps: workflow.steps || []
      })
      workflowDialogVisible.value = true
      loadBasicData()
    }
    
    const resetWorkflowForm = () => {
      Object.assign(workflowForm, {
        id: null,
        name: '',
        description: '',
        is_active: true,
        steps: []
      })
      workflowFormRef.value?.clearValidate()
    }
    
    const addStep = () => {
      workflowForm.steps.push({
        step_number: workflowForm.steps.length + 1,
        approval_type: 'USER',
        approved_by_id: null,
        approved_by_role_id: null,
        approved_by_group_id: null
      })
    }
    
    const removeStep = (index) => {
      workflowForm.steps.splice(index, 1)
      // 重新编号
      workflowForm.steps.forEach((step, idx) => {
        step.step_number = idx + 1
      })
    }
    
    const handleWorkflowSubmit = async () => {
      try {
        const valid = await workflowFormRef.value?.validate()
        if (!valid) return
        
        if (workflowForm.steps.length === 0) {
          ElMessage.error('请至少添加一个审批步骤')
          return
        }
        
        workflowSubmitting.value = true
        
        if (isEditWorkflow.value) {
          await approvals.updateWorkflow(workflowForm.id, workflowForm)
          ElMessage.success('审批流程更新成功')
        } else {
          await approvals.createWorkflow(workflowForm)
          ElMessage.success('审批流程创建成功')
        }
        
        workflowDialogVisible.value = false
        loadWorkflows()
      } catch (error) {
        ElMessage.error('审批流程保存失败')
      } finally {
        workflowSubmitting.value = false
      }
    }
    
    const deleteWorkflow = async (workflow) => {
      try {
        await ElMessageBox.confirm(`确定要删除审批流程“${workflow.name}”吗？`, '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        await approvals.deleteWorkflow(workflow.id)
        ElMessage.success('审批流程删除成功')
        loadWorkflows()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('审批流程删除失败')
        }
      }
    }
    
    const viewApproval = (approval) => {
      ElMessage.info('查看审批详情功能开发中')
    }
    
    const approveItem = async (approval) => {
      try {
        await approvals.approve(approval.id, { comments: '已批准' })
        ElMessage.success('审批批准成功')
        loadApprovals()
      } catch (error) {
        ElMessage.error('审批批准失败')
      }
    }
    
    const rejectItem = async (approval) => {
      try {
        await approvals.reject(approval.id, { comments: '已拒绝' })
        ElMessage.success('审批拒绝成功')
        loadApprovals()
      } catch (error) {
        ElMessage.error('审批拒绝失败')
      }
    }
    
    const getStatusType = (status) => {
      const types = {
        'PENDING': 'warning',
        'APPROVED': 'success',
        'REJECTED': 'danger'
      }
      return types[status] || 'info'
    }
    
    const getStatusText = (status) => {
      const texts = {
        'PENDING': '待审批',
        'APPROVED': '已批准',
        'REJECTED': '已拒绝'
      }
      return texts[status] || status
    }
    
    const formatDate = (dateStr) => {
      return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
    }
    
    // 角色中文映射
    const getRoleText = (role) => {
      const roleMap = {
        'Admin': '超级管理员',
        'Problem Manager': '故障经理',
        'Engineer': '工程师',
        'Service Desk': '服务台',
        'Viewer': '只读用户'
      }
      return roleMap[role] || role
    }
    
    onMounted(() => {
      loadApprovals()
      loadWorkflows()
    })
    
    return {
      loading,
      workflowLoading,
      workflowSubmitting,
      approvalsList,
      workflowsList,
      usersList,
      rolesList,
      groupsList,
      activeTab,
      workflowDialogVisible,
      workflowDialogTitle,
      workflowFormRef,
      workflowForm,
      workflowRules,
      showWorkflowDialog,
      editWorkflow,
      handleWorkflowSubmit,
      deleteWorkflow,
      addStep,
      removeStep,
      viewApproval,
      approveItem,
      rejectItem,
      getStatusType,
      getStatusText,
      getRoleText,
      formatDate
    }
  }
}
</script>

<style scoped>
.approvals {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  color: #303133;
}

.approval-tabs {
  margin-bottom: 20px;
}

.approval-steps {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 16px;
  background-color: #fafafa;
}

.step-item {
  background-color: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 16px;
  margin-bottom: 16px;
}

.step-item:last-child {
  margin-bottom: 0;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-weight: bold;
  color: #303133;
}

:deep(.el-button.success) {
  color: #67c23a;
}

:deep(.el-button.danger) {
  color: #f56c6c;
}
</style>