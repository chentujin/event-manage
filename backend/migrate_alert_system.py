#!/usr/bin/env python3
"""
故障管理系统重新设计 - 数据迁移脚本
将现有的incidents表数据迁移到新的alert和incident结构
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app import create_app, db
from app.models.user import User
from app.models.incident import Service
from sqlalchemy import text
import json

def backup_existing_data():
    """备份现有数据"""
    print("正在备份现有数据...")
    
    # 创建备份表
    db.session.execute(text("""
        CREATE TABLE incidents_backup AS 
        SELECT * FROM incidents
    """))
    
    db.session.execute(text("""
        CREATE TABLE incident_comments_backup AS 
        SELECT * FROM incident_comments
    """))
    
    db.session.execute(text("""
        CREATE TABLE incident_status_logs_backup AS 
        SELECT * FROM incident_status_logs
    """))
    
    db.session.commit()
    print("数据备份完成")

def create_new_tables():
    """创建新的表结构"""
    print("正在创建新的表结构...")
    
    # 创建alerts表
    db.session.execute(text("""
        CREATE TABLE alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            alert_source VARCHAR(100),
            alert_rule VARCHAR(255),
            level VARCHAR(20) NOT NULL CHECK (level IN ('Critical', 'Warning', 'Info')),
            status VARCHAR(20) DEFAULT 'New' CHECK (status IN ('New', 'Acknowledged', 'Linked', 'Ignored')),
            metric_name VARCHAR(255),
            metric_value VARCHAR(100),
            threshold VARCHAR(100),
            service_id INTEGER,
            host VARCHAR(255),
            environment VARCHAR(20) CHECK (environment IN ('Production', 'Staging', 'Development')),
            incident_id INTEGER,
            acknowledged_by INTEGER,
            fired_at DATETIME NOT NULL,
            resolved_at DATETIME,
            acknowledged_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (service_id) REFERENCES services (id),
            FOREIGN KEY (incident_id) REFERENCES incidents_new (id),
            FOREIGN KEY (acknowledged_by) REFERENCES users (id)
        )
    """))
    
    # 创建新的incidents表
    db.session.execute(text("""
        CREATE TABLE incidents_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id VARCHAR(50) UNIQUE NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            status VARCHAR(20) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Investigating', 'Recovering', 'Recovered', 'Post-Mortem', 'Closed')),
            severity VARCHAR(5) NOT NULL CHECK (severity IN ('P1', 'P2', 'P3', 'P4')),
            impact_scope TEXT,
            affected_services TEXT,
            business_impact TEXT,
            incident_commander INTEGER,
            assignee_id INTEGER,
            reporter_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            detected_at DATETIME,
            acknowledged_at DATETIME,
            recovered_at DATETIME,
            closed_at DATETIME,
            emergency_chat_url VARCHAR(500),
            notification_sent BOOLEAN DEFAULT FALSE,
            external_status_page BOOLEAN DEFAULT FALSE,
            postmortem_required BOOLEAN DEFAULT TRUE,
            postmortem_id INTEGER,
            FOREIGN KEY (incident_commander) REFERENCES users (id),
            FOREIGN KEY (assignee_id) REFERENCES users (id),
            FOREIGN KEY (reporter_id) REFERENCES users (id),
            FOREIGN KEY (postmortem_id) REFERENCES post_mortems (id)
        )
    """))
    
    # 创建incident_timelines表
    db.session.execute(text("""
        CREATE TABLE incident_timelines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            entry_type VARCHAR(20) NOT NULL CHECK (entry_type IN ('status_change', 'comment', 'action', 'emergency_response', 'alert_linked')),
            title VARCHAR(255) NOT NULL,
            description TEXT,
            timestamp DATETIME NOT NULL,
            related_alert_id INTEGER,
            attachments TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (incident_id) REFERENCES incidents_new (id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (related_alert_id) REFERENCES alerts (id)
        )
    """))
    
    # 创建post_mortems表
    db.session.execute(text("""
        CREATE TABLE post_mortems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER,
            title VARCHAR(255) NOT NULL,
            status VARCHAR(20) DEFAULT 'Draft' CHECK (status IN ('Draft', 'In Review', 'Approved', 'Published')),
            incident_summary TEXT,
            timeline_analysis TEXT,
            root_cause_analysis TEXT,
            lessons_learned TEXT,
            meeting_date DATETIME,
            attendees TEXT,
            author_id INTEGER NOT NULL,
            reviewer_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            published_at DATETIME,
            FOREIGN KEY (incident_id) REFERENCES incidents_new (id),
            FOREIGN KEY (author_id) REFERENCES users (id),
            FOREIGN KEY (reviewer_id) REFERENCES users (id)
        )
    """))
    
    # 创建action_items表
    db.session.execute(text("""
        CREATE TABLE action_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            postmortem_id INTEGER NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            category VARCHAR(20) CHECK (category IN ('Technical', 'Process', 'Documentation', 'Training', 'Monitoring')),
            priority VARCHAR(10) DEFAULT 'Medium' CHECK (priority IN ('High', 'Medium', 'Low')),
            status VARCHAR(20) DEFAULT 'Open' CHECK (status IN ('Open', 'In Progress', 'Completed', 'Cancelled')),
            assignee_id INTEGER,
            due_date DATETIME,
            completed_at DATETIME,
            external_link VARCHAR(500),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (postmortem_id) REFERENCES post_mortems (id),
            FOREIGN KEY (assignee_id) REFERENCES users (id)
        )
    """))
    
    # 创建alert_comments表
    db.session.execute(text("""
        CREATE TABLE alert_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            is_private BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (alert_id) REFERENCES alerts (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """))
    
    db.session.commit()
    print("新表结构创建完成")

def migrate_incidents_to_alerts():
    """将现有incidents数据迁移为alerts"""
    print("正在将现有incidents迁移为alerts...")
    
    # 获取所有现有incidents
    old_incidents = db.session.execute(text("""
        SELECT * FROM incidents_backup
    """)).fetchall()
    
    for incident in old_incidents:
        # 将incident转换为alert
        # 确定告警级别
        if incident.impact == 'High' and incident.urgency == 'High':
            level = 'Critical'
        elif incident.impact == 'High' or incident.urgency == 'High':
            level = 'Warning'
        else:
            level = 'Info'
        
        # 确定告警状态
        if incident.status in ['New']:
            alert_status = 'New'
        elif incident.status in ['In Progress', 'On Hold']:
            alert_status = 'Acknowledged'
        else:
            alert_status = 'Linked'  # 已解决或关闭的当作已关联
        
        # 插入alert记录
        db.session.execute(text("""
            INSERT INTO alerts (
                title, description, level, status, service_id, 
                fired_at, resolved_at, created_at, updated_at,
                alert_source
            ) VALUES (
                :title, :description, :level, :status, :service_id,
                :fired_at, :resolved_at, :created_at, :updated_at,
                'Legacy System'
            )
        """), {
            'title': incident.title,
            'description': incident.description,
            'level': level,
            'status': alert_status,
            'service_id': incident.service_id,
            'fired_at': incident.created_at,
            'resolved_at': incident.resolved_at,
            'created_at': incident.created_at,
            'updated_at': incident.updated_at
        })
    
    db.session.commit()
    print(f"已迁移 {len(old_incidents)} 条incident记录为alert")

def create_sample_incidents():
    """为重要的alerts创建故障记录"""
    print("正在为重要告警创建故障记录...")
    
    # 获取Critical级别的alerts
    critical_alerts = db.session.execute(text("""
        SELECT * FROM alerts WHERE level = 'Critical'
    """)).fetchall()
    
    incident_count = 0
    for alert in critical_alerts[:5]:  # 限制只为前5个关键告警创建故障
        # 生成故障ID
        today = datetime.now().strftime('%Y%m%d')
        incident_id = f'F-{today}-{incident_count + 1:03d}'
        
        # 确定故障等级
        severity = 'P1' if alert.level == 'Critical' else 'P2'
        
        # 插入故障记录
        result = db.session.execute(text("""
            INSERT INTO incidents_new (
                incident_id, title, description, status, severity,
                reporter_id, created_at, updated_at, detected_at
            ) VALUES (
                :incident_id, :title, :description, 'Investigating', :severity,
                1, :created_at, :updated_at, :detected_at
            )
        """), {
            'incident_id': incident_id,
            'title': f'【故障】{alert.title}',
            'description': f'基于告警自动创建的故障记录。原始告警描述：{alert.description}',
            'severity': severity,
            'created_at': alert.created_at,
            'updated_at': alert.updated_at,
            'detected_at': alert.fired_at
        })
        
        new_incident_id = result.lastrowid
        
        # 关联alert到故障
        db.session.execute(text("""
            UPDATE alerts SET incident_id = :incident_id, status = 'Linked'
            WHERE id = :alert_id
        """), {
            'incident_id': new_incident_id,
            'alert_id': alert.id
        })
        
        # 创建时间线记录
        db.session.execute(text("""
            INSERT INTO incident_timelines (
                incident_id, user_id, entry_type, title, description, timestamp
            ) VALUES (
                :incident_id, 1, 'alert_linked', '关联告警', 
                :description, :timestamp
            )
        """), {
            'incident_id': new_incident_id,
            'description': f'自动关联告警 #{alert.id}: {alert.title}',
            'timestamp': alert.created_at
        })
        
        incident_count += 1
    
    db.session.commit()
    print(f"已创建 {incident_count} 条故障记录")

def migrate_comments():
    """迁移评论数据"""
    print("正在迁移评论数据...")
    
    # 获取所有incident comments
    old_comments = db.session.execute(text("""
        SELECT * FROM incident_comments_backup
    """)).fetchall()
    
    for comment in old_comments:
        # 查找对应的alert
        alert = db.session.execute(text("""
            SELECT id FROM alerts WHERE title = (
                SELECT title FROM incidents_backup WHERE id = :incident_id
            ) LIMIT 1
        """), {'incident_id': comment.incident_id}).fetchone()
        
        if alert:
            # 插入alert comment
            db.session.execute(text("""
                INSERT INTO alert_comments (
                    alert_id, user_id, content, is_private, created_at
                ) VALUES (
                    :alert_id, :user_id, :content, :is_private, :created_at
                )
            """), {
                'alert_id': alert.id,
                'user_id': comment.user_id,
                'content': comment.content,
                'is_private': comment.is_private,
                'created_at': comment.created_at
            })
    
    db.session.commit()
    print(f"已迁移 {len(old_comments)} 条评论")

def cleanup_old_tables():
    """清理旧表结构"""
    print("正在清理旧表结构...")
    
    # 重命名新表
    db.session.execute(text("ALTER TABLE incidents RENAME TO incidents_old"))
    db.session.execute(text("ALTER TABLE incidents_new RENAME TO incidents"))
    
    # 删除中间表
    db.session.execute(text("DROP TABLE IF EXISTS incident_problem"))
    
    db.session.commit()
    print("表结构清理完成")

def main():
    """主迁移流程"""
    app = create_app()
    
    with app.app_context():
        print("开始故障管理系统重新设计数据迁移...")
        print("=" * 50)
        
        try:
            # 1. 备份现有数据
            backup_existing_data()
            
            # 2. 创建新表结构
            create_new_tables()
            
            # 3. 迁移incidents为alerts
            migrate_incidents_to_alerts()
            
            # 4. 创建示例故障记录
            create_sample_incidents()
            
            # 5. 迁移评论
            migrate_comments()
            
            # 6. 清理旧表
            cleanup_old_tables()
            
            print("=" * 50)
            print("数据迁移完成！")
            print("\n迁移总结：")
            print("- 原有incidents表已重命名为incidents_old")
            print("- 新的alerts表包含所有原有的incident数据")
            print("- 新的incidents表包含基于关键告警创建的故障记录")
            print("- 时间线、复盘等新功能表已创建")
            print("- 评论数据已迁移到alerts")
            
        except Exception as e:
            print(f"迁移过程中出现错误: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    main()