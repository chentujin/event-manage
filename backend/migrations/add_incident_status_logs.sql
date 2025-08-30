-- 创建事件状态变更日志表
CREATE TABLE incident_status_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    incident_id INT NOT NULL,
    user_id INT NOT NULL,
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    comments TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (incident_id) REFERENCES incidents(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 创建索引以提高查询性能
CREATE INDEX idx_incident_status_logs_incident_id ON incident_status_logs(incident_id);
CREATE INDEX idx_incident_status_logs_created_at ON incident_status_logs(created_at);