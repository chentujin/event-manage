from app import create_app, db
from app.models import *  # 确保所有模型都被导入

app = create_app()

with app.app_context():
    db.create_all()
    print("数据库表创建完成！")