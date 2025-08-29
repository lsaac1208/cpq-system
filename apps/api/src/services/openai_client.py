# -*- coding: utf-8 -*-
"""
OpenAI API客户端
负责与OpenAI API通信，提供产品文档分析功能
"""
import os
import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from flask import current_app

logger = logging.getLogger(__name__)

class OpenAIClient:
    """OpenAI API客户端"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("OpenAI API key not found in environment variables")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key)
    
    def is_available(self) -> bool:
        """检查OpenAI客户端是否可用"""
        return self.client is not None and self.api_key is not None
    
    def analyze_product_document(self, document_content: str, document_name: str = "") -> Dict[str, Any]:
        """
        分析产品文档，提取产品信息
        
        Args:
            document_content: 文档内容文本
            document_name: 文档名称（用于上下文）
            
        Returns:
            Dict: 包含提取的产品信息和置信度分数
        """
        if not self.is_available():
            raise Exception("OpenAI client is not available. Please check API key configuration.")
        
        try:
            prompt = self._build_extraction_prompt()
            
            # 构建消息
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"文档名称: {document_name}\n\n文档内容:\n{document_content}"}
            ]
            
            # 调用OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # 使用更经济的模型
                messages=messages,
                temperature=0.1,  # 降低随机性，提高一致性
                max_tokens=2000,
                response_format={"type": "json_object"}  # 确保返回JSON格式
            )
            
            # 解析响应
            result = self._parse_response(response)
            
            # 记录API使用情况
            usage = response.usage
            logger.info(f"OpenAI API usage - Prompt tokens: {usage.prompt_tokens}, "
                       f"Completion tokens: {usage.completion_tokens}, "
                       f"Total tokens: {usage.total_tokens}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing document with OpenAI: {str(e)}")
            raise Exception(f"AI analysis failed: {str(e)}")
    
    def _build_extraction_prompt(self) -> str:
        """构建产品信息提取的prompt"""
        return """你是一个专业的电气设备产品信息提取专家。请从提供的文档中提取产品信息，严格按照以下JSON格式返回：

{
  "basic_info": {
    "name": "产品全称",
    "code": "产品型号/代码",
    "category": "产品分类",
    "base_price": 0,
    "description": "简要描述"
  },
  "specifications": {
    "参数名1": {"value": "值", "unit": "单位", "description": "描述"},
    "参数名2": {"value": "值", "unit": "单位", "description": "描述"}
  },
  "features": [
    {"title": "特性标题", "description": "详细描述", "icon": ""}
  ],
  "application_scenarios": [
    {"name": "应用场景名称", "icon": "", "sort_order": 0}
  ],
  "accessories": [
    {"name": "配件名称", "description": "配件描述", "type": "standard"}
  ],
  "certificates": [
    {"name": "认证名称", "type": "quality", "certificate_number": "证书编号", "description": "认证描述"}
  ],
  "support_info": {
    "warranty": {
      "period": "质保期限",
      "coverage": "质保内容",
      "terms": ["质保条款1", "质保条款2"]
    },
    "contact_info": {
      "sales_phone": "销售电话",
      "sales_email": "销售邮箱",
      "support_phone": "技术支持电话",
      "support_email": "技术支持邮箱"
    },
    "service_promises": ["服务承诺1", "服务承诺2"]
  },
  "confidence": {
    "basic_info": 0.95,
    "specifications": 0.87,
    "features": 0.92,
    "overall": 0.91
  }
}

重要提取规则：
1. 基础价格必须是数字，如果没有明确价格信息则设为0
2. 产品分类尽量归入：变压器、开关设备、保护装置、测量仪表、其他 等标准分类
3. 技术规格要包含具体的数值、单位和描述
4. 特别关注电气参数、安全认证、应用环境等关键信息
5. 置信度分数范围0-1，表示对提取信息的可信程度
6. 如果某些信息不存在，对应字段设为空值或空数组，但保持JSON结构完整

请仔细分析文档，准确提取信息。"""
    
    def _parse_response(self, response) -> Dict[str, Any]:
        """解析OpenAI API响应"""
        try:
            content = response.choices[0].message.content.strip()
            
            # 尝试解析JSON
            result = json.loads(content)
            
            # 验证响应结构
            if not isinstance(result, dict):
                raise ValueError("Response is not a valid JSON object")
            
            # 确保必需的字段存在
            required_fields = ['basic_info', 'specifications', 'features', 'confidence']
            for field in required_fields:
                if field not in result:
                    result[field] = {}
            
            # 确保置信度字段有默认值
            if 'confidence' not in result:
                result['confidence'] = {
                    'basic_info': 0.5,
                    'specifications': 0.5,
                    'features': 0.5,
                    'overall': 0.5
                }
            
            # 计算总体置信度
            confidence_scores = result.get('confidence', {})
            if 'overall' not in confidence_scores:
                scores = [v for k, v in confidence_scores.items() if isinstance(v, (int, float))]
                result['confidence']['overall'] = sum(scores) / len(scores) if scores else 0.5
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {content}")
            raise ValueError(f"Invalid JSON response from OpenAI: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing OpenAI response: {str(e)}")
            raise ValueError(f"Failed to parse AI response: {str(e)}")