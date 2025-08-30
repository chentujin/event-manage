<template>
  <div class="incidents">
    <div class="page-header">
      <h1>事件管理</h1>
      <el-button type="primary" @click="showCreateDialog = true">
        <el-icon><Plus /></el-icon>
        新建事件
      </el-button>
    </div>
    
    <!-- 筛选器 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 150px">
            <el-option label="待处理" value="New" />
            <el-option label="处理中" value="In Progress" />
            <el-option label="挂起" value="On Hold" />
            <el-option label="已解决" value="Resolved" />
            <el-option label="已关闭" value="Closed" />
            <el-option label="重新打开" value="Reopened" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="优先级">
          <el-select v-model="filters.priority" placeholder="全部优先级" clearable style="width: 150px">
            <el-option label="紧急" value="Critical" />
            <el-option label="高" value="High" />
            <el-option label="中" value="Medium" />
            <el-option label="低" value="Low" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="服务">
          <el-select v-model="filters.service_id" placeholder="全部服务" clearable style="width: 200px">
            <el-option
              v-for="service in servicesList"
              :key="service.id"
              :label="service.name"
              :value="service.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="分配状态">
          <el-select v-model="filters.assignment" placeholder="全部事件" clearable style="width: 150px">
            <el-option label="我的事件" value="mine" />
            <el-option label="未分配" value="unassigned" />
            <el-option label="已分配" value="assigned" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleFilter">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 事件列表 -->
    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="incidentsList"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="priority" label="优先级" width="100">
          <template #default="scope">
            <el-tag
              :type="getPriorityType(scope.row.priority)"
              size="small"
            >
              {{ getPriorityText(scope.row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="scope">
            <el-tag
              :type="getStatusType(scope.row.status)"
              size="small"
            >
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="service" label="服务" width="150">
          <template #default="scope">
            {{ scope.row.service?.name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="reporter" label="报告人" width="120">
          <template #default="scope">
            {{ scope.row.reporter?.real_name || scope.row.reporter?.username }}
          </template>
        </el-table-column>
        <el-table-column prop="assignee" label="处理人" width="120">
          <template #default="scope">
            <span v-if="scope.row.last_updated_user" :class="{ 'my-assignment': isMyAssignment(scope.row) }">
              {{ scope.row.last_updated_user.real_name || scope.row.last_updated_user.username }}
            </span>
            <span v-else-if="scope.row.assignee" :class="{ 'my-assignment': isMyAssignment(scope.row) }">
              {{ scope.row.assignee.real_name || scope.row.assignee.username }}
            </span>
            <span v-else class="unassigned">未分配</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="scope">
            <el-button
              type="text"
              size="small"
              @click="viewIncident(scope.row)"
            >
              查看
            </el-button>
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
          @current-change="loadIncidents"
          @size-change="loadIncidents"
        />
      </div>
    </el-card>
    
    <!-- 新建事件对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="新建事件"
      width="600px"
      @close="resetCreateForm"
    >
      <el-form
        ref="createForm"
        :model="createFormData"
        :rules="createRules"
        label-width="100px"
      >
        <el-form-item label="标题" prop="title">
          <el-input v-model="createFormData.title" placeholder="请输入事件标题" />
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="createFormData.description"
            type="textarea"
            :rows="4"
            placeholder="请详细描述事件情况"
          />
        </el-form-item>
        
        <el-form-item label="影响度" prop="impact">
          <el-select v-model="createFormData.impact" placeholder="请选择影响度">
            <el-option label="高" value="High" />
            <el-option label="中" value="Medium" />
            <el-option label="低" value="Low" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="紧急度" prop="urgency">
          <el-select v-model="createFormData.urgency" placeholder="请选择紧急度">
            <el-option label="高" value="High" />
            <el-option label="中" value="Medium" />
            <el-option label="低" value="Low" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="关联服务">
          <el-select v-model="createFormData.service_id" placeholder="请选择关联服务">
            <el-option
              v-for="service in servicesList"
              :key="service.id"
              :label="service.name"
              :value="service.id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="handleCreate">
          创建
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 事件详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="事件详情"
      width="800px"
      @close="currentIncident = null"
    >
      <div v-if="currentIncident" class="incident-detail">
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="detail-section">
              <h4>基本信息</h4>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="标题">{{ currentIncident.title }}</el-descriptions-item>
                <el-descriptions-item label="状态">
                  <el-tag :type="getStatusType(currentIncident.status)" size="small">
                    {{ getStatusText(currentIncident.status) }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="优先级">
                  <el-tag :type="getPriorityType(currentIncident.priority)" size="small">
                    {{ getPriorityText(currentIncident.priority) }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="影响度">{{ currentIncident.impact }}</el-descriptions-item>
                <el-descriptions-item label="紧急度">{{ currentIncident.urgency }}</el-descriptions-item>
                <el-descriptions-item label="关联服务">{{ currentIncident.service?.name || '-' }}</el-descriptions-item>
                <el-descriptions-item label="报告人">{{ currentIncident.reporter?.real_name }}</el-descriptions-item>
                <el-descriptions-item label="创建时间">{{ formatDate(currentIncident.created_at) }}</el-descriptions-item>
              </el-descriptions>
            </div>
            
            <div class="detail-section">
              <h4>描述</h4>
              <p>{{ currentIncident.description }}</p>
            </div>
          </el-col>
          
          <el-col :span="12">
            <!-- 事件分配区域 - 未解决和未关闭的事件都可以分配 -->
            <div v-if="currentIncident.status !== 'Closed'" class="detail-section">
              <h4>事件分配</h4>
              <div class="assign-section">
                <el-form :inline="true">
                  <el-form-item label="分配给:">
                    <el-select v-model="assigneeId" placeholder="请选择处理人" style="width: 200px">
                      <el-option
                        v-for="user in usersList"
                        :key="user.id"
                        :label="user.real_name || user.username"
                        :value="user.id"
                      />
                    </el-select>
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" size="small" @click="assignIncident" :loading="assignLoading">
                      {{ currentIncident.assignee ? '重新分配' : '分配' }}
                    </el-button>
                  </el-form-item>
                </el-form>
                <div v-if="currentIncident.assignee" class="current-assignee">
                  当前处理人: {{ currentIncident.assignee.real_name || currentIncident.assignee.username }}
                </div>
                <div v-if="currentIncident.status === 'Resolved'" class="resolved-info">
                  <el-alert
                    title="该事件已解决，如需重新分配请先重新打开事件"
                    type="info"
                    :closable="false"
                    show-icon
                  />
                </div>
              </div>
            </div>
            
            <div class="detail-section">
              <h4>状态流转</h4>
              <div class="status-actions">
                <el-button 
                  v-if="canTransitionTo('In Progress')" 
                  type="primary" 
                  size="small" 
                  @click="updateIncidentStatus('In Progress')"
                >
                  开始处理
                </el-button>
                <el-button 
                  v-if="canTransitionTo('On Hold')" 
                  type="warning" 
                  size="small" 
                  @click="updateIncidentStatus('On Hold')"
                >
                  挂起
                </el-button>
                <el-button 
                  v-if="canTransitionTo('Resolved')" 
                  type="success" 
                  size="small" 
                  @click="updateIncidentStatus('Resolved')"
                >
                  解决
                </el-button>
                <el-button 
                  v-if="canTransitionTo('Closed')" 
                  type="info" 
                  size="small" 
                  @click="updateIncidentStatus('Closed')"
                >
                  关闭
                </el-button>
                <el-button 
                  v-if="canTransitionTo('Reopened')" 
                  type="danger" 
                  size="small" 
                  @click="updateIncidentStatus('Reopened')"
                >
                  重新打开
                </el-button>
              </div>
            </div>
            
            <div class="detail-section">
              <h4>生命周期</h4>
              <el-timeline>
                <el-timeline-item
                  v-for="log in incidentLogs"
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
            
            <!-- 事件评论区域 -->
            <div class="detail-section">
              <h4>评论记录</h4>
              
              <!-- 评论列表 -->
              <div class="comments-list" v-if="currentIncident.comments && currentIncident.comments.length > 0">
                <div 
                  v-for="comment in currentIncident.comments" 
                  :key="comment.id" 
                  class="comment-item"
                  :class="{ 'private-comment': comment.is_private }"
                >
                  <div class="comment-header">
                    <span class="comment-author">{{ comment.user?.real_name || comment.user?.username }}</span>
                    <span class="comment-time">{{ formatDate(comment.created_at) }}</span>
                    <el-tag v-if="comment.is_private" size="small" type="warning">私有</el-tag>
                  </div>
                  <div class="comment-content">{{ comment.content }}</div>
                </div>
              </div>
              
              <div v-else class="no-comments">
                <el-empty description="暂无评论" />
              </div>
              
              <!-- 添加评论 -->
              <div v-if="currentIncident.status !== 'Closed'" class="add-comment-section">
                <el-form :model="commentForm" label-width="80px">
                  <el-form-item label="添加评论">
                    <el-input 
                      v-model="commentForm.content" 
                      type="textarea" 
                      :rows="4" 
                      placeholder="请输入评论内容..."
                      maxlength="1000"
                      show-word-limit
                    />
                  </el-form-item>
                  <el-form-item>
                    <el-checkbox v-model="commentForm.is_private">私有评论</el-checkbox>
                    <el-button 
                      type="primary" 
                      size="small" 
                      @click="addComment" 
                      :loading="commentLoading"
                      :disabled="!commentForm.content.trim()"
                      style="margin-left: 10px;"
                    >
                      添加评论
                    </el-button>
                  </el-form-item>
                </el-form>
              </div>
              
              <!-- 已关闭事件的提示信息 -->
              <div v-else class="closed-comment-tip">
                <el-alert
                  title="已关闭的事件无法添加评论"
                  description="此事件已关闭，如需添加评论请先重新打开事件"
                  type="info"
                  show-icon
                  :closable="false"
                />
              </div>
            </div>
          </el-col>
        </el-row>
      </div>
      
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { incidents, services } from '@/api'
import { getUserInfo } from '@/utils/auth'
import dayjs from 'dayjs'

export default {
  name: 'Incidents',
  components: {
    Plus
  },
  setup() {
    const loading = ref(false)
    const createLoading = ref(false)
    const assignLoading = ref(false)
    const commentLoading = ref(false)
    const showCreateDialog = ref(false)
    const showDetailDialog = ref(false)
    const createForm = ref(null)
    const currentIncident = ref(null)
    const incidentLogs = ref([])
    const assigneeId = ref(null)
    
    const incidentsList = ref([])
    const servicesList = ref([])
    const usersList = ref([])
    
    const filters = reactive({
      status: '',
      priority: '',
      service_id: '',
      assignment: ''
    })
    
    const pagination = reactive({
      page: 1,
      per_page: 20,
      total: 0
    })
    
    const createFormData = reactive({
      title: '',
      description: '',
      impact: '',
      urgency: '',
      service_id: null
    })
    
    const commentForm = reactive({
      content: '',
      is_private: false
    })
    
    const createRules = {
      title: [
        { required: true, message: '请输入事件标题', trigger: 'blur' }
      ],
      description: [
        { required: true, message: '请输入事件描述', trigger: 'blur' }
      ],
      impact: [
        { required: true, message: '请选择影响度', trigger: 'change' }
      ],
      urgency: [
        { required: true, message: '请选择紧急度', trigger: 'change' }
      ]
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
    
    // 状态中文映射
    const getStatusText = (status) => {
      const statusMap = {
        'New': '待处理',
        'In Progress': '处理中',
        'On Hold': '暂停',
        'Resolved': '已解决',
        'Closed': '已关闭',
        'Reopened': '重新打开'
      }
      return statusMap[status] || status
    }
    
    const loadIncidents = async () => {
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
        
        const data = await incidents.list(params)
        incidentsList.value = data.incidents || []
        pagination.total = data.total || 0
      } catch (error) {
        ElMessage.error('获取事件列表失败')
      } finally {
        loading.value = false
      }
    }
    
    const loadServices = async () => {
      try {
        const data = await services.list()
        servicesList.value = data.services || []
      } catch (error) {
        console.error('获取服务列表失败:', error)
      }
    }
    
    const loadUsers = async () => {
      try {
        const data = await incidents.getAssignableUsers()
        usersList.value = data.users || []
      } catch (error) {
        console.error('获取用户列表失败:', error)
        ElMessage.error('获取用户列表失败，请检查权限配置')
      }
    }
    
    const resetFilters = () => {
      Object.keys(filters).forEach(key => {
        filters[key] = ''
      })
      pagination.page = 1
      loadIncidents()
    }
    
    const handleFilter = () => {
      pagination.page = 1  // 重置到第一页
      loadIncidents()
    }
    
    const resetCreateForm = () => {
      Object.keys(createFormData).forEach(key => {
        createFormData[key] = ''
      })
      if (createForm.value) {
        createForm.value.resetFields()
      }
    }
    
    const handleCreate = async () => {
      if (!createForm.value) return
      
      try {
        const valid = await createForm.value.validate()
        if (!valid) return
        
        createLoading.value = true
        
        await incidents.create(createFormData)
        
        ElMessage.success('事件创建成功')
        showCreateDialog.value = false
        resetCreateForm()
        loadIncidents()
        
      } catch (error) {
        console.error('创建事件失败:', error)
      } finally {
        createLoading.value = false
      }
    }
    
    const viewIncident = async (incident) => {
      try {
        // 获取完整的事件详情（包含评论）
        const response = await incidents.get(incident.id)
        currentIncident.value = response.incident
        assigneeId.value = response.incident.assignee_id || null
        showDetailDialog.value = true
        
        // 从后端API获取事件状态日志
        try {
          const logsResponse = await incidents.getLogs(incident.id)
          incidentLogs.value = logsResponse.logs || []
        } catch (error) {
          console.error('获取事件日志失败:', error)
          // 如果API失败，使用默认日志
          incidentLogs.value = [
            {
              id: 1,
              action: '事件创建',
              comments: '用户报告的新事件',
              user: incident.reporter,
              created_at: incident.created_at
            }
          ]
        }
      } catch (error) {
        console.error('获取事件详情失败:', error)
        ElMessage.error('获取事件详情失败')
      }
    }
    
    const canTransitionTo = (targetStatus) => {
      if (!currentIncident.value) return false
      
      const currentStatus = currentIncident.value.status
      const transitions = {
        'New': ['In Progress'],
        'In Progress': ['On Hold', 'Resolved'],
        'On Hold': ['In Progress', 'Resolved'],
        'Resolved': ['Closed', 'Reopened'], // 已解决的事件可以关闭或重新打开
        'Closed': [], // 已关闭的事件不能重新打开
        'Reopened': ['In Progress']
      }
      
      return transitions[currentStatus]?.includes(targetStatus) || false
    }
    
    const updateIncidentStatus = async (newStatus) => {
      if (!currentIncident.value) return
      
      try {
        await incidents.update(currentIncident.value.id, { status: newStatus })
        
        ElMessage.success('事件状态更新成功')
        
        // 更新当前事件状态
        currentIncident.value.status = newStatus
        
        // 重新加载状态日志
        try {
          const response = await incidents.getLogs(currentIncident.value.id)
          incidentLogs.value = response.logs || []
        } catch (error) {
          console.error('刷新事件日志失败:', error)
        }
        
        // 刷新列表
        loadIncidents()
        
      } catch (error) {
        ElMessage.error('更新事件状态失败')
      }
    }
    
    const assignIncident = async () => {
      if (!currentIncident.value || !assigneeId.value) {
        ElMessage.warning('请选择处理人')
        return
      }
      
      // 已解决的事件不允许直接重新分配
      if (currentIncident.value.status === 'Resolved') {
        ElMessage.warning('已解决的事件无法重新分配，请先重新打开事件')
        return
      }
      
      try {
        assignLoading.value = true
        
        await incidents.update(currentIncident.value.id, { 
          assignee_id: assigneeId.value 
        })
        
        ElMessage.success('事件分配成功')
        
        // 更新当前事件的分配人
        const assignee = usersList.value.find(u => u.id === assigneeId.value)
        currentIncident.value.assignee = assignee
        currentIncident.value.assignee_id = assigneeId.value
        
        // 重新加载状态日志
        try {
          const response = await incidents.getLogs(currentIncident.value.id)
          incidentLogs.value = response.logs || []
        } catch (error) {
          console.error('刷新事件日志失败:', error)
        }
        
        // 刷新列表
        loadIncidents()
        
      } catch (error) {
        ElMessage.error('事件分配失败')
      } finally {
        assignLoading.value = false
      }
    }
    
    const getTimelineType = (action) => {
      if (action.includes('创建')) return 'primary'
      if (action.includes('已解决')) return 'success'
      if (action.includes('关闭')) return 'info'
      if (action.includes('挂起')) return 'warning'
      return 'primary'
    }
    
    const getPriorityType = (priority) => {
      const types = {
        'Critical': 'danger',
        'High': 'warning',
        'Medium': 'primary',
        'Low': 'success'
      }
      return types[priority] || 'info'
    }
    
    const getStatusType = (status) => {
      const types = {
        'New': 'info',
        'In Progress': 'primary',
        'On Hold': 'warning',
        'Resolved': 'success',
        'Closed': 'info',
        'Reopened': 'danger'
      }
      return types[status] || 'info'
    }
    
    const formatDate = (dateStr) => {
      return dayjs(dateStr).format('YYYY-MM-DD HH:mm')
    }
    
    const isMyAssignment = (incident) => {
      const currentUser = getUserInfo()
      return incident.assignee_id === currentUser?.id
    }
    
    const addComment = async () => {
      if (!currentIncident.value || !commentForm.content.trim()) {
        ElMessage.warning('请输入评论内容')
        return
      }
      
      // 检查事件状态，已关闭的事件不能添加评论
      if (currentIncident.value.status === 'Closed') {
        ElMessage.warning('已关闭的事件无法添加评论')
        return
      }
      
      try {
        commentLoading.value = true
        
        const response = await incidents.addComment(currentIncident.value.id, {
          content: commentForm.content.trim(),
          is_private: commentForm.is_private
        })
        
        ElMessage.success('评论添加成功')
        
        // 清空评论表单
        commentForm.content = ''
        commentForm.is_private = false
        
        // 重新加载事件详情（包含评论）
        try {
          const incidentResponse = await incidents.get(currentIncident.value.id)
          currentIncident.value = incidentResponse.incident
        } catch (error) {
          console.error('刷新事件详情失败:', error)
        }
        
        // 刷新列表
        loadIncidents()
        
      } catch (error) {
        console.error('添加评论失败:', error)
        ElMessage.error('添加评论失败')
      } finally {
        commentLoading.value = false
      }
    }
    
    onMounted(() => {
      loadIncidents()
      loadServices()
      loadUsers()
    })
    
    return {
      loading,
      createLoading,
      assignLoading,
      commentLoading,
      showCreateDialog,
      showDetailDialog,
      createForm,
      currentIncident,
      incidentLogs,
      assigneeId,
      incidentsList,
      servicesList,
      usersList,
      filters,
      pagination,
      createFormData,
      commentForm,
      createRules,
      loadIncidents,
      resetFilters,
      handleFilter,
      resetCreateForm,
      handleCreate,
      viewIncident,
      canTransitionTo,
      updateIncidentStatus,
      assignIncident,
      addComment,
      getTimelineType,
      getPriorityType,
      getStatusType,
      getPriorityText,
      getStatusText,
      formatDate,
      isMyAssignment
    }
  }
}
</script>

<style scoped>
.incidents {
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

.incident-detail {
  padding: 20px 0;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h4 {
  margin-bottom: 16px;
  color: #303133;
  font-size: 16px;
}

.status-actions {
  margin-bottom: 20px;
}

.status-actions .el-button {
  margin-right: 8px;
  margin-bottom: 8px;
}

.assign-section {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
  margin-bottom: 16px;
}

.current-assignee {
  margin-top: 12px;
  color: #606266;
  font-size: 14px;
}

.resolved-info {
  margin-top: 12px;
}

.timeline-content {
  padding-bottom: 8px;
}

.timeline-action {
  font-weight: bold;
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

.my-assignment {
  color: #409EFF;
  font-weight: 600;
  background: #ecf5ff;
  padding: 2px 6px;
  border-radius: 3px;
}

.unassigned {
  color: #909399;
  font-style: italic;
}

/* 评论区域样式 */
.comments-list {
  margin-bottom: 20px;
}

.comment-item {
  background: #f8f9fa;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}

.comment-item.private-comment {
  background: #fff7e6;
  border-color: #ffd591;
}

.comment-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
}

.comment-author {
  font-weight: bold;
  color: #303133;
}

.comment-time {
  color: #909399;
  font-size: 12px;
}

.comment-content {
  color: #606266;
  line-height: 1.5;
  white-space: pre-wrap;
}

.no-comments {
  text-align: center;
  padding: 20px;
  color: #909399;
}

.add-comment-section {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  margin-top: 20px;
}

.closed-comment-tip {
  margin-top: 20px;
}
</style>