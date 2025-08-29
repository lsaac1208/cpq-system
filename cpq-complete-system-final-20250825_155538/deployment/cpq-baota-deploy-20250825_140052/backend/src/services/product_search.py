"""
产品搜索服务
实现多层次搜索策略：精确匹配 > 前缀匹配 > 全文搜索 > 模糊匹配
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy import or_, and_, text, func, desc, asc
from sqlalchemy.orm import Query
from src.models import db, Product
from src.models.search import SearchLog, SearchSuggestion

logger = logging.getLogger(__name__)


class ProductSearchService:
    """产品搜索服务类"""
    
    def __init__(self):
        self.search_weights = {
            'exact_code': 100,      # 精确代码匹配
            'exact_name': 95,       # 精确名称匹配
            'prefix_code': 90,      # 代码前缀匹配
            'prefix_name': 85,      # 名称前缀匹配
            'fulltext': 70,         # 全文搜索
            'contains_name': 60,    # 名称包含
            'contains_desc': 50,    # 描述包含
            'category_match': 40,   # 分类匹配
            'fuzzy': 30            # 模糊匹配
        }
    
    def search(self, 
               query: str, 
               filters: Optional[Dict] = None,
               sort: str = 'relevance',
               page: int = 1,
               per_page: int = 20,
               user_id: Optional[int] = None) -> Dict[str, Any]:
        """
        执行产品搜索
        
        Args:
            query: 搜索查询字符串
            filters: 过滤条件字典
            sort: 排序方式 ('relevance', 'name', 'price', 'newest')
            page: 页码
            per_page: 每页数量
            user_id: 用户ID（用于记录搜索日志）
            
        Returns:
            Dict: 搜索结果和分页信息
        """
        try:
            # 记录搜索日志
            if user_id and query:
                self._log_search(query, user_id)
            
            # 构建搜索查询
            search_query = self._build_search_query(query, filters)
            
            # 计算总数
            total = search_query.count()
            
            # 应用排序
            search_query = self._apply_sorting(search_query, sort, query)
            
            # 应用分页
            offset = (page - 1) * per_page
            products = search_query.offset(offset).limit(per_page).all()
            
            # 计算相关性分数
            results = []
            for product in products:
                relevance_score = self._calculate_relevance_score(product, query)
                product_dict = product.to_dict()
                product_dict['relevance_score'] = relevance_score
                product_dict['match_highlights'] = self._generate_highlights(product, query)
                results.append(product_dict)
            
            # 如果按相关性排序，重新排序结果
            if sort == 'relevance' and query:
                results.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return {
                'products': results,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                },
                'search_info': {
                    'query': query,
                    'total_results': total,
                    'search_time': datetime.utcnow().isoformat(),
                    'filters_applied': filters or {}
                }
            }
            
        except Exception as e:
            logger.error(f"搜索失败: {str(e)}")
            raise
    
    def _build_search_query(self, query: str, filters: Optional[Dict] = None) -> Query:
        """构建搜索查询"""
        base_query = Product.query.filter(Product.is_active == True)
        
        # 如果有搜索词，应用搜索条件
        if query and query.strip():
            query = query.strip()
            search_conditions = []
            
            # 精确匹配（代码和名称）
            search_conditions.append(Product.code == query)
            search_conditions.append(Product.name == query)
            
            # 前缀匹配
            search_conditions.append(Product.code.like(f"{query}%"))
            search_conditions.append(Product.name.like(f"{query}%"))
            
            # 包含匹配
            search_conditions.append(Product.name.like(f"%{query}%"))
            search_conditions.append(Product.description.like(f"%{query}%"))
            search_conditions.append(Product.category.like(f"%{query}%"))
            
            # 规格匹配（JSON字段）
            search_conditions.append(Product.specifications.like(f"%{query}%"))
            
            # 应用搜索条件
            base_query = base_query.filter(or_(*search_conditions))
        
        # 应用过滤器
        if filters:
            base_query = self._apply_filters(base_query, filters)
        
        return base_query
    
    def _apply_filters(self, query: Query, filters: Dict) -> Query:
        """应用过滤条件"""
        
        # 分类过滤
        if filters.get('category'):
            query = query.filter(Product.category == filters['category'])
        
        # 价格范围过滤
        if filters.get('price_min'):
            query = query.filter(Product.base_price >= filters['price_min'])
        
        if filters.get('price_max'):
            query = query.filter(Product.base_price <= filters['price_max'])
        
        # 可配置性过滤
        if filters.get('is_configurable') is not None:
            query = query.filter(Product.is_configurable == filters['is_configurable'])
        
        # 状态过滤
        if filters.get('is_active') is not None:
            query = query.filter(Product.is_active == filters['is_active'])
        
        # 关键词过滤（规格）
        if filters.get('specs'):
            for key, value in filters['specs'].items():
                # 在JSON字段中搜索特定规格
                spec_condition = Product.specifications.like(f'%"{key}"%{value}%')
                query = query.filter(spec_condition)
        
        return query
    
    def _apply_sorting(self, query: Query, sort: str, search_query: str = None) -> Query:
        """应用排序"""
        if sort == 'relevance' and search_query:
            # 相关性排序将在Python代码中处理
            return query
        elif sort == 'name':
            return query.order_by(asc(Product.name))
        elif sort == 'price':
            return query.order_by(asc(Product.base_price))
        elif sort == 'price_desc':
            return query.order_by(desc(Product.base_price))
        elif sort == 'newest':
            return query.order_by(desc(Product.created_at))
        elif sort == 'oldest':
            return query.order_by(asc(Product.created_at))
        else:
            # 默认排序
            return query.order_by(desc(Product.created_at))
    
    def _calculate_relevance_score(self, product: Product, query: str) -> int:
        """计算相关性分数"""
        if not query:
            return 50  # 默认分数
        
        query = query.lower()
        score = 0
        
        # 精确匹配
        if product.code.lower() == query:
            score += self.search_weights['exact_code']
        elif product.name.lower() == query:
            score += self.search_weights['exact_name']
        
        # 前缀匹配
        elif product.code.lower().startswith(query):
            score += self.search_weights['prefix_code']
        elif product.name.lower().startswith(query):
            score += self.search_weights['prefix_name']
        
        # 包含匹配
        elif query in product.name.lower():
            score += self.search_weights['contains_name']
        elif product.description and query in product.description.lower():
            score += self.search_weights['contains_desc']
        elif query in product.category.lower():
            score += self.search_weights['category_match']
        
        # 规格匹配
        if product.specifications:
            try:
                specs = json.loads(product.specifications)
                specs_text = json.dumps(specs).lower()
                if query in specs_text:
                    score += self.search_weights['fulltext']
            except:
                pass
        
        # 模糊匹配奖励
        if self._is_fuzzy_match(query, product.name.lower()):
            score += self.search_weights['fuzzy']
        
        return max(score, 1)  # 最小分数为1
    
    def _is_fuzzy_match(self, query: str, text: str) -> bool:
        """检查是否为模糊匹配"""
        # 简单的编辑距离检查
        if len(query) < 3:
            return False
        
        # 检查是否有共同的字符序列
        common_chars = set(query) & set(text)
        return len(common_chars) >= len(query) * 0.6
    
    def _generate_highlights(self, product: Product, query: str) -> Dict[str, str]:
        """生成搜索高亮"""
        if not query:
            return {}
        
        highlights = {}
        query_lower = query.lower()
        
        # 高亮产品名称
        if query_lower in product.name.lower():
            highlights['name'] = self._highlight_text(product.name, query)
        
        # 高亮描述
        if product.description and query_lower in product.description.lower():
            highlights['description'] = self._highlight_text(product.description, query, max_length=200)
        
        # 高亮分类
        if query_lower in product.category.lower():
            highlights['category'] = self._highlight_text(product.category, query)
        
        return highlights
    
    def _highlight_text(self, text: str, query: str, max_length: int = None) -> str:
        """添加高亮标记"""
        if not text or not query:
            return text
        
        # 如果需要截取文本
        if max_length and len(text) > max_length:
            # 找到查询词的位置
            query_pos = text.lower().find(query.lower())
            if query_pos != -1:
                start = max(0, query_pos - max_length // 3)
                end = min(len(text), start + max_length)
                text = text[start:end]
                if start > 0:
                    text = "..." + text
                if end < len(text):
                    text = text + "..."
        
        # 添加高亮标记
        pattern = re.compile(re.escape(query), re.IGNORECASE)
        return pattern.sub(f'<mark>\\g<0></mark>', text)
    
    def get_search_suggestions(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取搜索建议"""
        if not query or len(query) < 2:
            return []
        
        suggestions = []
        
        try:
            # 产品名称建议
            name_matches = Product.query.filter(
                and_(
                    Product.is_active == True,
                    Product.name.like(f"%{query}%")
                )
            ).limit(limit // 2).all()
            
            for product in name_matches:
                suggestions.append({
                    'type': 'product',
                    'text': product.name,
                    'category': product.category,
                    'product_id': product.id,
                    'highlighted': self._highlight_text(product.name, query)
                })
            
            # 产品代码建议
            code_matches = Product.query.filter(
                and_(
                    Product.is_active == True,
                    Product.code.like(f"%{query}%")
                )
            ).limit(limit // 2).all()
            
            for product in code_matches:
                if not any(s['product_id'] == product.id for s in suggestions):
                    suggestions.append({
                        'type': 'code',
                        'text': product.code,
                        'name': product.name,
                        'category': product.category,
                        'product_id': product.id,
                        'highlighted': self._highlight_text(product.code, query)
                    })
            
            # 分类建议
            categories = db.session.query(Product.category).filter(
                and_(
                    Product.is_active == True,
                    Product.category.like(f"%{query}%")
                )
            ).distinct().limit(3).all()
            
            for category in categories:
                category_name = category[0]
                count = Product.query.filter(
                    and_(
                        Product.is_active == True,
                        Product.category == category_name
                    )
                ).count()
                
                suggestions.append({
                    'type': 'category',
                    'text': category_name,
                    'count': count,
                    'highlighted': self._highlight_text(category_name, query)
                })
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"获取搜索建议失败: {str(e)}")
            return []
    
    def get_hot_searches(self, limit: int = 10, days: int = 7) -> List[Dict[str, Any]]:
        """获取热门搜索"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            hot_searches = db.session.query(
                SearchLog.query,
                func.count(SearchLog.id).label('search_count')
            ).filter(
                and_(
                    SearchLog.created_at >= since_date,
                    SearchLog.query.isnot(None),
                    SearchLog.query != ''
                )
            ).group_by(SearchLog.query).order_by(
                desc('search_count')
            ).limit(limit).all()
            
            results = []
            for search_term, count in hot_searches:
                results.append({
                    'query': search_term,
                    'count': count,
                    'trend': 'up'  # 这里可以后续添加趋势分析
                })
            
            return results
            
        except Exception as e:
            logger.error(f"获取热门搜索失败: {str(e)}")
            return []
    
    def _log_search(self, query: str, user_id: int):
        """记录搜索日志"""
        try:
            search_log = SearchLog(
                query=query,
                user_id=user_id,
                search_time=datetime.utcnow()
            )
            search_log.save()
        except Exception as e:
            logger.warning(f"记录搜索日志失败: {str(e)}")
    
    def get_search_stats(self, days: int = 30) -> Dict[str, Any]:
        """获取搜索统计信息"""
        try:
            since_date = datetime.utcnow() - timedelta(days=days)
            
            # 总搜索次数
            total_searches = SearchLog.query.filter(
                SearchLog.created_at >= since_date
            ).count()
            
            # 无结果搜索
            no_result_searches = SearchLog.query.filter(
                and_(
                    SearchLog.created_at >= since_date,
                    SearchLog.result_count == 0
                )
            ).count()
            
            # 平均搜索结果数
            avg_results = db.session.query(
                func.avg(SearchLog.result_count)
            ).filter(
                SearchLog.created_at >= since_date
            ).scalar() or 0
            
            return {
                'period_days': days,
                'total_searches': total_searches,
                'no_result_searches': no_result_searches,
                'no_result_rate': no_result_searches / max(total_searches, 1) * 100,
                'average_results': round(float(avg_results), 2)
            }
            
        except Exception as e:
            logger.error(f"获取搜索统计失败: {str(e)}")
            return {}


class BatchSearchService:
    """批量搜索服务类"""
    
    def __init__(self):
        self.search_service = ProductSearchService()
        self.max_batch_size = 1000
        self.default_results_per_query = 5
    
    def batch_search(self, queries: List[str], 
                    options: Optional[Dict] = None,
                    user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        批量搜索产品
        
        Args:
            queries: 搜索查询列表
            options: 搜索选项
            user_id: 用户ID
            
        Returns:
            List: 批量搜索结果
        """
        if not queries:
            return []
        
        if len(queries) > self.max_batch_size:
            raise ValueError(f"批量搜索数量不能超过 {self.max_batch_size}")
        
        options = options or {}
        results_per_query = options.get('per_query', self.default_results_per_query)
        filters = options.get('filters', {})
        
        results = []
        
        for i, query in enumerate(queries):
            try:
                # 执行单个搜索
                search_result = self.search_service.search(
                    query=query.strip() if query else '',
                    filters=filters,
                    per_page=results_per_query,
                    page=1,
                    user_id=user_id
                )
                
                results.append({
                    'index': i,
                    'query': query,
                    'success': True,
                    'results': search_result['products'],
                    'total_found': search_result['pagination']['total'],
                    'timestamp': datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                logger.error(f"批量搜索第 {i} 项失败: {str(e)}")
                results.append({
                    'index': i,
                    'query': query,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        return results
    
    def search_from_file_data(self, file_data: List[Dict], 
                             query_field: str = 'query',
                             options: Optional[Dict] = None,
                             user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        从文件数据执行批量搜索
        
        Args:
            file_data: 文件解析后的数据列表
            query_field: 搜索查询字段名
            options: 搜索选项
            user_id: 用户ID
            
        Returns:
            List: 批量搜索结果
        """
        queries = []
        metadata = []
        
        for row in file_data:
            query = row.get(query_field, '').strip()
            queries.append(query)
            metadata.append(row)
        
        # 执行批量搜索
        search_results = self.batch_search(queries, options, user_id)
        
        # 合并元数据
        for i, result in enumerate(search_results):
            if i < len(metadata):
                result['metadata'] = metadata[i]
        
        return search_results