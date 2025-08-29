# -*- coding: utf-8 -*-
"""
复杂表格解析服务
专门处理各种格式的规格表、参数表等结构化数据
"""
import re
import logging
from typing import Dict, List, Any, Tuple, Optional
import pandas as pd
from io import StringIO

logger = logging.getLogger(__name__)

class TableParser:
    """复杂表格解析器"""
    
    def __init__(self):
        # 表格识别模式
        self.table_patterns = {
            'pipe_table': r'\|.*\|',  # |column1|column2|
            'tab_table': r'.*\t.*\t.*',  # tab分隔
            'colon_table': r'.*:\s*.*',  # 键值对 key: value
            'dash_table': r'[-\s]*[-]+[-\s]*',  # 分隔线
            'spec_table': r'^\s*[^\s]+\s+[^\s]+.*$',  # 规格表格式
        }
        
        # 🚫 无效规格参数过滤模式 - 增强过滤策略，针对截图中的奇怪数据
        self.invalid_spec_patterns = {
            # Word文档内部格式 - 保留HYPERLINK过滤但减少误杀
            'word_format': [
                r'^(EMBED|MERGEFORMAT|CERTIFICATE|PACKING)$',
                r'^(PBrush|Word\.Picture|OF CONFORMITY|LIST DATE).*',
                r'.*EMBED.*',
                r'.*\.Picture\.',
                # 🔧 增强HYPERLINK过滤，处理复合格式
                r'^HYPERLINK$',  # 只过滤纯HYPERLINK
                r'^\d+\s+HYPERLINK\s*$',  # 只过滤 "数字 HYPERLINK" 且后面没有其他内容
                r'^HYPERLINK\s+["\'].*["\']$',  # 过滤 HYPERLINK "url" 格式
                r'^[a-z]+\s+\d+\s+HYPERLINK.*$',  # 处理 "h 9 HYPERLINK HYPE" 类型
                r'.*HYPERLINK\s+HYPE.*'  # 处理截断的HYPERLINK
            ],
            # 🆕 页面和文档结构元素 - 针对 "PAGE 7" 等问题
            'page_elements': [
                r'^PAGE\s+\d+$',  # 精确匹配 "PAGE 7" 格式  
                r'^第\s*\d+\s*页$',  # 中文页码
                r'^页\s*\d+$',  # 简化页码
                r'^\d+\s*页$',  # 数字页
                r'^(CHAPTER|SECTION)\s+\d+$',  # 章节标记
                r'^(目录|索引|页码|章节|标题)$',
                r'^(CONTENTS|INDEX|TITLE)$'
            ],
            # 文档结构标识 - 减少单字符过滤的误杀
            'doc_structure': [
                r'^(Toc\d+|_Toc|_Ref).*',
                r'.*Toc\d+.*',
                r'^\d+$'  # 只过滤纯数字
            ],
            # 🆕 表格格式噪声 - 针对 "A A AB X B", "Ca a a a b" 等问题
            'table_format_noise': [
                # 处理表格边框和格式化符号被误识别的情况
                r'^[A-Z]\s+[A-Z]\s+[A-Z][A-Z]?\s+[A-Z]\s+[A-Z]$',  # "A A AB X B" 类型
                r'^[A-Z][a-z]?\s+[a-z]\s+[a-z]\s+[a-z]\s+[a-z]$',  # "Ca a a a b" 类型
                r'^[A-Z]{1,2}\s+[A-Z]{1,2}\s+[A-Z]{1,2}.*[A-Z]\s+[A-Z]$',  # 类似的大写字母组合
                r'^[a-z]+\s+[a-z]\s+[a-z].*[a-z]\s+[a-z]$',  # 类似的小写字母组合
                # 表格边框线被误识别
                r'^[\|\s\-\+\=]{3,}$',  # 表格边框线
                r'^[│┌┐└┘├┤┬┴┼]{2,}$',  # Unicode表格边框字符
                r'^\s*[｜\|]\s*$',  # 单独的管道符
                r'^\s*[\-]{2,}\s*$',  # 连字符分隔线
            ],
            # 格式化字符和控制字符
            'format_chars': [
                r'^[\s\-_=]{3,}$',  # 只过滤3个以上连续格式字符
                r'^[^\w\u4e00-\u9fff]+$',  # 只有非文字字符
                r'.*[\x00-\x1f\x7f-\x9f].*'  # 控制字符
            ],
            # 🆕 明确的垃圾内容模式
            'obvious_garbage': [
                r'^[^a-zA-Z\u4e00-\u9fff\d]*$',  # 完全没有文字和数字的内容
                r'^\s*$',  # 空白内容
                r'^(.)\1{4,}$',  # 同一字符重复5次以上
                # 单个无意义字符或字符组合
                r'^[a-zA-Z]{1}$',  # 单个字母（除非在技术上下文中）
                r'^[a-zA-Z]\s+$',  # 单个字母加空格
            ]
        }
        
        # ✅ 有效技术规格标识模式 - 针对电力设备文档优化
        self.valid_spec_patterns = [
            # 中文技术参数 - 专门针对电力测试设备扩展
            r'(电压|电流|功率|频率|温度|湿度|精度|范围|容量|速度|时间|压力|流量|阻抗|相数|输出|输入)',
            r'(工作|额定|最大|最小|标准|测量|测试|检测|保护|控制|显示|通信|接口|尺寸|重量|负载)',
            r'(继电|保护|装置|设备|仪器|仪表|模块|单元|系统|回路|电路|变压器|变比|组别)',
            # 🆕 专门针对变比测试仪等电力设备的关键词
            r'(变比|组别|测试仪|检测仪|保护|继电|电力|高压|低压|绝缘|耐压|测试|校验)',
            r'(互感器|CT|PT|开关|断路器|接触器|电抗器|电容器|避雷器)',
            # 英文技术参数 - 扩展电力设备词汇
            r'(voltage|current|power|frequency|temperature|humidity|accuracy|range|capacity)',
            r'(speed|time|pressure|flow|impedance|phase|output|input|working|rated|max|min)',
            r'(relay|protection|device|equipment|instrument|module|unit|system|circuit)',
            r'(transformer|ratio|test|high|low|insulation|withstand|measurement)',
            # 单位模式 - 扩展电力设备常用单位
            r'.*[VvAaWwHhΩ℃℉%mMkKgGΩ]+.*',
            r'.*[0-9]+\s*[VvAaWwHhΩ℃℉%mMkKgGΨτ].*',  # 数字+单位，增加电力单位
            r'.*[0-9]+\s*(kV|kA|MW|kW|Hz|Ω|°C|°F).*',  # 常见电力单位
            # 数值模式 - 更宽松的数值识别
            r'.*\d+.*',
            r'.*[0-9]+[\.,][0-9]+.*',  # 小数
            r'.*[0-9]+\s*[-~±]\s*[0-9]+.*',  # 范围值
            r'.*[0-9]+\s*[xX×]\s*[0-9]+.*',  # 倍数关系
            # 比值和分数模式（变比测试仪常见）
            r'.*[0-9]+\s*[:/]\s*[0-9]+.*',  # 比值如 220:110
            r'.*[0-9]+/[0-9]+.*',  # 分数
            # OCR常见的技术词汇（包括可能的识别错误）
            r'.*(测试|检测|保护|继电|装置|设备|性能|参数|规格|指标|配置|特性).*',
            r'.*(test|protect|relay|device|spec|param|performance|config|feature).*',
            # 🆕 特殊模式：短技术参数名（常见于表格）
            r'^[A-Z]{2,5}$',  # 如 AC、DC、RS485等技术缩写
            r'^[a-z]{2,8}$',  # 小写技术参数
            r'^\w{1,3}\d+$',   # 如 V1、A2、f0等参数编号
            # 🆕 包含数字和字母的混合模式
            r'^[a-zA-Z\u4e00-\u9fff]+\d+[a-zA-Z\u4e00-\u9fff]*$',  # 如 频率1、电压A等
            r'^\d+[a-zA-Z\u4e00-\u9fff]+$'  # 如 3相、220V等
        ]
        
        # 常见表头识别
        self.header_patterns = {
            'zh': {
                'parameter': r'(参数|规格|指标|项目|名称)',
                'value': r'(值|数值|参数值|规格值)',
                'unit': r'(单位|量纲)',
                'description': r'(说明|描述|备注|注释)',
                'range': r'(范围|区间|限值)',
                'condition': r'(条件|环境|状态)'
            },
            'en': {
                'parameter': r'(parameter|specification|spec|item|name)',
                'value': r'(value|val|data)',
                'unit': r'(unit|dimension)',
                'description': r'(description|desc|note|remark)',
                'range': r'(range|limit)',
                'condition': r'(condition|environment|state)'
            }
        }
        
        # 数值和单位识别模式
        self.value_patterns = {
            'number_with_unit': r'([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*([a-zA-Z°℃℉%Ω]+)',
            'range_value': r'([-+]?\d*\.?\d+)\s*[-~]\s*([-+]?\d*\.?\d+)',
            'tolerance': r'([-+]?\d*\.?\d+)\s*[±]\s*([-+]?\d*\.?\d+)',
            'percentage': r'([-+]?\d*\.?\d+)\s*%',
            'scientific': r'([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)',
        }
    
    def parse_document_tables(self, text_content: str) -> Dict[str, Any]:
        """
        从文档中解析所有表格
        
        Args:
            text_content: 文档文本内容
            
        Returns:
            Dict: 解析结果
        """
        try:
            # 按行分割文本
            lines = text_content.split('\n')
            
            # 识别表格区域
            table_regions = self._identify_table_regions(lines)
            
            # 解析每个表格区域
            parsed_tables = []
            for region in table_regions:
                table_data = self._parse_table_region(region)
                if table_data:
                    parsed_tables.append(table_data)
            
            # 提取规格信息
            specifications = self._extract_specifications(parsed_tables, text_content)
            
            # 提取性能参数
            performance_params = self._extract_performance_params(parsed_tables, text_content)
            
            result = {
                'tables_found': len(parsed_tables),
                'specifications': specifications,
                'performance_parameters': performance_params,
                'raw_tables': parsed_tables,
                'parsing_confidence': self._calculate_parsing_confidence(parsed_tables)
            }
            
            logger.info(f"Parsed {len(parsed_tables)} tables with {len(specifications)} specifications")
            return result
            
        except Exception as e:
            logger.error(f"Table parsing failed: {str(e)}")
            return {
                'tables_found': 0,
                'specifications': {},
                'performance_parameters': {},
                'raw_tables': [],
                'parsing_confidence': 0.0,
                'error': str(e)
            }
    
    def _identify_table_regions(self, lines: List[str]) -> List[Dict[str, Any]]:
        """识别文本中的表格区域"""
        regions = []
        current_region = None
        
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if not line_clean:
                continue
            
            # 检查是否为表格行
            table_type = self._identify_table_type(line_clean)
            
            if table_type:
                if current_region is None:
                    # 开始新的表格区域
                    current_region = {
                        'start_line': i,
                        'end_line': i,
                        'lines': [line_clean],
                        'type': table_type,
                        'confidence': 0.5
                    }
                else:
                    # 继续当前表格区域
                    current_region['end_line'] = i
                    current_region['lines'].append(line_clean)
                    current_region['confidence'] = min(1.0, current_region['confidence'] + 0.1)
            else:
                if current_region and len(current_region['lines']) >= 2:
                    # 结束当前表格区域
                    regions.append(current_region)
                current_region = None
        
        # 处理最后一个区域
        if current_region and len(current_region['lines']) >= 2:
            regions.append(current_region)
        
        return regions
    
    def _identify_table_type(self, line: str) -> Optional[str]:
        """识别行的表格类型"""
        for table_type, pattern in self.table_patterns.items():
            if re.search(pattern, line, re.IGNORECASE):
                return table_type
        return None
    
    def _parse_table_region(self, region: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """解析表格区域"""
        try:
            table_type = region['type']
            lines = region['lines']
            
            if table_type == 'pipe_table':
                return self._parse_pipe_table(lines)
            elif table_type == 'tab_table':
                return self._parse_tab_table(lines)
            elif table_type == 'colon_table':
                return self._parse_colon_table(lines)
            elif table_type == 'spec_table':
                return self._parse_spec_table(lines)
            else:
                return self._parse_generic_table(lines)
                
        except Exception as e:
            logger.warning(f"Failed to parse table region: {str(e)}")
            return None
    
    def _parse_pipe_table(self, lines: List[str]) -> Dict[str, Any]:
        """解析管道分隔表格 |col1|col2|col3|"""
        rows = []
        headers = None
        
        for line in lines:
            # 清理管道符号
            cells = [cell.strip() for cell in line.split('|') if cell.strip()]
            if not cells:
                continue
                
            # 跳过分隔行
            if all(re.match(r'[-\s:]+', cell) for cell in cells):
                continue
                
            if headers is None:
                headers = cells
            else:
                rows.append(cells)
        
        return {
            'type': 'pipe_table',
            'headers': headers or [],
            'rows': rows,
            'column_count': len(headers) if headers else 0,
            'row_count': len(rows)
        }
    
    def _parse_tab_table(self, lines: List[str]) -> Dict[str, Any]:
        """解析制表符分隔表格"""
        rows = []
        headers = None
        
        for line in lines:
            cells = [cell.strip() for cell in line.split('\t') if cell.strip()]
            if not cells:
                continue
                
            if headers is None:
                headers = cells
            else:
                rows.append(cells)
        
        return {
            'type': 'tab_table',
            'headers': headers or [],
            'rows': rows,
            'column_count': len(headers) if headers else 0,
            'row_count': len(rows)
        }
    
    def _parse_colon_table(self, lines: List[str]) -> Dict[str, Any]:
        """解析键值对表格 key: value"""
        pairs = {}
        
        for line in lines:
            match = re.match(r'^([^:]+):\s*(.+)$', line.strip())
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                pairs[key] = value
        
        return {
            'type': 'colon_table',
            'pairs': pairs,
            'pair_count': len(pairs)
        }
    
    def _parse_spec_table(self, lines: List[str]) -> Dict[str, Any]:
        """解析规格表格式"""
        specs = {}
        
        for line in lines:
            # 尝试匹配 "参数名 值 单位" 格式
            parts = line.split()
            if len(parts) >= 2:
                param_name = parts[0]
                value_part = ' '.join(parts[1:])
                
                # 尝试分离数值和单位
                parsed_value = self._parse_value_with_unit(value_part)
                specs[param_name] = parsed_value
        
        return {
            'type': 'spec_table',
            'specifications': specs,
            'spec_count': len(specs)
        }
    
    def _parse_generic_table(self, lines: List[str]) -> Dict[str, Any]:
        """通用表格解析"""
        # 尝试用pandas解析
        try:
            text_data = '\n'.join(lines)
            # 尝试不同的分隔符
            separators = ['\t', '  ', ' ']
            
            for sep in separators:
                try:
                    df = pd.read_csv(StringIO(text_data), sep=sep, engine='python')
                    if len(df.columns) > 1 and len(df) > 0:
                        return {
                            'type': 'generic_table',
                            'headers': df.columns.tolist(),
                            'rows': df.values.tolist(),
                            'column_count': len(df.columns),
                            'row_count': len(df)
                        }
                except:
                    continue
        except:
            pass
        
        # 失败时返回原始行数据
        return {
            'type': 'raw_lines',
            'lines': lines,
            'line_count': len(lines)
        }
    
    def _parse_value_with_unit(self, value_str: str) -> Dict[str, Any]:
        """解析带单位的数值"""
        result = {
            'raw_value': value_str,
            'numeric_value': None,
            'unit': '',
            'range': None,
            'tolerance': None
        }
        
        # 尝试匹配不同的数值模式
        for pattern_name, pattern in self.value_patterns.items():
            match = re.search(pattern, value_str, re.IGNORECASE)
            if match:
                if pattern_name == 'number_with_unit':
                    result['numeric_value'] = float(match.group(1))
                    result['unit'] = match.group(2)
                elif pattern_name == 'range_value':
                    result['range'] = {
                        'min': float(match.group(1)),
                        'max': float(match.group(2))
                    }
                elif pattern_name == 'tolerance':
                    result['numeric_value'] = float(match.group(1))
                    result['tolerance'] = float(match.group(2))
                elif pattern_name == 'percentage':
                    result['numeric_value'] = float(match.group(1))
                    result['unit'] = '%'
                elif pattern_name == 'scientific':
                    result['numeric_value'] = float(match.group(1))
                break
        
        return result
    
    def _extract_specifications(self, tables: List[Dict], text_content: str) -> Dict[str, Any]:
        """从解析的表格中提取规格信息"""
        specifications = {}
        
        for table in tables:
            if table['type'] == 'colon_table':
                # 键值对表格
                for key, value in table.get('pairs', {}).items():
                    spec_info = self._parse_value_with_unit(value)
                    spec_info['source'] = 'colon_table'
                    specifications[key] = spec_info
                    
            elif table['type'] == 'spec_table':
                # 规格表
                for key, value in table.get('specifications', {}).items():
                    value['source'] = 'spec_table'
                    specifications[key] = value
                    
            elif table['type'] in ['pipe_table', 'tab_table', 'generic_table']:
                # 结构化表格
                headers = table.get('headers', [])
                rows = table.get('rows', [])
                
                # 尝试识别参数列和值列
                param_col, value_col = self._identify_param_value_columns(headers)
                
                if param_col is not None and value_col is not None:
                    for row in rows:
                        if len(row) > max(param_col, value_col):
                            param_name = row[param_col]
                            param_value = row[value_col]
                            
                            spec_info = self._parse_value_with_unit(param_value)
                            spec_info['source'] = table['type']
                            specifications[param_name] = spec_info
        
        return specifications
    
    def _extract_performance_params(self, tables: List[Dict], text_content: str) -> Dict[str, Any]:
        """提取性能参数"""
        performance_keywords = [
            '精度', '准确度', '误差', '分辨率', '响应时间', '功耗', '效率',
            'accuracy', 'precision', 'error', 'resolution', 'response', 'power', 'efficiency'
        ]
        
        performance_params = {}
        
        # 从规格中筛选性能相关参数
        for table in tables:
            if table['type'] == 'colon_table':
                for key, value in table.get('pairs', {}).items():
                    if any(keyword in key.lower() for keyword in performance_keywords):
                        spec_info = self._parse_value_with_unit(value)
                        spec_info['category'] = 'performance'
                        performance_params[key] = spec_info
        
        return performance_params
    
    def _identify_param_value_columns(self, headers: List[str]) -> Tuple[Optional[int], Optional[int]]:
        """识别参数列和值列的位置"""
        param_col = None
        value_col = None
        
        for i, header in enumerate(headers):
            header_lower = header.lower()
            
            # 检查是否为参数列
            if any(re.search(pattern, header_lower) for pattern in 
                   list(self.header_patterns['zh']['parameter']) + [self.header_patterns['en']['parameter']]):
                param_col = i
            
            # 检查是否为值列
            if any(re.search(pattern, header_lower) for pattern in 
                   list(self.header_patterns['zh']['value']) + [self.header_patterns['en']['value']]):
                value_col = i
        
        return param_col, value_col
    
    def _calculate_parsing_confidence(self, tables: List[Dict]) -> float:
        """计算解析置信度"""
        if not tables:
            return 0.0
        
        total_confidence = 0.0
        for table in tables:
            confidence = 0.5  # 基础置信度
            
            # 根据表格类型调整置信度
            if table['type'] in ['pipe_table', 'tab_table']:
                confidence += 0.3  # 结构化表格置信度更高
            elif table['type'] == 'colon_table':
                confidence += 0.2
            
            # 根据数据量调整
            data_count = table.get('row_count', table.get('pair_count', table.get('spec_count', 0)))
            if data_count > 5:
                confidence += 0.1
            if data_count > 10:
                confidence += 0.1
            
            total_confidence += min(1.0, confidence)
        
        return total_confidence / len(tables)
    
    def _is_valid_specification(self, spec_name: str, spec_value: str = "") -> bool:
        """
        验证规格参数是否有效 - 优化版本，减少误杀，增加调试信息
        
        Args:
            spec_name: 规格参数名称
            spec_value: 规格参数值（可选）
            
        Returns:
            bool: 是否为有效的技术规格参数
        """
        if not spec_name or not spec_name.strip():
            return False
            
        spec_name = spec_name.strip()
        spec_value = spec_value.strip() if spec_value else ""
        
        # 🔧 预处理：移除常见的OCR错误
        cleaned_name = spec_name.replace('l', '1').replace('O', '0')
        combined_text = spec_name + " " + spec_value
        
        # 🚨 优先级1: 如果参数值明确包含技术信息，直接通过
        if spec_value and self._contains_technical_info(spec_value):
            logger.debug(f"✅ 规格参数 '{spec_name}' = '{spec_value}' 包含明确技术信息，直接通过")
            return True
        
        # 🚨 优先级2: 检查是否匹配有效技术模式
        for pattern in self.valid_spec_patterns:
            if re.search(pattern, combined_text, re.IGNORECASE):
                logger.debug(f"✅ 规格参数 '{spec_name}' 匹配有效技术模式")
                return True
        
        # 🚫 优先级3: 过滤明显的无效模式 - 增强过滤逻辑
        invalid_score = 0
        for category, patterns in self.invalid_spec_patterns.items():
            for pattern in patterns:
                if re.match(pattern, spec_name, re.IGNORECASE):
                    invalid_score += 1
                    logger.debug(f"🔍 规格参数 '{spec_name}' 匹配无效模式 {category}: {pattern}")
                    
                    # 🔧 如果参数值包含技术信息，给一次机会
                    if spec_value and self._contains_technical_info(spec_value):
                        logger.debug(f"⚠️ 规格参数 '{spec_name}' 匹配无效模式但值包含技术信息，继续评估")
                        break
                    elif category in ['obvious_garbage', 'format_chars', 'table_format_noise', 'page_elements']:
                        # 明显垃圾内容、表格格式噪声、页面元素直接过滤
                        logger.debug(f"❌ 规格参数 '{spec_name}' 被直接过滤 (类别: {category})")
                        return False
        
        # 🔍 智能验证逻辑 - 多维度评分系统
        validation_score = 0
        validation_reasons = []
        
        # 1. 长度合理性检查
        if 1 <= len(spec_name) <= 30:
            validation_score += 10
            validation_reasons.append("长度合理")
        
        # 2. 包含数字（技术参数经常有数字）
        if re.search(r'\d', combined_text):
            validation_score += 15
            validation_reasons.append("包含数字")
        
        # 3. 包含中文或英文
        has_chinese = bool(re.search(r'[\u4e00-\u9fff]', spec_name))
        has_english = bool(re.search(r'[a-zA-Z]{2,}', spec_name))
        if has_chinese or has_english:
            validation_score += 15
            validation_reasons.append("包含文字")
        
        # 4. 技术单位模式
        if re.search(r'[0-9]+\s*[a-zA-Z%°℃ΩkMG]+', combined_text):
            validation_score += 25
            validation_reasons.append("包含技术单位")
        
        # 5. 比值和范围模式（电力设备常见）
        if re.search(r'[0-9]+\s*[:/\-~±×]\s*[0-9]+', combined_text):
            validation_score += 20
            validation_reasons.append("包含比值/范围")
        
        # 6. 技术关键词加分
        technical_keywords = [
            # 中文关键词
            '电', '流', '压', '功', '率', '频', '温', '度', '精', '量', '测', '试', '保', '护',
            '变', '比', '组', '别', '输', '出', '入', '相', '线', '负', '载', '阻', '抗',
            # 英文关键词
            'volt', 'amp', 'watt', 'freq', 'temp', 'test', 'prot', 'meas', 'spec', 'param',
            'ratio', 'phase', 'output', 'input', 'current', 'power', 'trans'
        ]
        
        for keyword in technical_keywords:
            if keyword in spec_name.lower() or keyword in spec_value.lower():
                validation_score += 20
                validation_reasons.append(f"包含技术关键词: {keyword}")
                break
        
        # 7. 技术缩写加分
        if re.match(r'^[A-Z]{2,5}$', spec_name):  # AC, DC, RS485等
            validation_score += 15
            validation_reasons.append("技术缩写格式")
        
        # 8. 参数编号格式加分
        if re.match(r'^\w{1,3}\d+$', spec_name):  # V1, A2, f0等
            validation_score += 15
            validation_reasons.append("参数编号格式")
        
        # 9. 如果有值，检查值的技术性
        if spec_value:
            if re.search(r'[\d\.]+', spec_value):
                validation_score += 10
                validation_reasons.append("值包含数字")
            if len(spec_value) >= 2:
                validation_score += 5
                validation_reasons.append("有实际值")
        
        # 扣分项：无效模式匹配
        validation_score -= invalid_score * 5
        
        # 决策阈值
        threshold = 30  # 降低阈值，减少误杀
        is_valid = validation_score >= threshold
        
        if is_valid:
            logger.debug(f"✅ 规格参数 '{spec_name}' = '{spec_value}' 验证通过 (得分: {validation_score}, 原因: {', '.join(validation_reasons)})")
        else:
            logger.debug(f"❌ 规格参数 '{spec_name}' = '{spec_value}' 验证失败 (得分: {validation_score}, 原因: {', '.join(validation_reasons)})")
        
        return is_valid
    
    def _contains_technical_info(self, value: str) -> bool:
        """检查值是否包含明确的技术信息"""
        if not value:
            return False
            
        # 包含单位的数值
        if re.search(r'\d+\s*[VvAaWwHhΩ℃℉%kKmMgG]', value):
            return True
        
        # 包含明确的技术词汇
        if re.search(r'(电压|电流|功率|频率|变比|组别|相|线|voltage|current|power|frequency|ratio|phase)', value, re.IGNORECASE):
            return True
        
        # 包含范围值
        if re.search(r'\d+\s*[-~±]\s*\d+', value):
            return True
        
        # 包含比值
        if re.search(r'\d+\s*[:/]\s*\d+', value):
            return True
            
        return False
    
    def _clean_specification_data(self, specifications: Dict[str, Any]) -> Dict[str, Any]:
        """
        清理规格参数数据，移除无效项目
        
        Args:
            specifications: 原始规格参数字典
            
        Returns:
            Dict: 清理后的规格参数字典
        """
        cleaned_specs = {}
        filtered_count = 0
        
        for spec_name, spec_data in specifications.items():
            # 获取规格值用于验证
            spec_value = ""
            if isinstance(spec_data, dict):
                spec_value = spec_data.get('value', '') or spec_data.get('raw_value', '')
            elif isinstance(spec_data, str):
                spec_value = spec_data
            
            # 验证规格参数
            if self._is_valid_specification(spec_name, str(spec_value)):
                cleaned_specs[spec_name] = spec_data
            else:
                filtered_count += 1
                logger.debug(f"过滤无效规格参数: {spec_name} = {spec_value}")
        
        if filtered_count > 0:
            logger.info(f"规格参数清理完成：保留 {len(cleaned_specs)} 项，过滤 {filtered_count} 项无效参数")
        
        return cleaned_specs

    def enhance_extraction_with_tables(self, base_extraction: Dict[str, Any], 
                                     text_content: str) -> Dict[str, Any]:
        """用表格解析结果增强基础提取"""
        try:
            # 解析表格
            table_results = self.parse_document_tables(text_content)
            
            # 🔧 合并规格信息 - 添加数据清理
            enhanced_specs = base_extraction.get('specifications', {}).copy()
            
            # 先清理基础提取的规格数据
            enhanced_specs = self._clean_specification_data(enhanced_specs)
            
            # 清理表格提取的规格数据
            table_specs = self._clean_specification_data(table_results.get('specifications', {}))
            
            for spec_name, spec_data in table_specs.items():
                if spec_name not in enhanced_specs:
                    # 转换格式以匹配基础提取格式
                    enhanced_specs[spec_name] = {
                        'value': spec_data.get('raw_value', ''),
                        'unit': spec_data.get('unit', ''),
                        'description': f"从{spec_data.get('source', '表格')}中提取"
                    }
                    
                    # 如果有数值，添加数值信息
                    if spec_data.get('numeric_value') is not None:
                        enhanced_specs[spec_name]['numeric_value'] = spec_data['numeric_value']
                    
                    # 如果有范围，添加范围信息
                    if spec_data.get('range'):
                        enhanced_specs[spec_name]['range'] = spec_data['range']
                    
                    # 如果有容差，添加容差信息
                    if spec_data.get('tolerance'):
                        enhanced_specs[spec_name]['tolerance'] = spec_data['tolerance']
            
            # 更新基础提取结果
            enhanced_extraction = base_extraction.copy()
            enhanced_extraction['specifications'] = enhanced_specs
            
            # 添加表格解析元数据
            enhanced_extraction['table_parsing'] = {
                'tables_found': table_results.get('tables_found', 0),
                'parsing_confidence': table_results.get('parsing_confidence', 0.0),
                'performance_params_count': len(table_results.get('performance_parameters', {}))
            }
            
            logger.info(f"Enhanced extraction with {len(enhanced_specs)} specifications from tables")
            return enhanced_extraction
            
        except Exception as e:
            logger.error(f"Table enhancement failed: {str(e)}")
            return base_extraction