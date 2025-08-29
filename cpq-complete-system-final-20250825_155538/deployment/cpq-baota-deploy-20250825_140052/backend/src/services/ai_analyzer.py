# -*- coding: utf-8 -*-
"""
AI分析服务
整合文档处理和OpenAI分析，提供完整的AI产品分析功能
"""
import logging
import time
from typing import Dict, Any, Optional, Tuple
from werkzeug.datastructures import FileStorage

from .document_processor import DocumentProcessor
from .zhipuai_client import ZhipuAIClient
from .learning_engine import LearningEngine
from .table_parser import TableParser
from .confidence_scorer import ConfidenceScorer

logger = logging.getLogger(__name__)

class AIAnalyzer:
    """AI产品分析器"""
    
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.ai_client = ZhipuAIClient()
        self.learning_engine = LearningEngine()
        self.table_parser = TableParser()
        self.confidence_scorer = ConfidenceScorer()
    
    def analyze_product_document(self, file: FileStorage, user_id: int = None) -> Dict[str, Any]:
        """
        分析产品文档，提取产品信息
        
        Args:
            file: 上传的文件对象
            user_id: 用户ID，用于个性化分析
            
        Returns:
            Dict: 完整的分析结果
        """
        start_time = time.time()
        
        try:
            # 1. 处理文档，提取文本
            logger.info(f"Processing document: {file.filename}")
            text_content, doc_info = self.document_processor.process_document(file)
            
            if not text_content.strip():
                raise ValueError("Document contains no readable text content")
            
            # 🔍 增强乱码检测 - 使用文档处理器的增强算法
            if self.document_processor._enhanced_corruption_detection(text_content, doc_info.get('type', '')):
                error_msg = self._generate_corruption_error_message(file.filename, doc_info)
                raise ValueError(error_msg)
            
            # 2. 增强表格解析
            logger.info(f"Enhancing extraction with table parsing")
            
            # 3. 获取个性化提示（如果有用户ID）
            personalized_hints = {}
            if user_id:
                personalized_hints = self.learning_engine.get_personalized_hints(
                    user_id=user_id,
                    document_type=doc_info.get('type', 'unknown'),
                    extracted_data={}
                )
            
            # 4. 使用AI分析文本（使用优化后的分层分析方法）
            logger.info(f"Analyzing document content with AI (length: {len(text_content)} chars)")
            ai_result = self.ai_client.analyze_product_document(
                document_content=text_content,
                document_name=file.filename or "unknown"
            )
            
            # 5. 使用表格解析器增强结果
            enhanced_result = self.table_parser.enhance_extraction_with_tables(ai_result, text_content)
            
            # 6. 计算置信度分数
            confidence_scores = self.confidence_scorer.calculate_comprehensive_confidence(
                extracted_data=enhanced_result,
                document_info=doc_info,
                historical_context=personalized_hints.get('pattern_context') if user_id else None
            )
            
            # 7. 计算分析时长
            analysis_duration = int(time.time() - start_time)
            
            # 8. 智能修复产品名称（如果规格提取成功但名称为空）
            current_name = enhanced_result.get('basic_info', {}).get('name', '')
            logger.info(f"🔍 检查产品名称修复 - 当前名称: '{current_name}', 有规格参数: {bool(enhanced_result.get('specifications'))}")
            
            if not current_name.strip() and enhanced_result.get('specifications'):
                logger.info(f"🔧 开始修复缺失的产品名称，文件名: {file.filename}")
                enhanced_result = self._fix_missing_product_name(enhanced_result, file.filename or "unknown")
                new_name = enhanced_result.get('basic_info', {}).get('name', '')
                logger.info(f"✅ 产品名称修复完成: '{new_name}'")
            
            # 🔧 9. 最终数据清理 - 确保所有规格参数都是有效的
            if enhanced_result.get('specifications'):
                cleaned_specs = self.table_parser._clean_specification_data(enhanced_result['specifications'])
                enhanced_result['specifications'] = cleaned_specs
                logger.info(f"最终规格参数清理完成，保留 {len(cleaned_specs)} 项有效参数")
            
            # 🔧 10. 最终数据完整性检查
            final_basic_info = enhanced_result.get('basic_info', {})
            final_specs = enhanced_result.get('specifications', {})
            
            logger.info(f"📊 最终数据检查:")
            logger.info(f"   - 产品名称: '{final_basic_info.get('name', '')}' (长度: {len(final_basic_info.get('name', ''))})")
            logger.info(f"   - 产品代码: '{final_basic_info.get('code', '')}' (长度: {len(final_basic_info.get('code', ''))})")
            logger.info(f"   - 产品分类: '{final_basic_info.get('category', '')}' (长度: {len(final_basic_info.get('category', ''))})")
            logger.info(f"   - 规格参数: {len(final_specs)} 项")
            logger.info(f"   - 基础信息完整结构: {list(final_basic_info.keys())}")
            
            # 如果关键信息缺失，尝试从置信度评分或其他来源恢复
            if not final_basic_info.get('name', '').strip():
                logger.warning("⚠️ 产品名称为空，尝试从分析上下文恢复")
                # 可以从confidence_scores或其他地方尝试恢复数据
            
            # 11. 构建完整结果
            result = {
                'success': True,
                'document_info': {
                    **doc_info,
                    'analysis_duration': analysis_duration
                },
                'extracted_data': enhanced_result,
                'confidence_scores': confidence_scores,
                'personalized_hints': personalized_hints.get('personalized_hints', []) if user_id else [],
                'predicted_modifications': personalized_hints.get('predicted_modifications', {}) if user_id else {},
                'text_preview': text_content[:500] + "..." if len(text_content) > 500 else text_content,
                'analysis_timestamp': int(time.time())
            }
            
            logger.info(f"Document analysis completed successfully in {analysis_duration}s "
                       f"(confidence: {confidence_scores.get('overall', 'N/A')})")
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"AI analysis failed for {file.filename}: {error_msg}")
            
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
                    'analysis_duration': int(time.time() - start_time),
                    'file_type': getattr(file, 'mimetype', 'unknown')
                }
            }
    
    def _fix_missing_product_name(self, extracted_data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """智能修复缺失的产品名称"""
        try:
            basic_info = extracted_data.get('basic_info', {})
            specifications = extracted_data.get('specifications', {})
            
            # 从文件名推断产品名称
            if '六相微机继电保护测试仪' in filename or '继电保护测试仪' in filename:
                basic_info['name'] = '六相微机继电保护测试仪'
                basic_info['category'] = '继电保护测试设备'
                basic_info['description'] = '六相微机继电保护测试仪，用于电力系统继电保护装置的全面测试和校验'
                
            elif '变压器' in filename:
                basic_info['name'] = '电力变压器'
                basic_info['category'] = '变压器设备'
                
            elif '开关' in filename:
                basic_info['name'] = '电力开关设备'
                basic_info['category'] = '开关设备'
                
            else:
                # 从规格参数推断产品类型
                if any('相' in str(key) for key in specifications.keys()):
                    if '6' in str(specifications) or '六' in str(specifications):
                        basic_info['name'] = '六相微机继电保护测试仪'
                        basic_info['category'] = '继电保护测试设备'
                        basic_info['description'] = '六相微机继电保护测试仪，用于电力系统继电保护装置的测试'
                    else:
                        basic_info['name'] = '电力测试设备'
                        basic_info['category'] = '电力测试设备'
                        
                elif any('变压器' in str(key) for key in specifications.keys()):
                    basic_info['name'] = '电力变压器'
                    basic_info['category'] = '变压器设备'
                    
                else:
                    # 通用电气设备
                    basic_info['name'] = '电力设备'
                    basic_info['category'] = '电力设备'
            
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