#!/usr/bin/env python3
"""
测试recent-results API端点，检查返回数据格式
"""
import requests
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_recent_results_api():
    """测试recent-results API端点的数据格式"""
    
    try:
        # 获取认证
        login_data = {"username": "admin", "password": "admin123"}
        login_response = requests.post("http://127.0.0.1:5001/api/v1/auth/login", json=login_data)
        
        if login_response.status_code != 200:
            logger.error("❌ 登录失败")
            return False
        
        token = login_response.json().get('data', {}).get('tokens', {}).get('access_token')
        headers = {'Authorization': f'Bearer {token}'}
        
        # 测试recent-results API
        logger.info("📤 调用recent-results API...")
        response = requests.get(
            "http://127.0.0.1:5001/api/v1/ai-analysis/recent-results?limit=5",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            logger.info(f"\n📊 recent-results API响应分析:")
            logger.info(f"  success: {result.get('success')}")
            logger.info(f"  total_count: {result.get('total_count')}")
            
            results = result.get('results', [])
            logger.info(f"  results数量: {len(results)}")
            
            if results:
                # 检查第一个结果的数据结构
                first_result = results[0]
                logger.info(f"\n📋 第一个结果数据结构:")
                logger.info(f"  id: {first_result.get('id')}")
                logger.info(f"  document_name: {first_result.get('document_name')}")
                logger.info(f"  analysis_date: {first_result.get('analysis_date')}")
                logger.info(f"  status: {first_result.get('status')}")
                logger.info(f"  success: {first_result.get('success')}")
                
                # 重点检查product_info结构
                product_info = first_result.get('product_info', {})
                logger.info(f"\n🔍 product_info结构:")
                logger.info(f"  name: '{product_info.get('name')}'")
                logger.info(f"  code: '{product_info.get('code')}'")
                logger.info(f"  category: '{product_info.get('category')}'")
                logger.info(f"  specs_count: {product_info.get('specs_count')}")
                
                # 检查analysis_duration
                duration = first_result.get('analysis_duration')
                logger.info(f"  analysis_duration: {duration}")
                
                # 分析数据质量问题
                problems = []
                
                # 检查specs_count是否为0
                specs_count = product_info.get('specs_count', 0)
                if specs_count == 0:
                    problems.append(f"规格数量显示为0，但应该有规格数据")
                
                # 检查基础信息是否缺失
                if not product_info.get('name'):
                    problems.append("产品名称缺失")
                if not product_info.get('code'): 
                    problems.append("产品代码缺失")
                if not product_info.get('category'):
                    problems.append("产品分类缺失")
                
                # 检查处理时间是否异常
                if duration and duration > 3600:  # 超过1小时
                    problems.append(f"分析时长异常: {duration}秒 ({duration/3600:.1f}小时)")
                
                if problems:
                    logger.error(f"\n❌ 发现的API数据问题:")
                    for i, problem in enumerate(problems, 1):
                        logger.error(f"    {i}. {problem}")
                    
                    logger.info(f"\n💡 这些问题解释了为什么前端显示虚假数据:")
                    logger.info(f"    - 前端显示的统计数据来自这个API")
                    logger.info(f"    - API返回了错误的统计信息")
                    logger.info(f"    - 需要检查数据库中的实际数据")
                    return False
                else:
                    logger.info(f"\n✅ recent-results API数据正常")
                    logger.info(f"    - 规格数量: {specs_count}")
                    logger.info(f"    - 产品信息完整")
                    logger.info(f"    - 时长合理: {duration}秒")
                    return True
            else:
                logger.warning("⚠️ 没有分析结果数据")
                return False
                
        else:
            logger.error(f"❌ API调用失败: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"💥 测试错误: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_recent_results_api()
    if success:
        logger.info("\n🎉 recent-results API数据正常！")
    else:
        logger.warning("\n⚠️ recent-results API数据有问题，需要修复")