<template>
  <div class="incidents-page">
    <!-- 页面标题和操作栏 -->
    <div class="page-header">
      <h1>故障管理</h1>
      <div class="actions">
        <el-button type="primary" @click="showCreateDialog">创建故障</el-button>
        <el-button @click="refreshIncidents">刷新</el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ statistics.active_incidents || 0 }}</div>
              <div class="stat-label">活跃故障</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ statistics.today_incidents || 0 }}</div>
              <div class="stat-label">今日新增</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ statistics.pending_postmortem || 0 }}</div>
              <div class="stat-label">待复盘</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ getP1Count() }}</div>
              <div class="stat-label">P1故障</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 故障列表 -->
    <el-card class="table-card">
      <el-table
        v-loading="loading"
        :data="incidents"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="incident_id" label="故障ID" width="100" />
        <el-table-column prop="title" label="标题" min-width="200" />
        <el-table-column prop="severity" label="严重度" width="100">
          <template #default="scope">
            <el-tag
              :type="getSeverityTagType(scope.row.severity)"
              size="small"
            >
              {{ scope.row.severity }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="scope">
            <el-tag
              :type="getStatusTagType(scope.row.status)"
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
            <span v-if="scope.row.assignee">
              {{ scope.row.assignee.real_name || scope.row.assignee.username }}
            </span>
            <span v-else class="unassigned">未分配</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="scope">
            {{ formatDateTime(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="scope">
            <el-button
              type="text"
              size="small"
              @click="showIncidentDetail(scope.row)"
            >
              查看
            </el-button>
            <el-button
              type="text"
              size="small"
              @click="showNotificationDialog(scope.row)"
            >
              通知
            </el-button>
            <el-button
              v-if="canChangeStatus(scope.row, 'Pending')"
              type="text"
              size="small"
              @click="changeStatus(scope.row, 'Pending')"
            >
              确认
            </el-button>
            <el-button
              v-if="canChangeStatus(scope.row, 'Investigating')"
              type="text"
              size="small"
              @click="changeStatus(scope.row, 'Investigating')"
            >
              处理
            </el-button>
            <el-button
              v-if="canChangeStatus(scope.row, 'Recovered')"
              type="text"
              size="small"
              @click="changeStatus(scope.row, 'Recovered')"
            >
              恢复
            </el-button>
            <el-button
              v-if="canChangeStatus(scope.row, 'Closed')"
              type="text"
              size="small"
              @click="changeStatus(scope.row, 'Closed')"
            >
              关闭
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

    <!-- 通知选择对话框 -->
    <el-dialog v-model="notificationDialogVisible" title="发送通知" width="600px">
      <el-form :model="notificationForm" label-width="120px">
        <el-form-item label="通知渠道">
          <el-checkbox-group v-model="notificationForm.channelIds">
            <el-checkbox 
              v-for="channel in notificationChannels" 
              :key="channel.id" 
              :label="channel.id"
              :disabled="!channel.is_active"
            >
              {{ channel.name }} ({{ formatChannelType(channel.type) }})
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        
        <el-form-item label="通知用户组" v-if="showUserGroupSelection">
          <el-select 
            v-model="notificationForm.groupIds" 
            multiple 
            placeholder="请选择用户组"
            style="width: 100%"
          >
            <el-option 
              v-for="group in userGroups" 
              :key="group.id" 
              :label="group.name" 
              :value="group.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="通知消息">
          <el-input 
            v-model="notificationForm.message" 
            type="textarea" 
            :rows="4" 
            placeholder="请输入通知消息内容"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="notificationDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="sendNotification">确认</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 故障详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="故障详情" width="80%">
      <div v-if="selectedIncident" class="incident-detail">
        <el-tabs v-model="activeTab" type="border-card">
          <!-- 基本信息 -->
          <el-tab-pane label="基本信息" name="basic">
            <el-descriptions :column="2" border>
              <el-descriptions-item label="故障ID">{{ selectedIncident.incident_id }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusTagType(selectedIncident.status)">
                  {{ getStatusText(selectedIncident.status) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="严重度">
                <el-tag :type="getSeverityTagType(selectedIncident.severity)">
                  {{ selectedIncident.severity }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="负责人">
                {{ selectedIncident.assignee ? selectedIncident.assignee.real_name : '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="标题" :span="2">{{ selectedIncident.title }}</el-descriptions-item>
              <el-descriptions-item label="描述" :span="2">{{ selectedIncident.description || '-' }}</el-descriptions-item>
            </el-descriptions>
            
            <!-- 操作按钮 - 已隐藏 -->
            <!-- <div class="action-buttons" style="margin-top: 20px;">
              <el-button 
                v-if="canChangeStatus(selectedIncident, 'Pending')"
                type="warning" 
                @click="changeStatus('Pending')">
                确认故障
              </el-button>
              <el-button 
                v-if="canChangeStatus(selectedIncident, 'Investigating')"
                type="primary" 
                @click="changeStatus('Investigating')">
                开始处理
              </el-button>
              <el-button 
                v-if="canChangeStatus(selectedIncident, 'Recovered')"
                type="success" 
                @click="changeStatus('Recovered')">
                标记恢复
              </el-button>
              <el-button 
                v-if="canChangeStatus(selectedIncident, 'Post-Mortem')"
                @click="changeStatus('Post-Mortem')">
                进入复盘
              </el-button>
              <el-button 
                v-if="canChangeStatus(selectedIncident, 'Closed')"
                @click="changeStatus('Closed')">
                关闭故障
              </div> -->
          </el-tab-pane>

          <!-- 关联告警 -->
          <el-tab-pane label="关联告警" name="alerts">
            <div class="related-alerts">
              <h4>关联告警 ({{ selectedIncident.alerts ? selectedIncident.alerts.length : 0 }})</h4>
              <el-table :data="selectedIncident.alerts || []" style="margin-top: 10px;">
                <el-table-column prop="id" label="告警ID" width="80"></el-table-column>
                <el-table-column prop="title" label="标题" min-width="200"></el-table-column>
                <el-table-column prop="level" label="级别" width="80">
                  <template #default="scope">
                    <el-tag :type="getLevelTagType(scope.row.level)" size="small">
                      {{ getLevelText(scope.row.level) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="fired_at" label="触发时间" width="180">
                  <template #default="scope">
                    {{ formatDateTime(scope.row.fired_at) }}
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-tab-pane>

          <!-- 时间线 -->
          <el-tab-pane label="处理时间线" name="timeline">
            <div class="timeline-section">
              <h4>处理时间线</h4>
              
              <!-- 添加进展记录 -->
              <div v-if="selectedIncident.status === 'Investigating'" class="add-progress">
                <el-form :model="progressForm" label-width="80px">
                  <el-form-item label="进展标题">
                    <el-input v-model="progressForm.title" placeholder="请输入进展标题" />
                  </el-form-item>
                  <el-form-item label="进展详情">
                    <el-input 
                      v-model="progressForm.description" 
                      type="textarea" 
                      :rows="3" 
                      placeholder="请描述处理进展" 
                    />
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" @click="addProgress" :loading="addingProgress">
                      添加进展
                    </el-button>
                  </el-form-item>
                </el-form>
              </div>
              
              <el-timeline style="margin-top: 20px;">
                <el-timeline-item
                  v-for="entry in selectedIncident.timeline || []"
                  :key="entry.id"
                  :timestamp="formatDateTime(entry.timestamp)">
                  <div class="timeline-content">
                    <h4>{{ entry.title }}</h4>
                    <p>{{ entry.description }}</p>
                    <small>操作人: {{ entry.user ? entry.user.real_name : '系统' }}</small>
                  </div>
                </el-timeline-item>
              </el-timeline>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>

    <!-- 创建故障对话框 -->
    <el-dialog v-model="createDialogVisible" title="创建故障" width="60%">
      <el-form :model="newIncident" :rules="incidentRules" ref="incidentForm" label-width="120px">
        <el-form-item label="故障标题" prop="title">
          <el-input v-model="newIncident.title" placeholder="请输入故障标题"></el-input>
        </el-form-item>
        <el-form-item label="严重度" prop="severity">
          <el-select v-model="newIncident.severity" placeholder="请选择严重度">
            <el-option label="P1 - 严重" value="P1"></el-option>
            <el-option label="P2 - 高" value="P2"></el-option>
            <el-option label="P3 - 中" value="P3"></el-option>
            <el-option label="P4 - 低" value="P4"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="故障描述">
          <el-input type="textarea" v-model="newIncident.description" :rows="3" placeholder="请描述故障详情"></el-input>
        </el-form-item>
        <el-form-item label="影响范围">
          <el-input v-model="newIncident.impact_scope" placeholder="如：订单服务、支付模块等"></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="createIncident" :loading="creating">创建</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import request from '@/utils/request'
import { formatDateTime } from '@/utils/date'

export default {
  name: 'IncidentsNew',
  setup() {
    const router = useRouter()
    const loading = ref(false)
    const incidents = ref([])
    const statistics = ref({})
    
    const detailDialogVisible = ref(false)
    const createDialogVisible = ref(false)
    const notificationDialogVisible = ref(false)
    const selectedIncident = ref(null)
    const activeTab = ref('basic')
    const creating = ref(false)
    const incidentForm = ref(null)
    const addingProgress = ref(false)
    
    // 通知相关数据
    const notificationChannels = ref([])
    const userGroups = ref([])
    const notificationForm = reactive({
      channelIds: [],
      groupIds: [],
      message: ''
    })
    
    const progressForm = reactive({
      title: '',
      description: ''
    })
    
    // 分页数据
    const pagination = reactive({
      page: 1,
      per_page: 20,
      total: 0
    })
    
    const newIncident = reactive({
      title: '',
      description: '',
      severity: '',
      impact_scope: ''
    })
    
    const statusColumns = [
      { key: 'New', title: '新建', class: 'new' },
      { key: 'Pending', title: '待确认', class: 'pending' },
      { key: 'Investigating', title: '处理中', class: 'investigating' },
      { key: 'Recovering', title: '恢复中', class: 'recovering' },
      { key: 'Recovered', title: '已恢复', class: 'recovered' },
      { key: 'Post-Mortem', title: '待复盘', class: 'postmortem' },
      { key: 'Closed', title: '已关闭', class: 'closed' }
    ]
    
    const incidentRules = {
      title: [{ required: true, message: '请输入故障标题', trigger: 'blur' }],
      severity: [{ required: true, message: '请选择严重度', trigger: 'change' }]
    }
    
    // 计算属性
    const showUserGroupSelection = computed(() => {
      // 如果选择了需要用户信息的渠道（如邮件、短信、语音），则显示用户组选择
      return notificationForm.channelIds.some(channelId => {
        const channel = notificationChannels.value.find(c => c.id === channelId)
        return channel && ['EMAIL', 'SMS', 'VOICE_CALL'].includes(channel.type)
      })
    })
    
    // 加载数据
    const loadIncidents = async () => {
      loading.value = true
      try {
        const params = {
          page: pagination.page,
          per_page: pagination.per_page
        }
        const response = await request.get('/incidents-new', { params })
        incidents.value = response.incidents
        pagination.total = response.pagination?.total || 0
      } catch (error) {
        ElMessage.error('加载故障列表失败')
      } finally {
        loading.value = false
      }
    }
    
    const loadStatistics = async () => {
      try {
        const response = await request.get('/incidents-new/statistics')
        statistics.value = response
      } catch (error) {
        console.error('加载统计数据失败:', error)
      }
    }
    
    // 故障操作
    const showIncidentDetail = async (incident) => {
      try {
        const response = await request.get(`/incidents-new/${incident.id}`)
        selectedIncident.value = response.incident
        
        // 如果没有时间线数据，尝试单独获取
        if (!selectedIncident.value.timeline || selectedIncident.value.timeline.length === 0) {
          try {
            const timelineResponse = await request.get(`/incidents-new/${incident.id}/timeline`)
            selectedIncident.value.timeline = timelineResponse.timeline || []
          } catch (error) {
            console.error('获取时间线失败:', error)
            selectedIncident.value.timeline = []
          }
        }
        
        detailDialogVisible.value = true
        activeTab.value = 'basic'
      } catch (error) {
        ElMessage.error('加载故障详情失败')
      }
    }
    
    const createIncident = async () => {
      try {
        await incidentForm.value.validate()
        creating.value = true
        
        await request.post('/incidents-new', newIncident)
        ElMessage.success('故障创建成功')
        createDialogVisible.value = false
        resetNewIncident()
        loadIncidents()
        loadStatistics()
      } catch (error) {
        console.error('创建故障失败:', error)
        ElMessage.error('故障创建失败')
      } finally {
        creating.value = false
      }
    }
    
    const changeStatus = async (incident, newStatus) => {
      try {
        await ElMessageBox.confirm(`确定要将故障状态变更为"${getStatusText(newStatus)}"吗？`, '确认操作', {
          type: 'warning'
        })
        
        // 更新故障状态
        await request.put(`/incidents-new/${incident.id}/status`, {
          status: newStatus,
          comments: `状态变更为${getStatusText(newStatus)}`
        })
        
        // 如果是关闭故障，提示用户是否需要创建问题或改进措施
        if (newStatus === 'Closed') {
          await showPostCloseOptions(incident)
          // 关闭故障后不重新显示故障详情页，因为用户可能已经跳转到其他页面
          ElMessage.success('状态更新成功')
          loadIncidents()
          loadStatistics()
        } else {
          // 非关闭状态才显示故障详情页
          ElMessage.success('状态更新成功')
          // 重新加载故障详情以获取最新的时间线数据
          await showIncidentDetail(incident)
          loadIncidents()
          loadStatistics()
        }
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('状态更新失败')
        }
      }
    }
    
    // 添加处理进展
    const addProgress = async () => {
      if (!progressForm.title || !progressForm.description) {
        ElMessage.warning('请填写进展标题和详情')
        return
      }
      
      try {
        addingProgress.value = true
        
        // 添加进展记录到时间线
        await request.post(`/incidents-new/${selectedIncident.value.id}/progress`, {
          title: progressForm.title,
          description: progressForm.description
        })
        
        ElMessage.success('进展记录添加成功')
        
        // 清空表单
        progressForm.title = ''
        progressForm.description = ''
        
        // 刷新时间线数据
        try {
          const timelineResponse = await request.get(`/incidents-new/${selectedIncident.value.id}/timeline`)
          selectedIncident.value.timeline = timelineResponse.timeline || []
        } catch (error) {
          console.error('刷新时间线失败:', error)
        }
        
      } catch (error) {
        console.error('添加进展记录失败:', error)
        ElMessage.error('添加进展记录失败')
      } finally {
        addingProgress.value = false
      }
    }
    
    // 显示通知选择对话框
    const showNotificationDialog = async (incident) => {
      try {
        // 加载通知渠道
        const channelsResponse = await request.get('/notification/channels')
        // 后端直接返回数组，不需要.channels
        notificationChannels.value = channelsResponse || []
        
        if (notificationChannels.value.length === 0) {
          ElMessage.warning('没有可用的通知渠道，请先配置通知集成')
          return
        }
        
        // 加载用户组
        const groupsResponse = await request.get('/groups')
        userGroups.value = groupsResponse.groups || []
        
        // 重置表单
        notificationForm.channelIds = []
        notificationForm.groupIds = []
        notificationForm.message = `故障通知：${incident.title}\n\n状态：${getStatusText(incident.status)}\n描述：${incident.description || '无'}`
        
        // 保存当前故障信息
        selectedIncident.value = incident
        
        // 显示对话框
        notificationDialogVisible.value = true
        
      } catch (error) {
        ElMessage.error('加载通知配置失败')
      }
    }
    
    // 发送通知
    const sendNotification = async () => {
      try {
        if (notificationForm.channelIds.length === 0) {
          ElMessage.warning('请选择至少一个通知渠道')
          return
        }
        
        if (!notificationForm.message.trim()) {
          ElMessage.warning('请输入通知消息')
          return
        }
        
        // 检查是否需要选择用户组
        const needsUserGroup = notificationForm.channelIds.some(channelId => {
          const channel = notificationChannels.value.find(c => c.id === channelId)
          return channel && ['EMAIL', 'SMS', 'VOICE_CALL'].includes(channel.type)
        })
        
        if (needsUserGroup && notificationForm.groupIds.length === 0) {
          ElMessage.warning('选择的通知渠道需要指定用户组')
          return
        }
        
        // 发送通知
        await request.post('/notification/send', {
          incident_id: selectedIncident.value.id,
          channel_ids: notificationForm.channelIds,
          group_ids: notificationForm.groupIds,
          message: notificationForm.message
        })
        
        ElMessage.success('通知发送成功')
        notificationDialogVisible.value = false
        
      } catch (error) {
        ElMessage.error('发送通知失败')
      }
    }
    
    // 格式化通知渠道类型
    const formatChannelType = (type) => {
      const types = {
        EMAIL: '邮件',
        SMS: '短信',
        VOICE_CALL: '语音电话',
        WEBHOOK: 'Webhook',
        DINGTALK: '钉钉',
        TEAMS: '企业微信',
        SLACK: 'Slack'
      }
      return types[type] || type
    }
    
    // 显示故障关闭后的选项
    const showPostCloseOptions = async (incident) => {
      try {
        const result = await ElMessageBox.confirm(
          `故障"${incident.title}"已关闭。\n\n是否需要：\n1. 创建问题（用于跟踪根本原因）\n2. 创建改进措施（用于复盘总结）\n\n选择"确定"将跳转到问题管理页面，选择"取消"将跳转到复盘管理页面。`,
          '故障关闭后续操作',
          {
            confirmButtonText: '创建问题',
            cancelButtonText: '创建改进措施',
            type: 'info',
            distinguishCancelAndClose: true
          }
        )
        
        if (result === 'confirm') {
          // 跳转到问题管理页面，并传递故障信息
          ElMessage.info('即将跳转到问题管理页面')
          // 这里可以通过路由跳转或打开问题管理对话框
          showCreateProblemDialog(incident)
        } else if (result === 'cancel') {
          // 跳转到复盘管理页面，并传递故障信息
          ElMessage.info('即将跳转到复盘管理页面')
          showCreatePostMortemDialog(incident)
        }
      } catch (error) {
        // 用户关闭对话框，不做任何操作
      }
    }
    
    // 显示创建问题对话框
    const showCreateProblemDialog = async (incident) => {
      try {
        // 关闭故障详情对话框
        detailDialogVisible.value = false
        
        // 跳转到问题管理页面，并传递故障信息
        ElMessage.success(`正在跳转到问题管理页面，为故障"${incident.title}"创建问题记录`)
        
        // 使用路由跳转到问题管理页面，并传递故障ID参数
        router.push({
          path: '/problems',
          query: { 
            create_from_incident: incident.id,
            incident_title: incident.title,
            incident_description: incident.description
          }
        })
        
      } catch (error) {
        ElMessage.error('跳转到问题管理页面失败')
      }
    }
    
    // 显示创建复盘对话框
    const showCreatePostMortemDialog = async (incident) => {
      try {
        // 关闭故障详情对话框
        detailDialogVisible.value = false
        
        // 跳转到复盘管理页面，并传递故障信息
        ElMessage.success(`正在跳转到复盘管理页面，为故障"${incident.title}"创建复盘记录`)
        
        // 使用路由跳转到复盘管理页面，并传递故障ID参数
        router.push({
          path: '/postmortems',
          query: { 
            create_from_incident: incident.id,
            incident_title: incident.title,
            incident_description: incident.description
          }
        })
        
      } catch (error) {
        ElMessage.error('跳转到复盘管理页面失败')
      }
    }
    
    // 工具方法
    const getIncidentsByStatus = (status) => {
      return incidents.value.filter(incident => incident.status === status)
    }
    
    const getStatusCount = (status) => {
      return getIncidentsByStatus(status).length
    }
    
    const getP1Count = () => {
      return incidents.value.filter(incident => 
        incident.severity === 'P1' && incident.status !== 'Closed'
      ).length
    }
    
    const getSeverityTagType = (severity) => {
      const types = { P1: 'danger', P2: 'warning', P3: 'info', P4: 'success' }
      return types[severity] || ''
    }
    
    const getStatusTagType = (status) => {
      const types = {
        New: 'success',
        Pending: 'danger',
        Investigating: 'warning', 
        Recovering: 'primary',
        Recovered: 'success',
        'Post-Mortem': 'info',
        Closed: ''
      }
      return types[status] || ''
    }
    
    const getStatusText = (status) => {
      const texts = {
        New: '新建',
        Pending: '待确认',
        Investigating: '处理中',
        Recovering: '恢复中',
        Recovered: '已恢复',
        'Post-Mortem': '待复盘',
        Closed: '已关闭'
      }
      return texts[status] || status
    }
    
    const getActionText = (status) => {
      const actions = {
        New: '故障创建',
        Pending: '故障确认',
        Investigating: '开始处理',
        Recovering: '开始恢复',
        Recovered: '故障恢复',
        'Post-Mortem': '进入复盘',
        Closed: '故障关闭'
      }
      return actions[status] || `状态变更：${status}`
    }
    
    const getLevelTagType = (level) => {
      const types = { Critical: 'danger', Warning: 'warning', Info: 'info' }
      return types[level] || ''
    }
    
    const getLevelText = (level) => {
      const texts = { Critical: '严重', Warning: '警告', Info: '信息' }
      return texts[level] || level
    }
    
    const canChangeStatus = (incident, targetStatus) => {
      const validTransitions = {
        New: ['Pending', 'Investigating', 'Closed'],
        Pending: ['Investigating', 'Closed'],
        Investigating: ['Recovering', 'Closed'],
        Recovering: ['Recovered', 'Investigating'],
        Recovered: ['Post-Mortem', 'Investigating'],
        'Post-Mortem': ['Closed'],
        Closed: []
      }
      
      // 确保incident和status都存在
      if (!incident || !incident.status || !targetStatus) {
        return false
      }
      
      return validTransitions[incident.status]?.includes(targetStatus) || false
    }
    
    const showCreateDialog = () => {
      resetNewIncident()
      createDialogVisible.value = true
    }
    
    const resetNewIncident = () => {
      Object.assign(newIncident, {
        title: '',
        description: '',
        severity: '',
        impact_scope: ''
      })
    }
    
    const refreshIncidents = () => {
      loadIncidents()
      loadStatistics()
    }
    
    onMounted(() => {
      loadIncidents()
      loadStatistics()
    })
    
    return {
      loading,
      incidents,
      statistics,
      pagination,
      statusColumns,
      detailDialogVisible,
      createDialogVisible,
      selectedIncident,
      activeTab,
      creating,
      newIncident,
      incidentRules,
      incidentForm,
      addingProgress,
      progressForm,
      showIncidentDetail,
      createIncident,
      changeStatus,
      addProgress,
      getIncidentsByStatus,
      getStatusCount,
      getP1Count,
      getSeverityTagType,
      getStatusTagType,
      getStatusText,
      getActionText,
      getLevelTagType,
      getLevelText,
      canChangeStatus,
      showCreateDialog,
      refreshIncidents,
      formatDateTime,
      showPostCloseOptions,
      showCreateProblemDialog,
      showCreatePostMortemDialog,
      notificationDialogVisible,
      notificationChannels,
      userGroups,
      notificationForm,
      showUserGroupSelection,
      showNotificationDialog,
      sendNotification,
      formatChannelType
    }
  }
}
</script>

<style scoped>
.incidents-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.stats-cards {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-number {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
}

.stat-label {
  color: #666;
  font-size: 14px;
  margin-top: 5px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.unassigned {
  color: #999;
  font-style: italic;
}

.incident-board {
  background: #f5f5f5;
  padding: 20px;
  border-radius: 8px;
}

.board-column {
  background: white;
  border-radius: 8px;
  height: 600px;
  display: flex;
  flex-direction: column;
}

.column-header {
  padding: 15px;
  border-radius: 8px 8px 0 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: white;
}

.column-header.pending { background: #f56c6c; }
.column-header.investigating { background: #e6a23c; }
.column-header.recovering { background: #409eff; }
.column-header.recovered { background: #67c23a; }
.column-header.postmortem { background: #909399; }
.column-header.closed { background: #b3c0d1; }
.column-header.new { background: #67c23a; } /* Added New status color */

.column-header h3 {
  margin: 0;
  font-size: 16px;
}

.count {
  background: rgba(255, 255, 255, 0.3);
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
}

.column-content {
  flex: 1;
  padding: 10px;
  overflow-y: auto;
}

.incident-card {
  background: white;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 12px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.3s;
}

.incident-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.incident-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.incident-id {
  font-weight: bold;
  color: #409eff;
  font-size: 12px;
}

.incident-title {
  font-weight: 500;
  margin-bottom: 8px;
  font-size: 14px;
  line-height: 1.4;
}

.incident-meta {
  font-size: 12px;
  color: #666;
}

.assignee {
  margin-bottom: 4px;
}

.timeline-content h4 {
  margin: 0 0 5px 0;
  font-size: 14px;
}

.timeline-content p {
  margin: 0 0 5px 0;
  color: #666;
}

.action-buttons {
  border-top: 1px solid #e4e7ed;
  padding-top: 20px;
}
</style>