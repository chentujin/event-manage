from flask import Blueprint

# 创建认证蓝图
auth_bp = Blueprint('auth', __name__)

# 导入认证相关路由
from . import routes