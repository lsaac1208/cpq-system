#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI分析器服务单元测试
覆盖AI分析器的所有功能
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.services.ai_analyzer import AIAnalyzer


class TestAIAnalyzer:
    """测试AIAnalyzer服务"""

    @pytest.fixture
    def ai_analyzer(self):
        """创建AI分析器实例"""
        return AIAnalyzer()

    @pytest.fixture
    def mock_zhipu_response(self):
        """模拟智谱AI响应"""
        return {
            'choices': [{
                'message': {
                    'content': '''```json
{
    "analysis_type": "customer_requirements",
    "business_insights": {
        "customer_requirements": {
            "raw_analysis": "{\\"技术需求\\": {\\"性能规格要求\\": [\\"高性能\\", \\"低延迟\\"]}, \\"商务需求\\": {\\"预算范围\\": \\"100-200万元\\"}}",
            "risk_assessment": {
                "technical_risk": "medium",
                "schedule_risk": "low",
                "budget_risk": "low"
            }
        }
    },
    "confidence_scores": {
        "overall": 0.85,
        "technical": 0.90,
        "business": 0.80
    }
}
```'''
                }
            }],
            'usage': {
                'total_tokens': 1500,
                'prompt_tokens': 800,
                'completion_tokens': 700
            }
        }

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    def test_ai_analyzer_initialization(self, ai_analyzer):
        """测试AI分析器初始化"""
        assert ai_analyzer.zhipu_client is not None
        assert ai_analyzer.business_analyzer is not None
        assert hasattr(ai_analyzer, 'analysis_prompts')

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    def test_validate_analysis_type_valid(self, ai_analyzer):
        """测试有效的分析类型验证"""
        valid_types = [
            'customer_requirements',
            'competitor_analysis',
            'project_mining',
            'product_extraction',
            'document_classification',
            'quality_assessment',
            'comprehensive'
        ]
        
        for analysis_type in valid_types:
            # 应该不抛出异常
            ai_analyzer._validate_analysis_type(analysis_type)

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    def test_validate_analysis_type_invalid(self, ai_analyzer):
        """测试无效的分析类型验证"""
        with pytest.raises(ValueError, match="Unsupported analysis type"):
            ai_analyzer._validate_analysis_type('invalid_type')

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    def test_prepare_prompt_customer_requirements(self, ai_analyzer):
        """测试客户需求分析提示准备"""
        content = "项目需求：高性能ERP系统，预算200万"
        context = {
            'industry': 'technology',
            'project_type': 'development'
        }
        
        prompt = ai_analyzer._prepare_prompt('customer_requirements', content, context)
        
        assert '客户需求分析' in prompt
        assert content in prompt
        assert 'technology' in prompt
        assert 'development' in prompt

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    def test_prepare_prompt_competitor_analysis(self, ai_analyzer):
        """测试竞品分析提示准备"""
        content = "产品：用友ERP，价格：100万元"
        context = {'market': 'enterprise'}
        
        prompt = ai_analyzer._prepare_prompt('competitor_analysis', content, context)
        
        assert '竞品分析' in prompt
        assert content in prompt
        assert 'enterprise' in prompt

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    def test_prepare_prompt_comprehensive(self, ai_analyzer):
        """测试综合分析提示准备"""
        content = "复杂的业务需求文档"
        context = {}
        
        prompt = ai_analyzer._prepare_prompt('comprehensive', content, context)
        
        assert '综合分析' in prompt
        assert content in prompt

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    @patch('src.services.ai_analyzer.ZhipuAIClient')
    def test_analyze_document_success(self, mock_zhipu_client, ai_analyzer, mock_zhipu_response):
        """测试成功分析文档"""
        # 配置模拟客户端
        mock_client = Mock()
        mock_client.chat_completion.return_value = mock_zhipu_response
        mock_zhipu_client.return_value = mock_client
        ai_analyzer.zhipu_client = mock_client
        
        content = "技术需求：高性能，预算：200万元"
        context = {'industry': 'technology'}
        
        result = ai_analyzer.analyze_document(
            content=content,
            analysis_type='customer_requirements',
            context=context
        )
        
        assert result['analysis_type'] == 'customer_requirements'
        assert 'business_insights' in result
        assert 'confidence_scores' in result
        assert result['confidence_scores']['overall'] == 0.85
        assert 'processing_time' in result

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    @patch('src.services.ai_analyzer.ZhipuAIClient')
    def test_analyze_document_api_error(self, mock_zhipu_client, ai_analyzer):
        """测试API调用错误"""
        # 配置模拟客户端抛出异常
        mock_client = Mock()
        mock_client.chat_completion.side_effect = Exception("API Error")
        mock_zhipu_client.return_value = mock_client
        ai_analyzer.zhipu_client = mock_client
        
        with pytest.raises(Exception, match="AI analysis failed"):
            ai_analyzer.analyze_document(
                content="test content",
                analysis_type='customer_requirements'
            )

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    @patch('src.services.ai_analyzer.ZhipuAIClient')
    def test_analyze_document_invalid_response(self, mock_zhipu_client, ai_analyzer):
        """测试无效响应处理"""
        # 配置无效响应
        invalid_response = {
            'choices': [{
                'message': {
                    'content': 'Invalid JSON response'
                }
            }]
        }
        
        mock_client = Mock()
        mock_client.chat_completion.return_value = invalid_response
        mock_zhipu_client.return_value = mock_client
        ai_analyzer.zhipu_client = mock_client
        
        with pytest.raises(Exception, match="Failed to parse AI response"):
            ai_analyzer.analyze_document(
                content="test content",
                analysis_type='customer_requirements'
            )

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    def test_extract_json_from_response_valid(self, ai_analyzer):
        """测试从响应中提取JSON"""
        response_content = '''```json
{
    "analysis_type": "customer_requirements",
    "data": "test"
}
```'''
        
        result = ai_analyzer._extract_json_from_response(response_content)
        
        assert result['analysis_type'] == 'customer_requirements'
        assert result['data'] == 'test'

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    def test_extract_json_from_response_no_json_block(self, ai_analyzer):
        """测试响应中没有JSON代码块"""
        response_content = '{"analysis_type": "customer_requirements"}'
        
        result = ai_analyzer._extract_json_from_response(response_content)
        
        assert result['analysis_type'] == 'customer_requirements'

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    def test_extract_json_from_response_invalid(self, ai_analyzer):
        """测试无效JSON响应"""
        response_content = 'This is not valid JSON'
        
        with pytest.raises(ValueError, match="Invalid JSON in AI response"):
            ai_analyzer._extract_json_from_response(response_content)

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    def test_validate_analysis_result_valid(self, ai_analyzer):
        """测试有效分析结果验证"""
        result = {
            'analysis_type': 'customer_requirements',
            'business_insights': {
                'customer_requirements': {
                    'raw_analysis': 'test data'
                }
            },
            'confidence_scores': {
                'overall': 0.85
            }
        }
        
        # 应该不抛出异常
        ai_analyzer._validate_analysis_result(result)

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    def test_validate_analysis_result_missing_fields(self, ai_analyzer):
        """测试缺少必需字段的分析结果"""
        result = {
            'analysis_type': 'customer_requirements'
            # 缺少 business_insights 和 confidence_scores
        }
        
        with pytest.raises(ValueError, match="Missing required field"):
            ai_analyzer._validate_analysis_result(result)

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    def test_validate_analysis_result_invalid_confidence(self, ai_analyzer):
        """测试无效置信度分数"""
        result = {
            'analysis_type': 'customer_requirements',
            'business_insights': {
                'customer_requirements': {
                    'raw_analysis': 'test'
                }
            },
            'confidence_scores': {
                'overall': 1.5  # 超出范围
            }
        }
        
        with pytest.raises(ValueError, match="Invalid confidence score"):
            ai_analyzer._validate_analysis_result(result)

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    @patch('src.services.ai_analyzer.ZhipuAIClient')
    def test_batch_analyze_documents(self, mock_zhipu_client, ai_analyzer, mock_zhipu_response):
        """测试批量分析文档"""
        # 配置模拟客户端
        mock_client = Mock()
        mock_client.chat_completion.return_value = mock_zhipu_response
        mock_zhipu_client.return_value = mock_client
        ai_analyzer.zhipu_client = mock_client
        
        documents = [
            {'content': 'Document 1', 'analysis_type': 'customer_requirements'},
            {'content': 'Document 2', 'analysis_type': 'competitor_analysis'}
        ]
        
        results = ai_analyzer.batch_analyze_documents(documents)
        
        assert len(results) == 2
        for result in results:
            assert 'analysis_type' in result
            assert 'business_insights' in result
            assert 'confidence_scores' in result

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    def test_get_analysis_statistics(self, ai_analyzer):
        """测试获取分析统计"""
        stats = ai_analyzer.get_analysis_statistics()
        
        assert 'total_analyses' in stats
        assert 'success_rate' in stats
        assert 'average_processing_time' in stats
        assert 'analysis_type_distribution' in stats

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    def test_get_supported_analysis_types(self, ai_analyzer):
        """测试获取支持的分析类型"""
        types = ai_analyzer.get_supported_analysis_types()
        
        expected_types = [
            'customer_requirements',
            'competitor_analysis',
            'project_mining',
            'product_extraction',
            'document_classification',
            'quality_assessment',
            'comprehensive'
        ]
        
        for expected_type in expected_types:
            assert expected_type in types

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    @patch('src.services.ai_analyzer.ZhipuAIClient')
    def test_analyze_with_retry_success_on_second_attempt(self, mock_zhipu_client, ai_analyzer, mock_zhipu_response):
        """测试重试机制成功"""
        # 配置第一次失败，第二次成功
        mock_client = Mock()
        mock_client.chat_completion.side_effect = [
            Exception("First attempt failed"),
            mock_zhipu_response
        ]
        mock_zhipu_client.return_value = mock_client
        ai_analyzer.zhipu_client = mock_client
        
        result = ai_analyzer.analyze_document(
            content="test content",
            analysis_type='customer_requirements'
        )
        
        assert result['analysis_type'] == 'customer_requirements'
        # 验证调用了两次
        assert mock_client.chat_completion.call_count == 2

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    @patch('src.services.ai_analyzer.ZhipuAIClient')
    def test_analyze_with_retry_all_attempts_fail(self, mock_zhipu_client, ai_analyzer):
        """测试所有重试都失败"""
        # 配置所有尝试都失败
        mock_client = Mock()
        mock_client.chat_completion.side_effect = Exception("All attempts failed")
        mock_zhipu_client.return_value = mock_client
        ai_analyzer.zhipu_client = mock_client
        
        with pytest.raises(Exception, match="AI analysis failed"):
            ai_analyzer.analyze_document(
                content="test content",
                analysis_type='customer_requirements'
            )

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    def test_calculate_confidence_score(self, ai_analyzer):
        """测试置信度分数计算"""
        # 测试高质量分析结果
        high_quality_result = {
            'business_insights': {
                'customer_requirements': {
                    'raw_analysis': '{"detailed": "analysis", "comprehensive": "data"}',
                    'risk_assessment': {
                        'technical_risk': 'low',
                        'budget_risk': 'medium'
                    }
                }
            }
        }
        
        score = ai_analyzer._calculate_confidence_score(high_quality_result)
        assert 0.7 <= score <= 1.0
        
        # 测试低质量分析结果
        low_quality_result = {
            'business_insights': {
                'customer_requirements': {
                    'raw_analysis': '{"minimal": "data"}'
                }
            }
        }
        
        score = ai_analyzer._calculate_confidence_score(low_quality_result)
        assert 0.0 <= score <= 0.7

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.ai
    def test_analyze_document_with_custom_context(self, ai_analyzer):
        """测试带自定义上下文的文档分析"""
        with patch.object(ai_analyzer, 'zhipu_client') as mock_client:
            mock_response = {
                'choices': [{
                    'message': {
                        'content': '''```json
{
    "analysis_type": "customer_requirements",
    "business_insights": {
        "customer_requirements": {
            "raw_analysis": "{\\"custom\\": \\"context_applied\\"}"
        }
    },
    "confidence_scores": {"overall": 0.9}
}
```'''
                    }
                }]
            }
            mock_client.chat_completion.return_value = mock_response
            
            context = {
                'industry': 'healthcare',
                'project_type': 'digital_transformation',
                'urgency': 'high'
            }
            
            result = ai_analyzer.analyze_document(
                content="Healthcare system requirements",
                analysis_type='customer_requirements',
                context=context
            )
            
            assert result['analysis_type'] == 'customer_requirements'
            # 验证上下文被传递到提示中
            call_args = mock_client.chat_completion.call_args
            prompt = call_args[1]['messages'][0]['content']
            assert 'healthcare' in prompt
            assert 'digital_transformation' in prompt
            assert 'high' in prompt