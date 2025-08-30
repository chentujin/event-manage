# 事件与故障管理平台

基于ITIL框架和SRE实践的企业级事件管理与故障管理平台。

## 项目特性

- **事件管理**：完整的事件生命周期管理，支持多种创建方式
- **故障管理**：根本原因分析和知识库管理
- **权限管理**：基于角色的访问控制(RBAC)
- **审批流程**：可配置的多级审批系统
- **通知集成**：多渠道通知（邮件、短信、IM、语音电话）
- **数据分析**：仪表盘和报表功能

## 技术栈

- **后端**: Python 3.9+, Flask 2.3+, SQLAlchemy
- **数据库**: MySQL 8.0+
- **前端**: Vue 3.x
- **认证**: JWT (JSON Web Tokens)

## 项目结构

```
event-manage/
├── backend/                 # Flask后端应用
│   ├── app/                # 主应用模块
│   │   ├── models/         # 数据模型
│   │   ├── api/           # API路由
│   │   ├── auth/          # 认证模块
│   │   ├── notification/  # 通知模块
│   │   └── utils/         # 工具函数
│   ├── migrations/        # 数据库迁移
│   ├── tests/            # 测试用例
│   ├── config.py         # 配置文件
│   ├── run.py           # 应用启动入口
│   └── requirements.txt  # Python依赖
├── frontend/            # Vue.js前端应用
├── docs/               # 文档
└── docker/            # Docker配置
```

## 快速开始

### 后端设置

1. 安装依赖：
```bash
cd backend
pip install -r requirements.txt
```

2. 配置数据库：
```bash
# 编辑 config.py 中的数据库连接信息
# 运行数据库初始化
python run.py init-db
```

3. 启动后端服务：
```bash
python run.py
```

### 前端设置

1. 安装依赖：
```bash
cd frontend
npm install
```

2. 启动开发服务器：
```bash
npm run dev
```

## API文档

后端服务启动后，访问 `/api/docs` 查看完整的API文档。

## 许可证

MIT License