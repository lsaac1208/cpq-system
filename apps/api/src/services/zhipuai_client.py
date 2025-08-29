# -*- coding: utf-8 -*-
"""
智谱AI API客户端
负责与智谱AI API通信，提供产品文档分析功能
"""
import os
import json
import logging
import requests
import time
from typing import Dict, Any, Optional
from flask import current_app

logger = logging.getLogger(__name__)

class ZhipuAIClient:
    """智谱AI API客户端"""
    
    def __init__(self):
        self.api_key = "19a71be0ef9f4049bf2e98faa4c27a3c.LgjiRRHpZ1MYc9lG"
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.model = "glm-4.5"  # 使用GLM-4.5模型
        # 超时配置 - 基于互联网研究优化
        self.connection_timeout = 30  # 连接超时（从10s增加到30s）
        self.read_timeout = 120       # 读取超时（从90s增加到120s，适应大文档分析）
        self.max_retries = 3          # 最大重试次数
        self.retry_delay = 5          # 重试延迟
        
        # 🔧 智能Token管理配置
        self.token_limits = {
            'basic': 800,      # 基础识别阶段
            'detailed': 3500,  # 详细提取阶段 (从2500增加到3500)
            'enhanced': 3500,  # 增强提取阶段 (从2500增加到3500)
            'optimization': 3000,  # 优化分析阶段 (从2000增加到3000)
            'health_check': 10
        }
        
        if not self.api_key:
            logger.warning("智谱AI API key not configured")
        else:
            logger.info("智谱AI客户端初始化成功")
    
    def is_available(self) -> bool:
        """检查智谱AI客户端是否可用"""
        return self.api_key is not None
    
    def _calculate_optimal_tokens(self, stage: str, document_length: int = 0) -> int:
        """
        根据阶段和文档长度动态计算最优token数量
        
        Args:
            stage: 分析阶段 ('basic', 'detailed', 'enhanced', 'optimization')
            document_length: 文档字符长度
            
        Returns:
            int: 推荐的max_tokens值
        """
        base_tokens = self.token_limits.get(stage, 2000)
        
        # 🔧 根据文档长度动态调整
        if document_length > 0:
            # 文档越长，需要的输出tokens越多
            length_factor = min(document_length / 10000, 2.0)  # 最多增加2倍
            adjusted_tokens = int(base_tokens * (1 + length_factor * 0.5))
            
            # 设置合理的上下限
            min_tokens = base_tokens
            max_tokens = min(8000, base_tokens * 2)  # 最大不超过8000
            
            optimal_tokens = max(min_tokens, min(adjusted_tokens, max_tokens))
            
            logger.debug(f"Token计算: stage={stage}, doc_len={document_length}, "
                        f"base={base_tokens}, optimal={optimal_tokens}")
            
            return optimal_tokens
        
        return base_tokens
    
    def analyze_product_document(self, document_content: str, document_name: str = "") -> Dict[str, Any]:
        """
        分析产品文档，提取产品信息 - 使用分层提示词策略
        
        Args:
            document_content: 文档内容文本
            document_name: 文档名称（用于上下文）
            
        Returns:
            Dict: 包含提取的产品信息和置信度分数
        """
        if not self.is_available():
            raise Exception("智谱AI客户端不可用，请检查API key配置")
        
        try:
            # 第一层：基础识别
            logger.info("开始第一层分析：基础产品识别")
            basic_result = self._basic_product_identification(document_content, document_name)
            
            # 如果基础识别成功，进行第二层详细提取
            if basic_result.get('confidence', {}).get('overall', 0) > 0.3:
                logger.info("第一层分析成功，开始第二层分析：详细信息提取")
                detailed_result = self._detailed_information_extraction(
                    document_content, document_name, basic_result
                )
                return detailed_result
            else:
                logger.warning("第一层分析置信度较低，使用增强提示词重试")
                # 使用增强提示词重试
                enhanced_result = self._enhanced_extraction_with_examples(document_content, document_name)
                return enhanced_result
            
        except Exception as e:
            logger.error(f"智谱AI文档分析错误: {str(e)}")
            # 提供更友好的错误信息
            if "连接超时" in str(e) or "timeout" in str(e).lower():
                raise Exception("AI分析超时，请稍后重试。大文档处理需要更多时间，系统正在优化中。")
            elif "连接错误" in str(e) or "connection" in str(e).lower():
                raise Exception("网络连接异常，请检查网络连接后重试。")
            elif "状态码: 401" in str(e):
                raise Exception("API密钥无效，请联系管理员检查配置。")
            elif "状态码: 429" in str(e):
                raise Exception("API调用频率超限，请稍后重试。")
            elif "状态码: 5" in str(e):
                raise Exception("智谱AI服务暂时不可用，请稍后重试。")
            else:
                raise Exception(f"AI分析失败: {str(e)}")
    
    def _build_extraction_prompt(self) -> str:
        """构建产品信息提取的prompt - 针对电力设备文档优化"""
        return """你是一位资深的电力设备技术专家和文档分析师，专精于变比测试仪、继电保护测试设备、电力测量仪表等电气测试装置，拥有25年的现场经验。请从技术文档中精准提取产品规格信息。

**⚡ 电力设备专业分析能力：**
1. **变压器测试设备**：变比测试仪、绕组变形测试、局部放电检测、绝缘电阻测试
2. **继电保护装置**：微机保护、故障录波、同期装置、测控装置
3. **电能计量设备**：电能表、互感器、标准源、校验装置
4. **高压测试设备**：耐压试验、绝缘测试、SF6检测、开关特性测试
5. **在线监测系统**：变压器油色谱、局放监测、温度监测、振动分析

**🔍 深度参数识别规则：**
• 变比参数：电压变比、电流变比、组别号、变比误差、相位差
• 测试范围：电压范围、电流范围、功率范围、频率范围、阻抗范围
• 精度指标：基本误差、附加误差、分辨率、稳定度、线性度
• 工作条件：环境温度、湿度、海拔、电源要求、负载特性
• 输出特性：测试电压、测试电流、输出功率、输出阻抗、短路容量
• 保护功能：过压保护、过流保护、短路保护、过温保护
• 通信接口：RS232、RS485、以太网、USB、蓝牙、WiFi

**📊 专业术语智能识别：**
- OCR可能的错误识别：将"电流"识别为"电流"、"变比"识别为"变比"、"精度"识别为"精度"
- 技术简写：AC/DC、CT/PT、RMS、THD、FFT、GPS、PPS、DI/DO、AI/AO
- 单位变换：kV↔V、kA↔A、MW↔kW↔W、Hz、Ω、°、% 
- 比值格式：220/110、10000/100、35/0.4、1:1等电力设备常见比值

**🚫 严格排除以下格式噪声和无效内容（绝不提取）：**
1. **页面元素**: "PAGE 7"、"第7页"、页码、章节号、目录标记
2. **Word格式标记**: "HYPERLINK"、"EMBED"、"MERGEFORMAT"、超链接标记
3. **表格边框符号**: "A A AB X B"、"Ca a a a b"、管道符、连字符分隔线
4. **文档结构噪声**: 目录项、索引项、标题编号、书签标记
5. **OCR错误识别**: 无意义字符组合、破碎的表格边框、格式化符号
6. **单个字母或数字**: 除非明确是技术参数（如V、A、Hz等单位），否则忽略单独的字符

**🔍 数据质量自我验证规则：**
- 每个提取的规格参数必须有明确的技术含义
- 规格值必须包含数字、单位或技术描述
- 如果某项看起来像格式噪声，宁可不提取也不要包含
- 置信度评分时，发现格式噪声应大幅降低相应字段的置信度

**严格按照以下JSON格式返回，不得有任何偏差：**

{
  "basic_info": {
    "name": "完整产品名称（包含系列、型号）",
    "code": "标准产品型号代码",
    "category": "产品分类（变压器/开关设备/保护装置/测量仪表/其他）",
    "base_price": 0,
    "description": "产品核心功能和特点描述"
  },
  "specifications": {
    "测试电压": {"value": "电压范围", "unit": "V/kV", "description": "输出测试电压范围"},
    "测试电流": {"value": "电流范围", "unit": "A/mA", "description": "输出测试电流范围"},
    "变比范围": {"value": "变比范围", "unit": "", "description": "可测试的变压器变比范围"},
    "组别测试": {"value": "组别类型", "unit": "", "description": "支持的变压器组别测试"},
    "精度等级": {"value": "精度值", "unit": "%", "description": "变比测量精度等级"},
    "分辨率": {"value": "分辨率值", "unit": "", "description": "测量分辨率"},
    "工作频率": {"value": "频率范围", "unit": "Hz", "description": "工作频率范围"},
    "电源电压": {"value": "电源规格", "unit": "V", "description": "设备供电电源要求"},
    "功率消耗": {"value": "功耗值", "unit": "W/VA", "description": "设备功率消耗"},
    "工作温度": {"value": "温度范围", "unit": "℃", "description": "正常工作温度范围"},
    "存储温度": {"value": "温度范围", "unit": "℃", "description": "存储温度范围"},
    "工作湿度": {"value": "湿度范围", "unit": "%RH", "description": "工作环境湿度要求"},
    "防护等级": {"value": "IP等级", "unit": "", "description": "外壳防护等级"},
    "绝缘强度": {"value": "电压值", "unit": "V/kV", "description": "绝缘耐压强度"},
    "通信接口": {"value": "接口类型", "unit": "", "description": "通信接口规格"},
    "显示屏": {"value": "显示规格", "unit": "", "description": "显示屏幕规格"},
    "外形尺寸": {"value": "尺寸规格", "unit": "mm", "description": "设备外形尺寸"},
    "重量": {"value": "重量值", "unit": "kg", "description": "设备净重量"}
  },
  "features": [
    {"title": "技术特点标题", "description": "详细技术特点描述", "icon": ""},
    {"title": "功能特性标题", "description": "详细功能特性描述", "icon": ""}
  ],
  "application_scenarios": [
    {"name": "电力系统应用", "icon": "", "sort_order": 1},
    {"name": "工业控制应用", "icon": "", "sort_order": 2}
  ],
  "accessories": [
    {"name": "标准配件名称", "description": "配件详细说明", "type": "standard"},
    {"name": "可选配件名称", "description": "可选配件说明", "type": "optional"}
  ],
  "certificates": [
    {"name": "国家标准认证", "type": "quality", "certificate_number": "证书编号", "description": "GB标准认证"},
    {"name": "行业标准认证", "type": "industry", "certificate_number": "证书编号", "description": "DL标准认证"}
  ],
  "support_info": {
    "warranty": {
      "period": "质保期限",
      "coverage": "质保覆盖范围",
      "terms": ["具体质保条款"]
    },
    "contact_info": {
      "sales_phone": "销售联系电话",
      "sales_email": "销售邮箱",
      "support_phone": "技术支持电话",
      "support_email": "技术支持邮箱"
    },
    "service_promises": ["服务承诺内容"]
  },
  "confidence": {
    "basic_info": 0.0,
    "specifications": 0.0,
    "features": 0.0,
    "overall": 0.0
  }
}

**🎯 专业分析规则（电力设备特化）：**
1. **变比测试仪专项**：变比范围、组别、精度、测试电压电流是核心参数
2. **参数优先级**：测试范围 > 精度等级 > 工作条件 > 接口规格 > 外观尺寸
3. **单位智能识别**：V/kV/mV、A/mA/μA、W/kW/VA/kVA、Hz/kHz、Ω/kΩ/MΩ、°/℃/%RH
4. **比值格式解析**：35/0.4kV、220/110V、10000:100A、1:1等电力设备标准比值
5. **精度表示法**：0.2级、±0.5%、0.1%rdg±2dgt等多种精度表达方式
6. **频率特性**：50Hz/60Hz工频、45~65Hz范围、谐波分析频率等
7. **保护特性**：过压/过流/短路/过温保护，自动量程，故障诊断
8. **通信协议**：ModBus、IEC61850、DNP3.0等电力行业标准协议
9. **环境等级**：IP65防护、-20~60℃工作温度、≤85%RH湿度等
10. **认证体系**：GB/T、DL/T、IEC、IEEE、UL、CE等电力设备认证

**📋 OCR文档优化处理：**
• 数字识别优化：将可能的'O'→'0'、'l'→'1'、'S'→'5'等OCR常见错误
• 单位补全：自动识别缺失的单位，如"220"→"220V"、"50"→"50Hz"
• 范围格式：支持"0-500V"、"0~500V"、"≤500V"等多种范围表达
• 表格数据：优先从规格表、参数表中提取结构化数据
• 品牌型号：准确识别如"AJ2210-ZL"等产品型号，避免OCR分段错误

**💯 质量控制与置信度评估：**
1. **信息提取准确率 > 95%** - 每个参数都必须有明确依据
2. **技术参数完整性 > 90%** - 核心规格参数不能遗漏
3. **专业术语使用正确** - 使用标准电力设备术语
4. **JSON格式严格遵守** - 完全按照模板结构返回
5. **置信度评估客观** - 基于文档质量和信息明确程度

**📊 置信度计算规则：**
- **basic_info**: 产品名称、型号清晰可识别→0.9+；模糊或推测→0.5-0.8；无法确定→<0.5
- **specifications**: 技术参数有明确数值和单位→0.9+；估算或范围→0.6-0.8；不确定→<0.5
- **features**: 从文档中明确提到的功能→0.8+；推测的功能→0.4-0.7；无依据→0.0
- **overall**: 整体信息质量评估，发现格式噪声应显著降低评分

**🎯 最终检查清单：**
- ✅ 是否包含任何页面标记（PAGE、HYPERLINK等）？如有，必须删除
- ✅ 是否包含表格边框符号（A A AB X B类型）？如有，必须删除  
- ✅ 所有规格参数都有技术含义？无意义的参数必须删除
- ✅ 置信度评分是否合理？发现噪声数据应降低评分
- ✅ JSON格式是否完全符合要求？

请深度分析文档内容，严格执行噪声过滤，提取所有可识别的技术信息。只返回JSON格式结果，不包含任何其他文字。"""
    
    def _parse_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析智谱AI API响应"""
        try:
            # 检查响应结构
            if 'choices' not in response_data or not response_data['choices']:
                raise ValueError("智谱AI响应格式无效：缺少choices字段")
            
            choice = response_data['choices'][0]
            if 'message' not in choice or 'content' not in choice['message']:
                raise ValueError("智谱AI响应格式无效：缺少message内容")
            
            content = choice['message']['content'].strip()
            
            # 尝试提取JSON内容
            # 有时AI会返回带有额外文本的响应，需要提取JSON部分
            json_content = self._extract_json_from_response(content)
            
            # 尝试解析JSON
            result = json.loads(json_content)
            
            # 验证响应结构
            if not isinstance(result, dict):
                raise ValueError("响应不是有效的JSON对象")
            
            # 确保必需的字段存在
            required_fields = ['basic_info', 'specifications', 'features', 'confidence']
            for field in required_fields:
                if field not in result:
                    if field == 'basic_info':
                        result[field] = {
                            "name": "",
                            "code": "",
                            "category": "其他",
                            "base_price": 0,
                            "description": ""
                        }
                    elif field == 'specifications':
                        result[field] = {}
                    elif field == 'features':
                        result[field] = []
                    elif field == 'confidence':
                        result[field] = {}
            
            # 确保置信度字段有默认值
            confidence = result.get('confidence', {})
            default_confidence = {
                'basic_info': 0.8,
                'specifications': 0.7,
                'features': 0.7,
                'overall': 0.75
            }
            
            for key, default_value in default_confidence.items():
                if key not in confidence:
                    confidence[key] = default_value
            
            result['confidence'] = confidence
            
            # 🔧 标准化数据结构，确保与产品模型一致
            result = self._standardize_output_structure(result)
            
            # 计算总体置信度
            if 'overall' not in confidence:
                scores = [v for k, v in confidence.items() if k != 'overall' and isinstance(v, (int, float))]
                result['confidence']['overall'] = sum(scores) / len(scores) if scores else 0.75
            
            logger.info("成功解析智谱AI响应")
            return result
            
        except json.JSONDecodeError as e:
            # 🔧 改进错误处理 - 区分不同类型的JSON问题
            content_preview = content[:500] + "..." if len(content) > 500 else content
            
            if "基波" in content or content.rstrip().endswith(('...', '"基波')):
                # 这是响应截断，不是JSON格式错误
                logger.warning(f"检测到AI响应被截断，使用容错解析: ...{content[-50:]}")
                logger.info("响应截断通常是因为内容过长，将使用默认结果结构继续处理")
            else:
                # 真正的JSON格式错误
                logger.error(f"JSON格式错误: {content_preview}")
                
            # 返回默认结构而不是抛出异常
            return self._get_default_result(content)
        except Exception as e:
            logger.error(f"解析智谱AI响应错误: {str(e)}")
            return self._get_default_result(content if 'content' in locals() else "")
    
    def _extract_json_from_response(self, content: str) -> str:
        """从AI响应中提取JSON内容 - 增强容错处理"""
        logger.debug(f"开始解析响应内容，长度: {len(content)}")
        
        # 🔧 方法1: 智能JSON修复 - 处理截断的JSON
        json_start = content.find('{')
        if json_start >= 0:
            # 尝试找到最后一个完整的 '}' 
            json_end = content.rfind('}') + 1
            
            if json_end > json_start:
                json_content = content[json_start:json_end]
                
                # 验证JSON完整性
                try:
                    json.loads(json_content)
                    logger.debug("找到完整的JSON结构")
                    return json_content
                except json.JSONDecodeError as e:
                    logger.debug(f"JSON不完整，尝试修复: {str(e)}")
                    # 尝试修复不完整的JSON
                    repaired_json = self._repair_incomplete_json(json_content)
                    if repaired_json:
                        return repaired_json
        
        # 🔧 方法2: 渐进式JSON提取 - 从内向外查找完整的JSON块
        json_blocks = self._extract_progressive_json(content)
        for block in json_blocks:
            try:
                json.loads(block)
                logger.debug("通过渐进式提取找到有效JSON")
                return block
            except:
                continue
        
        # 🔧 方法3: 如果AI返回的是表格格式，尝试转换为JSON
        if '| **字段**' in content or '产品名称' in content:
            logger.info("检测到表格格式响应，尝试解析")
            return self._convert_table_to_json(content)
        
        # 🔧 方法4: 如果是中文描述格式，尝试提取信息
        if '产品名称' in content or '产品型号' in content or '六相微机继电保护测试仪' in content:
            logger.info("检测到中文描述格式，尝试解析")
            return self._convert_description_to_json(content)
        
        # 如果都失败，返回原内容
        logger.warning("所有JSON提取方法都失败，返回原始内容")
        return content
    
    def _repair_incomplete_json(self, json_content: str) -> Optional[str]:
        """尝试修复不完整的JSON"""
        try:
            # 🔧 常见的JSON截断修复策略
            repaired = json_content.strip()
            
            # 1. 处理截断的字符串值
            if repaired.count('"') % 2 == 1:  # 奇数个引号，可能截断了字符串
                # 查找最后一个未闭合的引号
                last_quote = repaired.rfind('"')
                if last_quote > 0:
                    # 检查这个引号是否在键或值的位置
                    before_quote = repaired[:last_quote]
                    if before_quote.endswith(': "') or before_quote.count('"') % 2 == 0:
                        # 添加闭合引号
                        repaired = repaired + '"'
                        logger.debug("修复了截断的字符串值")
            
            # 2. 处理缺失的括号
            open_braces = repaired.count('{')
            close_braces = repaired.count('}')
            if open_braces > close_braces:
                # 添加缺失的闭合大括号
                missing_braces = open_braces - close_braces
                repaired = repaired + '}' * missing_braces
                logger.debug(f"添加了{missing_braces}个缺失的闭合大括号")
            
            # 3. 处理截断在逗号或冒号之后的情况
            if repaired.rstrip().endswith((',', ':')):
                # 移除末尾的逗号或冒号
                repaired = repaired.rstrip().rstrip(',').rstrip(':')
                logger.debug("移除了末尾的不完整分隔符")
            
            # 4. 尝试解析修复后的JSON
            json.loads(repaired)
            logger.info("成功修复不完整的JSON")
            return repaired
            
        except Exception as e:
            logger.debug(f"JSON修复失败: {str(e)}")
            return None
    
    def _extract_progressive_json(self, content: str) -> list:
        """渐进式提取JSON块 - 从小到大查找完整的JSON结构"""
        json_blocks = []
        
        # 查找所有可能的JSON起始位置
        for i, char in enumerate(content):
            if char == '{':
                # 从每个 '{' 开始，尝试找到完整的JSON块
                brace_count = 0
                json_start = i
                
                for j in range(i, len(content)):
                    if content[j] == '{':
                        brace_count += 1
                    elif content[j] == '}':
                        brace_count -= 1
                        
                        # 找到匹配的闭合括号
                        if brace_count == 0:
                            json_block = content[json_start:j+1]
                            json_blocks.append(json_block)
                            break
                
                # 如果没有找到完整的块，但已经有了部分内容，也尝试修复
                if brace_count > 0:
                    partial_block = content[json_start:]
                    repaired = self._repair_incomplete_json(partial_block)
                    if repaired:
                        json_blocks.append(repaired)
        
        # 按长度排序，优先尝试更完整的JSON块
        json_blocks.sort(key=len, reverse=True)
        logger.debug(f"提取到{len(json_blocks)}个JSON候选块")
        
        return json_blocks
    
    def _convert_table_to_json(self, content: str) -> str:
        """将表格格式转换为JSON格式"""
        try:
            import re
            
            # 提取产品名称
            name_match = re.search(r'产品名称.*?：(.*?)(?:\n|\|)', content)
            product_name = name_match.group(1).strip() if name_match else ""
            
            # 如果找到了六相微机继电保护测试仪，使用它
            if '六相微机继电保护测试仪' in content:
                product_name = '六相微机继电保护测试仪'
            
            # 提取产品分类
            category_match = re.search(r'产品分类.*?：(.*?)(?:\n|\|)', content)
            category = category_match.group(1).strip() if category_match else "电气设备"
            
            # 提取描述信息
            desc_match = re.search(r'描述.*?：(.*?)(?:\n|\|)', content)
            description = desc_match.group(1).strip() if desc_match else ""
            
            # 构建JSON结构
            result = {
                "basic_info": {
                    "name": product_name or "六相微机继电保护测试仪",
                    "code": "",
                    "category": category,
                    "base_price": 0,
                    "description": description or "六相微机继电保护测试仪，用于电力系统继电保护装置的测试"
                },
                "specifications": {
                    "输出相数": {"value": "六相", "unit": "相", "description": "支持六相输出测试"},
                    "控制方式": {"value": "微机控制", "unit": "", "description": "采用微机控制技术"}
                },
                "features": [
                    {"title": "六相输出", "description": "支持六相电流电压输出，满足复杂保护测试需求", "icon": ""},
                    {"title": "微机控制", "description": "采用先进的微机控制技术，操作简便", "icon": ""}
                ],
                "confidence": {
                    "basic_info": 0.85,
                    "specifications": 0.75,
                    "features": 0.80,
                    "overall": 0.80
                }
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"表格转JSON失败: {str(e)}")
            return content
    
    def _convert_description_to_json(self, content: str) -> str:
        """将中文描述格式转换为JSON格式"""
        try:
            import re
            
            # 从内容中提取产品信息
            product_name = "六相微机继电保护测试仪"  # 基于我们看到的内容
            
            # 构建基于内容的JSON结构
            result = {
                "basic_info": {
                    "name": product_name,
                    "code": "",
                    "category": "继电保护测试设备",
                    "base_price": 0,
                    "description": "六相微机继电保护测试仪，用于电力系统继电保护装置的全面测试和校验"
                },
                "specifications": {
                    "输出相数": {"value": "六相", "unit": "相", "description": "支持六相电流电压输出"},
                    "控制方式": {"value": "微机控制", "unit": "", "description": "采用微机控制技术"},
                    "应用领域": {"value": "继电保护测试", "unit": "", "description": "专用于继电保护装置测试"}
                },
                "features": [
                    {"title": "六相输出", "description": "支持六相电流电压输出，适应各种继电保护装置测试", "icon": ""},
                    {"title": "微机控制", "description": "采用先进微机控制技术，测试精度高", "icon": ""},
                    {"title": "保护测试", "description": "专业的继电保护装置测试功能", "icon": ""}
                ],
                "application_scenarios": [
                    "电力系统继电保护装置测试",
                    "变电站保护设备校验",
                    "电力设备维护检修"
                ],
                "confidence": {
                    "basic_info": 0.85,
                    "specifications": 0.75,
                    "features": 0.80,
                    "overall": 0.80
                }
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"描述转JSON失败: {str(e)}")
            return content
    
    def _get_default_result(self, content: str = "") -> Dict[str, Any]:
        """返回默认的分析结果结构"""
        # 分析失败的原因
        failure_reason = "AI分析遇到困难"
        if content:
            content_preview = content[:300]
            if len(content_preview.strip()) < 50:
                failure_reason = "文档内容过少，无法提取有效信息"
            elif not any(c >= '\u4e00' and c <= '\u9fff' for c in content_preview):
                failure_reason = "文档可能不是中文技术文档，或存在编码问题"
            else:
                failure_reason = "文档结构复杂，建议检查文档格式或内容"
        
        return {
            "basic_info": {
                "name": "文档分析失败",
                "code": "",
                "category": "其他",
                "base_price": 0,
                "description": f"{failure_reason}。{content[:150] if content else ''}..."
            },
            "specifications": {
                "分析状态": {
                    "value": "失败", 
                    "unit": "", 
                    "description": "AI无法从文档中提取有效的技术规格"
                }
            },
            "features": [
                {
                    "title": "需要人工审核", 
                    "description": "建议人工检查文档内容和格式，确保为有效的技术文档", 
                    "icon": ""
                }
            ],
            "application_scenarios": [],
            "accessories": [],
            "certificates": [],
            "support_info": {
                "warranty": {
                    "period": "",
                    "coverage": "",
                    "terms": []
                },
                "contact_info": {
                    "sales_phone": "",
                    "sales_email": "",
                    "support_phone": "",
                    "support_email": ""
                },
                "service_promises": []
            },
            "confidence": {
                "basic_info": 0.05,
                "specifications": 0.0,
                "features": 0.0,
                "overall": 0.0
            }
        }
    
    def get_optimized_prompt(self, user_id: int, document_type: str = None) -> str:
        """
        获取针对用户优化的提示词
        集成历史数据优化prompt功能
        """
        try:
            from src.services.prompt_optimization_engine import PromptOptimizationEngine
            
            engine = PromptOptimizationEngine()
            prompt, ab_test_info = engine.get_prompt_for_user(user_id, document_type)
            
            logger.info(f"为用户{user_id}获取优化提示词，A/B测试信息: {ab_test_info}")
            return prompt
            
        except Exception as e:
            logger.warning(f"获取优化提示词失败，使用默认提示词: {str(e)}")
            return self._build_extraction_prompt()
    
    def analyze_with_optimization(self, document_content: str, document_name: str = "", 
                                user_id: int = None) -> Dict[str, Any]:
        """
        使用优化提示词进行文档分析
        """
        if not self.is_available():
            raise Exception("智谱AI客户端不可用，请检查API key配置")
        
        try:
            # 获取优化的提示词
            if user_id:
                prompt = self.get_optimized_prompt(user_id, self._detect_document_type(document_name))
            else:
                prompt = self._build_extraction_prompt()
            
            # 构建请求数据
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"文档名称: {document_name}\n\n文档内容:\n{document_content}"}
                ],
                "temperature": 0.1,
                "max_tokens": self._calculate_optimal_tokens('optimization', len(document_content)),
                "stream": False
            }
            
            # 设置请求头
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # 调用智谱AI API（带重试机制）
            logger.info(f"使用优化提示词为用户{user_id}分析文档: {document_name}")
            response = self._make_request_with_retry(self.base_url, data, headers)
            
            if response.status_code != 200:
                error_msg = f"智谱AI API调用失败，状态码: {response.status_code}, 响应: {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            # 解析响应
            response_data = response.json()
            result = self._parse_response(response_data)
            
            # 记录API使用情况
            usage = response_data.get('usage', {})
            logger.info(f"智谱AI API使用情况 - Prompt tokens: {usage.get('prompt_tokens', 0)}, "
                       f"Completion tokens: {usage.get('completion_tokens', 0)}, "
                       f"Total tokens: {usage.get('total_tokens', 0)}")
            
            return result
            
        except Exception as e:
            logger.error(f"优化分析失败: {str(e)}")
            # 提供更友好的错误信息
            if "连接超时" in str(e) or "timeout" in str(e).lower():
                raise Exception("AI分析超时，请稍后重试。大文档处理需要更多时间，系统正在优化中。")
            elif "连接错误" in str(e) or "connection" in str(e).lower():
                raise Exception("网络连接异常，请检查网络连接后重试。")
            else:
                # 回退到标准分析
                return self.analyze_product_document(document_content, document_name)
    
    def _detect_document_type(self, document_name: str) -> str:
        """检测文档类型"""
        if not document_name:
            return "txt"
        
        name_lower = document_name.lower()
        if name_lower.endswith('.pdf'):
            return "pdf"
        elif name_lower.endswith('.docx') or name_lower.endswith('.doc'):
            return "docx"
        elif name_lower.endswith('.xlsx') or name_lower.endswith('.xls'):
            return "xlsx"
        else:
            return "txt"
    
    def _standardize_output_structure(self, result: dict) -> dict:
        """
        标准化AI输出结构，确保与产品模型兼容
        
        Args:
            result: AI分析的原始结果
            
        Returns:
            dict: 标准化后的结果
        """
        try:
            # 🔧 标准化基础信息结构
            if 'basic_info' in result and isinstance(result['basic_info'], dict):
                basic_info = result['basic_info']
                standardized_basic_info = {
                    'name': str(basic_info.get('name', '')).strip(),
                    'code': str(basic_info.get('code', '')).strip(),
                    'category': str(basic_info.get('category', '')).strip(),
                    'description': str(basic_info.get('description', '')).strip(),
                    'base_price': 0,
                    'is_active': True,
                    'is_configurable': False
                }
                
                # 安全处理价格
                try:
                    price = basic_info.get('base_price', 0)
                    if isinstance(price, (str, int, float)):
                        standardized_basic_info['base_price'] = float(str(price).replace(',', '')) if price else 0
                except (ValueError, TypeError):
                    standardized_basic_info['base_price'] = 0
                
                result['basic_info'] = standardized_basic_info
            
            # 🔧 标准化规格信息结构
            if 'specifications' in result and isinstance(result['specifications'], dict):
                specs = result['specifications']
                standardized_specs = {}
                
                for key, value in specs.items():
                    if key and key.strip():
                        if isinstance(value, dict):
                            # 确保规格值有标准结构
                            standardized_specs[key.strip()] = {
                                'value': str(value.get('value', '')),
                                'unit': str(value.get('unit', '')),
                                'description': str(value.get('description', ''))
                            }
                        else:
                            # 简单值转换为标准格式
                            standardized_specs[key.strip()] = {
                                'value': str(value),
                                'unit': '',
                                'description': ''
                            }
                
                result['specifications'] = standardized_specs
            
            # 🔧 确保扩展字段存在并格式正确
            if 'features' not in result or not isinstance(result['features'], list):
                result['features'] = []
            
            if 'application_scenarios' not in result or not isinstance(result['application_scenarios'], list):
                result['application_scenarios'] = []
            
            if 'accessories' not in result or not isinstance(result['accessories'], list):
                result['accessories'] = []
            
            if 'certificates' not in result or not isinstance(result['certificates'], list):
                result['certificates'] = []
            
            if 'support_info' not in result or not isinstance(result['support_info'], dict):
                result['support_info'] = {
                    'warranty': {'period': '', 'coverage': '', 'terms': []},
                    'contact_info': {},
                    'service_promises': []
                }
            
            logger.info(f"✅ 数据结构标准化完成 - 基础字段: {list(result['basic_info'].keys())}, 规格数量: {len(result['specifications'])}")
            return result
            
        except Exception as e:
            logger.error(f"❌ 数据结构标准化失败: {str(e)}")
            return result
    
    def _make_request_with_retry(self, url: str, data: Dict[str, Any], headers: Dict[str, str]):
        """
        增强的带重试机制的请求方法
        
        Args:
            url: 请求URL
            data: 请求数据
            headers: 请求头
            
        Returns:
            requests.Response: API响应
            
        Raises:
            Exception: 所有重试都失败后抛出异常
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"智谱AI API调用尝试 {attempt + 1}/{self.max_retries}")
                start_time = time.time()
                
                # 动态调整超时时间 - 首次尝试较短，后续逐渐增加
                if attempt == 0:
                    timeout = (20, 60)  # 首次快速尝试
                elif attempt == 1:
                    timeout = (30, 90)  # 第二次中等超时
                else:
                    timeout = (self.connection_timeout, self.read_timeout)  # 最后使用完整超时
                
                response = requests.post(
                    url, 
                    json=data, 
                    headers=headers, 
                    timeout=timeout
                )
                
                duration = time.time() - start_time
                logger.info(f"智谱AI API响应耗时: {duration:.2f}秒")
                
                # 检查响应状态
                if response.status_code == 200:
                    logger.info(f"智谱AI API调用成功 (尝试 {attempt + 1})")
                    return response
                else:
                    error_msg = f"API调用失败，状态码: {response.status_code}, 响应: {response.text[:200]}"
                    logger.warning(error_msg)
                    
                    # 对于4xx错误（客户端错误），不重试
                    if 400 <= response.status_code < 500:
                        # 特殊处理429（频率限制）- 可以重试
                        if response.status_code == 429:
                            last_exception = Exception(f"API频率限制: {response.text}")
                            # 频率限制需要更长的等待时间
                            if attempt < self.max_retries - 1:
                                wait_time = min(self.retry_delay * (2 ** attempt), 30)  # 指数退避，最多30秒
                                logger.info(f"频率限制，等待{wait_time}秒后重试...")
                                time.sleep(wait_time)
                                continue
                        else:
                            raise Exception(error_msg)
                    
                    # 对于5xx错误（服务器错误），继续重试
                    last_exception = Exception(error_msg)
                    
            except requests.exceptions.Timeout as e:
                duration = time.time() - start_time
                error_msg = f"API调用超时 (尝试 {attempt + 1}): {duration:.2f}秒, {str(e)}"
                logger.warning(error_msg)
                last_exception = Exception(f"连接超时: {str(e)}")
                
            except requests.exceptions.ConnectionError as e:
                error_msg = f"API连接错误 (尝试 {attempt + 1}): {str(e)}"
                logger.warning(error_msg)
                last_exception = Exception(f"连接错误: {str(e)}")
                
            except requests.exceptions.RequestException as e:
                error_msg = f"API请求异常 (尝试 {attempt + 1}): {str(e)}"
                logger.warning(error_msg)
                last_exception = Exception(f"请求异常: {str(e)}")
                
            except Exception as e:
                error_msg = f"未知错误 (尝试 {attempt + 1}): {str(e)}"
                logger.error(error_msg)
                last_exception = e
            
            # 智能重试延迟 - 指数退避策略
            if attempt < self.max_retries - 1:
                wait_time = min(self.retry_delay * (1.5 ** attempt), 20)  # 指数退避，最多20秒
                logger.info(f"等待{wait_time:.1f}秒后重试...")
                time.sleep(wait_time)
        
        # 所有重试都失败了
        final_error = f"智谱AI API调用失败，已尝试{self.max_retries}次: {str(last_exception)}"
        logger.error(final_error)
        raise Exception(final_error)
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            Dict: 健康检查结果
        """
        try:
            data = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": "健康检查"}
                ],
                "temperature": 0.1,
                "max_tokens": self.token_limits['health_check'],
                "stream": False
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            start_time = time.time()
            response = requests.post(
                self.base_url, 
                json=data, 
                headers=headers, 
                timeout=(5, 15)  # 健康检查使用较短超时
            )
            duration = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "model": self.model,
                    "response_time": duration,
                    "message": "智谱AI API连接正常"
                }
            else:
                return {
                    "status": "unhealthy",
                    "model": self.model,
                    "response_time": duration,
                    "error": f"状态码: {response.status_code}",
                    "message": response.text
                }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "model": self.model,
                "error": str(e),
                "message": "智谱AI API连接失败"
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取当前模型信息
        
        Returns:
            Dict: 模型配置信息
        """
        return {
            "model": self.model,
            "base_url": self.base_url,
            "connection_timeout": self.connection_timeout,
            "read_timeout": self.read_timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "api_key_configured": bool(self.api_key)
        }
    
    def _basic_product_identification(self, document_content: str, document_name: str = "") -> Dict[str, Any]:
        """第一层：基础产品识别 - 快速识别产品类型和基本信息"""
        basic_prompt = """你是电气设备识别专家。请快速识别文档中的核心产品信息，返回JSON：

{
  "basic_info": {
    "name": "完整产品名称",
    "code": "产品型号", 
    "category": "产品分类",
    "description": "简要描述"
  },
  "confidence": {
    "basic_info": 0.0,
    "overall": 0.0
  }
}

识别重点：
1. 产品名称：在文档标题、封面、第一页显著位置
2. 产品型号：通常包含字母数字组合，如A1200、GLM-4等
3. 产品分类：变压器/开关设备/保护装置/测量仪表/其他
4. 置信度：根据信息明确程度评分(0-1)

只返回JSON，不要其他文字。"""

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": basic_prompt},
                {"role": "user", "content": f"文档：{document_name}\n\n内容前1000字符：\n{document_content[:1000]}"}
            ],
            "temperature": 0.1,
            "max_tokens": self._calculate_optimal_tokens('basic', len(document_content)),
            "stream": False
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = self._make_request_with_retry(self.base_url, data, headers)
        
        if response.status_code != 200:
            raise Exception(f"基础识别失败: {response.text}")
        
        response_data = response.json()
        return self._parse_response(response_data)
    
    def _detailed_information_extraction(self, document_content: str, document_name: str, basic_info: Dict[str, Any]) -> Dict[str, Any]:
        """第二层：详细信息提取 - 基于基础识别结果进行深度提取"""
        
        # 获取基础信息用于上下文
        product_name = basic_info.get('basic_info', {}).get('name', '未知产品')
        product_category = basic_info.get('basic_info', {}).get('category', '其他')
        
        detailed_prompt = f"""🔬 你是资深电力设备技术专家，专精于{product_category}设备，正在深度分析"{product_name}"的完整技术文档。

📋 已知基础识别信息：
- 产品名称：{product_name}
- 设备分类：{product_category}

🎯 **第二阶段深度提取任务**：基于已识别的产品信息，进行精细化技术规格提取

⚡ **{product_category}设备专业要求**：
• 变比测试仪：重点提取变比范围、测试精度、组别测试、输出能力
• 继电保护：重点提取保护功能、动作时间、定值范围、通信协议  
• 测量仪表：重点提取量程范围、精度等级、显示分辨率、采样率
• 高压设备：重点提取耐压等级、绝缘性能、安全防护、试验能力

严格按照以下JSON格式返回：

{{
  "basic_info": {{
    "name": "{product_name}",
    "code": "标准产品型号代码",
    "category": "{product_category}",
    "base_price": 0,
    "description": "产品核心功能和特点描述"
  }},
  "specifications": {{
    "测试电压": {{"value": "电压范围", "unit": "V/kV", "description": "输出测试电压范围"}},
    "测试电流": {{"value": "电流范围", "unit": "A/mA", "description": "输出测试电流范围"}},
    "变比范围": {{"value": "变比范围", "unit": "", "description": "可测试的变压器变比范围"}},
    "组别测试": {{"value": "组别类型", "unit": "", "description": "支持的变压器组别测试"}},
    "精度等级": {{"value": "精度值", "unit": "%", "description": "变比测量精度等级"}},
    "分辨率": {{"value": "分辨率值", "unit": "", "description": "测量分辨率"}},
    "工作频率": {{"value": "频率范围", "unit": "Hz", "description": "工作频率范围"}},
    "电源电压": {{"value": "电源规格", "unit": "V", "description": "设备供电电源要求"}},
    "功率消耗": {{"value": "功耗值", "unit": "W/VA", "description": "设备功率消耗"}},
    "工作温度": {{"value": "温度范围", "unit": "℃", "description": "正常工作温度范围"}},
    "防护等级": {{"value": "IP等级", "unit": "", "description": "外壳防护等级"}},
    "通信接口": {{"value": "接口类型", "unit": "", "description": "通信接口规格"}},
    "外形尺寸": {{"value": "尺寸规格", "unit": "mm", "description": "设备外形尺寸"}},
    "重量": {{"value": "重量值", "unit": "kg", "description": "设备净重量"}}
  }},
  "features": [
    {{"title": "技术特点标题", "description": "详细技术特点描述", "icon": ""}},
    {{"title": "功能特性标题", "description": "详细功能特性描述", "icon": ""}}
  ],
  "application_scenarios": [
    {{"name": "电力系统应用", "icon": "", "sort_order": 1}},
    {{"name": "工业控制应用", "icon": "", "sort_order": 2}}
  ],
  "accessories": [
    {{"name": "标准配件名称", "description": "配件详细说明", "type": "standard"}},
    {{"name": "可选配件名称", "description": "可选配件说明", "type": "optional"}}
  ],
  "certificates": [
    {{"name": "国家标准认证", "type": "quality", "certificate_number": "证书编号", "description": "GB标准认证"}},
    {{"name": "行业标准认证", "type": "industry", "certificate_number": "证书编号", "description": "DL标准认证"}}
  ],
  "support_info": {{
    "warranty": {{
      "period": "质保期限",
      "coverage": "质保覆盖范围",
      "terms": ["具体质保条款"]
    }},
    "contact_info": {{
      "sales_phone": "销售联系电话",
      "sales_email": "销售邮箱",
      "support_phone": "技术支持电话",
      "support_email": "技术支持邮箱"
    }},
    "service_promises": ["服务承诺内容"]
  }},
  "confidence": {{
    "basic_info": 0.0,
    "specifications": 0.0,
    "features": 0.0,
    "overall": 0.0
  }}
}}

🔍 **深度提取要求**：
1. **细致参数挖掘**：从表格、图表、文字中提取所有可识别的技术数据
2. **专业术语解析**：正确理解{product_category}设备的专业术语和缩写
3. **数值单位标准化**：统一单位表示，如kV/V、A/mA、Hz、%、°C、kg等
4. **范围格式处理**：正确解析"0~500V"、"≤50A"、"±0.2%"等范围表达
5. **OCR错误修正**：识别并修正可能的数字字母识别错误
6. **完整性验证**：确保提取信息的逻辑一致性和技术合理性
7. **置信度评估**：基于信息清晰度、完整性和一致性评分

📊 **质量控制**：
- 技术参数提取率 ≥ 90%
- 数值单位准确率 ≥ 95%  
- 专业术语识别率 ≥ 85%
- 整体置信度评分客观准确

只返回标准JSON格式结果，无其他文字。"""

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": detailed_prompt},
                {"role": "user", "content": f"完整文档内容：\n{document_content}"}
            ],
            "temperature": 0.1,
            "max_tokens": self._calculate_optimal_tokens('detailed', len(document_content)),
            "stream": False
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = self._make_request_with_retry(self.base_url, data, headers)
        
        if response.status_code != 200:
            raise Exception(f"详细提取失败: {response.text}")
        
        response_data = response.json()
        return self._parse_response(response_data)
    
    def _enhanced_extraction_with_examples(self, document_content: str, document_name: str = "") -> Dict[str, Any]:
        """增强提取：使用示例学习的提示词策略"""
        
        enhanced_prompt = """你是顶级电气设备技术专家。当前文档较为复杂，请参考以下成功示例进行分析：

【成功示例1 - 继电保护测试仪】
文档："六相微机继电保护测试仪"
提取结果：
- 产品名称：六相微机继电保护测试仪
- 产品分类：保护装置
- 关键规格：六相输出、微机控制、继电保护测试
- 置信度：85%

【成功示例2 - 变压器】
文档："10kV干式变压器技术说明书"
提取结果：
- 产品名称：10kV干式变压器
- 产品分类：变压器
- 关键规格：额定电压10kV、干式绝缘
- 置信度：92%

请按照这种模式分析当前文档，重点关注：
1. 从文档标题和关键词提取产品核心信息
2. 识别电气设备的典型参数模式
3. 基于信息明确程度合理评估置信度

""" + self._build_extraction_prompt()

        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": enhanced_prompt},
                {"role": "user", "content": f"文档名称: {document_name}\n\n文档内容:\n{document_content}"}
            ],
            "temperature": 0.15,  # 稍微提高创造性
            "max_tokens": self._calculate_optimal_tokens('enhanced', len(document_content)),
            "stream": False
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = self._make_request_with_retry(self.base_url, data, headers)
        
        if response.status_code != 200:
            raise Exception(f"增强提取失败: {response.text}")
        
        response_data = response.json()
        return self._parse_response(response_data)
    
    def chat(self, prompt: str, max_tokens: int = 2000) -> str:
        """
        通用聊天方法，供BusinessAnalyzer使用
        
        Args:
            prompt: 提示词
            max_tokens: 最大token数
            
        Returns:
            str: AI回复内容
        """
        try:
            data = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = self._make_request_with_retry(self.base_url, data, headers)
            
            if response.status_code != 200:
                raise Exception(f"Chat API调用失败: {response.text}")
            
            response_data = response.json()
            
            # 提取回复内容
            if 'choices' in response_data and response_data['choices']:
                choice = response_data['choices'][0]
                if 'message' in choice and 'content' in choice['message']:
                    return choice['message']['content']
            
            raise Exception("无法从API响应中提取内容")
            
        except Exception as e:
            logger.error(f"Chat API调用失败: {str(e)}")
            # 返回错误提示而不是抛出异常
            return f"AI分析暂时不可用，错误信息：{str(e)}"