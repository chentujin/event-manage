<template>
  <div class="postmortem-page">
    <!-- 页面标题和操作栏 -->
    <div class="page-header">
      <h1>复盘管理</h1>
      <div class="actions">
        <el-button type="primary" @click="showAddActionDialog">创建改进措施</el-button>
        <el-button @click="refreshData">刷新</el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ statistics.pending_publish || 0 }}</div>
              <div class="stat-label">待发布</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ statistics.overdue_action_items || 0 }}</div>
              <div class="stat-label">过期改进措施</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ getTotalActionItems() }}</div>
              <div class="stat-label">总改进措施</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <div class="stat-content">
              <div class="stat-number">{{ getCompletedActionItems() }}</div>
              <div class="stat-label">已完成措施</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 筛选条件 -->
    <div class="filters">
      <el-row :gutter="20">
        <el-col :span="4">
          <el-select v-model="filters.status" placeholder="状态" @change="loadPostMortems">
            <el-option label="全部" value=""></el-option>
            <el-option label="草稿" value="Draft"></el-option>
            <el-option label="审核中" value="In Review"></el-option>
            <el-option label="已审核" value="Approved"></el-option>
            <el-option label="已发布" value="Published"></el-option>
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select v-model="filters.author_id" placeholder="作者" @change="loadPostMortems" clearable>
            <el-option 
              v-for="user in users" 
              :key="user.id" 
              :label="user.real_name" 
              :value="user.id">
            </el-option>
          </el-select>
        </el-col>
      </el-row>
    </div>

    <!-- 复盘列表 -->
    <el-table
      :data="postmortems"
      v-loading="loading"
      style="width: 100%">
      
      <el-table-column prop="incident.incident_id" label="故障ID" width="120">
        <template #default="scope">
          <span class="incident-link">{{ scope.row.incident?.incident_id || '-' }}</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="title" label="复盘标题" min-width="200"></el-table-column>
      
      <el-table-column prop="status" label="状态" width="100">
        <template #default="scope">
          <el-tag :type="getStatusTagType(scope.row.status)" size="small">
            {{ getStatusText(scope.row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      
      <el-table-column prop="author" label="作者" width="120">
        <template #default="scope">
          {{ scope.row.author?.real_name || '-' }}
        </template>
      </el-table-column>
      
      <el-table-column prop="reviewer" label="审核人" width="120">
        <template #default="scope">
          {{ scope.row.reviewer?.real_name || '-' }}
        </template>
      </el-table-column>
      
      <el-table-column prop="action_items_count" label="改进措施" width="100">
        <template #default="scope">
          <span>{{ scope.row.action_items_count || 0 }} 项</span>
        </template>
      </el-table-column>
      
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="scope">
          {{ formatDateTime(scope.row.created_at) }}
        </template>
      </el-table-column>
      
      <el-table-column label="操作" width="200">
        <template #default="scope">
          <el-button-group>
            <el-button size="small" @click="viewPostMortem(scope.row)">查看</el-button>
            <el-button 
              v-if="canEdit(scope.row)"
              size="small" 
              type="primary" 
              @click="editPostMortem(scope.row)">
              编辑
            </el-button>
            <el-dropdown @command="handleCommand($event, scope.row)">
              <el-button size="small">
                更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item 
                    v-if="canSubmitReview(scope.row)"
                    command="submit_review">
                    提交审核
                  </el-dropdown-item>
                  <el-dropdown-item 
                    v-if="canApprove(scope.row)"
                    command="approve">
                    审核通过
                  </el-dropdown-item>
                  <el-dropdown-item 
                    v-if="canPublish(scope.row)"
                    command="publish">
                    发布
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>

    <!-- 改进措施列表 -->
    <el-card class="action-items-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>改进措施列表</span>
        </div>
      </template>
      
      <el-table :data="actionItems" v-loading="actionItemsLoading" style="width: 100%">
        <el-table-column prop="title" label="标题" min-width="200"></el-table-column>
        <el-table-column prop="description" label="描述" min-width="300">
          <template #default="scope">
            <div class="description-cell">{{ scope.row.description || '-' }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="incident_id" label="故障ID" width="120">
          <template #default="scope">
            <span v-if="scope.row.incident_id" class="incident-link">{{ scope.row.incident_id }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="类别" width="100">
          <template #default="scope">
            <el-tag size="small">{{ getCategoryText(scope.row.category) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="priority" label="优先级" width="80">
          <template #default="scope">
            <el-tag :type="getPriorityTagType(scope.row.priority)" size="small">
              {{ getPriorityText(scope.row.priority) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getActionStatusTagType(scope.row.status)" size="small">
              {{ getActionStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="assignee" label="负责人" width="120">
          <template #default="scope">
            {{ scope.row.assignee?.real_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="due_date" label="截止时间" width="120">
          <template #default="scope">
            {{ scope.row.due_date ? formatDate(scope.row.due_date) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="scope">
            <el-button size="small" @click="viewActionItem(scope.row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 改进措施详情对话框 -->
    <el-dialog v-model="actionDetailDialogVisible" title="改进措施详情" width="60%">
      <div v-if="selectedActionItem" class="action-item-detail">
        <el-descriptions :column="2" border style="margin-bottom: 20px;">
          <el-descriptions-item label="标题" :span="2">{{ selectedActionItem.title }}</el-descriptions-item>
          <el-descriptions-item label="描述" :span="2">{{ selectedActionItem.description || '-' }}</el-descriptions-item>
          <el-descriptions-item label="类别">
            <el-tag size="small">{{ getCategoryText(selectedActionItem.category) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="优先级">
            <el-tag :type="getPriorityTagType(selectedActionItem.priority)" size="small">
              {{ getPriorityText(selectedActionItem.priority) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getActionStatusTagType(selectedActionItem.status)" size="small">
              {{ getActionStatusText(selectedActionItem.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="负责人">
            {{ selectedActionItem.assignee?.real_name || '未分配' }}
          </el-descriptions-item>
          <el-descriptions-item label="关联故障ID">
            <span v-if="selectedActionItem.incident_id" class="incident-link">{{ selectedActionItem.incident_id }}</span>
            <span v-else>-</span>
          </el-descriptions-item>
          <el-descriptions-item label="截止时间">
            {{ selectedActionItem.due_date ? formatDate(selectedActionItem.due_date) : '未设置' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ selectedActionItem.created_at ? formatDateTime(selectedActionItem.created_at) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="外部链接" :span="2">
            <a v-if="selectedActionItem.external_link" :href="selectedActionItem.external_link" target="_blank" class="external-link">
              {{ selectedActionItem.external_link }}
            </a>
            <span v-else>-</span>
          </el-descriptions-item>
        </el-descriptions>
        
        <!-- 状态记录部分 -->
        <div class="status-logs-section">
          <h4>状态记录 ({{ actionItemStatusLogs.length }} 条)</h4>
          <!-- 调试信息 -->
          <div v-if="actionItemStatusLogs.length === 0" style="color: #999; font-size: 12px; margin-bottom: 10px;">
            调试: actionItemStatusLogs.length = {{ actionItemStatusLogs.length }}
          </div>
          
          <el-timeline v-if="actionItemStatusLogs.length > 0">
            <el-timeline-item
              v-for="log in actionItemStatusLogs"
              :key="log.id"
              :timestamp="formatDateTime(log.created_at)"
              :type="getStatusLogType(log.new_status)">
              <div class="status-log-item">
                <div class="status-change">
                  <span class="status-label">状态变更:</span>
                  <el-tag 
                    :type="getActionStatusTagType(log.old_status)" 
                    size="small" 
                    v-if="log.old_status">
                    {{ getActionStatusText(log.old_status) }}
                  </el-tag>
                  <span class="arrow">→</span>
                  <el-tag 
                    :type="getActionStatusTagType(log.new_status)" 
                    size="small">
                    {{ getActionStatusText(log.new_status) }}
                  </el-tag>
                </div>
                <div class="status-action" v-if="log.action">
                  <span class="action-label">操作:</span>
                  <span class="action-text">{{ log.action }}</span>
                </div>
                <div class="status-comments" v-if="log.comments">
                  <span class="comments-label">说明:</span>
                  <span class="comments-text">{{ log.comments }}</span>
                </div>
                <div class="status-user">
                  <span class="user-label">操作人:</span>
                  <span class="user-text">{{ log.user?.real_name || '未知用户' }}</span>
                </div>
              </div>
            </el-timeline-item>
          </el-timeline>
          <div v-else class="no-status-logs">
            <el-empty description="暂无状态记录" :image-size="60"></el-empty>
          </div>
        </div>
        
        <!-- 操作按钮部分 -->
        <div class="action-buttons-section">
          <h4>操作</h4>
          <div class="action-buttons">
            <!-- 状态变更按钮 -->
            <el-button 
              type="primary" 
              size="small" 
              @click="showStatusChangeDialog"
              :disabled="selectedActionItem.status === 'Completed'">
              变更状态
            </el-button>
            
            <!-- 分配负责人按钮 -->
            <el-button 
              type="success" 
              size="small" 
              @click="showAssigneeDialog">
              分配负责人
            </el-button>
            
            <!-- 设置截止时间按钮 -->
            <el-button 
              type="warning" 
              size="small" 
              @click="showDueDateDialog">
              设置截止时间
            </el-button>
            
            <!-- 编辑基本信息按钮 -->
            <el-button 
              type="info" 
              size="small" 
              @click="showEditDialog">
              编辑信息
            </el-button>
            
            <!-- 完成改进措施按钮 -->
            <el-button 
              type="success" 
              size="small" 
              @click="completeActionItem"
              :disabled="selectedActionItem.status === 'Completed'"
              v-if="selectedActionItem.status !== 'Completed'">
              标记完成
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>

    <!-- 状态变更对话框 -->
    <el-dialog v-model="statusChangeDialogVisible" title="变更改进措施状态" width="500px">
      <el-form :model="statusChangeForm" :rules="statusChangeRules" ref="statusChangeFormRef" label-width="100px">
        <el-form-item label="当前状态">
          <el-tag :type="getActionStatusTagType(selectedActionItem?.status)" size="large">
            {{ getActionStatusText(selectedActionItem?.status) }}
          </el-tag>
        </el-form-item>
        
        <el-form-item label="新状态" prop="new_status">
          <el-select v-model="statusChangeForm.new_status" placeholder="请选择新状态" style="width: 100%">
            <el-option label="待处理" value="Open"></el-option>
            <el-option label="进行中" value="In Progress"></el-option>
            <el-option label="已完成" value="Completed"></el-option>
            <el-option label="已取消" value="Cancelled"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="操作说明" prop="comments">
          <el-input 
            v-model="statusChangeForm.comments" 
            type="textarea" 
            :rows="3"
            placeholder="请说明状态变更的原因和下一步计划">
          </el-input>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="statusChangeDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitStatusChange" :loading="statusChanging">确认变更</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 分配负责人对话框 -->
    <el-dialog v-model="assigneeDialogVisible" title="分配负责人" width="500px">
      <el-form :model="assigneeForm" :rules="assigneeRules" ref="assigneeFormRef" label-width="100px">
        <el-form-item label="当前负责人">
          <span>{{ selectedActionItem?.assignee?.real_name || '未分配' }}</span>
        </el-form-item>
        
        <el-form-item label="新负责人" prop="assignee_id">
          <el-select v-model="assigneeForm.assignee_id" placeholder="请选择负责人" style="width: 100%">
            <el-option 
              v-for="user in users" 
              :key="user.id" 
              :label="user.real_name" 
              :value="user.id">
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="分配说明" prop="comments">
          <el-input 
            v-model="assigneeForm.comments" 
            type="textarea" 
            :rows="3"
            placeholder="请说明分配原因和期望">
          </el-input>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="assigneeDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitAssigneeChange" :loading="assigneeChanging">确认分配</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 设置截止时间对话框 -->
    <el-dialog v-model="dueDateDialogVisible" title="设置截止时间" width="500px">
      <el-form :model="dueDateForm" :rules="dueDateRules" ref="dueDateFormRef" label-width="100px">
        <el-form-item label="当前截止时间">
          <span>{{ selectedActionItem?.due_date ? formatDate(selectedActionItem.due_date) : '未设置' }}</span>
        </el-form-item>
        
        <el-form-item label="新截止时间" prop="due_date">
          <el-date-picker
            v-model="dueDateForm.due_date"
            type="datetime"
            placeholder="请选择截止时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
            style="width: 100%">
          </el-date-picker>
        </el-form-item>
        
        <el-form-item label="设置说明" prop="comments">
          <el-input 
            v-model="dueDateForm.comments" 
            type="textarea" 
            :rows="3"
            placeholder="请说明设置截止时间的原因">
          </el-input>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dueDateDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitDueDateChange" :loading="dueDateChanging">确认设置</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 编辑信息对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑改进措施信息" width="600px">
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="100px">
        <el-form-item label="标题" prop="title">
          <el-input v-model="editForm.title" placeholder="请输入改进措施标题"></el-input>
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input 
            v-model="editForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="请输入改进措施描述">
          </el-input>
        </el-form-item>
        
        <el-form-item label="类别" prop="category">
          <el-select v-model="editForm.category" placeholder="请选择类别" style="width: 100%">
            <el-option label="技术改进" value="Technical"></el-option>
            <el-option label="流程改进" value="Process"></el-option>
            <el-option label="文档改进" value="Documentation"></el-option>
            <el-option label="培训改进" value="Training"></el-option>
            <el-option label="监控改进" value="Monitoring"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="editForm.priority" placeholder="请选择优先级" style="width: 100%">
            <el-option label="高" value="High"></el-option>
            <el-option label="中" value="Medium"></el-option>
            <el-option label="低" value="Low"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="外部链接">
          <el-input 
            v-model="editForm.external_link" 
            placeholder="如Jira链接等（可选）">
          </el-input>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitEdit" :loading="editing">确认修改</el-button>
        </span>
      </template>
    </el-dialog>

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

    <!-- 复盘详情对话框 -->
    <el-dialog v-model="detailDialogVisible" title="复盘详情" width="80%">
      <div v-if="selectedPostMortem" class="postmortem-detail">
        <el-tabs v-model="activeTab" type="border-card">
          <!-- 基本信息 -->
          <el-tab-pane label="复盘内容" name="content">
            <el-descriptions :column="2" border style="margin-bottom: 20px;">
              <el-descriptions-item label="复盘标题" :span="2">{{ selectedPostMortem.title }}</el-descriptions-item>
              <el-descriptions-item label="关联故障">{{ selectedPostMortem.incident?.incident_id || '-' }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusTagType(selectedPostMortem.status)">
                  {{ getStatusText(selectedPostMortem.status) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="作者">{{ selectedPostMortem.author?.real_name || '-' }}</el-descriptions-item>
              <el-descriptions-item label="审核人">{{ selectedPostMortem.reviewer?.real_name || '-' }}</el-descriptions-item>
            </el-descriptions>

            <div class="content-sections">
              <div class="section" v-if="selectedPostMortem.incident_summary">
                <h4>故障概述</h4>
                <div class="section-content">{{ selectedPostMortem.incident_summary }}</div>
              </div>
              
              <div class="section" v-if="selectedPostMortem.timeline_analysis">
                <h4>时间线分析</h4>
                <div class="section-content">{{ selectedPostMortem.timeline_analysis }}</div>
              </div>
              
              <div class="section" v-if="selectedPostMortem.root_cause_analysis">
                <h4>根因分析</h4>
                <div class="section-content">{{ selectedPostMortem.root_cause_analysis }}</div>
              </div>
              
              <div class="section" v-if="selectedPostMortem.lessons_learned">
                <h4>经验教训</h4>
                <div class="section-content">{{ selectedPostMortem.lessons_learned }}</div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 改进措施 -->
          <el-tab-pane label="改进措施" name="actions">
            <div class="action-items-section">
              <div class="section-header">
                <h4>改进措施 ({{ selectedPostMortem.action_items?.length || 0 }})</h4>
                <el-button v-if="canEdit(selectedPostMortem)" size="small" @click="showAddActionDialog">添加措施</el-button>
              </div>
              
              <el-table :data="selectedPostMortem.action_items || []" style="margin-top: 10px;">
                <el-table-column prop="title" label="标题" min-width="200"></el-table-column>
                <el-table-column prop="category" label="类别" width="100"></el-table-column>
                <el-table-column prop="priority" label="优先级" width="80">
                  <template #default="scope">
                    <el-tag :type="getPriorityTagType(scope.row.priority)" size="small">
                      {{ scope.row.priority }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="status" label="状态" width="100">
                  <template #default="scope">
                    <el-tag :type="getActionStatusTagType(scope.row.status)" size="small">
                      {{ getActionStatusText(scope.row.status) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="assignee" label="负责人" width="120">
                  <template #default="scope">
                    {{ scope.row.assignee?.real_name || '-' }}
                  </template>
                </el-table-column>
                <el-table-column prop="due_date" label="截止时间" width="120">
                  <template #default="scope">
                    {{ scope.row.due_date ? formatDate(scope.row.due_date) : '-' }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="120">
                  <template #default="scope">
                    <el-button size="small" @click="viewActionItem(scope.row)">详情</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>

    <!-- 编辑复盘对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑复盘" width="70%">
      <el-form :model="editForm" :rules="postmortemRules" ref="postmortemForm" label-width="120px">
        <el-form-item label="复盘标题" prop="title">
          <el-input v-model="editForm.title"></el-input>
        </el-form-item>
        
        <el-form-item label="故障概述">
          <el-input type="textarea" v-model="editForm.incident_summary" :rows="4"></el-input>
        </el-form-item>
        
        <el-form-item label="时间线分析">
          <el-input type="textarea" v-model="editForm.timeline_analysis" :rows="4"></el-input>
        </el-form-item>
        
        <el-form-item label="根因分析">
          <el-input type="textarea" v-model="editForm.root_cause_analysis" :rows="4"></el-input>
        </el-form-item>
        
        <el-form-item label="经验教训">
          <el-input type="textarea" v-model="editForm.lessons_learned" :rows="4"></el-input>
        </el-form-item>
        
        <el-form-item label="审核人">
          <el-select v-model="editForm.reviewer_id" placeholder="请选择审核人" clearable>
            <el-option 
              v-for="user in users" 
              :key="user.id" 
              :label="user.real_name" 
              :value="user.id">
            </el-option>
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="savePostMortem" :loading="saving">保存</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 创建改进措施对话框 -->
    <el-dialog v-model="createActionDialogVisible" title="创建改进措施" width="60%">
      <el-form :model="actionForm" :rules="actionRules" ref="actionFormRef" label-width="120px">
        <el-form-item label="改进措施标题" prop="title">
          <el-input v-model="actionForm.title" placeholder="请输入改进措施标题"></el-input>
        </el-form-item>
        
        <el-form-item label="详细描述" prop="description">
          <el-input 
            type="textarea" 
            v-model="actionForm.description" 
            :rows="4" 
            placeholder="请详细描述改进措施内容">
          </el-input>
        </el-form-item>
        
        <el-form-item label="措施类别" prop="category">
          <el-select v-model="actionForm.category" placeholder="请选择措施类别">
            <el-option label="技术改进" value="Technical"></el-option>
            <el-option label="流程改进" value="Process"></el-option>
            <el-option label="文档改进" value="Documentation"></el-option>
            <el-option label="培训改进" value="Training"></el-option>
            <el-option label="监控改进" value="Monitoring"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="优先级" prop="priority">
          <el-select v-model="actionForm.priority" placeholder="请选择优先级">
            <el-option label="高" value="High"></el-option>
            <el-option label="中" value="Medium"></el-option>
            <el-option label="低" value="Low"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="关联故障ID">
          <el-input 
            v-model="actionForm.incident_id" 
            placeholder="请输入故障ID（可选）"
            clearable>
          </el-input>
          <div class="form-tip">如果关联故障ID，系统将自动创建或关联到复盘记录</div>
        </el-form-item>
        
        <el-form-item label="负责人">
          <el-select v-model="actionForm.assignee_id" placeholder="请选择负责人" clearable>
            <el-option 
              v-for="user in users" 
              :key="user.id" 
              :label="user.real_name" 
              :value="user.id">
            </el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="截止时间">
          <el-date-picker
            v-model="actionForm.due_date"
            type="datetime"
            placeholder="请选择截止时间"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss">
          </el-date-picker>
        </el-form-item>
        
        <el-form-item label="外部链接">
          <el-input 
            v-model="actionForm.external_link" 
            placeholder="如Jira链接等（可选）">
          </el-input>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="createActionDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="createActionItem" :loading="creatingAction">创建</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRoute } from 'vue-router'
import request from '@/utils/request'
import { formatDateTime, formatDate } from '@/utils/date'

export default {
  name: 'PostMortems',
  setup() {
    const route = useRoute()
    
    // 响应式数据
    const loading = ref(false)
    const actionItemsLoading = ref(false)  // 添加改进措施列表的独立加载状态
    const postmortems = ref([])
    const statistics = ref({})
    const users = ref([])
    const actionItems = ref([])
    const currentPage = ref(1)
    const pageSize = ref(20)
    const total = ref(0)
    const filters = ref({
      status: '',
      author_id: ''
    })
    
    // 对话框状态
    const createActionDialogVisible = ref(false)
    const actionDetailDialogVisible = ref(false) // 新增改进措施详情对话框状态
    const selectedActionItem = ref(null) // 选中的改进措施详情
    const actionItemStatusLogs = ref([]) // 改进措施状态记录
    
    // 操作相关对话框状态
    const statusChangeDialogVisible = ref(false)
    const assigneeDialogVisible = ref(false)
    const dueDateDialogVisible = ref(false)
    const editDialogVisible = ref(false)
    
    // 操作相关表单
    const statusChangeForm = ref({
      new_status: '',
      comments: ''
    })
    
    const assigneeForm = ref({
      assignee_id: null,
      comments: ''
    })
    
    const dueDateForm = ref({
      due_date: '',
      comments: ''
    })
    
    const editForm = ref({
      title: '',
      description: '',
      category: '',
      priority: '',
      external_link: ''
    })
    
    // 操作相关表单验证规则
    const statusChangeRules = {
      new_status: [
        { required: true, message: '请选择新状态', trigger: 'change' }
      ],
      comments: [
        { required: true, message: '请填写操作说明', trigger: 'blur' }
      ]
    }
    
    const assigneeRules = {
      assignee_id: [
        { required: true, message: '请选择负责人', trigger: 'change' }
      ]
    }
    
    const dueDateRules = {
      due_date: [
        { required: true, message: '请选择截止时间', trigger: 'change' }
      ]
    }
    
    const editRules = {
      title: [
        { required: true, message: '请输入改进措施标题', trigger: 'blur' }
      ],
      description: [
        { required: true, message: '请输入改进措施描述', trigger: 'blur' }
      ],
      category: [
        { required: true, message: '请选择措施类别', trigger: 'change' }
      ],
      priority: [
        { required: true, message: '请选择优先级', trigger: 'change' }
      ]
    }
    
    // 操作相关加载状态
    const statusChanging = ref(false)
    const assigneeChanging = ref(false)
    const dueDateChanging = ref(false)
    const editing = ref(false)
    
    // 操作相关表单引用
    const statusChangeFormRef = ref(null)
    const assigneeFormRef = ref(null)
    const dueDateFormRef = ref(null)
    const editFormRef = ref(null)
    
    // 改进措施表单
    const actionForm = ref({
      title: '',
      description: '',
      category: 'Technical',
      priority: 'Medium',
      incident_id: '',
      assignee_id: null,
      due_date: '',
      external_link: ''
    })
    
    // 表单验证规则
    const actionRules = {
      title: [
        { required: true, message: '请输入改进措施标题', trigger: 'blur' }
      ],
      description: [
        { required: true, message: '请输入改进措施描述', trigger: 'blur' }
      ],
      category: [
        { required: true, message: '请选择措施类别', trigger: 'change' }
      ],
      priority: [
        { required: true, message: '请选择优先级', trigger: 'change' }
      ]
    }
    
    // 加载状态
    const creatingAction = ref(false)
    
    // 表单引用
    const actionFormRef = ref(null)
    
    // 加载数据
    const loadPostMortems = async () => {
      try {
        loading.value = true
        const params = {
          page: currentPage.value,
          per_page: pageSize.value,
          ...filters.value
        }
        const response = await request.get('/postmortems', { params })
        postmortems.value = response.postmortems || []
        total.value = response.pagination?.total || 0
      } catch (error) {
        console.error('加载复盘列表失败:', error)
        ElMessage.error('加载复盘列表失败')
      } finally {
        loading.value = false
      }
    }
    
    const loadStatistics = async () => {
      try {
        const response = await request.get('/postmortems/statistics')
        statistics.value = response
      } catch (error) {
        console.error('加载统计数据失败:', error)
      }
    }
    
    const loadUsers = async () => {
      try {
        const response = await request.get('/users')
        users.value = response.users || []
      } catch (error) {
        console.error('加载用户列表失败:', error)
      }
    }
    
    const loadActionItems = async () => {
      try {
        actionItemsLoading.value = true // 开始加载改进措施
        const params = {
          page: currentPage.value,
          per_page: pageSize.value,
          ...filters.value // 使用当前筛选条件
        }
        const response = await request.get('/action-items', { params })
        actionItems.value = response.action_items || []
        total.value = response.pagination?.total || 0 // 更新总条数
      } catch (error) {
        console.error('加载改进措施失败:', error)
        ElMessage.error('加载改进措施失败')
      } finally {
        actionItemsLoading.value = false // 结束加载改进措施
      }
    }
    
    // 加载改进措施状态记录
    const loadActionItemStatusLogs = async (actionItemId) => {
      try {
        console.log(`🔄 开始加载改进措施 ${actionItemId} 的状态记录...`)
        const response = await request.get(`/action-items/${actionItemId}/logs`)
        console.log('📡 API响应:', response)
        
        actionItemStatusLogs.value = response.logs || []
        console.log('📊 状态记录数组:', actionItemStatusLogs.value)
        console.log(`✅ 成功加载 ${actionItemStatusLogs.value.length} 条状态记录`)
        
      } catch (error) {
        console.error('❌ 加载改进措施状态记录失败:', error)
        actionItemStatusLogs.value = []
      }
    }
    
    // 工具方法
    const getStatusTagType = (status) => {
      const types = {
        Draft: 'info',
        'In Review': 'warning',
        Approved: 'success',
        Published: 'primary'
      }
      return types[status] || ''
    }
    
    const getStatusText = (status) => {
      const texts = {
        Draft: '草稿',
        'In Review': '审核中',
        Approved: '已审核',
        Published: '已发布'
      }
      return texts[status] || status
    }
    
    const getPriorityTagType = (priority) => {
      const types = { High: 'danger', Medium: 'warning', Low: 'info' }
      return types[priority] || ''
    }
    
    const getPriorityText = (priority) => {
      const texts = { High: '高', Medium: '中', Low: '低' }
      return texts[priority] || priority
    }

    const getCategoryText = (category) => {
      const texts = {
        Technical: '技术改进',
        Process: '流程改进',
        Documentation: '文档改进',
        Training: '培训改进',
        Monitoring: '监控改进'
      }
      return texts[category] || category
    }
    
    const getActionStatusTagType = (status) => {
      const types = {
        Open: 'danger',
        'In Progress': 'warning',
        Completed: 'success',
        Cancelled: 'info'
      }
      return types[status] || ''
    }
    
    const getActionStatusText = (status) => {
      const texts = {
        Open: '待处理',
        'In Progress': '进行中',
        Completed: '已完成',
        Cancelled: '已取消'
      }
      return texts[status] || status
    }
    
    // 获取状态记录的时间线类型
    const getStatusLogType = (status) => {
      const types = {
        Open: 'primary',
        'In Progress': 'warning',
        Completed: 'success',
        Cancelled: 'info'
      }
      return types[status] || 'info'
    }
    
    const getTotalActionItems = () => {
      return actionItems.value.length
    }
    
    const getCompletedActionItems = () => {
      return actionItems.value.filter(item => item.status === 'Completed').length
    }
    
    const viewActionItem = async (actionItem) => {
      selectedActionItem.value = actionItem // 设置选中的改进措施
      actionDetailDialogVisible.value = true // 显示改进措施详情对话框
      
      // 加载改进措施的状态记录
      await loadActionItemStatusLogs(actionItem.id)
    }
    
    // 操作相关函数
    const showStatusChangeDialog = () => {
      statusChangeForm.value = {
        new_status: '',
        comments: ''
      }
      statusChangeDialogVisible.value = true
    }
    
    const showAssigneeDialog = () => {
      assigneeForm.value = {
        assignee_id: selectedActionItem.value?.assignee_id || null,
        comments: ''
      }
      assigneeDialogVisible.value = true
    }
    
    const showDueDateDialog = () => {
      dueDateForm.value = {
        due_date: selectedActionItem.value?.due_date || '',
        comments: ''
      }
      dueDateDialogVisible.value = true
    }
    
    const showEditDialog = () => {
      editForm.value = {
        title: selectedActionItem.value?.title || '',
        description: selectedActionItem.value?.description || '',
        category: selectedActionItem.value?.category || '',
        priority: selectedActionItem.value?.priority || '',
        external_link: selectedActionItem.value?.external_link || ''
      }
      editDialogVisible.value = true
    }
    
    const submitStatusChange = async () => {
      try {
        await statusChangeFormRef.value.validate()
        statusChanging.value = true
        
        const response = await request.put(`/action-items/${selectedActionItem.value.id}/status`, {
          new_status: statusChangeForm.value.new_status,
          comments: statusChangeForm.value.comments
        })
        
        ElMessage.success('状态变更成功')
        statusChangeDialogVisible.value = false
        
        // 刷新数据
        await loadActionItemStatusLogs(selectedActionItem.value.id)
        await loadActionItems()
        
        // 更新选中的改进措施
        selectedActionItem.value = response.action_item
        
      } catch (error) {
        console.error('状态变更失败:', error)
        ElMessage.error(error.response?.data?.error || '状态变更失败')
      } finally {
        statusChanging.value = false
      }
    }
    
    const submitAssigneeChange = async () => {
      try {
        await assigneeFormRef.value.validate()
        assigneeChanging.value = true
        
        const response = await request.put(`/action-items/${selectedActionItem.value.id}/assignee`, {
          assignee_id: assigneeForm.value.assignee_id,
          comments: assigneeForm.value.comments
        })
        
        ElMessage.success('负责人分配成功')
        assigneeDialogVisible.value = false
        
        // 刷新数据
        await loadActionItemStatusLogs(selectedActionItem.value.id)
        await loadActionItems()
        
        // 更新选中的改进措施
        selectedActionItem.value = response.action_item
        
      } catch (error) {
        console.error('分配负责人失败:', error)
        ElMessage.error(error.response?.data?.error || '分配负责人失败')
      } finally {
        assigneeChanging.value = false
      }
    }
    
    const submitDueDateChange = async () => {
      try {
        await dueDateFormRef.value.validate()
        dueDateChanging.value = true
        
        const response = await request.put(`/action-items/${selectedActionItem.value.id}/due-date`, {
          due_date: dueDateForm.value.due_date,
          comments: dueDateForm.value.comments
        })
        
        ElMessage.success('截止时间设置成功')
        dueDateDialogVisible.value = false
        
        // 刷新数据
        await loadActionItemStatusLogs(selectedActionItem.value.id)
        await loadActionItems()
        
        // 更新选中的改进措施
        selectedActionItem.value = response.action_item
        
      } catch (error) {
        console.error('设置截止时间失败:', error)
        ElMessage.error(error.response?.data?.error || '设置截止时间失败')
      } finally {
        dueDateChanging.value = false
      }
    }
    
    const submitEdit = async () => {
      try {
        await editFormRef.value.validate()
        editing.value = true
        
        const response = await request.put(`/action-items/${selectedActionItem.value.id}`, editForm.value)
        
        ElMessage.success('信息更新成功')
        editDialogVisible.value = false
        
        // 刷新数据
        await loadActionItemStatusLogs(selectedActionItem.value.id)
        await loadActionItems()
        
        // 更新选中的改进措施
        selectedActionItem.value = response.action_item
        
      } catch (error) {
        console.error('更新信息失败:', error)
        ElMessage.error(error.response?.data?.error || '更新信息失败')
      } finally {
        editing.value = false
      }
    }
    
    const completeActionItem = async () => {
      try {
        await ElMessageBox.confirm(
          '确定要将此改进措施标记为已完成吗？',
          '确认操作',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        
        statusChanging.value = true
        
        const response = await request.put(`/action-items/${selectedActionItem.value.id}/status`, {
          new_status: 'Completed',
          comments: '改进措施已完成'
        })
        
        ElMessage.success('改进措施已标记为完成')
        
        // 刷新数据
        await loadActionItemStatusLogs(selectedActionItem.value.id)
        await loadActionItems()
        
        // 更新选中的改进措施
        selectedActionItem.value = response.action_item
        
      } catch (error) {
        if (error !== 'cancel') {
          console.error('标记完成失败:', error)
          ElMessage.error(error.response?.data?.error || '标记完成失败')
        }
      } finally {
        statusChanging.value = false
      }
    }
    
    const viewPostMortem = (postmortem) => {
      ElMessage.info('复盘详情功能开发中...')
    }
    
    const editPostMortem = (postmortem) => {
      ElMessage.info('编辑复盘功能开发中...')
    }
    
    const canEdit = (postmortem) => {
      return postmortem.status === 'Draft'
    }
    
    const showAddActionDialog = () => {
      // 重置表单
      actionForm.value = {
        title: '',
        description: '',
        category: 'Technical',
        priority: 'Medium',
        incident_id: route.query.create_from_incident || '',
        assignee_id: null,
        due_date: '',
        external_link: ''
      }
      
      // 显示对话框
      createActionDialogVisible.value = true
    }
    
    const createActionItem = async () => {
      try {
        // 验证表单
        await actionFormRef.value.validate()
        
        creatingAction.value = true
        
        // 准备提交数据
        const submitData = {
          title: actionForm.value.title,
          description: actionForm.value.description,
          category: actionForm.value.category,
          priority: actionForm.value.priority,
          assignee_id: actionForm.value.assignee_id,
          due_date: actionForm.value.due_date,
          external_link: actionForm.value.external_link
        }
        
        // 如果有故障ID，添加到提交数据中
        if (actionForm.value.incident_id && actionForm.value.incident_id.trim()) {
          submitData.incident_id = actionForm.value.incident_id.trim()
        }
        
        // 创建改进措施
        const response = await request.post('/action-items', submitData)
        
        ElMessage.success('改进措施创建成功')
        
        // 关闭对话框
        createActionDialogVisible.value = false
        
        // 刷新数据
        loadActionItems()
        loadPostMortems()
        loadStatistics()
        
      } catch (error) {
        if (error !== 'cancel') {
          console.error('创建改进措施失败:', error)
          ElMessage.error('创建改进措施失败')
        }
      } finally {
        creatingAction.value = false
      }
    }
    
    const refreshData = () => {
      loadPostMortems()
      loadStatistics()
      loadActionItems()
    }
    
    const handleSizeChange = (size) => {
      pageSize.value = size
      loadPostMortems()
      loadActionItems() // 改进措施列表也刷新
    }
    
    const handleCurrentChange = (page) => {
      currentPage.value = page
      loadPostMortems()
      loadActionItems() // 改进措施列表也刷新
    }
    
    onMounted(() => {
      loadPostMortems()
      loadStatistics()
      loadUsers()
      loadActionItems()
      
      // 检查是否从故障管理页面跳转过来
      if (route.query.create_from_incident) {
        // 提示用户
        ElMessage.info(`正在为故障"${route.query.incident_title}"准备复盘记录，请联系管理员创建复盘`)
      }
    })
    
    return {
      loading,
      postmortems,
      statistics,
      users,
      actionItems,
      currentPage,
      pageSize,
      total,
      filters,
      createActionDialogVisible,
      actionForm,
      actionRules,
      actionFormRef,
      creatingAction,
      loadPostMortems,
      viewPostMortem,
      editPostMortem,
      getStatusText,
      getStatusTagType,
      getPriorityText,
      getPriorityTagType,
      getCategoryText,
      getActionStatusText,
      getActionStatusTagType,
      getStatusLogType, // 添加状态记录时间线类型函数
      viewActionItem,
      showAddActionDialog,
      createActionItem,
      refreshData,
      handleSizeChange,
      handleCurrentChange,
      formatDateTime,
      formatDate,
      getTotalActionItems,
      getCompletedActionItems,
      canEdit,
      actionItemsLoading, // 暴露改进措施列表的加载状态
      actionDetailDialogVisible, // 暴露改进措施详情对话框状态
      selectedActionItem, // 暴露选中的改进措施详情
      actionItemStatusLogs, // 暴露改进措施的状态记录
      
      // 操作相关对话框状态
      statusChangeDialogVisible,
      assigneeDialogVisible,
      dueDateDialogVisible,
      editDialogVisible,
      
      // 操作相关表单
      statusChangeForm,
      assigneeForm,
      dueDateForm,
      editForm,
      
      // 操作相关表单验证规则
      statusChangeRules,
      assigneeRules,
      dueDateRules,
      editRules,
      
      // 操作相关加载状态
      statusChanging,
      assigneeChanging,
      dueDateChanging,
      editing,
      
      // 操作相关表单引用
      statusChangeFormRef,
      assigneeFormRef,
      dueDateFormRef,
      editFormRef,
      
      // 操作相关函数
      showStatusChangeDialog,
      showAssigneeDialog,
      showDueDateDialog,
      showEditDialog,
      submitStatusChange,
      submitAssigneeChange,
      submitDueDateChange,
      submitEdit,
      completeActionItem
    }
  }
}
</script>

<style scoped>
.postmortem-page {
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

.filters {
  margin-bottom: 20px;
  padding: 20px;
  background: #f5f5f5;
  border-radius: 4px;
}

.incident-link {
  color: #409eff;
  cursor: pointer;
}

.incident-link:hover {
  text-decoration: underline;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.content-sections {
  margin-top: 20px;
}

.section {
  margin-bottom: 20px;
}

.section h4 {
  margin: 0 0 10px 0;
  color: #409eff;
  font-size: 16px;
}

.section-content {
  padding: 15px;
  background: #f9f9f9;
  border-radius: 4px;
  line-height: 1.6;
  white-space: pre-line;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.section-header h4 {
  margin: 0;
  color: #409eff;
}

.action-items-card .el-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-items-card .el-card__header .el-button {
  margin-left: 10px;
}

.description-cell {
  white-space: pre-wrap;
  word-break: break-word;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

.action-item-detail .el-descriptions {
  margin-bottom: 20px;
}

.action-item-detail .el-descriptions__header {
  margin-bottom: 10px;
}

.action-item-detail .el-descriptions__header h4 {
  margin: 0;
  color: #409eff;
}

.action-item-detail .el-descriptions__body {
  padding: 0 10px;
}

.action-item-detail .el-descriptions__cell {
  padding: 8px 10px;
}

.action-item-detail .el-descriptions__label {
  font-weight: bold;
  color: #333;
}

.action-item-detail .el-descriptions__value {
  color: #666;
  font-size: 14px;
}

.action-item-detail .el-descriptions__value .incident-link {
  color: #409eff;
  cursor: pointer;
}

.action-item-detail .el-descriptions__value .incident-link:hover {
  text-decoration: underline;
}

.action-item-detail .el-descriptions__value .external-link {
  color: #409eff;
  text-decoration: none;
}

.action-item-detail .el-descriptions__value .external-link:hover {
  text-decoration: underline;
}

.status-logs-section {
  margin-top: 20px;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 4px;
}

.status-logs-section h4 {
  margin: 0 0 10px 0;
  color: #409eff;
  font-size: 16px;
}

.status-log-item {
  padding: 10px 0;
  border-bottom: 1px solid #eee;
}

.status-log-item:last-child {
  border-bottom: none;
}

.status-change {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}

.status-change .status-label {
  font-weight: bold;
  color: #333;
}

.status-change .arrow {
  margin: 0 5px;
}

.status-action {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}

.status-action .action-label {
  font-weight: bold;
  color: #333;
}

.status-comments {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}

.status-comments .comments-label {
  font-weight: bold;
  color: #333;
}

.status-user {
  font-size: 14px;
  color: #666;
}

.status-user .user-label {
  font-weight: bold;
  color: #333;
}

.no-status-logs {
  text-align: center;
  padding: 20px;
}

.no-status-logs .el-empty__description {
  color: #909399;
}

.action-buttons-section {
  margin-top: 20px;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 4px;
}

.action-buttons-section h4 {
  margin: 0 0 10px 0;
  color: #409eff;
  font-size: 16px;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.action-buttons .el-button {
  flex: 1;
  min-width: 120px;
}
</style>