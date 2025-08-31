# 服务管理脚本使用说明

## 📋 概述

本项目提供了两个服务管理脚本，用于方便地管理前端和后端服务：

- `frontend_service.sh` - 前端服务管理脚本
- `backend_service.sh` - 后端服务管理脚本

## 🚀 前端服务管理脚本

### 功能特性
- ✅ 启动前端开发服务器
- ✅ 停止前端服务
- ✅ 重启前端服务
- ✅ 查看服务状态
- ✅ 自动清理Vite缓存
- ✅ 端口占用检查
- ✅ 彩色日志输出
- ✅ PID文件管理

### 使用方法

```bash
# 启动前端服务
./frontend_service.sh start

# 停止前端服务
./frontend_service.sh stop

# 重启前端服务
./frontend_service.sh restart

# 查看服务状态
./frontend_service.sh status

# 显示帮助信息
./frontend_service.sh help
```

### 配置说明
- **服务端口**: 3000
- **工作目录**: `/Users/chen/Qoder/event-manage/frontend`
- **PID文件**: `/tmp/frontend_service.pid`
- **日志文件**: `/tmp/frontend.log`

## 🐍 后端服务管理脚本

### 功能特性
- ✅ 启动Flask后端服务
- ✅ 停止后端服务
- ✅ 重启后端服务
- ✅ 查看服务状态
- ✅ 自动数据库检查
- ✅ 依赖包验证
- ✅ 健康检查测试
- ✅ 端口占用检查
- ✅ 彩色日志输出
- ✅ PID文件管理

### 使用方法

```bash
# 启动后端服务
./backend_service.sh start

# 停止后端服务
./backend_service.sh stop

# 重启后端服务
./backend_service.sh restart

# 查看服务状态
./backend_service.sh status

# 显示帮助信息
./backend_service.sh help
```

### 配置说明
- **服务端口**: 5001
- **工作目录**: `/Users/chen/Qoder/event-manage/backend`
- **PID文件**: `/tmp/backend_service.pid`
- **日志文件**: `/tmp/backend.log`
- **Python命令**: python3

## 🔧 快速启动指南

### 1. 启动所有服务
```bash
# 启动后端服务
./backend_service.sh start

# 等待后端启动完成后，启动前端服务
./frontend_service.sh start
```

### 2. 停止所有服务
```bash
# 停止前端服务
./frontend_service.sh stop

# 停止后端服务
./backend_service.sh stop
```

### 3. 重启所有服务
```bash
# 重启后端服务
./backend_service.sh restart

# 重启前端服务
./frontend_service.sh restart
```

### 4. 查看所有服务状态
```bash
# 查看后端服务状态
./backend_service.sh status

# 查看前端服务状态
./frontend_service.sh status
```

## 📊 服务状态说明

### 前端服务状态
- **运行中**: 显示PID、端口状态、进程信息、最新日志
- **未运行**: 显示未运行状态
- **启动失败**: 显示错误信息和日志

### 后端服务状态
- **运行中**: 显示PID、端口状态、进程信息、API健康检查、最新日志
- **未运行**: 显示未运行状态
- **启动失败**: 显示错误信息和日志

## 🚨 故障排除

### 常见问题

#### 1. 端口被占用
```bash
# 查看端口占用情况
lsof -i :3000  # 前端端口
lsof -i :5001  # 后端端口

# 强制释放端口
kill -9 <PID>
```

#### 2. 权限不足
```bash
# 添加执行权限
chmod +x frontend_service.sh backend_service.sh
```

#### 3. 依赖缺失
```bash
# 前端依赖
cd frontend && npm install

# 后端依赖
cd backend && pip install -r requirements.txt
```

#### 4. 数据库问题
```bash
# 重新初始化数据库
cd backend && python3 init_db.py
```

### 日志查看
```bash
# 查看前端日志
tail -f /tmp/frontend.log

# 查看后端日志
tail -f /tmp/backend.log
```

## 🔄 自动化脚本

### 一键启动脚本
```bash
#!/bin/bash
echo "启动事件管理系统..."

echo "1. 启动后端服务..."
./backend_service.sh start

echo "2. 等待后端启动..."
sleep 10

echo "3. 启动前端服务..."
./frontend_service.sh start

echo "4. 服务启动完成！"
echo "前端地址: http://localhost:3000"
echo "后端地址: http://localhost:5001"
```

### 一键停止脚本
```bash
#!/bin/bash
echo "停止事件管理系统..."

echo "1. 停止前端服务..."
./frontend_service.sh stop

echo "2. 停止后端服务..."
./backend_service.sh stop

echo "3. 所有服务已停止！"
```

## 📝 注意事项

1. **启动顺序**: 建议先启动后端服务，再启动前端服务
2. **端口配置**: 确保端口3000和5001未被其他服务占用
3. **依赖检查**: 脚本会自动检查必要的依赖是否安装
4. **日志管理**: 日志文件会自动备份，避免丢失
5. **进程管理**: 使用PID文件确保进程管理的准确性

## 🎯 使用建议

1. **开发环境**: 使用 `start` 和 `stop` 命令管理服务
2. **调试问题**: 使用 `status` 命令查看详细状态信息
3. **更新代码**: 使用 `restart` 命令快速重启服务
4. **监控服务**: 定期使用 `status` 命令检查服务健康状态

## 📞 技术支持

如果遇到问题，请检查：
1. 脚本执行权限
2. 端口占用情况
3. 依赖包安装状态
4. 日志文件内容
5. 目录路径配置
