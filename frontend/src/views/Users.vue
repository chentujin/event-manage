<template>
  <div class="users">
    <div class="page-header">
      <h1>用户管理</h1>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        新建用户
      </el-button>
    </div>
    
    <el-tabs v-model="activeTab" class="user-tabs">
      <el-tab-pane label="用户列表" name="users">
        <el-card>
      <!-- 搜索和筛选 -->
      <el-row :gutter="20" class="search-bar">
        <el-col :span="8">
          <el-input
            v-model="searchForm.keyword"
            placeholder="搜索用户名或邮箱"
            @keyup.enter="loadUsers"
          >
            <template #prepend>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="6">
          <el-select v-model="searchForm.status" placeholder="用户状态" clearable>
            <el-option label="全部" value="" />
            <el-option label="激活" value="true" />
            <el-option label="禁用" value="false" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="primary" @click="loadUsers">搜索</el-button>
        </el-col>
      </el-row>
      
      <!-- 用户列表 -->
      <el-table v-loading="loading" :data="usersList" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column prop="real_name" label="真实姓名" width="120" />
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column prop="department" label="部门" width="120" />
        <el-table-column label="角色" width="150">
          <template #default="scope">
            <el-tag
              v-for="role in scope.row.roles"
              :key="role"
              size="small"
              style="margin-right: 5px;"
            >
              {{ getRoleText(role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_active ? 'success' : 'danger'" size="small">
              {{ scope.row.is_active ? '活跃' : '禁用' }}
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
            <el-button type="text" size="small" @click="editUser(scope.row)">编辑</el-button>
            <el-button 
              type="text" 
              size="small" 
              :class="scope.row.is_active ? 'danger' : 'success'"
              @click="toggleUserStatus(scope.row)"
            >
              {{ scope.row.is_active ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.per_page"
        :page-sizes="[10, 20, 50, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadUsers"
        @current-change="loadUsers"
        class="pagination"
      />
    </el-card>
  </el-tab-pane>
  
  <el-tab-pane label="用户组" name="groups">
    <el-card>
      <div class="group-header">
        <el-button type="primary" @click="showGroupDialog">
          <el-icon><Plus /></el-icon>
          新建组
        </el-button>
      </div>
      
      <el-table v-loading="groupLoading" :data="groupsList" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="组名称" width="200" />
        <el-table-column prop="description" label="描述" min-width="250" />
        <el-table-column label="管理员" width="150">
          <template #default="scope">
            {{ scope.row.manager?.real_name || scope.row.manager?.username || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="成员数" width="100">
          <template #default="scope">
            {{ scope.row.members?.length || 0 }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button type="text" size="small" @click="editGroup(scope.row)">编辑</el-button>
            <el-button type="text" size="small" @click="manageGroupMembers(scope.row)">成员</el-button>
            <el-button type="text" size="small" class="danger" @click="deleteGroup(scope.row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </el-tab-pane>
</el-tabs>
    
    <!-- 新建用户对话框 -->
    <el-dialog v-model="createDialogVisible" title="新建用户" width="600px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="createForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="createForm.real_name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="createForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="createForm.password" type="password" placeholder="请输入密码" />
        </el-form-item>
        <el-form-item label="部门" prop="department">
          <el-input v-model="createForm.department" placeholder="请输入部门" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="createForm.phone_number" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="角色" prop="roles">
          <el-select v-model="createForm.roles" multiple placeholder="请选择角色">
            <el-option v-for="role in rolesList" :key="role.id" :label="getRoleText(role.name)" :value="role.id" />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleCreateUser" :loading="creating">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 编辑用户对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑用户" width="600px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="editForm.username" disabled />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="editForm.real_name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="部门" prop="department">
          <el-input v-model="editForm.department" placeholder="请输入部门" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="editForm.phone_number" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="角色" prop="roles">
          <el-select v-model="editForm.roles" multiple placeholder="请选择角色">
            <el-option v-for="role in rolesList" :key="role.id" :label="getRoleText(role.name)" :value="role.id" />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleUpdateUser" :loading="updating">保存</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 新建/编辑用户组对话框 -->
    <el-dialog v-model="groupDialogVisible" :title="groupDialogTitle" width="600px">
      <el-form ref="groupFormRef" :model="groupForm" :rules="groupRules" label-width="100px">
        <el-form-item label="组名称" prop="name">
          <el-input v-model="groupForm.name" placeholder="请输入组名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="groupForm.description" type="textarea" placeholder="请输入组描述" />
        </el-form-item>
        <el-form-item label="管理员" prop="manager_id">
          <el-select v-model="groupForm.manager_id" placeholder="请选择管理员" clearable>
            <el-option 
              v-for="user in usersList" 
              :key="user.id" 
              :label="user.real_name || user.username" 
              :value="user.id" 
            />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="groupDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleGroupSubmit" :loading="groupSubmitting">确定</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 成员管理对话框 -->
    <el-dialog v-model="membersDialogVisible" title="成员管理" width="800px">
      <div class="members-management">
        <div class="add-member">
          <el-select v-model="selectedUserId" placeholder="选择要添加的用户" style="width: 250px; margin-right: 10px;">
            <el-option 
              v-for="user in availableUsers" 
              :key="user.id" 
              :label="user.real_name || user.username" 
              :value="user.id" 
            />
          </el-select>
          <el-button type="primary" @click="addMember" :loading="addingMember">添加成员</el-button>
        </div>
        
        <el-table :data="currentGroupMembers" stripe style="margin-top: 20px;">
          <el-table-column prop="username" label="用户名" width="120" />
          <el-table-column prop="real_name" label="真实姓名" width="120" />
          <el-table-column prop="email" label="邮箱" min-width="200" />
          <el-table-column prop="department" label="部门" width="120" />
          <el-table-column label="操作" width="100">
            <template #default="scope">
              <el-button type="text" size="small" class="danger" @click="removeMember(scope.row)">移除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="membersDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { users } from '@/api'
import dayjs from 'dayjs'

export default {
  name: 'Users',
  components: { Plus, Search },
  setup() {
    const activeTab = ref('users')
    const loading = ref(false)
    const creating = ref(false)
    const updating = ref(false)
    const groupLoading = ref(false)
    const groupSubmitting = ref(false)
    const addingMember = ref(false)
    
    const usersList = ref([])
    const rolesList = ref([])
    const groupsList = ref([])
    const currentGroupMembers = ref([])
    const selectedUserId = ref(null)
    
    const createDialogVisible = ref(false)
    const editDialogVisible = ref(false)
    const groupDialogVisible = ref(false)
    const membersDialogVisible = ref(false)
    
    const createFormRef = ref(null)
    const editFormRef = ref(null)
    const groupFormRef = ref(null)
    
    const isEditGroup = ref(false)
    const currentGroupId = ref(null)
    
    const searchForm = reactive({
      keyword: '',
      status: ''
    })
    
    const pagination = reactive({
      page: 1,
      per_page: 20,
      total: 0
    })
    
    const createForm = reactive({
      username: '',
      real_name: '',
      email: '',
      password: '',
      department: '',
      phone_number: '',
      roles: []
    })
    
    const editForm = reactive({
      id: null,
      username: '',
      real_name: '',
      email: '',
      department: '',
      phone_number: '',
      roles: []
    })
    
    const groupForm = reactive({
      id: null,
      name: '',
      description: '',
      manager_id: null
    })
    
    const createRules = {
      username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 3, max: 50, message: '用户名长度在 3 到 50 个字符', trigger: 'blur' }
      ],
      real_name: [
        { required: true, message: '请输入真实姓名', trigger: 'blur' }
      ],
      email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
      ],
      department: [
        { required: true, message: '请输入部门', trigger: 'blur' }
      ],
      roles: [
        { required: true, message: '请选择角色', trigger: 'change' }
      ]
    }
    
    const editRules = {
      real_name: [
        { required: true, message: '请输入真实姓名', trigger: 'blur' }
      ],
      email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
      ],
      department: [
        { required: true, message: '请输入部门', trigger: 'blur' }
      ],
      roles: [
        { required: true, message: '请选择角色', trigger: 'change' }
      ]
    }
    
    const groupRules = {
      name: [
        { required: true, message: '请输入组名称', trigger: 'blur' },
        { min: 2, max: 50, message: '组名称长度在2到50个字符', trigger: 'blur' }
      ],
      description: [
        { required: true, message: '请输入组描述', trigger: 'blur' }
      ]
    }
    
    const groupDialogTitle = computed(() => {
      return isEditGroup.value ? '编辑用户组' : '新建用户组'
    })
    
    const availableUsers = computed(() => {
      return usersList.value.filter(user => 
        !currentGroupMembers.value.some(member => member.id === user.id)
      )
    })
    
    const loadUsers = async () => {
      try {
        loading.value = true
        const params = {
          page: pagination.page,
          per_page: pagination.per_page,
          ...searchForm
        }
        const data = await users.list(params)
        usersList.value = data.users || []
        pagination.total = data.total || 0
      } catch (error) {
        ElMessage.error('获取用户列表失败')
      } finally {
        loading.value = false
      }
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
    
    const loadRoles = async () => {
      try {
        const data = await users.roles()
        rolesList.value = data.roles || []
      } catch (error) {
        console.error('获取角色列表失败:', error)
      }
    }
    
    const showCreateDialog = () => {
      createDialogVisible.value = true
      loadRoles()
    }
    
    const resetCreateForm = () => {
      Object.assign(createForm, {
        username: '',
        real_name: '',
        email: '',
        password: '',
        department: '',
        phone_number: '',
        roles: []
      })
      createFormRef.value?.clearValidate()
    }
    
    const handleCreateUser = async () => {
      try {
        const valid = await createFormRef.value?.validate()
        if (!valid) return
        
        creating.value = true
        await users.create(createForm)
        
        ElMessage.success('用户创建成功')
        createDialogVisible.value = false
        resetCreateForm()
        loadUsers()
      } catch (error) {
        ElMessage.error('用户创建失败')
      } finally {
        creating.value = false
      }
    }
    
    const editUser = (user) => {
      Object.assign(editForm, {
        id: user.id,
        username: user.username,
        real_name: user.real_name,
        email: user.email,
        department: user.department,
        phone_number: user.phone_number || '',
        roles: user.roles ? user.roles.map(role => {
          const roleObj = rolesList.value.find(r => r.name === role)
          return roleObj ? roleObj.id : null
        }).filter(id => id !== null) : []
      })
      editDialogVisible.value = true
      loadRoles()
    }
    
    const handleUpdateUser = async () => {
      try {
        const valid = await editFormRef.value?.validate()
        if (!valid) return
        
        updating.value = true
        await users.update(editForm.id, editForm)
        
        ElMessage.success('用户更新成功')
        editDialogVisible.value = false
        loadUsers()
      } catch (error) {
        ElMessage.error('用户更新失败')
      } finally {
        updating.value = false
      }
    }
    
    const toggleUserStatus = async (user) => {
      try {
        const action = user.is_active ? '禁用' : '启用'
        await ElMessageBox.confirm(`确定要${action}用户“${user.real_name}”吗？`, '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        await users.toggleStatus(user.id, !user.is_active)
        ElMessage.success(`用户${action}成功`)
        loadUsers()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('操作失败')
        }
      }
    }
    
    // 用户组管理方法
    const loadGroups = async () => {
      try {
        groupLoading.value = true
        const data = await users.groups()
        groupsList.value = data.groups || []
      } catch (error) {
        ElMessage.error('获取用户组列表失败')
      } finally {
        groupLoading.value = false
      }
    }
    
    const showGroupDialog = () => {
      isEditGroup.value = false
      resetGroupForm()
      groupDialogVisible.value = true
    }
    
    const resetGroupForm = () => {
      Object.assign(groupForm, {
        id: null,
        name: '',
        description: '',
        manager_id: null
      })
      groupFormRef.value?.clearValidate()
    }
    
    const handleGroupSubmit = async () => {
      try {
        const valid = await groupFormRef.value?.validate()
        if (!valid) return
        
        groupSubmitting.value = true
        
        if (isEditGroup.value) {
          await users.updateGroup(groupForm.id, groupForm)
          ElMessage.success('用户组更新成功')
        } else {
          await users.createGroup(groupForm)
          ElMessage.success('用户组创建成功')
        }
        
        groupDialogVisible.value = false
        loadGroups()
      } catch (error) {
        ElMessage.error(isEditGroup.value ? '用户组更新失败' : '用户组创建失败')
      } finally {
        groupSubmitting.value = false
      }
    }
    
    const editGroup = (group) => {
      isEditGroup.value = true
      Object.assign(groupForm, {
        id: group.id,
        name: group.name,
        description: group.description,
        manager_id: group.manager_id
      })
      groupDialogVisible.value = true
    }
    
    const deleteGroup = async (group) => {
      try {
        await ElMessageBox.confirm(`确定要删除用户组"${group.name}"吗？`, '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        await users.deleteGroup(group.id)
        ElMessage.success('用户组删除成功')
        loadGroups()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('用户组删除失败')
        }
      }
    }
    
    const manageGroupMembers = async (group) => {
      try {
        currentGroupId.value = group.id
        const data = await users.getGroupMembers(group.id)
        currentGroupMembers.value = data.members || []
        membersDialogVisible.value = true
        selectedUserId.value = null
      } catch (error) {
        ElMessage.error('获取组成员列表失败')
      }
    }
    
    const addMember = async () => {
      if (!selectedUserId.value) {
        ElMessage.warning('请选择要添加的用户')
        return
      }
      
      try {
        addingMember.value = true
        await users.addGroupMember(currentGroupId.value, selectedUserId.value)
        ElMessage.success('成员添加成功')
        
        // 重新加载成员列表
        const data = await users.getGroupMembers(currentGroupId.value)
        currentGroupMembers.value = data.members || []
        selectedUserId.value = null
      } catch (error) {
        ElMessage.error('成员添加失败')
      } finally {
        addingMember.value = false
      }
    }
    
    const removeMember = async (member) => {
      try {
        await ElMessageBox.confirm(`确定要移除成员"${member.real_name}"吗？`, '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        await users.removeGroupMember(currentGroupId.value, member.id)
        ElMessage.success('成员移除成功')
        
        // 重新加载成员列表
        const data = await users.getGroupMembers(currentGroupId.value)
        currentGroupMembers.value = data.members || []
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('成员移除失败')
        }
      }
    }
    
    onMounted(() => {
      loadUsers()
      loadGroups()
    })
    
    return {
      activeTab,
      loading,
      creating,
      updating,
      groupLoading,
      groupSubmitting,
      addingMember,
      usersList,
      rolesList,
      groupsList,
      currentGroupMembers,
      selectedUserId,
      searchForm,
      pagination,
      createDialogVisible,
      editDialogVisible,
      groupDialogVisible,
      membersDialogVisible,
      createFormRef,
      editFormRef,
      groupFormRef,
      createForm,
      editForm,
      groupForm,
      createRules,
      editRules,
      groupRules,
      groupDialogTitle,
      availableUsers,
      loadUsers,
      loadGroups,
      formatDate,
      getRoleText,
      showCreateDialog,
      showGroupDialog,
      handleCreateUser,
      handleGroupSubmit,
      resetCreateForm,
      editUser,
      editGroup,
      handleUpdateUser,
      toggleUserStatus,
      deleteGroup,
      manageGroupMembers,
      addMember,
      removeMember
    }
  }
}
</script>

<style scoped>
.users {
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

.search-bar {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  text-align: center;
}

.group-header {
  margin-bottom: 20px;
  display: flex;
  justify-content: flex-end;
}

.members-management {
  padding: 20px 0;
}

.add-member {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

:deep(.el-button.danger) {
  color: #f56c6c;
}

:deep(.el-button.success) {
  color: #67c23a;
}

.user-tabs {
  margin-top: 20px;
}

.approval-steps {
  margin-top: 20px;
}

.step-item {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 15px;
  background-color: #fafafa;
}

.step-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  font-weight: bold;
}
</style>