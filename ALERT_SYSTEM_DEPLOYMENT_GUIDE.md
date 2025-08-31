# 故障管理系统重新设计 - 部署指南

## 📋 概述

本文档描述了如何部署和测试重新设计的故障管理系统。系统已从"事后处理"升级为"主动告警管理"，实现了完整的故障管理闭环。

## 🎯 主要变化

### 新增功能
- **告警管理** (`/alerts`) - 监控系统告警的统一入口
- **新故障管理** (`/incidents-new`) - 看板式故障管理界面
- **复盘管理** (`/postmortems`) - 结构化复盘和改进措施跟踪

### 架构变化
- `Alert` - 新增告警模型，代表监控系统的单个告警
- `Incident` - 重新设计，代表确认的业务影响故障
- `PostMortem` - 新增复盘模型
- `ActionItem` - 新增改进措施模型
- `IncidentTimeline` - 新增时间线模型

## 🚀 部署步骤

### 1. 数据库迁移

**重要提醒**: 请在生产环境操作前先在测试环境验证！

```bash
# 进入后端目录
cd backend

# 备份现有数据库
mysqldump -u username -p database_name > backup_$(date +%Y%m%d_%H%M%S).sql

# 执行数据迁移脚本
python migrate_alert_system.py
```

迁移脚本会执行以下操作：
- 备份现有 `incidents` 表为 `incidents_backup`
- 创建新的表结构（`alerts`, `incidents_new`, `post_mortems` 等）
- 将现有数据迁移到新结构
- 为关键告警自动创建故障记录

### 2. 后端部署

```bash
# 更新依赖（如有新增）
pip install -r requirements.txt

# 启动后端服务
python run.py
```

后端会在 `http://localhost:5001` 启动。

### 3. 前端部署

```bash
# 进入前端目录
cd frontend

# 安装依赖（如有更新）
npm install

# 启动前端服务
npm run dev
```

前端会在 `http://localhost:3000` 启动。

### 4. 验证部署

#### 检查新API端点

```bash
# 检查告警API
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:5001/api/v1/alerts

# 检查新故障API
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:5001/api/v1/incidents

# 检查复盘API
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:5001/api/v1/postmortems
```

#### 验证前端页面

访问以下页面确认功能正常：
- `http://localhost:3000/alerts` - 告警管理
- `http://localhost:3000/incidents-new` - 新故障管理
- `http://localhost:3000/postmortems` - 复盘管理

## 🧪 功能测试指南

### 告警管理测试

1. **创建测试告警**：
```bash
curl -X POST http://localhost:5001/api/v1/alerts \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "title": "CPU使用率过高",
    "description": "服务器CPU使用率超过90%",
    "level": "Critical",
    "alert_source": "Prometheus",
    "fired_at": "2024-08-30T10:00:00Z"
  }'
```

2. **测试告警操作**：
   - 确认告警
   - 忽略告警
   - 批量操作

### 故障管理测试

1. **创建故障**：
   - 从告警创建故障
   - 手动创建故障
   - 测试故障状态流转

2. **状态流转测试**：
   ```
   待确认 → 处理中 → 恢复中 → 已恢复 → 待复盘 → 已关闭
   ```

3. **应急响应测试**：
   - 触发应急响应
   - 验证通知发送
   - 测试时间线记录

### 复盘管理测试

1. **创建复盘**：
   - 为已恢复故障创建复盘
   - 填写复盘内容
   - 添加改进措施

2. **复盘流程测试**：
   ```
   草稿 → 审核中 → 已审核 → 已发布
   ```

3. **改进措施跟踪**：
   - 创建改进措施
   - 分配责任人
   - 跟踪完成状态

## 📊 监控和维护

### 性能监控

监控以下关键指标：
- 告警处理时间
- 故障解决时间（MTTR）
- 故障检测时间（MTTD）
- 复盘完成率

### 数据清理

定期清理历史数据：
```sql
-- 清理90天前的已关闭故障的告警
DELETE FROM alerts 
WHERE status = 'Linked' 
AND incident_id IN (
  SELECT id FROM incidents 
  WHERE status = 'Closed' 
  AND closed_at < DATE_SUB(NOW(), INTERVAL 90 DAY)
);
```

### 备份策略

- 每日自动备份数据库
- 保留30天备份历史
- 定期测试恢复流程

## 🔧 故障排除

### 常见问题

1. **迁移失败**
   ```bash
   # 回滚到备份
   mysql -u username -p database_name < backup_filename.sql
   ```

2. **API 404错误**
   - 检查路由注册：`backend/app/api/__init__.py`
   - 确认新API文件已正确导入

3. **前端页面空白**
   - 检查路由配置：`frontend/src/router/index.js`
   - 确认组件路径正确

4. **权限错误**
   - 确认用户具有相应权限
   - 检查JWT token有效性

### 日志查看

```bash
# 后端日志
tail -f backend/logs/app.log

# 前端控制台
# 打开浏览器开发者工具查看Console
```

## 🔄 回滚计划

如果需要回滚到原系统：

1. **停止新系统服务**
2. **恢复数据库**：
   ```sql
   DROP TABLE incidents;
   ALTER TABLE incidents_backup RENAME TO incidents;
   ```
3. **重启原系统**
4. **验证功能**

## 📞 技术支持

遇到问题请联系：
- 技术负责人：[联系信息]
- 系统管理员：[联系信息]
- 紧急联系：[24小时支持热线]

---

## 📝 更新日志

### v2.0.0 (2024-08-30)
- ✅ 完成故障管理系统重新设计
- ✅ 实现告警管理功能
- ✅ 新增复盘管理流程
- ✅ 添加故障时间线功能
- ✅ 支持应急响应机制

### 下一步计划
- 🔄 集成第三方监控系统
- 🔄 添加移动端支持
- 🔄 实现智能告警聚合
- 🔄 增强数据分析功能