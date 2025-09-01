#!/usr/bin/env python3
"""
测试document_info数据结构，检查前端显示的虚假数据问题
"""
import requests
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_document_info_structure():
    """测试document_info返回结构"""
    
    # 创建测试文档
    doc_content = """A703三相继电保护测试仪
产品名称: A703三相继电保护测试仪
产品型号: A703
测试电压: 0-240V AC
测试电流: 0-60A AC
重量: 15kg
"""
    
    doc_path = "/tmp/A703三相继电保护测试仪-说明书.txt"
    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(doc_content)
    
    try:
        # 获取认证
        login_data = {"username": "admin", "password": "admin123"}
        login_response = requests.post("http://127.0.0.1:5001/api/v1/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            logger.error("❌ 登录失败")
            return False
        
        token = login_response.json().get('data', {}).get('tokens', {}).get('access_token')
        headers = {'Authorization': f'Bearer {token}'}
        
        # 测试文档分析
        with open(doc_path, 'rb') as f:
            files = {'document': (doc_path.split('/')[-1], f, 'text/plain')}
            
            logger.info("📤 发送文档分析请求...")
            response = requests.post(
                "http://127.0.0.1:5001/api/v1/ai-analysis/analyze-document",
                files=files,
                headers=headers,
                timeout=180
            )
            
            if response.status_code == 200:
                result = response.json()
                
                logger.info("\n📊 完整的API响应结构分析:")
                logger.info(f"  success: {result.get('success')}")
                
                # 重点检查document_info
                document_info = result.get('document_info', {})
                logger.info(f"\n📄 document_info结构:")
                logger.info(f"  类型: {type(document_info)}")
                logger.info(f"  内容: {json.dumps(document_info, ensure_ascii=False, indent=2)}")
                
                # 检查extracted_data中的统计数据
                extracted_data = result.get('extracted_data', {})
                logger.info(f"\n📋 extracted_data统计:")
                logger.info(f"  specifications数量: {len(extracted_data.get('specifications', {}))}")
                logger.info(f"  features数量: {len(extracted_data.get('features', []))}")
                logger.info(f"  certificates数量: {len(extracted_data.get('certificates', []))}")
                
                # 检查processing_time
                processing_time = result.get('processing_time', 0)
                logger.info(f"  processing_time: {processing_time}秒")
                
                # 分析问题数据
                problems = []
                
                # 检查文件大小显示
                size = document_info.get('size', 0)
                if size == 0:
                    problems.append("文件大小显示为0字节")
                    
                # 检查处理时间
                analysis_duration = document_info.get('analysis_duration', 0)
                if analysis_duration > 3600:  # 超过1小时
                    problems.append(f"分析时长异常: {analysis_duration}秒 ({analysis_duration/3600:.1f}小时)")
                
                # 检查规格数量
                specs_count = len(extracted_data.get('specifications', {}))
                if specs_count == 0:
                    problems.append("规格数量显示为0项")
                
                if problems:
                    logger.error(f"\n❌ 发现的数据问题:")
                    for i, problem in enumerate(problems, 1):
                        logger.error(f"    {i}. {problem}")
                    return False
                else:
                    logger.info(f"\n✅ document_info数据结构正常")
                    return True
                    
            else:
                logger.error(f"❌ 分析失败: {response.status_code}")
                return False
                
    except Exception as e:
        logger.error(f"💥 测试错误: {str(e)}")
        return False
    finally:
        import os
        if os.path.exists(doc_path):
            os.remove(doc_path)

if __name__ == "__main__":
    success = test_document_info_structure()
    if success:
        logger.info("\n🎉 document_info数据结构测试通过！")
    else:
        logger.warning("\n⚠️ document_info数据结构存在问题，需要修复")