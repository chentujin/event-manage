<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '200px'" class="sidebar">
      <div class="logo">
        <i class="el-icon-monitor"></i>
        <span v-show="!isCollapse">事件管理平台</span>
      </div>
      
      <el-menu
        :default-active="$route.path"
        class="sidebar-menu"
        :collapse="isCollapse"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/">
          <el-icon><Monitor /></el-icon>
          <span>仪表盘</span>
        </el-menu-item>
        
        <el-menu-item index="/alerts">
          <el-icon><Bell /></el-icon>
          <span>告警管理</span>
        </el-menu-item>
        
        <el-menu-item index="/incidents">
          <el-icon><Warning /></el-icon>
          <span>事件管理</span>
        </el-menu-item>
        
        <el-menu-item index="/incidents-new">
          <el-icon><Flag /></el-icon>
          <span>故障管理</span>
        </el-menu-item>
        
        <el-menu-item index="/problems">
          <el-icon><Tools /></el-icon>
          <span>问题管理</span>
        </el-menu-item>
        
        <el-menu-item index="/postmortems">
          <el-icon><Document /></el-icon>
          <span>复盘管理</span>
        </el-menu-item>
        
        <el-menu-item index="/services">
          <el-icon><Setting /></el-icon>
          <span>服务目录</span>
        </el-menu-item>
        
        <el-menu-item index="/approvals">
          <el-icon><Document /></el-icon>
          <span>审批管理</span>
        </el-menu-item>
        
        <el-menu-item index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        
        <el-menu-item index="/notifications">
          <el-icon><Message /></el-icon>
          <span>通知集成</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <!-- 主内容区 -->
    <el-container>
      <!-- 顶部导航 -->
      <el-header class="navbar">
        <div class="navbar-left">
          <el-button
            type="text"
            @click="toggleSidebar"
            class="toggle-btn"
          >
            <el-icon><Fold v-if="!isCollapse" /><Expand v-else /></el-icon>
          </el-button>
        </div>
        
        <div class="navbar-right">
          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-icon><Avatar /></el-icon>
              {{ userInfo?.real_name || userInfo?.username }}
              <el-icon><CaretBottom /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">个人设置</el-dropdown-item>
                <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <!-- 主内容 -->
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
    
    <!-- 个人设置对话框 -->
    <el-dialog v-model="profileDialogVisible" title="个人设置" width="600px">
      <el-form ref="profileFormRef" :model="profileForm" :rules="profileRules" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="profileForm.username" disabled />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="profileForm.real_name" disabled />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="profileForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="部门" prop="department">
          <el-input v-model="profileForm.department" placeholder="请输入部门" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone_number">
          <el-input v-model="profileForm.phone_number" placeholder="请输入手机号" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="profileDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleUpdateProfile" :loading="profileLoading">保存</el-button>
        </span>
      </template>
    </el-dialog>
  </el-container>
</template>

<script>
import { ref, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import { getUserInfo, removeToken, updateUserInfo } from '@/utils/auth'
import { users } from '@/api'
import {
  Monitor, Warning, Tools, Setting, Document, User, Message,
  Fold, Expand, Avatar, CaretBottom, Bell, Flag
} from '@element-plus/icons-vue'

export default {
  name: 'Layout',
  components: {
    Monitor, Warning, Tools, Setting, Document, User, Message,
    Fold, Expand, Avatar, CaretBottom, Bell, Flag
  },
  setup() {
    const router = useRouter()
    const isCollapse = ref(false)
    const profileDialogVisible = ref(false)
    const profileLoading = ref(false)
    const profileFormRef = ref(null)
    
    const userInfo = computed(() => getUserInfo())
    
    const profileForm = reactive({
      id: null,
      username: '',
      real_name: '',
      email: '',
      department: '',
      phone_number: ''
    })
    
    const profileRules = {
      email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
      ],
      department: [
        { required: true, message: '请输入部门', trigger: 'blur' }
      ],
      phone_number: [
        { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的11位手机号', trigger: 'blur' }
      ]
    }
    
    const toggleSidebar = () => {
      isCollapse.value = !isCollapse.value
    }
    
    const handleCommand = async (command) => {
      if (command === 'logout') {
        try {
          await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          })
          
          removeToken()
          router.push('/login')
        } catch (error) {
          // 用户取消
        }
      } else if (command === 'profile') {
        showProfileDialog()
      }
    }
    
    const showProfileDialog = () => {
      const currentUser = getUserInfo()
      if (currentUser) {
        Object.assign(profileForm, {
          id: currentUser.id,
          username: currentUser.username,
          real_name: currentUser.real_name || '',
          email: currentUser.email || '',
          department: currentUser.department || '',
          phone_number: currentUser.phone_number || ''
        })
      }
      profileDialogVisible.value = true
    }
    
    const handleUpdateProfile = async () => {
      if (!profileFormRef.value) return
      
      try {
        const valid = await profileFormRef.value.validate()
        if (!valid) return
        
        profileLoading.value = true
        
        // 使用专门的个人设置更新API，只提交允许修改的字段
        await users.updateProfile({
          email: profileForm.email,
          department: profileForm.department,
          phone_number: profileForm.phone_number
        })
        
        // 更新本地用户信息（保持真实姓名不变）
        updateUserInfo({
          ...getUserInfo(),
          email: profileForm.email,
          department: profileForm.department,
          phone_number: profileForm.phone_number
        })
        
        ElMessage.success('个人信息更新成功')
        profileDialogVisible.value = false
        
      } catch (error) {
        console.error('更新个人设置失败:', error)
        if (error.response?.data?.error) {
          ElMessage.error(error.response.data.error)
        } else {
          ElMessage.error('更新失败')
        }
      } finally {
        profileLoading.value = false
      }
    }
    
    return {
      isCollapse,
      userInfo,
      profileDialogVisible,
      profileLoading,
      profileForm,
      profileRules,
      profileFormRef,
      toggleSidebar,
      handleCommand,
      showProfileDialog,
      handleUpdateProfile
    }
  }
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

.sidebar {
  background: #304156;
  transition: width 0.28s;
  overflow: hidden;
}

.logo {
  height: 60px;
  line-height: 60px;
  text-align: center;
  color: #fff;
  font-size: 20px;
  font-weight: bold;
  border-bottom: 1px solid #434a50;
}

.logo i {
  margin-right: 10px;
}

.sidebar-menu {
  border: none;
}

.navbar {
  background: #fff;
  border-bottom: 1px solid #d8dce5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.toggle-btn {
  font-size: 18px;
  color: #5a5e66;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
  color: #5a5e66;
}

.user-info i {
  margin: 0 5px;
}

.main-content {
  background: #f0f2f5;
  padding: 20px;
}
</style>