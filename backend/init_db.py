from app import create_app, db
from app.utils.init_data import init_default_data

app = create_app()

with app.app_context():
    db.create_all()
    init_default_data()
    print("数据库初始化完成！")