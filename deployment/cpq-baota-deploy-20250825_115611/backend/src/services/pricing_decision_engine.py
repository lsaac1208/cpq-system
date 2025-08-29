# -*- coding: utf-8 -*-
"""
报价决策支持引擎
基于批量分析的业务洞察生成智能报价建议
"""
import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
import statistics
from datetime import datetime, timedelta

from ..models.batch_analysis import BatchAnalysisJob, BatchAnalysisFile
from ..models.product import Product
from ..models.quote import Quote, QuoteStatus
from ..models.ai_analysis import AIAnalysisRecord

logger = logging.getLogger(__name__)

class PricingDecisionEngine:
    """报价决策支持引擎"""
    
    def __init__(self):
        self.confidence_threshold = 0.7  # 置信度阈值
        self.price_adjustment_range = (0.8, 1.2)  # 价格调整范围
        
    def generate_pricing_recommendations(self, job_id: str, user_id: int = None) -> Dict[str, Any]:
        """
        基于批量分析结果生成报价建议
        
        Args:
            job_id: 批量分析任务ID
            user_id: 用户ID
            
        Returns:
            Dict: 完整的报价建议结果
        """
        try:
            # 1. 获取批量分析结果
            analysis_data = self._extract_analysis_insights(job_id)
            if not analysis_data:
                raise ValueError("No analysis data found for the job")
            
            # 2. 分析客户需求和市场环境
            market_context = self._analyze_market_context(analysis_data)
            
            # 3. 产品匹配和推荐
            product_recommendations = self._generate_product_recommendations(analysis_data, market_context)
            
            # 4. 定价策略建议
            pricing_strategies = self._generate_pricing_strategies(analysis_data, market_context, product_recommendations)
            
            # 5. 风险评估和机会分析
            risk_opportunity_analysis = self._analyze_risks_opportunities(analysis_data, market_context)
            
            # 6. 生成完整建议
            recommendations = {
                'job_id': job_id,
                'generated_at': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'market_context': market_context,
                'product_recommendations': product_recommendations,
                'pricing_strategies': pricing_strategies,
                'risk_opportunity_analysis': risk_opportunity_analysis,
                'summary': self._generate_executive_summary(market_context, product_recommendations, pricing_strategies),
                'confidence_score': self._calculate_overall_confidence(analysis_data, market_context)
            }
            
            logger.info(f"Generated pricing recommendations for job {job_id}")
            return {
                'success': True,
                'data': recommendations
            }
            
        except Exception as e:
            logger.error(f"Error generating pricing recommendations: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_analysis_insights(self, job_id: str) -> Dict[str, Any]:
        """提取分析洞察"""
        try:
            # 获取批量分析任务
            job = BatchAnalysisJob.query.filter_by(job_id=job_id).first()
            if not job:
                return None
            
            # 获取成功分析的文件
            files = BatchAnalysisFile.query.filter_by(
                job_id=job_id,
                status='completed'
            ).all()
            
            if not files:
                return None
            
            insights = {
                'job_info': job.to_dict(),
                'analysis_results': [],
                'aggregated_insights': {}
            }
            
            # 收集所有分析结果
            for file in files:
                if file.analysis_result:
                    file_insights = {
                        'file_id': file.file_id,
                        'filename': file.filename,
                        'confidence_score': file.confidence_score,
                        'analysis_result': file.analysis_result
                    }
                    insights['analysis_results'].append(file_insights)
            
            # 聚合分析洞察
            insights['aggregated_insights'] = self._aggregate_business_insights(insights['analysis_results'])
            
            return insights
            
        except Exception as e:
            logger.error(f"Error extracting analysis insights: {str(e)}")
            return None
    
    def _aggregate_business_insights(self, analysis_results: List[Dict]) -> Dict[str, Any]:
        """聚合业务洞察"""
        aggregated = {
            'customer_requirements': [],
            'competitor_info': [],
            'project_opportunities': [],
            'product_demands': [],
            'market_trends': [],
            'pricing_indicators': [],
            'quality_concerns': []
        }
        
        for result in analysis_results:
            analysis_data = result.get('analysis_result', {})
            business_insights = analysis_data.get('business_insights', {})
            
            # 客户需求分析
            if 'customer_needs' in business_insights:
                customer_data = business_insights['customer_needs']
                aggregated['customer_requirements'].extend(customer_data.get('requirements', []))
                aggregated['pricing_indicators'].extend(customer_data.get('budget_indicators', []))
            
            # 竞品分析
            if 'competitor_analysis' in business_insights:
                competitor_data = business_insights['competitor_analysis']
                aggregated['competitor_info'].extend(competitor_data.get('competitors', []))
                aggregated['pricing_indicators'].extend(competitor_data.get('pricing_info', []))
            
            # 项目挖掘
            if 'project_opportunities' in business_insights:
                project_data = business_insights['project_opportunities']
                aggregated['project_opportunities'].extend(project_data.get('opportunities', []))
            
            # 产品需求
            if 'product_extraction' in business_insights:
                product_data = business_insights['product_extraction']
                aggregated['product_demands'].extend(product_data.get('products', []))
            
            # 文档分类和质量
            if 'document_classification' in business_insights:
                doc_data = business_insights['document_classification']
                aggregated['market_trends'].extend(doc_data.get('trends', []))
            
            if 'quality_assessment' in business_insights:
                quality_data = business_insights['quality_assessment']
                aggregated['quality_concerns'].extend(quality_data.get('concerns', []))
        
        return aggregated
    
    def _analyze_market_context(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """分析市场环境"""
        insights = analysis_data.get('aggregated_insights', {})
        
        # 竞争强度分析
        competitors = insights.get('competitor_info', [])
        competition_intensity = self._calculate_competition_intensity(competitors)
        
        # 市场机会分析
        opportunities = insights.get('project_opportunities', [])
        market_opportunities = self._analyze_market_opportunities(opportunities)
        
        # 客户价格敏感度
        pricing_indicators = insights.get('pricing_indicators', [])
        price_sensitivity = self._analyze_price_sensitivity(pricing_indicators)
        
        # 产品需求热度
        product_demands = insights.get('product_demands', [])
        demand_heat = self._analyze_demand_heat(product_demands)
        
        return {
            'competition_intensity': competition_intensity,
            'market_opportunities': market_opportunities,
            'price_sensitivity': price_sensitivity,
            'demand_heat': demand_heat,
            'market_trend': self._determine_market_trend(competition_intensity, market_opportunities, demand_heat)
        }
    
    def _calculate_competition_intensity(self, competitors: List[Dict]) -> Dict[str, Any]:
        """计算竞争强度"""
        if not competitors:
            return {'level': 'low', 'score': 0.2, 'competitor_count': 0}
        
        competitor_count = len(competitors)
        
        # 根据竞争对手数量判断竞争强度
        if competitor_count >= 5:
            intensity = 'high'
            score = 0.8
        elif competitor_count >= 3:
            intensity = 'medium'
            score = 0.6
        else:
            intensity = 'low'
            score = 0.4
        
        # 分析竞争对手特点
        competitor_analysis = {
            'large_enterprises': 0,
            'pricing_aggressive': 0,
            'technology_advanced': 0
        }
        
        for competitor in competitors:
            if competitor.get('size') == 'large':
                competitor_analysis['large_enterprises'] += 1
            if competitor.get('pricing_strategy') == 'aggressive':
                competitor_analysis['pricing_aggressive'] += 1
            if competitor.get('technology_level') == 'advanced':
                competitor_analysis['technology_advanced'] += 1
        
        return {
            'level': intensity,
            'score': score,
            'competitor_count': competitor_count,
            'analysis': competitor_analysis
        }
    
    def _analyze_market_opportunities(self, opportunities: List[Dict]) -> Dict[str, Any]:
        """分析市场机会"""
        if not opportunities:
            return {'level': 'low', 'score': 0.3, 'opportunities': []}
        
        # 分析机会质量和数量
        high_value_opportunities = [op for op in opportunities if op.get('value', 0) > 100000]
        opportunity_score = min(len(opportunities) / 10, 1.0)  # 标准化到0-1
        
        if opportunity_score >= 0.7:
            level = 'high'
        elif opportunity_score >= 0.4:
            level = 'medium'
        else:
            level = 'low'
        
        return {
            'level': level,
            'score': opportunity_score,
            'total_opportunities': len(opportunities),
            'high_value_opportunities': len(high_value_opportunities),
            'opportunities': opportunities[:5]  # 返回前5个机会
        }
    
    def _analyze_price_sensitivity(self, pricing_indicators: List[Dict]) -> Dict[str, Any]:
        """分析价格敏感度"""
        if not pricing_indicators:
            return {'level': 'medium', 'score': 0.5, 'indicators': []}
        
        # 分析价格相关指标
        budget_mentions = len([p for p in pricing_indicators if 'budget' in str(p).lower()])
        cost_concerns = len([p for p in pricing_indicators if any(word in str(p).lower() for word in ['cost', 'price', 'expensive', 'cheap'])])
        
        sensitivity_score = (budget_mentions + cost_concerns) / len(pricing_indicators)
        
        if sensitivity_score >= 0.7:
            level = 'high'
        elif sensitivity_score >= 0.4:
            level = 'medium'
        else:
            level = 'low'
        
        return {
            'level': level,
            'score': sensitivity_score,
            'budget_mentions': budget_mentions,
            'cost_concerns': cost_concerns,
            'indicators': pricing_indicators[:3]
        }
    
    def _analyze_demand_heat(self, product_demands: List[Dict]) -> Dict[str, Any]:
        """分析产品需求热度"""
        if not product_demands:
            return {'level': 'low', 'score': 0.3, 'trending_products': []}
        
        # 统计产品类型需求
        product_categories = {}
        for demand in product_demands:
            category = demand.get('category', 'unknown')
            if category not in product_categories:
                product_categories[category] = 0
            product_categories[category] += 1
        
        # 计算需求热度
        demand_score = min(len(product_demands) / 20, 1.0)  # 标准化
        
        if demand_score >= 0.7:
            level = 'high'
        elif demand_score >= 0.4:
            level = 'medium'
        else:
            level = 'low'
        
        # 找出热门产品类型
        trending_products = sorted(product_categories.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'level': level,
            'score': demand_score,
            'total_demands': len(product_demands),
            'product_categories': product_categories,
            'trending_products': trending_products
        }
    
    def _determine_market_trend(self, competition_intensity: Dict, market_opportunities: Dict, demand_heat: Dict) -> str:
        """判断市场趋势"""
        scores = [
            competition_intensity['score'],
            market_opportunities['score'], 
            demand_heat['score']
        ]
        
        avg_score = statistics.mean(scores)
        
        if avg_score >= 0.7:
            return 'growing'
        elif avg_score >= 0.5:
            return 'stable'
        else:
            return 'declining'
    
    def _generate_product_recommendations(self, analysis_data: Dict[str, Any], market_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成产品推荐"""
        insights = analysis_data.get('aggregated_insights', {})
        customer_requirements = insights.get('customer_requirements', [])
        product_demands = insights.get('product_demands', [])
        
        # 获取所有活跃产品
        products = Product.query.filter_by(is_active=True).all()
        
        recommendations = []
        
        for product in products:
            # 计算产品匹配分数
            match_score = self._calculate_product_match_score(
                product, customer_requirements, product_demands, market_context
            )
            
            if match_score > 0.3:  # 只推荐匹配度较高的产品
                # 生成配置建议
                config_recommendations = self._generate_config_recommendations(
                    product, customer_requirements, market_context
                )
                
                # 计算推荐价格
                recommended_price = self._calculate_recommended_price(
                    product, market_context, match_score
                )
                
                recommendation = {
                    'product': product.to_dict(),
                    'match_score': match_score,
                    'match_reasons': self._explain_product_match(product, customer_requirements, product_demands),
                    'config_recommendations': config_recommendations,
                    'recommended_price': recommended_price,
                    'pricing_strategy': self._suggest_pricing_strategy(product, market_context, match_score)
                }
                
                recommendations.append(recommendation)
        
        # 按匹配分数排序
        recommendations.sort(key=lambda x: x['match_score'], reverse=True)
        
        return recommendations[:10]  # 返回前10个推荐
    
    def _calculate_product_match_score(self, product: Product, requirements: List, demands: List, market_context: Dict) -> float:
        """计算产品匹配分数"""
        score = 0.0
        
        # 基础分数
        score += 0.3
        
        # 需求匹配分析
        product_features = product.get_features()
        product_category = product.category.lower()
        
        # 检查客户需求匹配
        requirement_match = 0
        if requirements:
            for req in requirements:
                req_text = str(req).lower()
                if product_category in req_text:
                    requirement_match += 0.3
                for feature in product_features:
                    if str(feature).lower() in req_text:
                        requirement_match += 0.1
        
        score += min(requirement_match, 0.4)
        
        # 检查产品需求匹配
        demand_match = 0
        if demands:
            for demand in demands:
                if demand.get('category', '').lower() == product_category:
                    demand_match += 0.2
                if demand.get('name', '').lower() in product.name.lower():
                    demand_match += 0.1
        
        score += min(demand_match, 0.3)
        
        return min(score, 1.0)
    
    def _explain_product_match(self, product: Product, requirements: List, demands: List) -> List[str]:
        """解释产品匹配原因"""
        reasons = []
        
        product_category = product.category.lower()
        product_features = product.get_features()
        
        # 分析需求匹配
        for req in requirements[:3]:  # 只分析前3个需求
            req_text = str(req).lower()
            if product_category in req_text:
                reasons.append(f"产品类型 '{product.category}' 匹配客户需求")
            
            for feature in product_features[:3]:
                if str(feature).lower() in req_text:
                    reasons.append(f"产品特性 '{feature}' 符合客户要求")
        
        # 分析产品需求匹配
        for demand in demands[:3]:
            if demand.get('category', '').lower() == product_category:
                reasons.append(f"产品类别匹配市场需求趋势")
        
        return reasons[:5]  # 最多返回5个原因
    
    def _generate_config_recommendations(self, product: Product, requirements: List, market_context: Dict) -> Dict[str, Any]:
        """生成配置建议"""
        config_schema = product.get_configuration_schema()
        
        if not config_schema:
            return {'message': '该产品无需配置'}
        
        recommendations = {}
        
        # 基于市场环境和客户需求推荐配置
        if market_context.get('price_sensitivity', {}).get('level') == 'high':
            recommendations['cost_optimization'] = '建议选择基础配置以控制成本'
        elif market_context.get('demand_heat', {}).get('level') == 'high':
            recommendations['feature_enhancement'] = '建议选择高级配置以满足市场需求'
        
        # 基于客户需求推荐具体配置项
        for req in requirements[:3]:
            req_text = str(req).lower()
            if 'performance' in req_text or '性能' in req_text:
                recommendations['performance'] = '推荐高性能配置'
            if 'budget' in req_text or '预算' in req_text:
                recommendations['budget'] = '推荐标准配置平衡性价比'
        
        return recommendations
    
    def _calculate_recommended_price(self, product: Product, market_context: Dict, match_score: float) -> Dict[str, Any]:
        """计算推荐价格"""
        base_price = float(product.base_price)
        
        # 基于市场环境调整价格
        price_adjustment = 1.0
        
        # 竞争强度调整
        competition_score = market_context.get('competition_intensity', {}).get('score', 0.5)
        if competition_score > 0.7:
            price_adjustment *= 0.9  # 高竞争环境降价10%
        elif competition_score < 0.3:
            price_adjustment *= 1.1  # 低竞争环境涨价10%
        
        # 价格敏感度调整
        price_sensitivity = market_context.get('price_sensitivity', {}).get('level', 'medium')
        if price_sensitivity == 'high':
            price_adjustment *= 0.95  # 高价格敏感度降价5%
        elif price_sensitivity == 'low':
            price_adjustment *= 1.05  # 低价格敏感度涨价5%
        
        # 需求热度调整
        demand_heat = market_context.get('demand_heat', {}).get('level', 'medium')
        if demand_heat == 'high':
            price_adjustment *= 1.1  # 高需求涨价10%
        elif demand_heat == 'low':
            price_adjustment *= 0.9  # 低需求降价10%
        
        # 产品匹配度调整
        if match_score > 0.8:
            price_adjustment *= 1.05  # 高匹配度可以适当涨价
        elif match_score < 0.5:
            price_adjustment *= 0.95  # 低匹配度需要降价吸引
        
        # 确保价格调整在合理范围内
        price_adjustment = max(self.price_adjustment_range[0], 
                             min(self.price_adjustment_range[1], price_adjustment))
        
        recommended_price = base_price * price_adjustment
        
        return {
            'base_price': base_price,
            'recommended_price': round(recommended_price, 2),
            'adjustment_factor': round(price_adjustment, 3),
            'price_change_percentage': round((price_adjustment - 1) * 100, 1),
            'adjustment_reasons': self._explain_price_adjustment(market_context, match_score, price_adjustment)
        }
    
    def _explain_price_adjustment(self, market_context: Dict, match_score: float, adjustment: float) -> List[str]:
        """解释价格调整原因"""
        reasons = []
        
        if adjustment > 1.02:
            if market_context.get('demand_heat', {}).get('level') == 'high':
                reasons.append('市场需求旺盛，建议适当提价')
            if market_context.get('competition_intensity', {}).get('score', 0.5) < 0.3:
                reasons.append('竞争强度较低，有提价空间')
            if match_score > 0.8:
                reasons.append('产品高度匹配客户需求，支持溢价')
        elif adjustment < 0.98:
            if market_context.get('competition_intensity', {}).get('score', 0.5) > 0.7:
                reasons.append('市场竞争激烈，建议降价竞争')
            if market_context.get('price_sensitivity', {}).get('level') == 'high':
                reasons.append('客户价格敏感，需要控制价格')
            if match_score < 0.5:
                reasons.append('产品匹配度一般，通过价格优势吸引客户')
        else:
            reasons.append('当前市场条件下，建议维持标准价格')
        
        return reasons
    
    def _suggest_pricing_strategy(self, product: Product, market_context: Dict, match_score: float) -> Dict[str, Any]:
        """建议定价策略"""
        strategies = []
        
        competition_level = market_context.get('competition_intensity', {}).get('level', 'medium')
        demand_level = market_context.get('demand_heat', {}).get('level', 'medium')
        price_sensitivity = market_context.get('price_sensitivity', {}).get('level', 'medium')
        
        # 基于市场条件选择策略
        if competition_level == 'high' and price_sensitivity == 'high':
            strategies.append({
                'name': '成本领先策略',
                'description': '通过优化成本结构提供有竞争力的价格',
                'risk_level': 'medium'
            })
        
        if demand_level == 'high' and match_score > 0.7:
            strategies.append({
                'name': '价值定价策略',
                'description': '基于产品价值和客户需求进行定价',
                'risk_level': 'low'
            })
        
        if competition_level == 'low' and demand_level == 'high':
            strategies.append({
                'name': '撇脂定价策略',
                'description': '在市场需求旺盛时采用较高价格',
                'risk_level': 'medium'
            })
        
        if price_sensitivity == 'low' and match_score > 0.8:
            strategies.append({
                'name': '差异化定价策略',
                'description': '通过产品差异化实现溢价',
                'risk_level': 'low'
            })
        
        # 默认策略
        if not strategies:
            strategies.append({
                'name': '市场导向定价策略',
                'description': '基于市场平均水平进行定价',
                'risk_level': 'low'
            })
        
        return {
            'recommended_strategies': strategies,
            'primary_strategy': strategies[0] if strategies else None
        }
    
    def _generate_pricing_strategies(self, analysis_data: Dict[str, Any], market_context: Dict[str, Any], 
                                   product_recommendations: List[Dict]) -> Dict[str, Any]:
        """生成定价策略"""
        return {
            'overall_strategy': self._determine_overall_strategy(market_context),
            'bundle_opportunities': self._identify_bundle_opportunities(product_recommendations),
            'discount_recommendations': self._generate_discount_recommendations(market_context),
            'timing_considerations': self._analyze_timing_factors(analysis_data, market_context)
        }
    
    def _determine_overall_strategy(self, market_context: Dict) -> Dict[str, Any]:
        """确定整体策略"""
        competition = market_context.get('competition_intensity', {}).get('level', 'medium')
        demand = market_context.get('demand_heat', {}).get('level', 'medium')
        sensitivity = market_context.get('price_sensitivity', {}).get('level', 'medium')
        
        if competition == 'high' and sensitivity == 'high':
            strategy = 'aggressive_pricing'
            description = '采用积极的价格竞争策略'
        elif demand == 'high' and sensitivity == 'low':
            strategy = 'value_based_pricing'
            description = '基于价值进行定价，强调产品优势'
        elif competition == 'low':
            strategy = 'premium_pricing'
            description = '采用溢价策略，突出产品独特性'
        else:
            strategy = 'market_penetration'
            description = '采用市场渗透策略，平衡价格与价值'
        
        return {
            'strategy': strategy,
            'description': description,
            'success_probability': self._estimate_strategy_success(market_context, strategy)
        }
    
    def _identify_bundle_opportunities(self, product_recommendations: List[Dict]) -> List[Dict]:
        """识别打包销售机会"""
        bundles = []
        
        if len(product_recommendations) >= 2:
            # 按类别分组产品
            categories = {}
            for rec in product_recommendations:
                category = rec['product']['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(rec)
            
            # 生成打包建议
            for category, products in categories.items():
                if len(products) >= 2:
                    bundle = {
                        'category': category,
                        'products': [p['product']['name'] for p in products[:3]],
                        'estimated_discount': '5-15%',
                        'value_proposition': f'提供{category}完整解决方案'
                    }
                    bundles.append(bundle)
        
        return bundles
    
    def _generate_discount_recommendations(self, market_context: Dict) -> Dict[str, Any]:
        """生成折扣建议"""
        competition = market_context.get('competition_intensity', {}).get('score', 0.5)
        sensitivity = market_context.get('price_sensitivity', {}).get('score', 0.5)
        
        # 计算建议折扣范围
        base_discount = 0
        max_discount = 0
        
        if competition > 0.7:
            base_discount += 5
            max_discount += 10
        
        if sensitivity > 0.7:
            base_discount += 3
            max_discount += 8
        
        return {
            'volume_discount': {
                'threshold': 10,
                'discount_range': f'{base_discount}-{max_discount}%'
            },
            'early_bird_discount': {
                'duration': '30天内签约',
                'discount': f'{base_discount//2}-{base_discount}%'
            },
            'conditions': [
                '建议设置明确的折扣条件',
                '避免过度价格竞争',
                '重点强调产品价值'
            ]
        }
    
    def _analyze_timing_factors(self, analysis_data: Dict, market_context: Dict) -> Dict[str, Any]:
        """分析时机因素"""
        return {
            'optimal_timing': '基于市场需求热度，建议在1-2月内推进',
            'market_window': self._assess_market_window(market_context),
            'seasonal_factors': '考虑行业季节性特点',
            'urgency_indicators': self._extract_urgency_signals(analysis_data)
        }
    
    def _assess_market_window(self, market_context: Dict) -> str:
        """评估市场窗口"""
        trend = market_context.get('market_trend', 'stable')
        demand = market_context.get('demand_heat', {}).get('level', 'medium')
        
        if trend == 'growing' and demand == 'high':
            return 'excellent'
        elif trend == 'stable':
            return 'good'
        else:
            return 'challenging'
    
    def _extract_urgency_signals(self, analysis_data: Dict) -> List[str]:
        """提取紧急性信号"""
        insights = analysis_data.get('aggregated_insights', {})
        signals = []
        
        # 检查项目机会中的时间敏感信息
        opportunities = insights.get('project_opportunities', [])
        for opp in opportunities:
            if any(word in str(opp).lower() for word in ['urgent', '紧急', 'asap', 'immediate']):
                signals.append('发现紧急项目需求')
        
        # 检查客户需求中的时间因素
        requirements = insights.get('customer_requirements', [])
        for req in requirements:
            if any(word in str(req).lower() for word in ['deadline', '截止', 'schedule', '时间']):
                signals.append('客户有明确时间要求')
        
        return signals
    
    def _analyze_risks_opportunities(self, analysis_data: Dict, market_context: Dict) -> Dict[str, Any]:
        """分析风险和机会"""
        return {
            'opportunities': self._identify_opportunities(analysis_data, market_context),
            'risks': self._identify_risks(analysis_data, market_context),
            'mitigation_strategies': self._suggest_risk_mitigation(market_context)
        }
    
    def _identify_opportunities(self, analysis_data: Dict, market_context: Dict) -> List[Dict]:
        """识别机会"""
        opportunities = []
        
        # 市场机会
        if market_context.get('demand_heat', {}).get('level') == 'high':
            opportunities.append({
                'type': '市场需求',
                'description': '市场需求旺盛，有利于业务拓展',
                'impact': 'high'
            })
        
        # 竞争机会
        if market_context.get('competition_intensity', {}).get('level') == 'low':
            opportunities.append({
                'type': '竞争优势',
                'description': '竞争强度较低，容易获得市场份额',
                'impact': 'medium'
            })
        
        # 定价机会
        if market_context.get('price_sensitivity', {}).get('level') == 'low':
            opportunities.append({
                'type': '定价优势',
                'description': '客户价格敏感度低，支持溢价策略',
                'impact': 'medium'
            })
        
        return opportunities
    
    def _identify_risks(self, analysis_data: Dict, market_context: Dict) -> List[Dict]:
        """识别风险"""
        risks = []
        
        # 竞争风险
        if market_context.get('competition_intensity', {}).get('level') == 'high':
            risks.append({
                'type': '竞争风险',
                'description': '市场竞争激烈，可能面临价格压力',
                'probability': 'high',
                'impact': 'medium'
            })
        
        # 价格风险
        if market_context.get('price_sensitivity', {}).get('level') == 'high':
            risks.append({
                'type': '价格风险',
                'description': '客户价格敏感，定价策略需要谨慎',
                'probability': 'medium',
                'impact': 'high'
            })
        
        # 市场风险
        if market_context.get('market_trend') == 'declining':
            risks.append({
                'type': '市场风险',
                'description': '市场趋势下降，需要评估投入回报',
                'probability': 'medium',
                'impact': 'high'
            })
        
        return risks
    
    def _suggest_risk_mitigation(self, market_context: Dict) -> List[str]:
        """建议风险缓解策略"""
        strategies = []
        
        if market_context.get('competition_intensity', {}).get('level') == 'high':
            strategies.append('强化产品差异化，避免纯价格竞争')
            strategies.append('提升服务质量，增加客户粘性')
        
        if market_context.get('price_sensitivity', {}).get('level') == 'high':
            strategies.append('提供多层次产品方案，满足不同预算需求')
            strategies.append('强调产品ROI和长期价值')
        
        strategies.append('建立灵活的定价机制，快速响应市场变化')
        strategies.append('加强客户关系管理，提高续约率')
        
        return strategies
    
    def _generate_executive_summary(self, market_context: Dict, product_recommendations: List, pricing_strategies: Dict) -> str:
        """生成执行摘要"""
        summary_parts = []
        
        # 市场分析总结
        trend = market_context.get('market_trend', 'stable')
        summary_parts.append(f"市场趋势: {trend}")
        
        # 产品推荐总结
        if product_recommendations:
            top_product = product_recommendations[0]
            summary_parts.append(f"首选产品: {top_product['product']['name']} (匹配度: {top_product['match_score']:.1%})")
        
        # 定价策略总结
        strategy = pricing_strategies.get('overall_strategy', {}).get('strategy', 'market_penetration')
        summary_parts.append(f"推荐策略: {strategy}")
        
        return " | ".join(summary_parts)
    
    def _calculate_overall_confidence(self, analysis_data: Dict, market_context: Dict) -> float:
        """计算整体置信度"""
        # 基于分析数据质量和市场环境确定性计算置信度
        data_quality = len(analysis_data.get('analysis_results', [])) / 10  # 假设10个文件为最佳
        data_quality = min(data_quality, 1.0)
        
        # 市场环境确定性
        market_certainty = 0.8  # 基础市场分析置信度
        
        # 综合置信度
        overall_confidence = (data_quality * 0.6 + market_certainty * 0.4)
        return round(overall_confidence, 2)
    
    def _estimate_strategy_success(self, market_context: Dict, strategy: str) -> float:
        """估算策略成功概率"""
        # 基于市场条件和策略匹配度估算成功概率
        base_probability = 0.7
        
        # 根据策略和市场条件调整
        if strategy == 'value_based_pricing' and market_context.get('price_sensitivity', {}).get('level') == 'low':
            base_probability += 0.1
        elif strategy == 'aggressive_pricing' and market_context.get('competition_intensity', {}).get('level') == 'high':
            base_probability += 0.1
        
        return min(base_probability, 0.95)