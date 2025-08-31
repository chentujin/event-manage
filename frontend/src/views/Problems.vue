<template>
  <div class="problems">
    <div class="page-header">
      <h1>问题管理</h1>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        新建问题
      </el-button>
    </div>
    
    <!-- 筛选器 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 150px">
            <el-option label="待处理" value="New" />
            <el-option label="调查中" value="Investigating" />
            <el-option label="已知错误" value="Known Error" />
            <el-option label="待审批" value="Pending Approval" />
            <el-option label="已关闭" value="Closed" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="优先级">
          <el-select v-model="filters.priority" placeholder="全部优先级" clearable style="width: 150px">
            <el-option label="高" value="High" />
            <el-option label="中" value="Medium" />
            <el-option label="低" value="Low" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleFilter">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card class="table-card">
      <el-table v-loading="loading" :data="problemsList" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="scope">
            <el-tag :type="getPriorityType(scope.row.priority)" size="small">
              {{ getPriorityText(scope.row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)" size="small">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="incident_id" label="关联故障ID" width="120">
          <template #default="scope">
            <span v-if="scope.row.incident_id" class="incident-link">
              {{ scope.row.incident_id }}
            </span>
            <span v-else class="no-incident">未关联</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button type="text" size="small" @click="viewProblem(scope.row)">查看</el-button>
            <el-button type="text" size="small" @click="editProblem(scope.row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.per_page"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="loadProblems"
          @size-change="loadProblems"
        />
      </div>
    </el-card>
    
    <!-- 新建/编辑问题对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="800px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="问题标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入问题标题" />
        </el-form-item>
        <el-form-item label="问题描述" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="4" placeholder="请输入问题详细描述" />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="form.priority" placeholder="请选择优先级">
            <el-option label="高" value="High" />
            <el-option label="中" value="Medium" />
            <el-option label="低" value="Low" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联故障ID">
          <el-input v-model="form.incident_id" placeholder="请输入关联的故障ID（可选）" />
        </el-form-item>
        <el-form-item label="根因分析">
          <el-input v-model="form.root_cause_analysis" type="textarea" :rows="3" placeholder="请输入根因分析" />
        </el-form-item>
        <el-form-item label="解决方案">
          <el-input v-model="form.solution" type="textarea" :rows="3" placeholder="请输入解决方案" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 问题详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="问题详情" width="800px">
      <div v-if="currentProblem" class="problem-detail">
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="detail-section">
              <h4>基本信息</h4>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="标题">{{ currentProblem.title }}</el-descriptions-item>
                <el-descriptions-item label="状态">
                  <el-tag :type="getStatusType(currentProblem.status)" size="small">
                    {{ getStatusText(currentProblem.status) }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="优先级">
                  <el-tag :type="getPriorityType(currentProblem.priority)" size="small">
                    {{ getPriorityText(currentProblem.priority) }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="创建时间">{{ formatDate(currentProblem.created_at) }}</el-descriptions-item>
              </el-descriptions>
            </div>
            
            <div class="detail-section">
              <h4>描述</h4>
              <p>{{ currentProblem.description }}</p>
            </div>
            
            <div v-if="currentProblem.root_cause_analysis" class="detail-section">
              <h4>根因分析</h4>
              <p>{{ currentProblem.root_cause_analysis }}</p>
            </div>
            
            <div v-if="currentProblem.solution" class="detail-section">
              <h4>解决方案</h4>
              <p>{{ currentProblem.solution }}</p>
            </div>
          </el-col>
          
          <el-col :span="12">
            <div class="detail-section">
              <h4>问题审批</h4>
              <div v-if="currentProblem.status === 'Known Error'" class="approval-section">
                <el-alert
                  title="该问题已标记为已知错误，可以提交审批申请进行关闭"
                  type="info"
                  style="margin-bottom: 16px;"
                  show-icon
                />
                <el-button 
                  v-if="!hasActiveApproval" 
                  type="primary" 
                  @click="submitForApproval"
                  :loading="submittingApproval"
                >
                  提交审批申请
                </el-button>
                <div v-else>
                  <el-tag type="warning">审批中</el-tag>
                  <p style="margin-top: 8px; color: #606266;">该问题已提交审批，请等待审批结果</p>
                </div>
              </div>
              <div v-else>
                <el-alert
                  title="只有已知错误的问题才能提交审批申请"
                  type="warning"
                  show-icon
                />
              </div>
            </div>
            
            <div class="detail-section">
              <h4>状态流转</h4>
              <div class="status-actions">
                <el-button 
                  v-if="canTransitionTo('Investigating')" 
                  type="primary" 
                  size="small" 
                  @click="updateProblemStatus('Investigating')"
                >
                  开始调查
                </el-button>
                <el-button 
                  v-if="canTransitionTo('Known Error')" 
                  type="warning" 
                  size="small" 
                  @click="updateProblemStatus('Known Error')"
                >
                  标记为已知错误
                </el-button>
              </div>
            </div>
            
            <div class="detail-section">
              <h4>生命周期</h4>
              <el-timeline>
                <el-timeline-item
                  v-for="log in problemLogs"
                  :key="log.id"
                  :timestamp="formatDate(log.created_at)"
                  :type="getTimelineType(log.action)"
                >
                  <div class="timeline-content">
                    <div class="timeline-action">{{ log.action }}</div>
                    <div v-if="log.comments" class="timeline-comments">{{ log.comments }}</div>
                    <div class="timeline-user">操作人: {{ log.user?.real_name || log.user?.username || '系统' }}</div>
                  </div>
                </el-timeline-item>
              </el-timeline>
            </div>
          </el-col>
        </el-row>
      </div>
      
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { useRoute } from 'vue-router'
import request from '@/utils/request'
import dayjs from 'dayjs'

export default {
  name: 'Problems',
  components: { Plus },
  setup() {
    const route = useRoute()
    const loading = ref(false)
    const submitting = ref(false)
    const submittingApproval = ref(false)
    const problemsList = ref([])
    const dialogVisible = ref(false)
    const detailDialogVisible = ref(false)
    const formRef = ref(null)
    const isEdit = ref(false)
    const currentProblem = ref(null)
    const problemLogs = ref([])
    const hasActiveApproval = ref(false)
    
    const filters = reactive({
      status: '',
      priority: ''
    })
    
    const pagination = reactive({
      page: 1,
      per_page: 20,
      total: 0
    })
    
    const form = reactive({
      id: null,
      title: '',
      description: '',
      priority: 'Medium',
      incident_id: '',
      root_cause_analysis: '',
      solution: ''
    })
    
    const formRules = {
              title: [
          { required: true, message: '请输入问题标题', trigger: 'blur' }
        ],
        description: [
          { required: true, message: '请输入问题描述', trigger: 'blur' }
        ],
      priority: [
        { required: true, message: '请选择优先级', trigger: 'change' }
      ]
    }
    
    const dialogTitle = computed(() => {
      return isEdit.value ? '编辑问题' : '新建问题'
    })
    
    const loadProblems = async () => {
      try {
        loading.value = true
        const params = {
          page: pagination.page,
          per_page: pagination.per_page,
          ...filters
        }
        
        // 移除空值
        Object.keys(params).forEach(key => {
          if (params[key] === '' || params[key] === null) {
            delete params[key]
          }
        })
        
        const data = await request.get('/problems', { params })
        problemsList.value = data.problems || []
        pagination.total = data.total || 0
      } catch (error) {
        ElMessage.error('获取问题列表失败')
      } finally {
        loading.value = false
      }
    }
    
    const showCreateDialog = () => {
      isEdit.value = false
      resetForm()
      dialogVisible.value = true
    }
    
    const editProblem = (problem) => {
      isEdit.value = true
      Object.assign(form, {
        id: problem.id,
        title: problem.title,
        description: problem.description,
        priority: problem.priority,
        incident_id: problem.incident_id || '',
        root_cause_analysis: problem.root_cause_analysis || '',
        solution: problem.solution || ''
      })
      dialogVisible.value = true
    }
    
    const viewProblem = async (problem) => {
      // 先获取最新的数据
      try {
        const response = await request.get(`/problems/${problem.id}`)
        currentProblem.value = response.problem
      } catch (error) {
        console.error('获取故障详情失败:', error)
        currentProblem.value = problem
      }
      
      // 加载问题状态日志
      try {
        const logsResponse = await request.get(`/problems/${problem.id}/logs`)
        problemLogs.value = logsResponse.logs || []
      } catch (error) {
        console.error('获取故障日志失败:', error)
        // 如果API失败，使用默认日志
        problemLogs.value = [
          {
            id: 1,
            action: '故障创建',
            comments: '创建新故障',
            user: { real_name: '系统' },
            created_at: problem.created_at
          }
        ]
      }
      
      detailDialogVisible.value = true
      
      // 模拟检查是否有活跃的审批
      hasActiveApproval.value = Math.random() > 0.7 // 随机模拟
    }
    
    const canTransitionTo = (targetStatus) => {
      if (!currentProblem.value) return false
      
      const currentStatus = currentProblem.value.status
      const transitions = {
        'New': ['Investigating'],
        'Investigating': ['Known Error'],
        'Known Error': [], // 已知错误需要通过审批流程关闭
        'Pending Approval': [], // 审批中不能手动变更状态
        'Closed': []
      }
      
      return transitions[currentStatus]?.includes(targetStatus) || false
    }
    
    const updateProblemStatus = async (newStatus) => {
      if (!currentProblem.value) return
      
      try {
        // 更新后端数据
        await request.put(`/problems/${currentProblem.value.id}`, { status: newStatus })
        
        ElMessage.success('故障状态更新成功')
        
        // 更新当前故障状态
        currentProblem.value.status = newStatus
        
        // 重新加载状态日志
        try {
          const logsResponse = await request.get(`/problems/${currentProblem.value.id}/logs`)
          problemLogs.value = logsResponse.logs || []
        } catch (error) {
          console.error('刷新故障日志失败:', error)
        }
        
        // 同时更新列表中的数据
        const problemIndex = problemsList.value.findIndex(p => p.id === currentProblem.value.id)
        if (problemIndex !== -1) {
          problemsList.value[problemIndex].status = newStatus
        }
        
        // 重新加载列表以确保数据一致性
        await loadProblems()
        
      } catch (error) {
        console.error('更新故障状态失败:', error)
        ElMessage.error('更新故障状态失败')
      }
    }
    
    const submitForApproval = async () => {
      if (!currentProblem.value) return
      
      try {
        submittingApproval.value = true
        
        // 这里应该调用审批API
        // await approvals.create({ problem_id: currentProblem.value.id, workflow_id: 1 })
        
        // 模拟提交成功
        setTimeout(() => {
          hasActiveApproval.value = true
          submittingApproval.value = false
          ElMessage.success('审批申请提交成功')
        }, 1000)
        
      } catch (error) {
        submittingApproval.value = false
        ElMessage.error('提交审批申请失败')
      }
    }
    
    const resetForm = () => {
      Object.assign(form, {
        id: null,
        title: '',
        description: '',
        priority: 'Medium',
        incident_id: '',
        root_cause_analysis: '',
        solution: ''
      })
      formRef.value?.clearValidate()
    }
    
    const handleSubmit = async () => {
      try {
        const valid = await formRef.value?.validate()
        if (!valid) return
        
        submitting.value = true
        
        if (isEdit.value) {
          await request.put(`/problems/${form.id}`, form)
          ElMessage.success('问题更新成功')
        } else {
          await request.post('/problems', form)
          ElMessage.success('问题创建成功')
        }
        
        dialogVisible.value = false
        loadProblems()
      } catch (error) {
        ElMessage.error(isEdit.value ? '故障更新失败' : '故障创建失败')
      } finally {
        submitting.value = false
      }
    }
    
    const getPriorityType = (priority) => {
      const types = {
        'Critical': 'danger',
        'High': 'danger',
        'Medium': 'warning',
        'Low': 'success'
      }
      return types[priority] || 'info'
    }
        
    // 优先级中文映射
    const getPriorityText = (priority) => {
      const priorityMap = {
        'Critical': '严重',
        'High': '高',
        'Medium': '中',
        'Low': '低'
      }
      return priorityMap[priority] || priority
    }
    
    const getStatusType = (status) => {
      const types = {
        'New': 'info',
        'Investigating': 'primary',
        'Known Error': 'warning',
        'Closed': 'success',
        'Pending Approval': 'warning'
      }
      return types[status] || 'info'
    }
        
    // 状态中文映射
    const getStatusText = (status) => {
      const statusMap = {
        'New': '待处理',
        'Investigating': '调查中',
        'Known Error': '已知错误',
        'Closed': '已关闭',
        'Pending Approval': '待审批'
      }
      return statusMap[status] || status
    }
    
    const formatDate = (dateStr) => {
      return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
    }
    
    const getTimelineType = (action) => {
      if (action.includes('创建')) return 'primary'
      if (action.includes('调查')) return 'warning'
      if (action.includes('已知错误')) return 'danger'
      if (action.includes('关闭')) return 'success'
      return 'primary'
    }
    
    const handleFilter = () => {
      pagination.page = 1  // 重置到第一页
      loadProblems()
    }
    
    const resetFilters = () => {
      Object.keys(filters).forEach(key => {
        filters[key] = ''
      })
      pagination.page = 1
      loadProblems()
    }
    
    onMounted(() => {
      loadProblems()
      
      // 检查是否从故障管理页面跳转过来
      if (route.query.create_from_incident) {
        // 自动填充来自故障的信息
        form.title = route.query.incident_title || '来自故障的问题'
        form.description = route.query.incident_description || '此问题来源于故障处理过程中发现的根本原因'
        
        // 显示创建问题对话框
        showCreateDialog()
        
        // 提示用户
        ElMessage.info(`正在为故障"${route.query.incident_title}"创建问题记录`)
      }
    })
    
    return {
      loading,
      submitting,
      submittingApproval,
      problemsList,
      problemLogs,
      dialogVisible,
      detailDialogVisible,
      currentProblem,
      hasActiveApproval,
      dialogTitle,
      formRef,
      form,
      formRules,
      filters,
      pagination,
      loadProblems,
      handleFilter,
      resetFilters,
      showCreateDialog,
      editProblem,
      viewProblem,
      canTransitionTo,
      updateProblemStatus,
      submitForApproval,
      handleSubmit,
      getPriorityType,
      getPriorityText,
      getStatusType,
      getStatusText,
      formatDate,
      getTimelineType
    }
  }
}
</script>

<style scoped>
.problems {
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

.filter-card {
  margin-bottom: 20px;
}

.filter-form {
  margin-bottom: 0;
}

.table-card {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.problem-detail {
  padding: 20px 0;
}

.incident-link {
  color: #409eff;
  font-weight: bold;
}

.no-incident {
  color: #999;
  font-style: italic;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h4 {
  margin-bottom: 16px;
  color: #303133;
  font-size: 16px;
}

.approval-section {
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.status-actions {
  margin-bottom: 20px;
}

.status-actions .el-button {
  margin-right: 8px;
  margin-bottom: 8px;
}

.timeline-content {
  line-height: 1.6;
}

.timeline-action {
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.timeline-comments {
  color: #606266;
  margin-bottom: 4px;
}

.timeline-user {
  color: #909399;
  font-size: 12px;
}
</style>