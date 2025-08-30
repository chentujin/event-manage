<template>
  <div class="notifications">
    <div class="page-header">
      <h1>通知集成</h1>
      <el-button type="primary" @click="showTestDialog">
        <el-icon><Message /></el-icon>
        测试通知
      </el-button>
    </div>
    
    <!-- 通知配置 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card class="config-card">
          <template #header>
            <span>通知渠道配置</span>
          </template>
          
          <el-table :data="channelsList" v-loading="loading">
            <el-table-column prop="name" label="渠道名称" />
            <el-table-column prop="type" label="类型" width="120">
              <template #default="scope">
                <el-tag :type="getChannelTypeColor(scope.row.type)" size="small">
                  {{ formatChannelType(scope.row.type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="is_active" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.is_active ? 'success' : 'danger'" size="small">
                  {{ scope.row.is_active ? '启用' : '禁用' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="150">
              <template #default="scope">
                <el-button type="text" size="small" @click="editChannel(scope.row)">配置</el-button>
                <el-button type="text" size="small" @click="testChannel(scope.row)">测试</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card class="config-card">
          <template #header>
            <span>个人通知偏好</span>
          </template>
          
          <el-form :model="preferences" label-width="120px">
            <el-form-item label="邮件通知">
              <el-switch v-model="preferences.email" @change="updatePreferences" />
            </el-form-item>
            <el-form-item label="短信通知">
              <el-switch v-model="preferences.sms" @change="updatePreferences" />
            </el-form-item>
            <el-form-item label="语音电话">
              <el-switch v-model="preferences.voice_call" @change="updatePreferences" />
            </el-form-item>
            <el-form-item label="Webhook">
              <el-switch v-model="preferences.webhook" @change="updatePreferences" />
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 通知日志 -->
    <el-card class="log-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>通知日志</span>
          <el-button type="text" @click="loadNotificationLogs">刷新</el-button>
        </div>
      </template>
      
      <el-table :data="logsList" v-loading="logsLoading">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="trigger_event" label="触发事件" width="150" />
        <el-table-column prop="channel_type" label="通知渠道" width="120">
          <template #default="scope">
            <el-tag size="small">{{ formatChannelType(scope.row.channel_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target_user_id" label="目标用户" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.status === 'SUCCESS' ? 'success' : 'danger'" size="small">
              {{ scope.row.status === 'SUCCESS' ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="发送时间" width="160">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="scope">
            <el-button type="text" size="small" @click="viewLogDetail(scope.row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 测试通知对话框 -->
    <el-dialog v-model="testDialogVisible" title="测试通知" width="500px">
      <el-form :model="testForm" label-width="120px">
        <el-form-item label="通知类型">
          <el-select v-model="testForm.channel_type" placeholder="请选择通知类型">
            <el-option label="邮件" value="EMAIL" />
            <el-option label="短信" value="SMS" />
            <el-option label="语音电话" value="VOICE_CALL" />
            <el-option label="Webhook" value="WEBHOOK" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标用户">
          <el-input v-model="testForm.target" placeholder="邮箱或手机号" />
        </el-form-item>
        <el-form-item label="测试消息">
          <el-input v-model="testForm.message" type="textarea" placeholder="测试消息内容" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="testDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="sendTestNotification" :loading="testing">发送测试</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 通知渠道配置对话框 -->
    <el-dialog v-model="configDialogVisible" :title="configDialogTitle" width="600px">
      <el-form ref="configFormRef" :model="configForm" :rules="configRules" label-width="120px">
        <el-form-item label="渠道名称" prop="name">
          <el-input v-model="configForm.name" placeholder="请输入渠道名称" />
        </el-form-item>
        <el-form-item label="渠道类型">
          <el-select v-model="configForm.type" disabled>
            <el-option :label="formatChannelType(configForm.type)" :value="configForm.type" />
          </el-select>
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="configForm.is_active" />
        </el-form-item>
        
        <!-- 邮件配置 -->
        <template v-if="configForm.type === 'EMAIL'">
          <el-divider content-position="left">邮件服务器配置</el-divider>
          <el-form-item label="SMTP服务器" prop="smtp_host">
            <el-input v-model="configForm.config.smtp_host" placeholder="smtp.example.com" />
          </el-form-item>
          <el-form-item label="SMTP端口" prop="smtp_port">
            <el-input-number v-model="configForm.config.smtp_port" :min="1" :max="65535" placeholder="587" />
          </el-form-item>
          <el-form-item label="发件人邮箱" prop="from_email">
            <el-input v-model="configForm.config.from_email" placeholder="noreply@example.com" />
          </el-form-item>
          <el-form-item label="用户名" prop="smtp_username">
            <el-input v-model="configForm.config.smtp_username" placeholder="SMTP用户名" />
          </el-form-item>
          <el-form-item label="密码" prop="smtp_password">
            <el-input v-model="configForm.config.smtp_password" type="password" placeholder="SMTP密码" show-password />
          </el-form-item>
          <el-form-item label="启用TLS">
            <el-switch v-model="configForm.config.use_tls" />
          </el-form-item>
        </template>
        
        <!-- 短信配置 -->
        <template v-if="configForm.type === 'SMS'">
          <el-divider content-position="left">短信服务配置</el-divider>
          <el-form-item label="服务商" prop="provider">
            <el-select v-model="configForm.config.provider" placeholder="请选择短信服务商">
              <el-option label="阿里云短信" value="aliyun" />
              <el-option label="腾讯云短信" value="tencent" />
              <el-option label="华为云短信" value="huawei" />
            </el-select>
          </el-form-item>
          <el-form-item label="Access Key" prop="access_key">
            <el-input v-model="configForm.config.access_key" placeholder="请输入Access Key" />
          </el-form-item>
          <el-form-item label="Secret Key" prop="secret_key">
            <el-input v-model="configForm.config.secret_key" type="password" placeholder="请输入Secret Key" show-password />
          </el-form-item>
          <el-form-item label="短信签名" prop="sign_name">
            <el-input v-model="configForm.config.sign_name" placeholder="请输入短信签名" />
          </el-form-item>
          <el-form-item label="模板ID" prop="template_id">
            <el-input v-model="configForm.config.template_id" placeholder="请输入短信模板ID" />
          </el-form-item>
        </template>
        
        <!-- 语音电话配置 -->
        <template v-if="configForm.type === 'VOICE_CALL'">
          <el-divider content-position="left">语音服务配置</el-divider>
          <el-form-item label="服务商" prop="provider">
            <el-select v-model="configForm.config.provider" placeholder="请选择语音服务商">
              <el-option label="阿里云语音" value="aliyun" />
              <el-option label="腾讯云语音" value="tencent" />
            </el-select>
          </el-form-item>
          <el-form-item label="Access Key" prop="access_key">
            <el-input v-model="configForm.config.access_key" placeholder="请输入Access Key" />
          </el-form-item>
          <el-form-item label="Secret Key" prop="secret_key">
            <el-input v-model="configForm.config.secret_key" type="password" placeholder="请输入Secret Key" show-password />
          </el-form-item>
          <el-form-item label="语音模板" prop="voice_template">
            <el-input v-model="configForm.config.voice_template" placeholder="请输入语音模板内容" />
          </el-form-item>
        </template>
        
        <!-- Webhook配置 -->
        <template v-if="configForm.type === 'WEBHOOK'">
          <el-divider content-position="left">Webhook配置</el-divider>
          <el-form-item label="Webhook URL" prop="webhook_url">
            <el-input v-model="configForm.config.webhook_url" placeholder="https://example.com/webhook" />
          </el-form-item>
          <el-form-item label="请求方法" prop="method">
            <el-select v-model="configForm.config.method" placeholder="请选择请求方法">
              <el-option label="POST" value="POST" />
              <el-option label="PUT" value="PUT" />
            </el-select>
          </el-form-item>
          <el-form-item label="请求头">
            <el-input v-model="configForm.config.headers" type="textarea" placeholder='示例: {"Content-Type": "application/json", "Authorization": "Bearer token"}' :rows="3" />
          </el-form-item>
          <el-form-item label="超时时间(秒)" prop="timeout">
            <el-input-number v-model="configForm.config.timeout" :min="1" :max="60" placeholder="30" />
          </el-form-item>
        </template>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="configDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSaveConfig" :loading="configLoading">保存配置</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Message } from '@element-plus/icons-vue'
import { notifications } from '@/api'
import dayjs from 'dayjs'

export default {
  name: 'Notifications',
  components: { Message },
  setup() {
    const loading = ref(false)
    const logsLoading = ref(false)
    const testing = ref(false)
    const configLoading = ref(false)
    const channelsList = ref([])
    const logsList = ref([])
    const testDialogVisible = ref(false)
    const configDialogVisible = ref(false)
    const configFormRef = ref(null)
    const currentEditingChannel = ref(null)
    
    const preferences = reactive({
      email: true,
      sms: false,
      voice_call: false,
      webhook: false
    })
    
    const testForm = reactive({
      channel_type: '',
      target: '',
      message: '这是一条测试通知消息'
    })
    
    const configForm = reactive({
      id: null,
      name: '',
      type: '',
      is_active: true,
      config: {
        // 邮件配置
        smtp_host: '',
        smtp_port: 587,
        from_email: '',
        smtp_username: '',
        smtp_password: '',
        use_tls: true,
        // 短信/语音配置
        provider: '',
        access_key: '',
        secret_key: '',
        sign_name: '',
        template_id: '',
        voice_template: '',
        // Webhook配置
        webhook_url: '',
        method: 'POST',
        headers: '',
        timeout: 30
      }
    })
    
    const configRules = {
      name: [
        { required: true, message: '请输入渠道名称', trigger: 'blur' }
      ],
      smtp_host: [
        { required: true, message: '请输入SMTP服务器地址', trigger: 'blur' }
      ],
      smtp_port: [
        { required: true, message: '请输入SMTP端口', trigger: 'blur' }
      ],
      from_email: [
        { required: true, message: '请输入发件人邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
      ],
      provider: [
        { required: true, message: '请选择服务商', trigger: 'change' }
      ],
      access_key: [
        { required: true, message: '请输入Access Key', trigger: 'blur' }
      ],
      secret_key: [
        { required: true, message: '请输入Secret Key', trigger: 'blur' }
      ],
      webhook_url: [
        { required: true, message: '请输入Webhook URL', trigger: 'blur' },
        { type: 'url', message: '请输入正确的URL地址', trigger: 'blur' }
      ]
    }
    
    const configDialogTitle = computed(() => {
      return configForm.id ? `配置${configForm.name}` : '新增通知渠道'
    })
    
    const loadChannels = async () => {
      try {
        loading.value = true
        // 模拟数据，实际应该从API获取
        channelsList.value = [
          { id: 1, name: '系统邮件', type: 'EMAIL', is_active: true },
          { id: 2, name: '短信通知', type: 'SMS', is_active: false },
          { id: 3, name: '语音告警', type: 'VOICE_CALL', is_active: true },
          { id: 4, name: 'Webhook集成', type: 'WEBHOOK', is_active: true }
        ]
      } catch (error) {
        ElMessage.error('获取通知渠道失败')
      } finally {
        loading.value = false
      }
    }
    
    const loadNotificationLogs = async () => {
      try {
        logsLoading.value = true
        // 模拟数据，实际应该从API获取
        logsList.value = [
          {
            id: 1,
            trigger_event: 'incident_created',
            channel_type: 'EMAIL',
            target_user_id: 1,
            status: 'SUCCESS',
            created_at: new Date().toISOString()
          },
          {
            id: 2,
            trigger_event: 'problem_approved',
            channel_type: 'SMS',
            target_user_id: 2,
            status: 'FAILED',
            created_at: new Date(Date.now() - 3600000).toISOString()
          }
        ]
      } catch (error) {
        ElMessage.error('获取通知日志失败')
      } finally {
        logsLoading.value = false
      }
    }
    
    const getChannelTypeColor = (type) => {
      const colors = {
        'EMAIL': 'primary',
        'SMS': 'success',
        'VOICE_CALL': 'warning',
        'WEBHOOK': 'info'
      }
      return colors[type] || 'info'
    }
    
    const formatChannelType = (type) => {
      const types = {
        'EMAIL': '邮件',
        'SMS': '短信',
        'VOICE_CALL': '语音电话',
        'WEBHOOK': 'Webhook'
      }
      return types[type] || type
    }
    
    const formatDate = (dateStr) => {
      return dayjs(dateStr).format('YYYY-MM-DD HH:mm:ss')
    }
    
    const showTestDialog = () => {
      testDialogVisible.value = true
    }
    
    const editChannel = (channel) => {
      currentEditingChannel.value = channel
      // 设置表单默认值
      Object.assign(configForm, {
        id: channel.id,
        name: channel.name,
        type: channel.type,
        is_active: channel.is_active,
        config: {
          // 初始化配置，实际中应该从后端获取
          smtp_host: channel.config?.smtp_host || '',
          smtp_port: channel.config?.smtp_port || 587,
          from_email: channel.config?.from_email || '',
          smtp_username: channel.config?.smtp_username || '',
          smtp_password: '',  // 出于安全考虑，不显示原密码
          use_tls: channel.config?.use_tls !== false,
          provider: channel.config?.provider || '',
          access_key: channel.config?.access_key || '',
          secret_key: '',  // 出于安全考虑，不显示原密码
          sign_name: channel.config?.sign_name || '',
          template_id: channel.config?.template_id || '',
          voice_template: channel.config?.voice_template || '',
          webhook_url: channel.config?.webhook_url || '',
          method: channel.config?.method || 'POST',
          headers: channel.config?.headers ? JSON.stringify(channel.config.headers, null, 2) : '',
          timeout: channel.config?.timeout || 30
        }
      })
      configDialogVisible.value = true
    }
    
    const testChannel = (channel) => {
      testForm.channel_type = channel.type
      testDialogVisible.value = true
    }
    
    const sendTestNotification = async () => {
      try {
        testing.value = true
        // 实际应该调用API发送测试通知
        await new Promise(resolve => setTimeout(resolve, 1000))
        ElMessage.success('测试通知发送成功')
        testDialogVisible.value = false
      } catch (error) {
        ElMessage.error('测试通知发送失败')
      } finally {
        testing.value = false
      }
    }
    
    const updatePreferences = async () => {
      try {
        // 实际应该调用API更新偏好设置
        ElMessage.success('通知偏好已更新')
      } catch (error) {
        ElMessage.error('更新通知偏好失败')
      }
    }
    
    const handleSaveConfig = async () => {
      if (!configFormRef.value) return
      
      try {
        const valid = await configFormRef.value.validate()
        if (!valid) return
        
        configLoading.value = true
        
        // 准备保存的数据
        const configData = {
          id: configForm.id,
          name: configForm.name,
          type: configForm.type,
          is_active: configForm.is_active,
          config: { ...configForm.config }
        }
        
        // 处理headers格式
        if (configForm.type === 'WEBHOOK' && configForm.config.headers) {
          try {
            configData.config.headers = JSON.parse(configForm.config.headers)
          } catch (e) {
            ElMessage.error('请求头格式不正确，请输入有效的JSON格式')
            return
          }
        }
        
        // 调用API保存配置
        // await notifications.updateChannel(configData)
        
        // 模拟保存成功
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        // 更新本地数据
        const channelIndex = channelsList.value.findIndex(c => c.id === configForm.id)
        if (channelIndex !== -1) {
          channelsList.value[channelIndex] = {
            ...channelsList.value[channelIndex],
            name: configForm.name,
            is_active: configForm.is_active,
            config: configData.config
          }
        }
        
        ElMessage.success('通知渠道配置保存成功')
        configDialogVisible.value = false
        
      } catch (error) {
        ElMessage.error('保存配置失败')
      } finally {
        configLoading.value = false
      }
    }
    
    const viewLogDetail = (log) => {
      ElMessage.info('查看日志详情功能开发中')
    }
    
    onMounted(() => {
      loadChannels()
      loadNotificationLogs()
    })
    
    return {
      loading,
      logsLoading,
      testing,
      configLoading,
      channelsList,
      logsList,
      testDialogVisible,
      configDialogVisible,
      configFormRef,
      configDialogTitle,
      preferences,
      testForm,
      configForm,
      configRules,
      getChannelTypeColor,
      formatChannelType,
      formatDate,
      showTestDialog,
      editChannel,
      testChannel,
      sendTestNotification,
      updatePreferences,
      handleSaveConfig,
      viewLogDetail,
      loadNotificationLogs
    }
  }
}
</script>

<style scoped>
.notifications {
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

.config-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.log-card {
  margin-top: 20px;
}
</style>