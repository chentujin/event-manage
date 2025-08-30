import request from '@/utils/request'

// 认证相关API
export const auth = {
  login: (data) => request.post('/auth/login', data),
  getUserInfo: () => request.get('/auth/me'),
}

// 事件管理API
export const incidents = {
  list: (params) => request.get('/incidents', { params }),
  create: (data) => request.post('/incidents', data),
  get: (id) => request.get(`/incidents/${id}`),
  update: (id, data) => request.put(`/incidents/${id}`, data),
  getLogs: (id) => request.get(`/incidents/${id}/logs`),
  getAssignableUsers: () => request.get('/incidents/assignable-users'),
}

// 故障管理API
export const problems = {
  list: (params) => request.get('/problems', { params }),
  create: (data) => request.post('/problems', data),
  get: (id) => request.get(`/problems/${id}`),
  update: (id, data) => request.put(`/problems/${id}`, data),
  getLogs: (id) => request.get(`/problems/${id}/logs`),
}

// 服务管理API
export const services = {
  list: (params) => request.get('/services', { params }),
  create: (data) => request.post('/services', data),
  update: (id, data) => request.put(`/services/${id}`, data),
  delete: (id) => request.delete(`/services/${id}`),
}

// 用户管理API
export const users = {
  list: (params) => request.get('/users', { params }),
  create: (data) => request.post('/users', data),
  update: (id, data) => request.put(`/users/${id}`, data),
  toggleStatus: (id, isActive) => request.put(`/users/${id}/status`, { is_active: isActive }),
  roles: () => request.get('/roles'),
  groups: () => request.get('/groups'),
  createGroup: (data) => request.post('/groups', data),
  updateGroup: (id, data) => request.put(`/groups/${id}`, data),
  deleteGroup: (id) => request.delete(`/groups/${id}`),
  getGroupMembers: (id) => request.get(`/groups/${id}/members`),
  addGroupMember: (groupId, userId) => request.post(`/groups/${groupId}/members`, { user_id: userId }),
  removeGroupMember: (groupId, userId) => request.delete(`/groups/${groupId}/members/${userId}`),
}

// 仪表盘API
export const dashboard = {
  overview: () => request.get('/dashboard/overview'),
  incidentStats: () => request.get('/dashboard/incident-stats'),
  eventStatusDistribution: () => request.get('/dashboard/event-status-distribution'),
}

// 审批管理API
export const approvals = {
  list: (params) => request.get('/approvals', { params }),
  get: (id) => request.get(`/approvals/${id}`),
  approve: (id, data) => request.post(`/approvals/${id}/approve`, data),
  reject: (id, data) => request.post(`/approvals/${id}/reject`, data),
  workflows: () => request.get('/approval-workflows'),
  createWorkflow: (data) => request.post('/approval-workflows', data),
  updateWorkflow: (id, data) => request.put(`/approval-workflows/${id}`, data),
  deleteWorkflow: (id) => request.delete(`/approval-workflows/${id}`),
}

// 通知管理API
export const notifications = {
  channels: () => request.get('/notification/channels'),
  preferences: () => request.get('/notification/preferences'),
  updatePreferences: (data) => request.put('/notification/preferences', data),
  logs: (params) => request.get('/notification/logs', { params }),
  test: (data) => request.post('/notification/test', data),
}