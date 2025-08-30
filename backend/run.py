#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件与故障管理平台
启动入口
"""
import os
from app import create_app, register_cli_commands

app = create_app()
register_cli_commands(app)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)