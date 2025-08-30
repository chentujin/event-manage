# **事件与故障管理平台需求文档 (完整版)**

## **1. 项目概述**

### **1.1. 项目目标**
开发一个基于Web的、符合ITIL框架核心理念、并融入Google SRE实践的事件管理与故障管理平台。该平台旨在：
1.  **集中化管理**：为IT部门提供一个统一的入口来记录、跟踪、处理和归档所有事件（Incident）和故障（Problem）。
2.  **标准化流程**：引导用户遵循ITIL定义的标准化流程，确保处理过程的一致性和可追溯性。
3.  **提升效率**：通过自动化、清晰的协作和通信机制，减少平均修复时间（MTTR）。
4.  **生成洞察**：通过数据分析和报告，识别重复发生的事件、系统薄弱环节，为主动性问题管理提供数据支撑。
5.  **SRE集成**：集成SLO/SLI监控，将事件与服务的健康度直接关联。
6.  **全链路通知**：通过多渠道（邮件、短信、IM、语音电话）确保关键信息及时送达。

### **1.2. 目标用户**
- **一线支持 / 服务台**：接收和初步分类事件。
- **SRE / 运维工程师**：处理技术性事件，参与故障排查。
- **研发工程师**：协助处理与自身开发服务相关的深度故障。
- **团队负责人 / 经理**：监督处理进度，审批变更，查看分析报告。
- **On-Call值班人员**：接收并响应紧急告警。
- **其他利益相关者**：接收事件状态通知（如业务部门）。

### **1.3. 技术栈**
- **后端框架**: Python 3.9+, Flask 2.3+
- **数据库**: MySQL 8.0+
- **前端**: Vue 3.x
- **ORM**: SQLAlchemy
- **认证**: JWT (JSON Web Tokens)
- **API**: RESTful API
- **日志**：日志输出到文件中，包含：时间、日志级别、用户、操作内容或错误信息
- **配置**：配置文件存放于`config.py`中，包含：数据库连接信息、日志配置、JWT密钥等。
---

## **2. 核心概念与定义 (ITIL & SRE)**
- **事件 (Incident)**: 任何非计划内的服务中断、服务质量降低或尚未对服务造成影响但可能造成影响的事件。**核心是“尽快恢复服务”**。
- **故障 (Problem)**: 导致一个或多个事件发生的根本原因。**核心是“找到并消除根因”**。
- **已知错误 (Known Error)**: 已成功诊断并找到根本原因的故障，通常已有临时规避措施或永久性解决方案（通过变更请求实现）。
- **SLO (服务等级目标)**: 对服务可靠性目标的明确衡量指标（如“99.9%可用性”）。
- **SLI (服务等级指标)**: 用于衡量SLO的具体指标（如“请求成功率”、“错误率”）。

---

## **3. 功能需求**

### **3.1. 事件管理 (Incident Management)模块**

#### **3.1.1. 事件录入**
- 支持多种创建方式：
  - **手动创建**：通过Web表单。
  - **API创建**：提供`/api/v1/incidents` (POST)接口，允许监控系统（如Prometheus）、CI/CD工具、或其他系统自动创建事件。
- 必填字段：
  - `标题 (Title)`: 简短描述。
  - `描述 (Description)`: 详细的现象、报错信息、影响范围。
  - `影响度 (Impact)`: 下拉选择（高/中/低）。定义对业务的影响范围（如：全部用户/部分用户/单个用户）。
  - `紧急度 (Urgency)`: 下拉选择（高/中/低）。定义问题需要解决的速度。
  - **自动计算** `优先级 (Priority)`：规则为 `Priority = Impact + Urgency`（例如，高影响+高紧急=紧急优先级）。
  - `提交人 (Reporter)`: 自动关联当前登录用户或通过API传入。
  - `关联服务 (Service)`: 下拉选择受影响的业务服务（需提前配置服务目录）。
- 选填字段：
  - `附件 (Attachments)`: 上传日志、截图等文件。

#### **3.1.2. 事件生命周期与状态流转**
状态必须遵循以下流程，并记录每次状态变更的时间戳和操作人：
`新建 (New)` -> `处理中 (In Progress)` -> `已解决 (Resolved)` -> `已关闭 (Closed)`
- **重新打开**：从`已解决`状态可被`重新打开 (Reopened)`，回到`处理中`状态，需填写重新打开原因。
- **挂起**：可置为`挂起 (On Hold)`状态（如：等待其他团队响应），需填写挂起原因和预计恢复时间。

#### **3.1.3. 事件分配与协作**
- **指派**：可将事件指派给个人或一个小组（如“SRE-OnCall”、“后端开发组”）。
- **评论系统**：支持富文本评论，@提及用户（被提及用户需收到通知），用于记录排查过程和内部协作。
- **工作日志**：记录处理人员花费在该事件上的有效时间（手动填写），用于后续效率分析。

#### **3.1.4. 事件搜索与列表视图**
- 强大的列表过滤和搜索功能：按状态、优先级、指派给、服务、创建时间等组合筛选。
- 列表显示关键字段：ID、标题、优先级、状态、指派给、创建时间、最后更新时间。
- 支持导出筛选结果为CSV。

### **3.2. 故障管理 (Problem Management)模块**

#### **3.2.1. 故障创建**
- **手动创建**：用户根据经验或分析，手动创建一个故障记录。
- **自动关联**：在事件解决时，提供一个“创建故障”按钮，自动将事件信息、评论、附件关联到新的故障记录中。
- **必填字段**：`标题`，`描述`，`状态`（新建、调查中、已知错误、已关闭），`优先级`。

#### **3.2.2. 故障调查**
- **关联事件**：一个故障可以关联多个**事件**，用于分析共同模式。
- **根本原因分析 (RCA)**：提供专用字段记录根因分析过程和最终结论。
- **解决方案**：记录永久性解决方案（通常链接到一个变更请求ID）或临时规避措施。

#### **3.2.3. 已知错误管理**
- 当故障根因明确但尚未修复时，状态可置为`已知错误 (Known Error)`。
- 已知错误数据库应对所有支持人员可见，在处理新事件时可快速匹配已知错误并提供临时解决方案，加速事件解决。

#### **3.2.4. 故障审批流程**
- 对于需要实施重大变更的故障解决方案，可触发审批流程。
- **发起审批**：用户点击“提交审批”按钮，选择预定义的审批流程。
- **审批任务**：审批人在其“待办事项”中收到任务，可批准或拒绝并填写意见。
- **状态联动**：
  - 审批中：故障进入`待审批 (Pending Approval)`状态。
  - 审批通过：状态自动变为`已批准 (Approved)`或`已关闭 (Closed)`。
  - 审批被拒：状态回退到`调查中 (Investigating)`。

### **3.3. 服务与配置管理数据库 (CMDB) 集成**
- **服务目录**：预定义公司提供的业务服务（如“用户登录API”、“支付服务”），用于事件关联。

### **3.4. 报表与分析**
- **核心仪表盘 (Dashboard)**：
  - 实时显示：当前未解决事件数量（按优先级分组）。
  - MTTR (平均解决时间) 趋势图。
  - 事件数量趋势图（按日/周/月）。
  - TOP N 最常出现事件的服务。
- **标准报表**：
  - 事件报表：按时间、服务、团队分类统计。
  - 故障报表：显示所有已关闭的故障及其根因分类。

### **3.5. 系统管理**
- **用户与权限管理 (RBAC)**：
  - 角色：管理员、经理、工程师、只读用户。
  - 权限控制：例如，只有管理员和指派人可以修改事件状态/优先级；只读用户只能查看。
- **服务目录管理**：管理员可增删改服务。
- **配置项管理**：管理员可增删改基础CI。

### **3.6. 用户、组与角色管理**

#### **3.6.1. 用户管理**
- **用户注册**：
  - 提供用户注册页面，但注册请求默认状态为“禁用”，**必须由管理员审批激活**。
  - 注册字段：`用户名`（唯一）、`邮箱`（唯一）、`密码`、`真实姓名`、`所属部门`、`手机号码`（可选）。
- **用户生命周期**：状态包括 `待激活` -> `激活` -> `禁用`。
- **用户信息管理**：管理员可编辑所有用户信息，包括重置密码。用户可编辑自己的部分信息（如真实姓名、手机号码）。

#### **3.6.2. 组管理**
- 组用于**组织用户**和**简化权限分配**。例如：“SRE-北京团队”、“后端开发组”、“数据库管理员组”。
- 一个用户可以属于多个组。
- 管理员可以创建、编辑、删除组，并管理组的成员。

#### **3.6.3. 角色与权限管理 (RBAC)**
- 系统权限由**角色**控制，而非直接分配给用户或组。
- **角色定义**：系统预定义一系列角色，每个角色对应一组明确的权限（如`incident:write`, `problem:approve`）。
  - **超级管理员 (Admin)**：拥有所有权限，管理系统基础设置。
  - **故障经理 (Problem Manager)**：拥有故障相关所有权限，特别是**审批权限**。
  - **工程师 (Engineer)**：可以创建、编辑、解决事件和故障。
  - **只读用户 (Viewer)**：只能查看数据，不能进行任何修改。
  - **服务台 (Service Desk)**：专注于事件管理，权限介于工程师和只读用户之间。
- **权限分配**：将角色分配给**组**或**个人用户**。优先分配给组，以实现高效管理。

### **3.7. 集成审批流程**
- 系统需支持可配置的审批流程，由多个**审批节点**组成。
- 每个节点指定**审批人类型**：可以是“指定用户”、“指定角色”或“指定组的负责人”。
- 审批任务自动通知审批人，审批结果与故障状态联动。

### **3.8. 通知集成模块 (Notification Integration Module)**

该模块负责将系统内的重要动态通过多种渠道主动推送给相关用户或外部系统。

#### **3.8.1. 通知渠道管理**
系统需支持以下通知渠道：
1.  **邮件 (Email)**：通过SMTP服务器发送邮件。
2.  **短信 (SMS)**：通过第三方SMS API网关发送短信。
3.  **即时消息/机器人 (IM/Webhook)**：通过Webhook向协作工具发送消息（企业微信、钉钉、飞书等）。
4.  **语音电话 (Voice Call)**：通过第三方TTS API网关发起自动外呼，用于最高优先级的P0级故障告警。

#### **3.8.2. 通知配置**
- **全局系统配置**：管理员在后台配置各个渠道的全局参数（SMTP、SMS API、Webhook URL、语音电话API）。
- **用户个人配置**：用户可在个人设置中管理自己的通知偏好（渠道启用/禁用、通知范围）。

#### **3.8.3. 通知规则与路由**
- **触发事件 (Trigger)**：系统内发生的某个动作（事件新建/状态变更、被@提及、故障提交审批、审批任务待处理等）。
- **执行动作 (Action)**：当触发事件发生时，执行的通知动作（通知对象、通知渠道、通知模板）。
- **升级策略 (Escalation Policy)**：针对语音电话告警的核心策略。
  - **第一轮**：呼叫首要责任人，等待接听**30秒**。
  - **未接听**：自动升级呼叫第二责任人。
  - **仍未接听**：继续升级呼叫团队经理或下一轮值班员，直到有人确认为止。

#### **3.8.4. 通知模板管理**
- 支持为不同事件类型和不同渠道定义消息模板，使用类似**Jinja2**的语法。
- **示例模板（语音电话 - P0事件）**：
  ```jinja2
  （紧急告警音）
  您好，这是一条来自【{{ system_name }}】运维平台的紧急告警。
  发生P0级故障，事件ID：{{ incident.id }}，标题：{{ incident.title }}。
  影响服务：{{ incident.service.name }}。
  请立即登录系统查看处理。重复收听请按1，确认已收到本通知请按2。
  （紧急告警音）
  ```

#### **3.8.5. 通知日志与状态跟踪**
- 所有发出的通知都必须在数据库中有记录。
- 记录字段：`通知类型`、`目标用户`、`渠道`、`状态`（成功/失败）、`请求内容`、`响应内容`、`发送时间`。
- 对于语音电话，额外记录通话时长、呼叫状态和用户按键输入。

#### **3.8.6. 语音电话告警专属流程**
1.  **触发**：创建P0级别的事件。
2.  **启动呼叫**：通知引擎根据规则，获取on-call人员列表，发起第一轮呼叫。
3.  **交互与确认**：用户接听并可按键确认。
4.  **闭环跟踪**：整个呼叫链的每一步都实时记录，并在事件详情页可视化展示。

## **4. 非功能需求**

- **性能**：95%的页面加载时间应低于2秒。列表查询响应时间应低于1秒。
- **可用性**：系统自身应实现高可用，目标可用性SLO >= 99.9%。
- **安全性**：
  - 所有密码需加密存储（如bcrypt）。
  - API接口需进行身份认证和权限校验。
  - 防止常见Web漏洞（SQL注入、XSS、CSRF）。
- **可扩展性**：后端API设计应易于后期扩展新的模块（如变更管理、知识库）。

---

## **5. 数据库设计**

### **主要表结构**

```sql
-- 用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone_number VARCHAR(50) NULL,
    real_name VARCHAR(100),
    department VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 组表
CREATE TABLE `groups` (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    manager_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (manager_id) REFERENCES users(id)
);

-- 用户-组关联表
CREATE TABLE user_group (
    user_id INT,
    group_id INT,
    PRIMARY KEY (user_id, group_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES `groups`(id) ON DELETE CASCADE
);

-- 角色表
CREATE TABLE roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

-- 权限表
CREATE TABLE permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

-- 角色-权限关联表
CREATE TABLE role_permission (
    role_id INT,
    permission_id INT,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

-- 用户-角色关联表
CREATE TABLE user_role (
    user_id INT,
    role_id INT,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

-- 组-角色关联表
CREATE TABLE group_role (
    group_id INT,
    role_id INT,
    PRIMARY KEY (group_id, role_id),
    FOREIGN KEY (group_id) REFERENCES `groups`(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
);

-- 服务目录表
CREATE TABLE services (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_team VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE
);

-- 事件表
CREATE TABLE incidents (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    status ENUM('New', 'In Progress', 'On Hold', 'Resolved', 'Closed', 'Reopened') DEFAULT 'New',
    impact ENUM('High', 'Medium', 'Low') NOT NULL,
    urgency ENUM('High', 'Medium', 'Low') NOT NULL,
    priority ENUM('Critical', 'High', 'Medium', 'Low') GENERATED ALWAYS AS (
        CASE
            WHEN impact = 'High' AND urgency = 'High' THEN 'Critical'
            WHEN impact = 'High' AND urgency = 'Medium' THEN 'High'
            WHEN impact = 'Medium' AND urgency = 'High' THEN 'High'
            ELSE 'Low'
        END
    ) STORED,
    service_id INT,
    assignee_id INT,
    reporter_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP NULL,
    closed_at TIMESTAMP NULL,
    FOREIGN KEY (service_id) REFERENCES services(id),
    FOREIGN KEY (assignee_id) REFERENCES users(id),
    FOREIGN KEY (reporter_id) REFERENCES users(id)
);

-- 事件评论表
CREATE TABLE incident_comments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    incident_id INT NOT NULL,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    is_private BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 故障表
CREATE TABLE problems (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status ENUM('New', 'Investigating', 'Known Error', 'Closed', 'Pending Approval') DEFAULT 'New',
    priority ENUM('High', 'Medium', 'Low'),
    root_cause_analysis TEXT,
    solution TEXT,
    current_approval_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    closed_at TIMESTAMP NULL
);

-- 事件-故障关联表
CREATE TABLE incident_problem (
    incident_id INT,
    problem_id INT,
    PRIMARY KEY (incident_id, problem_id),
    FOREIGN KEY (incident_id) REFERENCES incidents(id),
    FOREIGN KEY (problem_id) REFERENCES problems(id)
);

-- 审批流程定义表
CREATE TABLE approval_workflows (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- 审批节点定义表
CREATE TABLE approval_steps (
    id INT PRIMARY KEY AUTO_INCREMENT,
    workflow_id INT NOT NULL,
    step_number INT NOT NULL,
    approval_type ENUM('USER', 'ROLE', 'GROUP_MANAGER') NOT NULL,
    approved_by_id INT NULL,
    approved_by_role_id INT NULL,
    approved_by_group_id INT NULL,
    FOREIGN KEY (workflow_id) REFERENCES approval_workflows(id) ON DELETE CASCADE,
    FOREIGN KEY (approved_by_id) REFERENCES users(id),
    FOREIGN KEY (approved_by_role_id) REFERENCES roles(id),
    FOREIGN KEY (approved_by_group_id) REFERENCES `groups`(id)
);

-- 审批实例表
CREATE TABLE approvals (
    id INT PRIMARY KEY AUTO_INCREMENT,
    workflow_id INT NOT NULL,
    problem_id INT NOT NULL,
    requester_id INT NOT NULL,
    status ENUM('PENDING', 'APPROVED', 'REJECTED') DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_id) REFERENCES approval_workflows(id),
    FOREIGN KEY (problem_id) REFERENCES problems(id) ON DELETE CASCADE,
    FOREIGN KEY (requester_id) REFERENCES users(id)
);

-- 审批日志表
CREATE TABLE approval_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    approval_id INT NOT NULL,
    step_id INT NOT NULL,
    approver_id INT NOT NULL,
    decision ENUM('APPROVED', 'REJECTED') NOT NULL,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (approval_id) REFERENCES approvals(id) ON DELETE CASCADE,
    FOREIGN KEY (step_id) REFERENCES approval_steps(id),
    FOREIGN KEY (approver_id) REFERENCES users(id)
);

-- 通知渠道配置表
CREATE TABLE notification_channels (
    id INT PRIMARY KEY AUTO_INCREMENT,
    type ENUM('EMAIL', 'SMS', 'SLACK', 'TEAMS', 'DINGTALK', 'WEBHOOK', 'VOICE_CALL') NOT NULL,
    name VARCHAR(100) NOT NULL,
    config JSON NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户通知偏好表
CREATE TABLE user_notification_preferences (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    channel_type ENUM('EMAIL', 'SMS', 'SLACK', 'TEAMS', 'DINGTALK', 'WEBHOOK', 'VOICE_CALL') NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    preferences JSON NULL,
    UNIQUE KEY (user_id, channel_type),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 通知规则表
CREATE TABLE notification_rules (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    trigger_event VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 通知规则动作表
CREATE TABLE notification_rule_actions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    rule_id INT NOT NULL,
    action_type ENUM('NOTIFY_USER', 'NOTIFY_GROUP', 'NOTIFY_ROLE', 'WEBHOOK') NOT NULL,
    target_identifier VARCHAR(100) NOT NULL,
    channel_priority JSON NOT NULL,
    FOREIGN KEY (rule_id) REFERENCES notification_rules(id) ON DELETE CASCADE
);

-- 通知模板表
CREATE TABLE notification_templates (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    trigger_event VARCHAR(100) NOT NULL,
    channel_type ENUM('EMAIL', 'SMS', 'SLACK', 'TEAMS', 'DINGTALK', 'WEBHOOK', 'VOICE_CALL') NOT NULL,
    subject_template TEXT,
    body_template TEXT NOT NULL,
    tts_voice VARCHAR(50) NULL,
    play_times INT DEFAULT 2,
    timeout_sec INT DEFAULT 30,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 通知发送日志表
CREATE TABLE notification_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    rule_id INT NULL,
    template_id INT NULL,
    trigger_event VARCHAR(100) NOT NULL,
    trigger_record_id INT NOT NULL,
    target_user_id INT NULL,
    channel_type ENUM('EMAIL', 'SMS', 'SLACK', 'TEAMS', 'DINGTALK', 'WEBHOOK', 'VOICE_CALL') NOT NULL,
    status ENUM('SUCCESS', 'FAILED') NOT NULL,
    request_content TEXT,
    response_content TEXT,
    external_id VARCHAR(255) NULL,
    call_duration INT NULL,
    call_status VARCHAR(50) NULL,
    dtmf_input VARCHAR(10) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rule_id) REFERENCES notification_rules(id),
    FOREIGN KEY (template_id) REFERENCES notification_templates(id),
    FOREIGN KEY (target_user_id) REFERENCES users(id)
);
```

---

## **6. API接口设计概要**

### **认证相关**
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/logout` - 用户登出
- `GET /api/v1/auth/me` - 获取当前用户信息

### **事件管理**
- `POST /api/v1/incidents` - 创建新事件
- `GET /api/v1/incidents` - 获取事件列表（支持分页和过滤）
- `GET /api/v1/incidents/<id>` - 获取单个事件详情
- `PUT /api/v1/incidents/<id>` - 更新事件
- `POST /api/v1/incidents/<id>/comments` - 为事件添加评论

### **故障管理**
- `POST /api/v1/problems` - 创建故障
- `GET /api/v1/problems` - 获取故障列表
- `GET /api/v1/problems/<id>` - 获取单个故障详情
- `PUT /api/v1/problems/<id>` - 更新故障
- `POST /api/v1/problems/<id>/submit-approval` - 提交审批

### **审批管理**
- `GET /api/v1/approvals` - 获取审批列表
- `GET /api/v1/approvals/<id>` - 获取审批详情
- `POST /api/v1/approvals/<id>/approve` - 批准
- `POST /api/v1/approvals/<id>/reject` - 拒绝
- `GET /api/v1/my-approvals` - 获取当前用户的待审批列表

### **通知管理**
- `GET /api/v1/notification/preferences` - 获取当前用户的通知偏好
- `PUT /api/v1/notification/preferences` - 更新当前用户的通知偏好
- `POST /api/v1/notification/test/{channel}` - （管理员）测试渠道配置
- `GET /api/v1/notification/logs` - （管理员）查看通知日志
- `POST /api/v1/notification/voice-call` - （内部/测试）发起语音呼叫
- `POST /api/v1/voice-call/status-callback` - （外部）语音服务商状态回调

### **系统管理**
- `GET /api/v1/users` - （管理员）获取用户列表
- `POST /api/v1/users` - （管理员）创建用户
- `PUT /api/v1/users/<id>` - （管理员）更新用户
- `GET /api/v1/groups` - 获取组列表
- `GET /api/v1/services` - 获取服务列表