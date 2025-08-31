#!/usr/bin/env python3
"""
检查邮件配置的脚本
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def check_email_config():
    print("🔍 检查邮件配置...")
    
    # 从环境变量或配置文件获取邮件配置
    mail_server = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    mail_port = int(os.environ.get('MAIL_PORT') or 587)
    mail_username = os.environ.get('MAIL_USERNAME')
    mail_password = os.environ.get('MAIL_PASSWORD')
    mail_use_tls = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', '1']
    
    print(f"📧 SMTP服务器: {mail_server}")
    print(f"🔌 SMTP端口: {mail_port}")
    print(f"👤 用户名: {mail_username}")
    print(f"🔑 密码: {'已设置' if mail_password else '未设置'}")
    print(f"🔒 使用TLS: {mail_use_tls}")
    
    if not all([mail_username, mail_password]):
        print("❌ 邮件配置不完整，请设置MAIL_USERNAME和MAIL_PASSWORD环境变量")
        return False
    
    # 测试SMTP连接
    print(f"\n🧪 测试SMTP连接...")
    try:
        if mail_use_tls:
            server = smtplib.SMTP(mail_server, mail_port)
            server.starttls()
        else:
            server = smtplib.SMTP(mail_server, mail_port)
        
        print("✅ SMTP连接成功")
        
        # 尝试登录
        print("🔐 尝试登录...")
        server.login(mail_username, mail_password)
        print("✅ SMTP登录成功")
        
        # 测试发送邮件
        print("📤 测试发送邮件...")
        test_email = mail_username  # 发送给自己测试
        
        msg = MIMEMultipart()
        msg['From'] = mail_username
        msg['To'] = test_email
        msg['Subject'] = '事件管理平台 - 邮件配置测试'
        
        body = '''
        这是一封测试邮件，用于验证邮件配置是否正确。
        
        如果您收到这封邮件，说明：
        1. SMTP服务器配置正确
        2. 用户名和密码验证成功
        3. 邮件发送功能正常
        
        发送时间: {}
        
        此邮件由事件管理平台自动发送，请勿回复。
        '''.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        msg.attach(MIMEText(body, 'plain'))
        
        server.send_message(msg)
        print(f"✅ 测试邮件发送成功到: {test_email}")
        
        server.quit()
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP认证失败: {e}")
        print("💡 请检查用户名和密码是否正确")
        return False
        
    except smtplib.SMTPConnectError as e:
        print(f"❌ SMTP连接失败: {e}")
        print("💡 请检查服务器地址和端口是否正确")
        return False
        
    except smtplib.SMTPRecipientsRefused as e:
        print(f"❌ 收件人地址被拒绝: {e}")
        print("💡 请检查收件人邮箱地址是否正确")
        return False
        
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False

def show_config_help():
    print("\n📋 邮件配置帮助:")
    print("1. 设置环境变量:")
    print("   export MAIL_SERVER=smtp.gmail.com")
    print("   export MAIL_PORT=587")
    print("   export MAIL_USERNAME=your-email@gmail.com")
    print("   export MAIL_PASSWORD=your-app-password")
    print("   export MAIL_USE_TLS=true")
    
    print("\n2. 常见SMTP服务器配置:")
    print("   Gmail: smtp.gmail.com:587 (需要应用专用密码)")
    print("   QQ邮箱: smtp.qq.com:587")
    print("   163邮箱: smtp.163.com:25")
    print("   企业邮箱: 请咨询IT部门")
    
    print("\n3. 安全提示:")
    print("   - 不要使用明文密码")
    print("   - Gmail需要使用应用专用密码")
    print("   - 确保防火墙允许SMTP端口")

if __name__ == "__main__":
    from datetime import datetime
    
    print("🚀 邮件配置检查工具")
    print("=" * 50)
    
    success = check_email_config()
    
    if not success:
        show_config_help()
    else:
        print("\n🎉 邮件配置检查完成，配置正确！")
