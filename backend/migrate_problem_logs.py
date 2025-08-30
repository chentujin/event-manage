#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.incident import ProblemStatusLog

app = create_app()

with app.app_context():
    # 创建表
    db.create_all()
    print("故障状态日志表创建成功！")