#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.incident import IncidentStatusLog

app = create_app()

with app.app_context():
    # 创建表
    db.create_all()
    print("数据库表创建成功！")