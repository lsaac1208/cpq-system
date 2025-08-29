#!/usr/bin/env python3
"""
Initialize system settings with default values
"""

import sys
import os

# Add the parent directory to the path so we can import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models import db, SystemSettings
from app import create_app

def init_settings():
    """Initialize system settings with default values."""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check if settings already exist
            existing_settings = SystemSettings.query.first()
            
            if existing_settings:
                print("✅ Settings already exist, skipping initialization")
                return
            
            # Create default settings
            settings = SystemSettings(
                company_name='您的公司名称',
                company_address='请在系统设置中配置公司地址',
                company_phone='+86 xxx-xxxx-xxxx',
                company_email='info@yourcompany.com',
                company_website='www.yourcompany.com',
                company_tax_number='请配置税号',
                default_currency='CNY',
                default_tax_rate='13.00',  # 中国增值税标准税率
                quote_validity_days='30',
                pdf_header_color='#2563eb',
                pdf_footer_text='感谢您选择我们的产品和服务',
                pdf_show_logo=True,
                smtp_enabled=False,
                smtp_host='',
                smtp_port='587',
                smtp_username='',
                smtp_password='',
                smtp_use_tls=True,
                auto_quote_numbering=True,
                require_customer_approval=False,
                max_discount_percentage='20.00'
            )
            
            settings.save()
            
            print("✅ Default system settings initialized successfully")
            print(f"   Company Name: {settings.company_name}")
            print(f"   Default Currency: {settings.default_currency}")
            print(f"   Tax Rate: {settings.default_tax_rate}%")
            print(f"   Quote Validity: {settings.quote_validity_days} days")
            
        except Exception as e:
            print(f"❌ Error initializing settings: {e}")
            db.session.rollback()
            return False
    
    return True

if __name__ == '__main__':
    print("初始化系统设置...")
    success = init_settings()
    
    if success:
        print("\n🎉 设置初始化完成！")
        print("现在您可以登录系统并在设置页面中配置您的公司信息。")
    else:
        print("\n❌ 设置初始化失败！")
        sys.exit(1)