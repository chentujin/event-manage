<template>
  <div class="dashboard">
    <div class="page-header">
      <h1>仪表盘</h1>
      <p>实时监控系统状态和关键指标</p>
    </div>
    
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon incidents">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ overview.incidents?.total || 0 }}</div>
              <div class="stat-label">总事件数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon open-incidents">
              <el-icon><CircleClose /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ overview.incidents?.open || 0 }}</div>
              <div class="stat-label">未解决事件</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon problems">
              <el-icon><Tools /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ overview.problems?.total || 0 }}</div>
              <div class="stat-label">总故障数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon services">
              <el-icon><Setting /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ overview.services?.total || 0 }}</div>
              <div class="stat-label">活跃服务</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 图表和列表 -->
    <el-row :gutter="20" class="content-row">
      <el-col :xs="24" :md="12">
        <el-card class="chart-card">
          <template #header>
            <span>事件状态分布</span>
          </template>
          <div class="chart-container">
            <canvas ref="chartRef" id="statusChart"></canvas>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :md="12">
        <el-card class="list-card">
          <template #header>
            <div class="card-header">
              <span>最近事件</span>
              <el-button type="text" @click="$router.push('/incidents')">
                查看全部
              </el-button>
            </div>
          </template>
          <div class="recent-incidents">
            <div v-if="recentIncidents.length === 0" class="empty-state">
              <el-empty description="暂无事件数据" />
            </div>
            <div v-else>
              <div
                v-for="incident in recentIncidents"
                :key="incident.id"
                class="incident-item"
              >
                <div class="incident-priority" :class="incident.priority.toLowerCase()">
                  {{ getPriorityText(incident.priority) }}
                </div>
                <div class="incident-info">
                  <div class="incident-title">{{ incident.title }}</div>
                  <div class="incident-meta">
                    <span>{{ getStatusText(incident.status) }}</span>
                    <span>{{ formatDate(incident.created_at) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Warning, CircleClose, Tools, Setting } from '@element-plus/icons-vue'
import { dashboard, incidents } from '@/api'
import dayjs from 'dayjs'
import {
  Chart,
  PieController,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

// 注册Chart.js组件
Chart.register(
  PieController,
  ArcElement,
  Title,
  Tooltip,
  Legend
)

export default {
  name: 'Dashboard',
  components: {
    Warning,
    CircleClose,
    Tools,
    Setting
  },
  setup() {
    const overview = ref({})
    const recentIncidents = ref([])
    const eventStatusData = ref({})
    const loading = ref(false)
    const chartRef = ref(null)
    let chartInstance = null
    
    const loadOverview = async () => {
      try {
        loading.value = true
        const data = await dashboard.overview()
        overview.value = data
      } catch (error) {
        ElMessage.error('获取概览数据失败')
      } finally {
        loading.value = false
      }
    }
    
    const loadRecentIncidents = async () => {
      try {
        const data = await incidents.list({ per_page: 5 })
        recentIncidents.value = data.incidents || []
      } catch (error) {
        console.error('获取最近事件失败:', error)
      }
    }
    
    const loadEventStatusData = async () => {
      try {
        const data = await dashboard.eventStatusDistribution()
        eventStatusData.value = data
        await nextTick()
        renderChart()
      } catch (error) {
        console.error('获取事件状态分布数据失败:', error)
      }
    }
    
    const renderChart = () => {
      if (!chartRef.value || !eventStatusData.value.incident_distribution) return
      
      const ctx = chartRef.value.getContext('2d')
      
      // 销毁之前的图表实例
      if (chartInstance) {
        chartInstance.destroy()
      }
      
      const incidentData = eventStatusData.value.incident_distribution
      
      chartInstance = new Chart(ctx, {
        type: 'pie',
        data: {
          labels: incidentData.map(item => item.name),
          datasets: [{
            data: incidentData.map(item => item.value),
            backgroundColor: incidentData.map(item => item.color),
            borderWidth: 2,
            borderColor: '#fff'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: {
              display: true,
              text: '事件状态分布',
              font: {
                size: 16
              }
            },
            legend: {
              position: 'bottom',
              labels: {
                padding: 20,
                usePointStyle: true,
                font: {
                  size: 12
                }
              }
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  const label = context.label || ''
                  const value = context.parsed
                  const total = context.dataset.data.reduce((sum, val) => sum + val, 0)
                  const percentage = ((value / total) * 100).toFixed(1)
                  return `${label}: ${value} (${percentage}%)`
                }
              }
            }
          }
        }
      })
    }
    
    const formatDate = (dateStr) => {
      return dayjs(dateStr).format('MM-DD HH:mm')
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
    
    onMounted(() => {
      loadOverview()
      loadRecentIncidents()
      loadEventStatusData()
    })
    
    return {
      overview,
      recentIncidents,
      eventStatusData,
      loading,
      chartRef,
      formatDate,
      getPriorityText,
      getStatusText
    }
  }
}
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  color: #303133;
  font-size: 28px;
}

.page-header p {
  margin: 5px 0 0 0;
  color: #909399;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
  margin-right: 15px;
}

.stat-icon.incidents {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.open-incidents {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.problems {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.services {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 5px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.content-row {
  margin-bottom: 20px;
}

.chart-card,
.list-card {
  height: 400px;
}

.chart-container {
  height: 300px;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-container canvas {
  max-height: 100%;
}

.chart-placeholder {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recent-incidents {
  height: 300px;
  overflow-y: auto;
}

.empty-state {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.incident-item {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.incident-item:last-child {
  border-bottom: none;
}

.incident-priority {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  color: #fff;
  margin-right: 12px;
  min-width: 60px;
  text-align: center;
}

.incident-priority.critical {
  background: #f56c6c;
}

.incident-priority.high {
  background: #e6a23c;
}

.incident-priority.medium {
  background: #409eff;
}

.incident-priority.low {
  background: #67c23a;
}

.incident-info {
  flex: 1;
}

.incident-title {
  font-size: 14px;
  color: #303133;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.incident-meta {
  font-size: 12px;
  color: #909399;
}

.incident-meta span {
  margin-right: 12px;
}
</style>