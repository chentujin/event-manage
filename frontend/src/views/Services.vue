<template>
  <div class="services">
    <div class="page-header">
      <h1>服务目录</h1>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        新增服务
      </el-button>
    </div>
    
    <!-- 筛选器 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters" class="filter-form">
        <el-form-item label="服务名称">
          <el-input 
            v-model="filters.name" 
            placeholder="请输入服务名称" 
            clearable 
            style="width: 200px"
            @keyup.enter="handleFilter"
          />
        </el-form-item>
        
        <el-form-item label="状态">
          <el-select v-model="filters.is_active" placeholder="全部状态" clearable style="width: 150px">
            <el-option label="活跃" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="负责团队">
          <el-input 
            v-model="filters.owner_team" 
            placeholder="请输入团队名称" 
            clearable 
            style="width: 200px"
            @keyup.enter="handleFilter"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleFilter">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card class="table-card">
      <el-table v-loading="loading" :data="servicesList" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="服务名称" min-width="200" />
        <el-table-column prop="description" label="描述" min-width="250" />
        <el-table-column prop="owner_team" label="负责团队" width="150" />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_active ? 'success' : 'danger'" size="small">
              {{ scope.row.is_active ? '活跃' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button type="text" size="small" @click="editService(scope.row)">编辑</el-button>
            <el-button type="text" size="small" class="danger" @click="deleteService(scope.row)">删除</el-button>
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
          @current-change="loadServices"
          @size-change="loadServices"
        />
      </div>
    </el-card>
    
    <!-- 新增/编辑服务对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form ref="formRef" :model="form" :rules="formRules" label-width="100px">
        <el-form-item label="服务名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入服务名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="form.description" type="textarea" placeholder="请输入服务描述" />
        </el-form-item>
        <el-form-item label="负责团队" prop="owner_team">
          <el-input v-model="form.owner_team" placeholder="请输入负责团队" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" active-text="活跃" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { services } from '@/api'

export default {
  name: 'Services',
  components: { Plus },
  setup() {
    const loading = ref(false)
    const submitting = ref(false)
    const servicesList = ref([])
    const dialogVisible = ref(false)
    const formRef = ref(null)
    const isEdit = ref(false)
    
    const filters = reactive({
      name: '',
      is_active: '',
      owner_team: ''
    })
    
    const pagination = reactive({
      page: 1,
      per_page: 20,
      total: 0
    })
    
    const form = reactive({
      id: null,
      name: '',
      description: '',
      owner_team: '',
      is_active: true
    })
    
    const formRules = {
      name: [
        { required: true, message: '请输入服务名称', trigger: 'blur' }
      ],
      description: [
        { required: true, message: '请输入服务描述', trigger: 'blur' }
      ],
      owner_team: [
        { required: true, message: '请输入负责团队', trigger: 'blur' }
      ]
    }
    
    const dialogTitle = computed(() => {
      return isEdit.value ? '编辑服务' : '新增服务'
    })
    
    const loadServices = async () => {
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
        
        const data = await services.list(params)
        servicesList.value = data.services || []
        pagination.total = data.total || 0
      } catch (error) {
        ElMessage.error('获取服务列表失败')
      } finally {
        loading.value = false
      }
    }
    
    const showCreateDialog = () => {
      isEdit.value = false
      resetForm()
      dialogVisible.value = true
    }
    
    const editService = (service) => {
      isEdit.value = true
      Object.assign(form, {
        id: service.id,
        name: service.name,
        description: service.description,
        owner_team: service.owner_team,
        is_active: service.is_active
      })
      dialogVisible.value = true
    }
    
    const resetForm = () => {
      Object.assign(form, {
        id: null,
        name: '',
        description: '',
        owner_team: '',
        is_active: true
      })
      formRef.value?.clearValidate()
    }
    
    const handleSubmit = async () => {
      try {
        const valid = await formRef.value?.validate()
        if (!valid) return
        
        submitting.value = true
        
        if (isEdit.value) {
          await services.update(form.id, form)
          ElMessage.success('服务更新成功')
        } else {
          await services.create(form)
          ElMessage.success('服务创建成功')
        }
        
        dialogVisible.value = false
        loadServices()
      } catch (error) {
        ElMessage.error(isEdit.value ? '服务更新失败' : '服务创建失败')
      } finally {
        submitting.value = false
      }
    }
    
    const deleteService = async (service) => {
      try {
        await ElMessageBox.confirm(`确定要删除服务“${service.name}”吗？`, '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        await services.delete(service.id)
        ElMessage.success('服务删除成功')
        loadServices()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('服务删除失败')
        }
      }
    }
    
    const handleFilter = () => {
      pagination.page = 1  // 重置到第一页
      loadServices()
    }
    
    const resetFilters = () => {
      Object.keys(filters).forEach(key => {
        filters[key] = ''
      })
      pagination.page = 1
      loadServices()
    }
    
    onMounted(() => {
      loadServices()
    })
    
    return {
      loading,
      submitting,
      servicesList,
      dialogVisible,
      dialogTitle,
      formRef,
      form,
      formRules,
      filters,
      pagination,
      loadServices,
      handleFilter,
      resetFilters,
      showCreateDialog,
      editService,
      handleSubmit,
      deleteService
    }
  }
}
</script>

<style scoped>
.services {
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

:deep(.el-button.danger) {
  color: #f56c6c;
}
</style>