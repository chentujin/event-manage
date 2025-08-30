from flask import Blueprint

# 创建API v1蓝图
api_v1 = Blueprint('api_v1', __name__)

# 导入所有API路由
from . import incidents, problems, users, services, dashboard, approvals, notifications