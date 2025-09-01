# -*- coding: utf-8 -*-
"""
AI分析服务
整合文档处理和OpenAI分析，提供完整的AI产品分析功能
"""
import logging
import time
import json
from typing import Dict, Any, Optional, Tuple, List
from werkzeug.datastructures import FileStorage
from datetime import datetime

from .document_processor import DocumentProcessor
from .zhipuai_client import ZhipuAIClient
from .learning_engine import LearningEngine
from .table_parser import TableParser
from .confidence_scorer import ConfidenceScorer

logger = logging.getLogger(__name__)

class DataQualityValidator:
    """数据质量验证器 - 专门处理AI分析结果的质量控制"""
    
    def __init__(self):
        # 格式噪声检测模式 - 增强版，针对页面截图中的问题和二进制垃圾数据
        self.noise_patterns = [
            # 🗂️ 文档格式标记
            r'PAGE\s+\d+',          # PAGE 7 格式
            r'HYPERLINK',           # HYPERLINK 标记
            r'EMBED',               # EMBED 标记
            r'^[A-Z]\s+[A-Z]\s+[A-Z][A-Z]?\s+[A-Z]\s+[A-Z]$',  # A A AB X B 类型
            r'^[A-Z][a-z]?\s+[a-z]\s+[a-z]\s+[a-z]\s+[a-z]$',  # Ca a a a b 类型
            r'^[a-z]+\s+\d+\s+[A-Z]+.*$',  # h 9 HYPERLINK 类型
            r'^\s*[｜\|]\s*$',      # 单独的管道符
            r'^[\|\s\-\+\=]{3,}$',  # 表格边框线
            
            # 🚮 用户反馈的具体问题规格
            r'^TEST\s*$',           # 单独的TEST
            r'^RS\s*$',             # 单独的RS
            r'^[A-Z]{1,2}\s*$',     # 单独的1-2个大写字母（如"D"、"I"）
            r'λspec.*?提取',        # λspec_table中提取 类型
            r'/λ\w*',              # /λ开头的特殊标记
            r'spec_table',          # spec_table标记
            r'WIRE\d+\s+\d+RS\d+',  # WIRE1 3RS232 类型的格式噪声
            r'^\d+\.\d+(\.\d+)?\s+[A-Z]{1,2}(-[a-z])?$',  # 3.2 D, 5.2.14 I-t 类型的无意义组合
            r'^\d+\.\d+(\.\d+)?\s+[A-Z]\s*$',  # 数字后跟单个字母
            r'^[A-Z]\s*-\s*[a-z]$',    # I-t 类型的无意义组合
            r'^\d+\.\d+\.\d+\s+[A-Z]-[a-z]$',  # 5.2.14 I-t 这种特定格式
            
            # 🗄️ 二进制垃圾数据检测模式 - 针对.doc文件解析产生的乱码
            r'^[^\u4e00-\u9fff\w\s\.,;:!?\-()\'"\[\]{}]{3,}$',  # 连续非标准字符
            r'^[\u0080-\u00ff]{2,}$',          # Latin-1扩展字符区域的乱码
            r'^[\ue000-\uf8ff]{1,}$',          # 私用区字符（常见于编码错误）
            r'^[\u2000-\u206f\u2070-\u209f\u20a0-\u20cf\u2100-\u214f]{2,}$',  # 特殊符号区
            r'^[潗摲楍牣獯景煅慵楴湯畱瑡潩卍潗摲潄吀瑩敬牁慩袈霡蠈袢]{1,}$',  # 常见.doc解析乱码字符
            r'^[㸳㠴㔷㤸㜹㈰㐱㠲㌳㘴㔵㘶㠷㤸㠹]{1,}$',  # 十六进制乱码字符
            r'^[\x00-\x1f\x7f-\x9f]{1,}$',    # 控制字符作为参数名
            r'^[^\x20-\x7e\u4e00-\u9fff]{2,}$',  # 非ASCII可打印字符和中文的组合
            
            # 🔍 ToC变体检测 - 防止产品型号变体被误识别
            r'^ToC\d{8,}$',         # ToC后跟过长数字的异常变体
            r'^ToC[^\d\w]*\d+$',    # ToC后跟特殊字符的变体
            r'^ToC.*[^\d\w\-].*$',  # ToC中包含异常字符的变体
        ]
        
        # OCR智能修正映射表
        self.ocr_correction_map = {
            # 通信接口修正
            'WIRE1 3RS232': 'RS232通信接口',
            '3RS232': 'RS232',
            'WIRE1': '串口1',
            # 常见OCR错误
            'O': '0',  # 字母O替换为数字0
            'l': '1',  # 小写l替换为数字1
            'S': '5',  # 在数字上下文中
            # 产品型号保持
            'ToC50900608': 'ToC50900608',  # 产品型号保持原样
            'ToC509006048': 'ToC509006048',  # 变体型号
        }
        
        # 有效技术参数模式 - 增强版
        self.valid_tech_patterns = [
            r'\d+[VvAaWwHh℃℉%]',    # 包含技术单位
            r'\d+\s*[-~±]\s*\d+',   # 数值范围
            r'\d+\s*[:/]\s*\d+',    # 比值格式
            r'(?:电|压|流|功|率|频|温|度|精|量)',  # 中文技术关键词
            r'(?:volt|amp|watt|freq|temp|test|spec)',  # 英文技术词
            r'RS232|RS485|以太网|USB',  # 通信接口
            r'IP\d{2}',            # 防护等级
            r'ToC\d+',             # 产品型号模式
            r'\d+\.\d+\s*[VvAaWwHh℃℉%]',  # 小数+单位
            r'\d+[km]?[VvAaWwHh℃℉%]',     # 带前缀的单位
            r'(?:通信|接口|协议|端口|串口)',    # 通信相关中文
            r'(?:工作|环境|存储|操作).*?(?:温度|湿度|条件)',  # 环境条件
            r'(?:外形|安装|显示|操作).*?(?:尺寸|方式|屏|界面)',  # 物理特性
        ]
    
    def validate_extracted_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证和清洁提取的数据
        
        Args:
            data: AI分析提取的原始数据
            
        Returns:
            Dict: 包含验证结果和清洁后的数据
        """
        validation_report = {
            'original_specs_count': 0,
            'noise_removed_count': 0,
            'invalid_removed_count': 0,
            'final_specs_count': 0,
            'quality_issues': [],
            'confidence_adjustments': {}
        }
        
        if not isinstance(data, dict):
            return {
                'cleaned_data': data,
                'validation_report': validation_report,
                'data_quality_score': 0.0
            }
        
        cleaned_data = data.copy()
        
        # 验证和清洁specifications字段
        if 'specifications' in cleaned_data:
            cleaned_specs, spec_validation = self._clean_specifications(cleaned_data['specifications'])
            cleaned_data['specifications'] = cleaned_specs
            validation_report.update(spec_validation)
        
        # 验证basic_info字段
        if 'basic_info' in cleaned_data:
            basic_validation = self._validate_basic_info(cleaned_data['basic_info'])
            validation_report['quality_issues'].extend(basic_validation['issues'])
        
        # 调整置信度评分
        if 'confidence' in cleaned_data:
            adjusted_confidence = self._adjust_confidence_scores(
                cleaned_data['confidence'], 
                validation_report
            )
            cleaned_data['confidence'] = adjusted_confidence
            validation_report['confidence_adjustments'] = adjusted_confidence
        
        # 计算数据质量评分
        quality_score = self._calculate_quality_score(validation_report)
        
        # 记录质量问题
        if validation_report['quality_issues']:
            logger.warning(f"数据质量问题: {len(validation_report['quality_issues'])}个, "
                         f"质量评分: {quality_score:.2f}")
        
        return {
            'cleaned_data': cleaned_data,
            'validation_report': validation_report,
            'data_quality_score': quality_score
        }
    
    def _clean_specifications(self, specifications: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """清洁规格参数数据"""
        import re
        
        cleaned_specs = {}
        validation_report = {
            'original_specs_count': len(specifications),
            'noise_removed_count': 0,
            'invalid_removed_count': 0,
            'final_specs_count': 0,
            'removed_specs': []
        }
        
        for spec_name, spec_data in specifications.items():
            if not spec_name or not spec_name.strip():
                continue
                
            spec_name = spec_name.strip()
            
            # 🔧 先尝试智能修正
            corrected_name, corrected_data, was_corrected = self._apply_intelligent_correction(spec_name, spec_data)
            if was_corrected:
                logger.info(f"🔧 智能修正: '{spec_name}' → '{corrected_name}'")
                spec_name = corrected_name
                spec_data = corrected_data
            
            # 🛡️ 优先检查：二进制垃圾数据检测
            if self._is_binary_garbage(spec_name):
                validation_report['noise_removed_count'] += 1
                validation_report['removed_specs'].append({
                    'name': spec_name,
                    'reason': 'binary_garbage_from_doc_parsing',
                    'detection': 'advanced_binary_detection'
                })
                continue
            
            # 检查是否为格式噪声
            is_noise = False
            for pattern in self.noise_patterns:
                if re.search(pattern, spec_name, re.IGNORECASE):
                    validation_report['noise_removed_count'] += 1
                    validation_report['removed_specs'].append({
                        'name': spec_name,
                        'reason': 'format_noise',
                        'pattern': pattern
                    })
                    is_noise = True
                    break
            
            if is_noise:
                continue
            
            # 获取规格值用于后续判断
            spec_value = ""
            if isinstance(spec_data, dict):
                spec_value = str(spec_data.get('value', ''))
            else:
                spec_value = str(spec_data)
            
            # 🚫 检查是否为基本产品信息（不应该作为技术规格）
            basic_info_patterns = [
                r'^产品名称$', r'^产品代码$', r'^制造商$', r'^厂商$',
                r'^产品类别$', r'^产品分类$', r'^类别$', r'^分类$',
                r'^概述$', r'^简介$', r'^描述$', r'^说明$',
                r'^附录[A-Z]?[:：]?.*', r'^表[0-9]+[:：]?.*', r'^图[0-9]+[:：]?.*',
                r'.*技术规格.*表.*', r'.*参数表.*', r'.*规格表.*',
                r'^第[0-9一二三四五六七八九十]+章', r'^[0-9]+\.[0-9]+\s',
                r'说明书$', r'手册$', r'指南$'
            ]
            
            # 🔍 特殊处理：产品型号如果没有具体值，则过滤
            if re.search(r'^产品型号$', spec_name, re.IGNORECASE):
                if not (spec_value and spec_value.strip() and len(spec_value.strip()) > 2):
                    basic_info_patterns.append(r'^产品型号$')
            
            is_basic_info = False
            for pattern in basic_info_patterns:
                if re.search(pattern, spec_name, re.IGNORECASE):
                    validation_report['invalid_removed_count'] += 1
                    validation_report['removed_specs'].append({
                        'name': spec_name,
                        'reason': 'basic_info_not_spec',
                        'pattern': pattern
                    })
                    is_basic_info = True
                    break
            
            if is_basic_info:
                continue
            
            # 检查是否为有效技术参数
            is_valid_tech = False
            
            combined_text = f"{spec_name} {spec_value}"
            
            # 检查技术有效性
            for pattern in self.valid_tech_patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    is_valid_tech = True
                    break
            
            # 如果包含明显的技术信息，则认为有效
            if (len(spec_name) > 1 and 
                (re.search(r'\d', combined_text) or  # 包含数字
                 re.search(r'[电压流功率频温度精量]', combined_text) or  # 包含技术关键词
                 re.search(r'[VvAaWwHh℃℉%]', combined_text))):  # 包含技术单位
                is_valid_tech = True
            
            # 🔍 额外检查：排除过于通用或描述性的内容
            generic_patterns = [
                r'^主要功能$', r'^特点$', r'^特色$', r'^优势$', 
                r'^应用$', r'^用途$', r'^适用$', r'^范围$',
                r'^注意事项$', r'^安全$', r'^警告$', r'^须知$'
            ]
            
            is_generic = False
            for pattern in generic_patterns:
                if re.search(pattern, spec_name, re.IGNORECASE):
                    is_generic = True
                    break
            
            if is_generic:
                validation_report['invalid_removed_count'] += 1
                validation_report['removed_specs'].append({
                    'name': spec_name,
                    'reason': 'generic_description',
                    'value': spec_value
                })
                continue
            
            # 🔍 检查产品型号变体错误：如果规格名称本身就是型号，但与基本信息中的型号不符，则过滤
            if re.search(r'^ToC\d+$', spec_name, re.IGNORECASE):
                # 这可能是错误的型号变体，应该过滤
                validation_report['invalid_removed_count'] += 1
                validation_report['removed_specs'].append({
                    'name': spec_name,
                    'reason': 'product_code_variant',
                    'value': spec_value
                })
                continue
            
            if is_valid_tech:
                cleaned_specs[spec_name] = spec_data
            else:
                validation_report['invalid_removed_count'] += 1
                validation_report['removed_specs'].append({
                    'name': spec_name,
                    'reason': 'not_technical',
                    'value': spec_value
                })
        
        validation_report['final_specs_count'] = len(cleaned_specs)
        
        return cleaned_specs, validation_report
    
    def _validate_basic_info(self, basic_info: Dict[str, Any]) -> Dict[str, Any]:
        """验证基本信息字段"""
        issues = []
        
        if not basic_info.get('name'):
            issues.append("产品名称缺失")
        elif len(basic_info['name'].strip()) < 3:
            issues.append("产品名称过短，可能不准确")
            
        if not basic_info.get('code'):
            issues.append("产品型号缺失")
            
        if not basic_info.get('category'):
            issues.append("产品分类缺失")
        
        return {'issues': issues}
    
    def _adjust_confidence_scores(self, confidence: Dict[str, Any], validation_report: Dict[str, Any]) -> Dict[str, Any]:
        """根据验证结果调整置信度评分"""
        adjusted_confidence = confidence.copy()
        
        # 如果发现大量格式噪声，降低specifications置信度
        noise_ratio = validation_report.get('noise_removed_count', 0) / max(validation_report.get('original_specs_count', 1), 1)
        if noise_ratio > 0.3:  # 如果超过30%是噪声
            if 'specifications' in adjusted_confidence:
                original_spec_confidence = adjusted_confidence['specifications']
                adjusted_confidence['specifications'] = original_spec_confidence * (1 - noise_ratio * 0.5)
                logger.warning(f"由于发现{noise_ratio:.1%}的格式噪声，规格参数置信度从{original_spec_confidence:.3f}调整为{adjusted_confidence['specifications']:.3f}")
        
        # 重新计算overall置信度
        if 'basic_info' in adjusted_confidence and 'specifications' in adjusted_confidence:
            adjusted_confidence['overall'] = (
                adjusted_confidence['basic_info'] * 0.3 + 
                adjusted_confidence['specifications'] * 0.7
            )
        
        return adjusted_confidence
    
    def _calculate_quality_score(self, validation_report: Dict[str, Any]) -> float:
        """计算数据质量评分（0-1）"""
        score = 1.0
        
        # 根据噪声比例扣分
        original_count = validation_report.get('original_specs_count', 1)
        noise_count = validation_report.get('noise_removed_count', 0)
        invalid_count = validation_report.get('invalid_removed_count', 0)
        
        noise_ratio = noise_count / max(original_count, 1)
        invalid_ratio = invalid_count / max(original_count, 1)
        
        # 噪声数据扣分
        score -= noise_ratio * 0.5  # 最多扣0.5分
        
        # 无效数据扣分
        score -= invalid_ratio * 0.3  # 最多扣0.3分
        
        # 质量问题扣分
        issues_count = len(validation_report.get('quality_issues', []))
        score -= issues_count * 0.05  # 每个问题扣0.05分
        
        return max(0.0, min(1.0, score))
    
    def _apply_intelligent_correction(self, spec_name: str, spec_data: Any) -> Tuple[str, Any, bool]:
        """
        智能修正OCR错误和格式问题
        
        Args:
            spec_name: 规格参数名称
            spec_data: 规格参数数据
            
        Returns:
            Tuple[str, Any, bool]: (修正后名称, 修正后数据, 是否进行了修正)
        """
        import re
        
        corrected_name = spec_name
        corrected_data = spec_data
        was_corrected = False
        
        # 直接映射修正
        if spec_name in self.ocr_correction_map:
            corrected_name = self.ocr_correction_map[spec_name]
            was_corrected = True
            
        # 智能模式匹配修正
        else:
            # 修正通信接口相关
            if re.match(r'WIRE\d+.*?RS\d+', spec_name):
                corrected_name = re.sub(r'WIRE\d+\s*(\d*)RS(\d+)', r'RS\2通信接口', spec_name)
                was_corrected = True
            elif re.match(r'\d+RS\d+', spec_name):
                corrected_name = re.sub(r'\d*RS(\d+)', r'RS\1', spec_name)
                was_corrected = True
                
            # 修正数值中的OCR错误
            elif re.search(r'\d+[OlS]', spec_name):
                corrected_name = re.sub(r'O', '0', spec_name)
                corrected_name = re.sub(r'l(?=\d|$)', '1', corrected_name)  # 只在数字上下文中替换
                corrected_name = re.sub(r'S(?=\d|$)', '5', corrected_name)
                was_corrected = True
                
            # 修正产品型号格式
            elif re.match(r'ToC\d+', spec_name):
                # 产品型号保持原样，但确保格式正确
                if not corrected_data or (isinstance(corrected_data, dict) and not corrected_data.get('value')):
                    corrected_data = {
                        'value': spec_name,
                        'unit': '',
                        'description': f'产品型号{spec_name}'
                    }
                    was_corrected = True
        
        # 数据结构修正
        if isinstance(corrected_data, str) and corrected_data and was_corrected:
            corrected_data = {
                'value': corrected_data,
                'unit': '',
                'description': f'智能修正后的{corrected_name}'
            }
            
        return corrected_name, corrected_data, was_corrected
    
    def _is_binary_garbage(self, text: str) -> bool:
        """
        高级二进制垃圾数据检测 - 专门检测.doc文件解析产生的乱码字符串
        
        Args:
            text: 待检测的文本
            
        Returns:
            bool: 是否为二进制垃圾数据
        """
        import re
        
        if not text or len(text.strip()) == 0:
            return True
        
        text = text.strip()
        
        # 🔍 检测1：Unicode编码范围异常检测
        # 检查私用区字符（Private Use Area）- 常见于编码错误
        private_use_count = sum(1 for c in text if 0xE000 <= ord(c) <= 0xF8FF)
        if private_use_count > 0:
            logger.debug(f"检测到私用区字符: {text} (count: {private_use_count})")
            return True
            
        # 检查控制字符作为参数名（除了正常的空白字符）
        control_chars = sum(1 for c in text if ord(c) < 32 and c not in '\t\n\r ')
        if control_chars > 0:
            logger.debug(f"检测到控制字符: {text} (count: {control_chars})")
            return True
            
        # 检查高位扩展ASCII字符（128-255）- Latin-1扩展区域的乱码
        high_ascii_count = sum(1 for c in text if 128 <= ord(c) <= 255)
        if high_ascii_count >= len(text) * 0.5:  # 超过50%是高位ASCII
            logger.debug(f"检测到高频高位ASCII字符: {text} (ratio: {high_ascii_count}/{len(text)})")
            return True
        
        # 🔍 检测2：常见.doc解析乱码字符模式
        doc_garbage_patterns = [
            # 常见的.doc解析产生的乱码字符
            r'[潗摲楍牣獯景煅慵楴湯畱瑡潩卍潗摲潄吀瑩敬牁慩袈霡蠈袢]',
            # 十六进制显示形式的乱码
            r'[㸳㠴㔷㤸㜹㈰㐱㠲㌳㘴㔵㘶㠷㤸㠹]',
            # Word文档结构字符泄漏
            r'[屜屝屬屭屨屪屢屣層履屦屧屨屩屲]',
            # OLE对象标识符字符
            r'[▉▊▋▌▍▎▏█▄▀■□▲△▼▽◆◇○●◎☆★]',
        ]
        
        for pattern in doc_garbage_patterns:
            if re.search(pattern, text):
                logger.debug(f"检测到.doc解析乱码模式: {text} (pattern: {pattern})")
                return True
        
        # 🔍 检测3：字符组合异常检测
        # 检测连续的异常高频字符（通常出现在编码错误中）
        char_freq = {}
        for char in text:
            char_freq[char] = char_freq.get(char, 0) + 1
        
        # 如果任何字符出现频率超过50%且字符串长度>2，可能是重复乱码
        for char, count in char_freq.items():
            if count > len(text) * 0.5 and len(text) > 2:
                logger.debug(f"检测到高频重复字符: {text} (char: {char}, freq: {count}/{len(text)})")
                return True
        
        # 🔍 检测4：可读性检查
        # 检查是否包含任何可读的中文、英文或数字内容
        readable_chars = 0
        
        # 中文字符
        readable_chars += len(re.findall(r'[\u4e00-\u9fff]', text))
        # 英文字母
        readable_chars += len(re.findall(r'[a-zA-Z]', text))
        # 数字
        readable_chars += len(re.findall(r'[0-9]', text))
        # 常见符号
        readable_chars += len(re.findall(r'[.,;:!?()\/\-+=%]', text))
        
        readable_ratio = readable_chars / len(text)
        
        # 🔧 特殊处理：对于短的中文技术词汇，降低可读性要求
        if len(text) <= 3 and len(re.findall(r'[\u4e00-\u9fff]', text)) >= 1:
            # 短的中文词汇（如"重量"、"电压"等）应该被保留
            return False
        
        if readable_ratio < 0.3:  # 可读字符少于30%
            logger.debug(f"检测到低可读性文本: {text} (readable: {readable_chars}/{len(text)})")
            return True
        
        # 🔍 检测5：特定长度和模式的异常检测
        # 检测明显的二进制数据表示
        if len(text) <= 3:
            # 短字符串更严格检查
            # 如果全是非标准字符，可能是乱码
            non_standard = sum(1 for c in text if ord(c) > 127 or ord(c) < 32)
            if non_standard > len(text) * 0.5:
                logger.debug(f"检测到短字符串乱码: {text}")
                return True
        
        # 🔍 检测6：编码错误特征检测
        # 尝试检测常见的编码错误模式
        encoding_error_indicators = [
            # 问号或替代字符（通常是编码失败的标志）
            r'[�\?]{2,}',
            # 明显的字节序标记泄漏
            r'[\ufeff\ufffe]',
            # null字符或其他控制字符
            r'[\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0e-\x1f]',
        ]
        
        for pattern in encoding_error_indicators:
            if re.search(pattern, text):
                logger.debug(f"检测到编码错误标识: {text} (pattern: {pattern})")
                return True
        
        # 🔍 检测7：特殊情况 - 用户反馈的具体问题
        # 检测用户截图中提到的具体问题字符串
        known_garbage_strings = [
            'ToC509006008', 'ToC509006048',  # 异常长的ToC变体
            '3.2 D', '5.2.14 I-t',          # 数字+字母的无意义组合
            'D', 'I', 'RS',                 # 单独的字母
            '/λspec_table中提取',            # 格式标记泄漏
        ]
        
        for garbage_str in known_garbage_strings:
            if text.strip() == garbage_str:
                logger.debug(f"检测到已知垃圾字符串: {text}")
                return True
        
        return False

class AnalysisMonitor:
    """分析过程监控器 - 提供详细的调试信息和性能统计"""
    
    def __init__(self):
        self.start_time = None
        self.stages = {}
        self.metrics = {
            'document_info': {},
            'text_extraction': {},
            'table_parsing': {},
            'ai_analysis': {},
            'quality_assessment': {},
            'overall': {}
        }
    
    def start_analysis(self, filename: str, file_size: int):
        """开始分析监控"""
        self.start_time = time.time()
        self.metrics['document_info'] = {
            'filename': filename,
            'file_size': file_size,
            'start_time': datetime.now().isoformat()
        }
        logger.info(f"📊 开始分析监控: {filename} ({file_size} bytes)")
    
    def stage_start(self, stage_name: str):
        """阶段开始"""
        self.stages[stage_name] = {'start': time.time()}
        logger.info(f"🔄 阶段开始: {stage_name}")
    
    def stage_end(self, stage_name: str, **kwargs):
        """阶段结束"""
        if stage_name in self.stages:
            duration = time.time() - self.stages[stage_name]['start']
            self.stages[stage_name].update({
                'duration': duration,
                'end': time.time(),
                **kwargs
            })
            logger.info(f"✅ 阶段完成: {stage_name} ({duration:.2f}s)")
    
    def record_metrics(self, category: str, data: Dict[str, Any]):
        """记录详细指标"""
        self.metrics[category].update(data)
        logger.debug(f"📊 指标记录 [{category}]: {data}")
    
    def get_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        total_duration = time.time() - self.start_time if self.start_time else 0
        
        return {
            'total_duration': round(total_duration, 2),
            'stages': {name: stage.get('duration', 0) for name, stage in self.stages.items()},
            'metrics': self.metrics,
            'completion_time': datetime.now().isoformat()
        }

class AIAnalyzer:
    """AI产品分析器 - 集成监控和调试功能"""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.ai_client = ZhipuAIClient()
        self.learning_engine = LearningEngine()
        self.table_parser = TableParser()
        self.confidence_scorer = ConfidenceScorer()
        self.quality_validator = DataQualityValidator()  # 数据质量验证器
        self.monitor = None  # 动态创建监控器
    
    def analyze_product_document(self, file: FileStorage, user_id: int = None) -> Dict[str, Any]:
        """
        分析产品文档，提取产品信息 - 集成详细监控和调试
        
        Args:
            file: 上传的文件对象
            user_id: 用户ID，用于个性化分析
            
        Returns:
            Dict: 完整的分析结果，包含调试信息
        """
        # 🔧 初始化监控器
        self.monitor = AnalysisMonitor()
        file_size = len(file.read())
        file.seek(0)  # 重置文件指针
        self.monitor.start_analysis(file.filename, file_size)
        
        try:
            # 🔄 阶段1: 文档处理和文本提取
            self.monitor.stage_start("document_processing")
            logger.info(f"📄 开始处理文档: {file.filename} ({file_size} bytes)")
            
            text_content, doc_info = self.document_processor.process_document(file)
            
            # 记录文档处理指标
            self.monitor.record_metrics('text_extraction', {
                'text_length': len(text_content),
                'doc_format': doc_info.get('format', 'unknown'),
                'pages': doc_info.get('pages', 0),
                'encoding': doc_info.get('encoding', 'unknown')
            })
            
            if not text_content.strip():
                raise ValueError("Document contains no readable text content")
                
            self.monitor.stage_end("document_processing", 
                                 text_chars=len(text_content), 
                                 format=doc_info.get('format', 'unknown'))
            
            # 🔍 增强乱码检测 - 使用文档处理器的增强算法
            if self.document_processor._enhanced_corruption_detection(text_content, doc_info.get('type', '')):
                error_msg = self._generate_corruption_error_message(file.filename, doc_info)
                raise ValueError(error_msg)
            
            # 🔄 阶段2: 个性化学习引擎
            personalized_hints = {}
            if user_id:
                self.monitor.stage_start("personalization")
                personalized_hints = self.learning_engine.get_personalized_hints(
                    user_id=user_id,
                    document_type=doc_info.get('type', 'unknown'),
                    extracted_data={}
                )
                self.monitor.stage_end("personalization", hints_count=len(personalized_hints))
            
            # 🔄 阶段3: AI文档分析（分层分析）
            self.monitor.stage_start("ai_analysis")
            logger.info(f"🤖 开始AI分析，文本长度: {len(text_content)} 字符")
            
            ai_result = self.ai_client.analyze_product_document(
                document_content=text_content,
                document_name=file.filename or "unknown"
            )
            
            # 记录AI分析指标
            ai_specs_count = len(ai_result.get('specifications', {}))
            ai_confidence = ai_result.get('confidence', {}).get('overall', 0)
            self.monitor.record_metrics('ai_analysis', {
                'specifications_extracted': ai_specs_count,
                'ai_confidence': ai_confidence,
                'has_basic_info': bool(ai_result.get('basic_info', {}).get('name', ''))
            })
            self.monitor.stage_end("ai_analysis", 
                                 specs_count=ai_specs_count, 
                                 confidence=ai_confidence)
            
            # 🔄 阶段4: 表格解析增强
            self.monitor.stage_start("table_parsing")
            logger.info(f"📊 开始表格解析增强")
            
            enhanced_result = self.table_parser.enhance_extraction_with_tables(ai_result, text_content)
            
            # 记录表格解析指标
            enhanced_specs_count = len(enhanced_result.get('specifications', {}))
            table_info = enhanced_result.get('table_parsing', {})
            self.monitor.record_metrics('table_parsing', {
                'tables_found': table_info.get('tables_found', 0),
                'parsing_confidence': table_info.get('parsing_confidence', 0),
                'specs_after_enhancement': enhanced_specs_count,
                'enhancement_gain': enhanced_specs_count - ai_specs_count
            })
            self.monitor.stage_end("table_parsing", 
                                 tables_found=table_info.get('tables_found', 0),
                                 final_specs=enhanced_specs_count)
            
            # 🔄 阶段5: 数据质量验证和清洁
            self.monitor.stage_start("data_quality_validation")
            logger.info("🔍 开始数据质量验证和清洁...")
            
            quality_validation = self.quality_validator.validate_extracted_data(enhanced_result)
            enhanced_result = quality_validation['cleaned_data']
            validation_report = quality_validation['validation_report']
            data_quality_score = quality_validation['data_quality_score']
            
            # 记录质量验证结果
            logger.info(f"📊 数据质量验证完成 - 质量评分: {data_quality_score:.2f}")
            if validation_report['noise_removed_count'] > 0:
                logger.info(f"🧹 清除格式噪声: {validation_report['noise_removed_count']}项")
            if validation_report['invalid_removed_count'] > 0:
                logger.info(f"🗑️ 清除无效参数: {validation_report['invalid_removed_count']}项")
            logger.info(f"✅ 最终有效规格参数: {validation_report['final_specs_count']}项")
            
            self.monitor.stage_end("data_quality_validation", 
                                 quality_score=data_quality_score,
                                 noise_removed=validation_report['noise_removed_count'],
                                 invalid_removed=validation_report['invalid_removed_count'])
            
            # 🔄 阶段6: 质量评估和置信度计算
            self.monitor.stage_start("quality_assessment")
            confidence_scores = self.confidence_scorer.calculate_comprehensive_confidence(
                extracted_data=enhanced_result,
                document_info=doc_info,
                historical_context=personalized_hints.get('pattern_context') if user_id else None
            )
            
            # 如果数据质量验证器调整了置信度，使用调整后的值
            if 'confidence_adjustments' in validation_report and validation_report['confidence_adjustments']:
                confidence_scores = validation_report['confidence_adjustments']
            
            self.monitor.stage_end("quality_assessment", confidence=confidence_scores.get('overall', 0))
            
            # 🔄 阶段7: 数据后处理和修复
            self.monitor.stage_start("data_postprocessing")
            
            # 智能修复产品名称（如果规格提取成功但名称为空）
            current_name = enhanced_result.get('basic_info', {}).get('name', '')
            logger.info(f"🔍 检查产品名称修复 - 当前名称: '{current_name}', 有规格参数: {bool(enhanced_result.get('specifications'))}")
            
            if not current_name.strip() and enhanced_result.get('specifications'):
                logger.info(f"🔧 开始修复缺失的产品名称，文件名: {file.filename}")
                enhanced_result = self._fix_missing_product_name(enhanced_result, file.filename or "unknown")
                new_name = enhanced_result.get('basic_info', {}).get('name', '')
                logger.info(f"✅ 产品名称修复完成: '{new_name}'")
            
            # 最终数据清理 - 确保所有规格参数都是有效的
            final_specs_count = 0
            if enhanced_result.get('specifications'):
                cleaned_specs = self.table_parser._clean_specification_data(enhanced_result['specifications'])
                enhanced_result['specifications'] = cleaned_specs
                final_specs_count = len(cleaned_specs)
                logger.info(f"最终规格参数清理完成，保留 {final_specs_count} 项有效参数")
            
            self.monitor.stage_end("data_postprocessing", final_specs_count=final_specs_count)
            
            # 🔄 完成分析，获取监控总结
            monitor_summary = self.monitor.get_summary()
            
            # 记录最终质量指标
            final_basic_info = enhanced_result.get('basic_info', {})
            final_specs = enhanced_result.get('specifications', {})
            
            self.monitor.record_metrics('overall', {
                'final_specs_count': len(final_specs),
                'has_product_name': bool(final_basic_info.get('name', '').strip()),
                'has_product_code': bool(final_basic_info.get('code', '').strip()),
                'has_category': bool(final_basic_info.get('category', '').strip()),
                'overall_confidence': confidence_scores.get('overall', 0)
            })
            
            # 打印详细的分析总结
            logger.info(f"📊 === 分析总结 ===")
            logger.info(f"🕐 总耗时: {monitor_summary['total_duration']}秒")
            for stage, duration in monitor_summary['stages'].items():
                logger.info(f"   {stage}: {duration:.2f}s")
            logger.info(f"📄 文档信息: {file.filename} ({file_size} bytes)")
            logger.info(f"🤖 AI提取: {len(ai_result.get('specifications', {}))} 项规格")
            logger.info(f"📊 表格增强: +{enhanced_specs_count - ai_specs_count} 项规格")
            logger.info(f"🎯 最终结果: {len(final_specs)} 项规格，置信度 {confidence_scores.get('overall', 0):.3f}")
            logger.info(f"================")
            
            # 构建完整结果（包含调试信息和质量验证）
            result = {
                'success': True,
                'document_info': {
                    **doc_info,
                    'analysis_duration': monitor_summary['total_duration']
                },
                'extracted_data': enhanced_result,
                'confidence_scores': confidence_scores,
                'personalized_hints': personalized_hints.get('personalized_hints', []) if user_id else [],
                'predicted_modifications': personalized_hints.get('predicted_modifications', {}) if user_id else {},
                'text_preview': text_content[:500] + "..." if len(text_content) > 500 else text_content,
                'analysis_timestamp': int(time.time()),
                
                # 🆕 数据质量相关信息
                'data_quality_score': data_quality_score,
                'validation_report': validation_report,
                
                # 🆕 详细的调试和监控信息
                'debug_info': {
                    'monitor_summary': monitor_summary,
                    'stage_breakdown': monitor_summary['stages'],
                    'performance_metrics': monitor_summary['metrics'],
                    'processing_pipeline': [
                        f"文档处理: {doc_info.get('format', 'unknown')} -> {len(text_content)} 字符",
                        f"AI分析: {ai_specs_count} 项规格 (置信度 {ai_confidence:.3f})",
                        f"表格增强: +{enhanced_specs_count - ai_specs_count} 项规格",
                        f"质量验证: 移除 {validation_report.get('noise_removed_count', 0)} 噪声, {validation_report.get('invalid_removed_count', 0)} 无效数据",
                        f"质量评估: 置信度 {confidence_scores.get('overall', 0):.3f}, 质量评分 {data_quality_score:.3f}",
                        f"数据后处理: 最终 {final_specs_count} 项规格"
                    ]
                }
            }
            
            logger.info(f"✅ 文档分析成功完成 - 耗时: {monitor_summary['total_duration']}s, 置信度: {confidence_scores.get('overall', 'N/A')}")
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"❌ AI分析失败 - 文件: {file.filename}, 错误: {error_msg}")
            
            # 获取失败时的监控信息
            if self.monitor:
                error_monitor_summary = self.monitor.get_summary()
                logger.error(f"💔 失败阶段分析: {error_monitor_summary}")
            
            # 🔧 增强错误分类和处理
            error_type = self._classify_error_type(e, error_msg)
            detailed_error = self._generate_detailed_error_message(e, error_type, file.filename, doc_info if 'doc_info' in locals() else {})
            
            return {
                'success': False,
                'error': detailed_error['message'],
                'error_type': error_type,
                'error_details': detailed_error['details'],
                'suggestions': detailed_error['suggestions'],
                'document_info': {
                    'filename': file.filename,
                    'analysis_duration': error_monitor_summary['total_duration'] if self.monitor else 0,
                    'file_type': getattr(file, 'mimetype', 'unknown')
                },
                # 🆕 错误调试信息
                'debug_info': {
                    'error_monitor_summary': error_monitor_summary if self.monitor else {},
                    'failed_stage': max(error_monitor_summary['stages'].keys()) if self.monitor and error_monitor_summary['stages'] else 'unknown',
                    'error_timestamp': datetime.now().isoformat()
                }
            }
    
    def _fix_missing_product_name(self, extracted_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """智能修复缺失的产品名称"""
        try:
            basic_info = extracted_data.get('basic_info', {})
            specifications = extracted_data.get('specifications', {})
            
            # 从文件名推断产品名称
            if 'A703' in filename and '继电保护测试仪' in filename:
                # A703三相继电保护测试仪特殊处理
                basic_info['name'] = 'A703三相继电保护测试仪'
                basic_info['code'] = 'A703'  # 重要：设置产品代码
                basic_info['category'] = '测量仪表'
                basic_info['description'] = 'A703三相继电保护测试仪，用于电力系统继电保护装置的全面测试和校验'
                
            elif '六相微机继电保护测试仪' in filename or '继电保护测试仪' in filename:
                basic_info['name'] = '六相微机继电保护测试仪'
                basic_info['code'] = 'REL_PROT_6P'  # 添加产品代码
                basic_info['category'] = '继电保护测试设备'
                basic_info['description'] = '六相微机继电保护测试仪，用于电力系统继电保护装置的全面测试和校验'
                
            elif '变压器' in filename:
                basic_info['name'] = '电力变压器'
                basic_info['code'] = 'TRANSFORMER'
                basic_info['category'] = '变压器设备'
                
            elif '开关' in filename:
                basic_info['name'] = '电力开关设备'
                basic_info['code'] = 'SWITCH_GEAR'
                basic_info['category'] = '开关设备'
                
            else:
                # 从规格参数推断产品类型
                if any('相' in str(key) for key in specifications.keys()):
                    if '6' in str(specifications) or '六' in str(specifications):
                        basic_info['name'] = '六相微机继电保护测试仪'
                        basic_info['code'] = 'REL_PROT_6P'
                        basic_info['category'] = '继电保护测试设备'
                        basic_info['description'] = '六相微机继电保护测试仪，用于电力系统继电保护装置的测试'
                    else:
                        basic_info['name'] = '三相继电保护测试仪'
                        basic_info['code'] = 'REL_PROT_3P'
                        basic_info['category'] = '测量仪表'
                        basic_info['description'] = '三相继电保护测试仪，用于电力系统继电保护装置的测试'
                        
                elif any('变压器' in str(key) for key in specifications.keys()):
                    basic_info['name'] = '电力变压器'
                    basic_info['code'] = 'TRANSFORMER'
                    basic_info['category'] = '变压器设备'
                    
                else:
                    # 通用电气设备
                    basic_info['name'] = '电力设备'
                    basic_info['code'] = 'POWER_DEVICE'
                    basic_info['category'] = '电力设备'
            
            # 🔧 确保产品代码存在 - 这是最关键的修复！
            if not basic_info.get('code') or not basic_info['code'].strip():
                if basic_info.get('name'):
                    name = basic_info['name']
                    # 从产品名称提取代码
                    if 'A703' in name:
                        basic_info['code'] = 'A703'
                    elif 'A703' in filename:
                        basic_info['code'] = 'A703'
                    elif '六相' in name:
                        basic_info['code'] = 'REL_PROT_6P'
                    elif '三相' in name and '继电' in name:
                        basic_info['code'] = 'REL_PROT_3P'
                    elif '变压器' in name:
                        basic_info['code'] = 'TRANSFORMER'
                    else:
                        # 生成通用代码
                        import hashlib
                        name_hash = hashlib.md5(name.encode('utf-8')).hexdigest()[:8].upper()
                        basic_info['code'] = f'AUTO_{name_hash}'
                logger.info(f"🔧 自动生成产品代码: {basic_info.get('code', 'N/A')}")
            
            # 更新置信度
            confidence = extracted_data.get('confidence', {})
            if basic_info.get('name'):
                confidence['basic_info'] = max(confidence.get('basic_info', 0), 0.8)
                confidence['overall'] = max(confidence.get('overall', 0), 
                                          (confidence.get('basic_info', 0.8) + confidence.get('specifications', 0.7)) / 2)
            
            extracted_data['basic_info'] = basic_info
            extracted_data['confidence'] = confidence
            
            logger.info(f"智能修复产品名称: {basic_info.get('name', 'N/A')}")
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"修复产品名称失败: {str(e)}")
            return extracted_data
    
    def _is_text_corrupted(self, text: str, file_extension: str = '') -> bool:
        """检测文本是否严重乱码，无法进行AI分析"""
        if not text or len(text.strip()) < 20:  # 🔧 进一步降低最小长度要求，OCR文本可能很短
            return True
        
        # 🖼️ 特殊处理图片文件的OCR文本
        is_image_ocr = file_extension.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']
        
        text_sample = text[:3000]  # 取前3000字符进行检测
        
        # 🔍 乱码特征检测
        import re
        
        # 1. 检测明显的编码错误字符 - 对图片OCR更宽松
        corruption_chars = sum(1 for c in text_sample if c in '揀釨娐醢藠俹牁慵楴湯畱瑡潩卍潗摲潄吀瑩敬楍牣獯景煅慵楴湯')
        corruption_threshold = 0.5 if is_image_ocr else 0.3  # 🖼️ 图片OCR允许更多错误字符
        if corruption_chars / len(text_sample) > corruption_threshold:
            return True
            
        # 2. 检测重复模式过多 - 对图片OCR更宽松
        repeated_patterns = re.findall(r'(.{2,4})\1{5,}', text_sample)
        repeat_threshold = 25 if is_image_ocr else 15  # 🖼️ 图片OCR允许更多重复模式
        if len(repeated_patterns) > repeat_threshold:
            return True
            
        # 3. 检测可读性 - 可读的中文或英文内容太少
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text_sample))
        english_words = len(re.findall(r'\b[a-zA-Z]{2,}\b', text_sample))  # 🔧 降低英文单词长度要求
        digits = len(re.findall(r'\d', text_sample))
        symbols = len(re.findall(r'[A-Za-z]\d+|\d+[A-Za-z]', text_sample))  # 🔧 添加字母数字组合检测
        
        # 计算可读内容比例 - 对图片OCR更宽松
        readable_content = chinese_chars + english_words * 2 + digits * 0.8 + symbols * 1.5  # 🖼️ 调整权重，重视数字和符号
        readable_ratio = readable_content / len(text_sample)
        
        # 🔧 针对不同文件类型的特殊检测
        # 检测是否有技术关键词或数字+单位的组合
        has_technical_content = bool(re.search(
            r'(电压|电流|功率|频率|测试|保护|继电|装置|设备|性能|精度|规格|参数|型号|'
            r'voltage|current|power|frequency|test|specification|model|type|parameter)',
            text_sample, re.IGNORECASE
        ))
        has_numeric_units = bool(re.search(r'\d+\s*[A-Za-z%°℃ΩΩμμ±]+', text_sample))
        has_product_codes = bool(re.search(r'[A-Z0-9-]{3,}', text_sample))  # 🔧 检测产品编码模式
        
        # 🖼️ 图片OCR的特殊检测 - 更宽松的判断
        if is_image_ocr:
            # 如果有任何技术内容、数字单位或产品编码，极大降低可读性要求
            if has_technical_content or has_numeric_units or has_product_codes:
                min_readable_ratio = 0.02  # 🖼️ 极低阈值，只要有一点技术内容就接受
            else:
                min_readable_ratio = 0.03  # 🖼️ 稍低阈值
        else:
            # 普通文档的检测
            if has_technical_content or has_numeric_units:
                min_readable_ratio = 0.05
            else:
                min_readable_ratio = 0.08
        
        if readable_ratio < min_readable_ratio:
            logger.debug(f"📄 文本可读性检测 - 文件类型: {'图片OCR' if is_image_ocr else '普通文档'}")
            logger.debug(f"❌ 可读性不足: {readable_ratio:.3f} < {min_readable_ratio} "
                        f"(中文:{chinese_chars}, 英文:{english_words}, 数字:{digits}, 符号:{symbols})")
            logger.debug(f"🔍 技术内容: {has_technical_content}, 数字单位: {has_numeric_units}, 产品编码: {has_product_codes}")
            return True
        
        logger.debug(f"✅ 文本质量检测通过 - 可读性: {readable_ratio:.3f} >= {min_readable_ratio}")
        return False
    
    def _generate_corruption_error_message(self, filename: str, doc_info: Dict[str, Any]) -> str:
        """生成乱码错误的详细信息"""
        file_type = doc_info.get('type', 'unknown')
        file_size = doc_info.get('size', 0)
        
        error_msg = f"文档分析失败：无法从文件 '{filename}' 中提取可读文本内容\n\n"
        
        # 🔍 具体诊断信息
        error_msg += "问题诊断：\n"
        error_msg += f"• 文件类型: {file_type.upper()}\n"
        error_msg += f"• 文件大小: {file_size:,} 字节\n"
        error_msg += "• 检测到文本编码问题或文件格式异常\n\n"
        
        # 🛠️ 解决建议
        error_msg += "建议的解决方案：\n"
        
        if file_type == 'doc':
            error_msg += "1. 将文件转换为 .docx 格式（推荐）\n"
            error_msg += "2. 使用Microsoft Word打开文件，另存为较新的格式\n"
            error_msg += "3. 确认文件未损坏且包含文本内容（而非纯图片）\n"
            error_msg += "4. 检查文件是否有密码保护或访问限制\n"
        elif file_type == 'pdf':
            error_msg += "1. 确认PDF包含可选择的文本（而非扫描图片）\n"
            error_msg += "2. 将PDF转换为Word文档格式\n"
            error_msg += "3. 使用OCR工具转换扫描版PDF\n"
        else:
            error_msg += "1. 检查文件格式和编码是否正确\n"
            error_msg += "2. 尝试使用其他软件重新保存文件\n"
            error_msg += "3. 确认文件包含可读的文本内容\n"
            
        error_msg += "\n如问题持续存在，请联系技术支持并提供文件样本。"
        
        return error_msg
    
    def _classify_error_type(self, exception: Exception, error_msg: str) -> str:
        """分类错误类型"""
        error_msg_lower = error_msg.lower()
        
        # 文档处理相关错误
        if "encoding" in error_msg_lower or "decode" in error_msg_lower or "无法从文件中提取可读文本" in error_msg:
            return "encoding_error"
        elif "file size" in error_msg_lower or "exceeds limit" in error_msg_lower:
            return "file_size_error"
        elif "unsupported file format" in error_msg_lower or "format" in error_msg_lower:
            return "format_error"
        elif "no text content" in error_msg_lower or "empty" in error_msg_lower:
            return "empty_content_error"
        elif "corrupted" in error_msg_lower or "乱码" in error_msg:
            return "corruption_error"
        
        # AI服务相关错误
        elif "api" in error_msg_lower and ("timeout" in error_msg_lower or "connection" in error_msg_lower):
            return "ai_service_timeout"
        elif "api" in error_msg_lower and ("rate limit" in error_msg_lower or "quota" in error_msg_lower):
            return "ai_service_quota"
        elif "api" in error_msg_lower and "key" in error_msg_lower:
            return "ai_service_auth"
        elif "ai" in error_msg_lower or "openai" in error_msg_lower or "zhipu" in error_msg_lower:
            return "ai_service_error"
        
        # 系统资源错误
        elif "memory" in error_msg_lower or "ram" in error_msg_lower:
            return "memory_error"
        elif "disk" in error_msg_lower or "space" in error_msg_lower:
            return "disk_error"
        elif "timeout" in error_msg_lower:
            return "timeout_error"
        
        # 权限错误
        elif "permission" in error_msg_lower or "access" in error_msg_lower:
            return "permission_error"
        
        # 未知错误
        else:
            return "unknown_error"
    
    def _generate_detailed_error_message(self, exception: Exception, error_type: str, 
                                       filename: str, doc_info: Dict[str, Any]) -> Dict[str, Any]:
        """生成详细的错误信息"""
        base_error = str(exception)
        
        error_messages = {
            "encoding_error": {
                "title": "文档编码问题",
                "message": f"无法正确读取文档 '{filename}' 的文本内容，可能存在编码问题",
                "details": [
                    "检测到文档编码格式不兼容或文件损坏",
                    "文档可能使用了不支持的字符编码",
                    "文件内容可能包含乱码或特殊字符"
                ],
                "suggestions": [
                    "尝试将文档转换为UTF-8编码格式",
                    "将.doc文件转换为.docx格式",
                    "使用Microsoft Word重新保存文档",
                    "确认文档完整且未损坏"
                ]
            },
            "format_error": {
                "title": "不支持的文件格式",
                "message": f"文件 '{filename}' 的格式不受支持",
                "details": [
                    f"检测到的文件类型: {doc_info.get('mimetype', '未知')}",
                    "系统只支持常见的办公文档格式",
                    "请确认文件扩展名与实际内容匹配"
                ],
                "suggestions": [
                    "支持格式: PDF, DOCX, DOC, XLSX, XLS, PPTX, TXT",
                    "将文件转换为支持的格式",
                    "检查文件是否完整下载",
                    "确认文件未被加密或密码保护"
                ]
            },
            "file_size_error": {
                "title": "文件大小超限",
                "message": f"文件 '{filename}' 大小超出系统限制",
                "details": [
                    f"当前文件大小: {doc_info.get('size', 0) / 1024 / 1024:.1f}MB",
                    "系统限制: 10MB",
                    "大文件可能影响处理性能和稳定性"
                ],
                "suggestions": [
                    "压缩文档或减少内容",
                    "分割大文档为多个小文档",
                    "移除文档中的大图片或媒体文件",
                    "使用PDF格式可以有效减小文件大小"
                ]
            },
            "empty_content_error": {
                "title": "文档内容为空",
                "message": f"文档 '{filename}' 中没有发现可读的文本内容",
                "details": [
                    "文档可能只包含图片或图表",
                    "文档可能是扫描版本",
                    "文档可能存在格式问题"
                ],
                "suggestions": [
                    "确认文档包含文本内容而非纯图片",
                    "对于扫描文档，请使用OCR软件转换",
                    "检查文档是否正确打开",
                    "尝试重新创建或导出文档"
                ]
            },
            "corruption_error": {
                "title": "文档内容损坏",
                "message": f"文档 '{filename}' 的内容出现损坏或严重乱码",
                "details": [
                    "检测到大量不可读字符",
                    "文档可能在传输过程中损坏",
                    "文档编码与实际内容不匹配"
                ],
                "suggestions": [
                    "重新下载或获取原始文档",
                    "使用原始软件重新保存文档",
                    "检查文档的完整性",
                    "联系文档提供方确认文档状态"
                ]
            },
            "ai_service_timeout": {
                "title": "AI服务超时",
                "message": "AI分析服务响应超时，请稍后重试",
                "details": [
                    "AI服务当前负载较高",
                    "网络连接可能不稳定",
                    "文档内容可能过于复杂"
                ],
                "suggestions": [
                    "稍后重新尝试分析",
                    "检查网络连接状态",
                    "尝试分析较简单的文档",
                    "联系系统管理员检查服务状态"
                ]
            },
            "ai_service_quota": {
                "title": "AI服务配额不足",
                "message": "AI服务使用量已达到限制",
                "details": [
                    "当前时段的API调用次数已用完",
                    "可能需要等待配额重置",
                    "或需要升级服务计划"
                ],
                "suggestions": [
                    "等待配额重置（通常为24小时）",
                    "联系管理员升级服务计划",
                    "暂时使用其他分析工具",
                    "减少同时进行的分析任务"
                ]
            },
            "ai_service_auth": {
                "title": "AI服务认证失败",
                "message": "AI服务认证失败，无法进行分析",
                "details": [
                    "API密钥可能已过期",
                    "服务配置可能不正确",
                    "认证信息可能被更改"
                ],
                "suggestions": [
                    "联系系统管理员检查API配置",
                    "确认服务订阅状态",
                    "检查网络防火墙设置",
                    "尝试重新启动服务"
                ]
            },
            "ai_service_error": {
                "title": "AI服务错误",
                "message": "AI分析服务出现错误，无法完成分析",
                "details": [
                    "AI服务内部出现问题",
                    "可能是临时性故障",
                    base_error if base_error else "未知AI服务错误"
                ],
                "suggestions": [
                    "稍后重新尝试",
                    "检查文档内容是否符合要求",
                    "尝试分析其他文档",
                    "联系技术支持"
                ]
            },
            "memory_error": {
                "title": "内存不足",
                "message": "系统内存不足，无法处理此文档",
                "details": [
                    "文档过大或过于复杂",
                    "系统当前负载较高",
                    "内存资源临时不足"
                ],
                "suggestions": [
                    "稍后重试",
                    "尝试分析较小的文档",
                    "分批处理大型文档",
                    "联系管理员优化系统资源"
                ]
            },
            "timeout_error": {
                "title": "处理超时",
                "message": "文档处理超时，分析未能完成",
                "details": [
                    "文档处理时间超过系统限制",
                    "文档可能过于复杂",
                    "系统当前处理负载较高"
                ],
                "suggestions": [
                    "稍后重试",
                    "简化文档内容",
                    "分段处理复杂文档",
                    "检查网络连接稳定性"
                ]
            },
            "unknown_error": {
                "title": "未知错误",
                "message": f"处理文档 '{filename}' 时发生未知错误",
                "details": [
                    "系统遇到了预期之外的问题",
                    base_error if base_error else "错误详情不明",
                    "可能是系统或文档的特殊情况"
                ],
                "suggestions": [
                    "重新尝试上传和分析",
                    "检查文档是否正常",
                    "尝试其他格式的文档",
                    "联系技术支持并提供文档样本"
                ]
            }
        }
        
        error_info = error_messages.get(error_type, error_messages["unknown_error"])
        
        return {
            "message": error_info["message"],
            "details": error_info["details"],
            "suggestions": error_info["suggestions"],
            "title": error_info["title"]
        }
    
    def get_supported_formats(self) -> Dict[str, Any]:
        """获取支持的文档格式信息"""
        doc_formats = self.document_processor.get_supported_formats()
        ai_available = self.ai_client.is_available()
        
        return {
            'document_formats': doc_formats,
            'ai_available': ai_available,
            'features': {
                'pdf_extraction': doc_formats['availability']['pdf'],
                'docx_extraction': doc_formats['availability']['docx'],
                'ocr_extraction': doc_formats['availability']['ocr'],
                'ai_analysis': ai_available
            }
        }
    
    def validate_analysis_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证分析结果的完整性和有效性
        
        Args:
            result: AI分析结果
            
        Returns:
            Dict: 验证结果和建议
        """
        validation = {
            'valid': True,
            'warnings': [],
            'suggestions': [],
            'completeness_score': 0
        }
        
        extracted_data = result.get('extracted_data', {})
        confidence_scores = result.get('confidence_scores', {})
        
        # 检查基础信息完整性
        basic_info = extracted_data.get('basic_info', {})
        required_fields = ['name', 'code', 'category']
        missing_fields = [field for field in required_fields if not basic_info.get(field)]
        
        if missing_fields:
            validation['warnings'].append(f"Missing basic info: {', '.join(missing_fields)}")
            validation['suggestions'].append("Please provide the missing basic product information")
        
        # 检查置信度
        overall_confidence = confidence_scores.get('overall', 0)
        if overall_confidence < 0.5:
            validation['warnings'].append("Low overall confidence in analysis results")
            validation['suggestions'].append("Consider reviewing and manually verifying the extracted information")
        
        # 计算完整性分数
        completeness_factors = [
            1 if basic_info.get('name') else 0,
            1 if basic_info.get('code') else 0,
            1 if basic_info.get('category') else 0,
            1 if basic_info.get('description') else 0,
            1 if extracted_data.get('specifications') else 0,
            1 if extracted_data.get('features') else 0
        ]
        
        validation['completeness_score'] = sum(completeness_factors) / len(completeness_factors)
        
        # 基于完整性给出建议
        if validation['completeness_score'] < 0.6:
            validation['suggestions'].append("Consider providing additional product documentation for better analysis")
        
        return validation
    
    def generate_analysis_summary(self, result: Dict[str, Any]) -> str:
        """生成分析结果摘要"""
        if not result.get('success'):
            return f"Analysis failed: {result.get('error', 'Unknown error')}"
        
        extracted_data = result.get('extracted_data', {})
        basic_info = extracted_data.get('basic_info', {})
        confidence = result.get('confidence_scores', {}).get('overall', 0)
        
        summary_parts = []
        
        # 产品名称
        if basic_info.get('name'):
            summary_parts.append(f"Product: {basic_info['name']}")
        
        # 型号
        if basic_info.get('code'):
            summary_parts.append(f"Model: {basic_info['code']}")
        
        # 分类
        if basic_info.get('category'):
            summary_parts.append(f"Category: {basic_info['category']}")
        
        # 规格数量
        specs_count = len(extracted_data.get('specifications', {}))
        if specs_count > 0:
            summary_parts.append(f"Specifications: {specs_count} items")
        
        # 特性数量
        features_count = len(extracted_data.get('features', []))
        if features_count > 0:
            summary_parts.append(f"Features: {features_count} items")
        
        # 置信度
        summary_parts.append(f"Confidence: {confidence:.1%}")
        
        return " | ".join(summary_parts) if summary_parts else "Analysis completed with limited information"
    
    def learn_from_user_modifications(self, analysis_record_id: int, 
                                    original_data: Dict[str, Any], 
                                    final_data: Dict[str, Any],
                                    user_modifications: Dict[str, Any]) -> Dict[str, Any]:
        """
        从用户修正中学习
        
        Args:
            analysis_record_id: 分析记录ID
            original_data: 原始AI提取数据
            final_data: 最终确认数据
            user_modifications: 用户修正记录
            
        Returns:
            Dict: 学习结果
        """
        try:
            learning_result = self.learning_engine.learn_from_modifications(
                analysis_record_id=analysis_record_id,
                original_data=original_data,
                final_data=final_data,
                user_modifications=user_modifications
            )
            
            logger.info(f"Learning completed for record {analysis_record_id}: "
                       f"{learning_result.get('patterns_identified', 0)} patterns")
            
            return learning_result
            
        except Exception as e:
            logger.error(f"Learning from modifications failed: {str(e)}")
            return {
                'patterns_identified': 0,
                'error': str(e)
            }
    
    def get_personalized_analysis_hints(self, user_id: int, document_type: str, 
                                      extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取个性化分析提示
        
        Args:
            user_id: 用户ID
            document_type: 文档类型
            extracted_data: 提取的数据
            
        Returns:
            Dict: 个性化提示
        """
        try:
            hints = self.learning_engine.get_personalized_hints(
                user_id=user_id,
                document_type=document_type,
                extracted_data=extracted_data
            )
            
            return hints
            
        except Exception as e:
            logger.error(f"Failed to get personalized hints: {str(e)}")
            return {
                'personalized_hints': [],
                'predicted_modifications': {},
                'error': str(e)
            }
    
    def optimize_analysis_for_document_type(self, document_type: str, 
                                          category: str = None) -> Dict[str, Any]:
        """
        为特定文档类型优化分析
        
        Args:
            document_type: 文档类型
            category: 产品分类
            
        Returns:
            Dict: 优化配置
        """
        try:
            optimization = self.learning_engine.optimize_extraction_prompt(
                document_type=document_type,
                category=category
            )
            
            return optimization
            
        except Exception as e:
            logger.error(f"Failed to optimize analysis: {str(e)}")
            return {
                'prompt_enhancements': {},
                'common_errors': [],
                'error': str(e)
            }
    
    def get_learning_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        获取学习统计信息
        
        Args:
            days: 统计天数
            
        Returns:
            Dict: 学习统计
        """
        try:
            stats = self.learning_engine.get_learning_statistics(days=days)
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get learning statistics: {str(e)}")
            return {
                'total_modifications': 0,
                'avg_modification_rate': 0.0,
                'error': str(e)
            }