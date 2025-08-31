<template>
  <div class="alerts-page">
    <!-- 页面标题和操作栏 -->
    <div class="page-header">
      <h1>告警管理</h1>
      <div class="actions">
        <el-button type="primary" @click="refreshAlerts">刷新</el-button>
        <el-button type="danger" @click="batchIgnore" :disabled="selectedAlerts.length === 0">
          批量忽略
        </el-button>
      </div>
    </div>

    <!-- 筛选条件 -->
    <div class="filters">
      <el-row :gutter="20">
        <el-col :span="4">
          <el-select v-model="filters.status" placeholder="状态" @change="loadAlerts">
            <el-option label="全部" value=""></el-option>
            <el-option label="新建" value="New"></el-option>
            <el-option label="已确认" value="Acknowledged"></el-option>
            <el-option label="已关联" value="Linked"></el-option>
            <el-option label="已忽略" value="Ignored"></el-option>
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.level" placeholder="级别" @change="loadAlerts">
            <el-option label="全部" value=""></el-option>
            <el-option label="严重" value="Critical"></el-option>
            <el-option label="警告" value="Warning"></el-option>
            <el-option label="信息" value="Info"></el-option>
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.environment" placeholder="环境" @change="loadAlerts">
            <el-option label="全部" value=""></el-option>
            <el-option label="生产" value="Production"></el-option>
            <el-option label="预发" value="Staging"></el-option>
            <el-option label="开发" value="Development"></el-option>
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-checkbox v-model="filters.unlinked" @change="loadAlerts">
            仅显示未关联
          </el-checkbox>
        </el-col>
      </el-row>
    </div>

    <!-- 告警列表 -->
    <el-table
      :data="alerts"
      v-loading="loading"
      @selection-change="handleSelectionChange"
      style="width: 100%">
      
      <el-table-column type="selection" width="55"></el-table-column>
      
      <el-table-column prop="level" label="级别" width="80">
        <template #default="scope">
          <el-tag 
            :type="getLevelTagType(scope.row.level)"
            size="small">
            {{ getLevelText(scope.row.level) }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="title" label="标题" min-width="200">
        <template #default="scope">
          <div class="alert-title" @click="showAlertDetail(scope.row)">
            {{ scope.row.title }}
          </div>
        </template>
      </el-table-column>
      
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag 
            :type="getStatusTagType(scope.row.status)"
            size="small">
            {{ getStatusText(scope.row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="alert_source" label="来源" width="120"></el-table-column>
      
      <el-table-column prop="environment" label="环境" width="80"></el-table-column>
      
      <el-table-column prop="incident_id" label="关联故障ID" width="120">
        <template #default="scope">
          <span v-if="scope.row.incident_id" class="incident-link">
            {{ scope.row.incident_id }}
          </span>
          <span v-else class="no-incident">未关联</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="fired_at" label="触发时间" width="180">
        <template #default="scope">
          {{ formatDateTime(scope.row.fired_at) }}
        </template>
      </el-table-column>
      
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button-group>
            <el-button 
              v-if="scope.row.status === 'New'"
              size="small" 
              type="primary" 
              @click="acknowledgeAlert(scope.row)">
              确认
            </el-button>
            <el-button 
              v-if="scope.row.status !== 'Linked'"
              size="small" 
              @click="linkToIncident(scope.row)">
              关联故障
            </el-button>
            <el-button 
              v-if="scope.row.status !== 'Ignored'"
              size="small" 
              type="warning" 
              @click="ignoreAlert(scope.row)">
              忽略
            </el-button>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange">
      </el-pagination>
    </div>

    <!-- 告警详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="告警详情" width="60%">
      <div v-if="selectedAlert">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="告警ID">{{ selectedAlert.id }}</el-descriptions-item>
          <el-descriptions-item label="级别">
            <el-tag :type="getLevelTagType(selectedAlert.level)">
              {{ getLevelText(selectedAlert.level) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTagType(selectedAlert.status)">
              {{ getStatusText(selectedAlert.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="来源">{{ selectedAlert.alert_source || '-' }}</el-descriptions-item>
          <el-descriptions-item label="规则">{{ selectedAlert.alert_rule || '-' }}</el-descriptions-item>
          <el-descriptions-item label="环境">{{ selectedAlert.environment || '-' }}</el-descriptions-item>
          <el-descriptions-item label="主机">{{ selectedAlert.host || '-' }}</el-descriptions-item>
          <el-descriptions-item label="指标">{{ selectedAlert.metric_name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="指标值">{{ selectedAlert.metric_value || '-' }}</el-descriptions-item>
          <el-descriptions-item label="阈值">{{ selectedAlert.threshold || '-' }}</el-descriptions-item>
          <el-descriptions-item label="触发时间" :span="2">
            {{ formatDateTime(selectedAlert.fired_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">
            {{ selectedAlert.description || '-' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>

    <!-- 关联故障对话框 -->
    <el-dialog v-model="linkDialogVisible" title="关联故障" width="60%">
      <div class="link-incident-form">
        <el-form :model="linkForm" label-width="100px">
          <el-form-item label="选择故障">
            <el-select 
              v-model="linkForm.incident_id" 
              placeholder="请选择要关联的故障"
              filterable
              style="width: 100%">
              <el-option
                v-for="incident in availableIncidents"
                :key="incident.id"
                :label="`${incident.incident_id} - ${incident.title}`"
                :value="incident.id">
                <div class="incident-option">
                  <div class="incident-id">{{ incident.incident_id }}</div>
                  <div class="incident-title">{{ incident.title }}</div>
                  <div class="incident-status">
                    <el-tag :type="getIncidentStatusType(incident.status)" size="small">
                      {{ getIncidentStatusText(incident.status) }}
                    </el-tag>
                  </div>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
          <el-form-item label="关联说明">
            <el-input 
              v-model="linkForm.link_reason" 
              type="textarea" 
              :rows="3"
              placeholder="请输入关联原因或说明">
            </el-input>
          </el-form-item>
        </el-form>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="linkDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmLinkIncident" :loading="linking">
            确认关联
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/utils/request'
import { formatDateTime } from '@/utils/date'

export default {
  name: 'Alerts',
  setup() {
    const loading = ref(false)
    const alerts = ref([])
    const selectedAlerts = ref([])
    const currentPage = ref(1)
    const pageSize = ref(20)
    const total = ref(0)
    
    const detailDialogVisible = ref(false)
    const selectedAlert = ref(null)
    
    // 关联故障相关
    const linkDialogVisible = ref(false)
    const availableIncidents = ref([])
    const linking = ref(false)
    const linkForm = reactive({
      incident_id: null,
      link_reason: ''
    })
    const currentAlert = ref(null)
    
    const filters = reactive({
      status: '',
      level: '',
      environment: '',
      unlinked: false
    })
    
    // 加载告警列表
    const loadAlerts = async () => {
      loading.value = true
      try {
        const params = {
          page: currentPage.value,
          per_page: pageSize.value,
          ...filters
        }
        const response = await request.get('/alerts', { params })
        alerts.value = response.alerts
        total.value = response.total
      } catch (error) {
        ElMessage.error('加载告警列表失败')
      } finally {
        loading.value = false
      }
    }
    
    // 确认告警
    const acknowledgeAlert = async (alert) => {
      try {
        await request.put(`/alerts/${alert.id}/acknowledge`)
        ElMessage.success('告警已确认')
        loadAlerts()
      } catch (error) {
        ElMessage.error('确认告警失败')
      }
    }
    
    // 忽略告警
    const ignoreAlert = async (alert) => {
      try {
        await ElMessageBox.confirm('确定要忽略这个告警吗？', '确认', {
          type: 'warning'
        })
        await request.put(`/alerts/${alert.id}/ignore`)
        ElMessage.success('告警已忽略')
        loadAlerts()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('忽略告警失败')
        }
      }
    }
    
    // 关联到故障
    const linkToIncident = async (alert) => {
      try {
        currentAlert.value = alert
        linkForm.incident_id = null
        linkForm.link_reason = ''
        
        // 加载可用的故障列表
        await loadAvailableIncidents()
        
        linkDialogVisible.value = true
      } catch (error) {
        ElMessage.error('加载故障列表失败')
      }
    }

    // 加载可用的故障列表
    const loadAvailableIncidents = async () => {
      try {
        const response = await request.get('/incidents-new', {
          params: {
            page: 1,
            per_page: 100,
            status: 'Pending,Investigating,Recovering,Recovered'
          }
        })
        availableIncidents.value = response.incidents || []
      } catch (error) {
        console.error('加载故障列表失败:', error)
        throw error
      }
    }

    // 确认关联故障
    const confirmLinkIncident = async () => {
      if (!linkForm.incident_id) {
        ElMessage.warning('请选择要关联的故障')
        return
      }

      try {
        linking.value = true
        
        // 调用API关联故障
        await request.put(`/alerts/${currentAlert.value.id}/link`, {
          incident_id: linkForm.incident_id,
          link_reason: linkForm.link_reason
        })

        ElMessage.success('故障关联成功')
        linkDialogVisible.value = false
        
        // 刷新告警列表
        await loadAlerts()
      } catch (error) {
        ElMessage.error('故障关联失败')
      } finally {
        linking.value = false
      }
    }

    // 获取故障状态类型
    const getIncidentStatusType = (status) => {
      const types = {
        'Pending': 'warning',
        'Investigating': 'primary',
        'Recovering': 'info',
        'Recovered': 'success',
        'Post-Mortem': 'warning',
        'Closed': 'info'
      }
      return types[status] || ''
    }

    // 获取故障状态文本
    const getIncidentStatusText = (status) => {
      const texts = {
        'Pending': '待确认',
        'Investigating': '处理中',
        'Recovering': '恢复中',
        'Recovered': '已恢复',
        'Post-Mortem': '待复盘',
        'Closed': '已关闭'
      }
      return texts[status] || status
    }
    
    // 批量忽略
    const batchIgnore = async () => {
      try {
        await ElMessageBox.confirm(`确定要忽略选中的 ${selectedAlerts.value.length} 个告警吗？`, '确认', {
          type: 'warning'
        })
        
        const alertIds = selectedAlerts.value.map(alert => alert.id)
        await request.put('/alerts/batch', {
          alert_ids: alertIds,
          action: 'ignore'
        })
        
        ElMessage.success('批量忽略成功')
        loadAlerts()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('批量忽略失败')
        }
      }
    }
    
    // 工具方法
    const getLevelTagType = (level) => {
      const types = {
        Critical: 'danger',
        Warning: 'warning',
        Info: 'info'
      }
      return types[level] || ''
    }
    
    const getLevelText = (level) => {
      const texts = {
        Critical: '严重',
        Warning: '警告',
        Info: '信息'
      }
      return texts[level] || level
    }
    
    const getStatusTagType = (status) => {
      const types = {
        New: 'danger',
        Acknowledged: 'warning',
        Linked: 'success',
        Ignored: 'info'
      }
      return types[status] || ''
    }
    
    const getStatusText = (status) => {
      const texts = {
        New: '新建',
        Acknowledged: '已确认',
        Linked: '已关联',
        Ignored: '已忽略'
      }
      return texts[status] || status
    }
    
    const showAlertDetail = (alert) => {
      selectedAlert.value = alert
      detailDialogVisible.value = true
    }
    
    const refreshAlerts = () => {
      loadAlerts()
    }
    
    const handleSelectionChange = (selection) => {
      selectedAlerts.value = selection
    }
    
    const handleSizeChange = (size) => {
      pageSize.value = size
      loadAlerts()
    }
    
    const handleCurrentChange = (page) => {
      currentPage.value = page
      loadAlerts()
    }
    
    onMounted(() => {
      loadAlerts()
    })
    
    return {
      loading,
      alerts,
      selectedAlerts,
      currentPage,
      pageSize,
      total,
      filters,
      detailDialogVisible,
      selectedAlert,
      loadAlerts,
      acknowledgeAlert,
      ignoreAlert,
      linkToIncident,
      batchIgnore,
      getLevelTagType,
      getLevelText,
      getStatusTagType,
      getStatusText,
      showAlertDetail,
      refreshAlerts,
      handleSelectionChange,
      handleSizeChange,
      handleCurrentChange,
      formatDateTime,
      linkDialogVisible,
      availableIncidents,
      linking,
      linkForm,
      confirmLinkIncident,
      getIncidentStatusType,
      getIncidentStatusText
    }
  }
}
</script>

<style scoped>
.alerts-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.filters {
  margin-bottom: 20px;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 4px;
}

.alert-title {
  color: #409eff;
  cursor: pointer;
}

.alert-title:hover {
  text-decoration: underline;
}

.incident-link {
  color: #409eff;
  font-weight: bold;
}

.no-incident {
  color: #999;
  font-style: italic;
}

.link-incident-form {
  padding: 20px 0;
}

.incident-option {
  display: flex;
  align-items: center;
  gap: 12px;
}

.incident-id {
  font-weight: bold;
  color: #409eff;
  min-width: 120px;
}

.incident-title {
  flex: 1;
  color: #333;
}

.incident-status {
  min-width: 80px;
  text-align: right;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}
</style>