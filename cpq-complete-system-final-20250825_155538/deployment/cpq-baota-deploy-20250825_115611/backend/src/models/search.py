from .base import db, BaseModel
from datetime import datetime
import json


class SearchLog(BaseModel):
    """搜索日志记录模型"""
    
    __tablename__ = 'search_logs'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    query = db.Column(db.String(500), nullable=False)
    filters = db.Column(db.Text)  # JSON格式的搜索过滤条件
    result_count = db.Column(db.Integer, default=0)  # 匹配服务中使用的字段名
    clicked_product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    search_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # 建立关系
    user = db.relationship('User', backref='search_histories')
    clicked_product = db.relationship('Product', backref='search_clicks')
    
    def get_filters(self):
        """获取搜索过滤条件字典"""
        if self.filters:
            return json.loads(self.filters)
        return {}
    
    def set_filters(self, filters_dict):
        """设置搜索过滤条件"""
        self.filters = json.dumps(filters_dict)
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data['filters'] = self.get_filters()
        return data
    
    def __repr__(self):
        return f'<SearchLog {self.user_id}: {self.query}>'


class PopularSearch(BaseModel):
    """热门搜索统计模型"""
    
    __tablename__ = 'popular_searches'
    
    query = db.Column(db.String(500), unique=True, nullable=False)
    search_count = db.Column(db.Integer, default=1, nullable=False)
    click_count = db.Column(db.Integer, default=0, nullable=False)
    last_searched = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # 计算点击率
    @property
    def click_rate(self):
        """计算点击率"""
        if self.search_count == 0:
            return 0.0
        return round(self.click_count / self.search_count, 2)
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data['click_rate'] = self.click_rate
        return data
    
    def __repr__(self):
        return f'<PopularSearch {self.query}: {self.search_count}>'


class SearchSuggestion(BaseModel):
    """搜索建议模型"""
    
    __tablename__ = 'search_suggestions'
    
    term = db.Column(db.String(200), unique=True, nullable=False)
    category = db.Column(db.String(100))  # 建议的分类
    source_type = db.Column(db.String(50), nullable=False)  # 来源类型: product_name, product_code, category, manual
    source_id = db.Column(db.Integer)  # 来源ID（如产品ID）
    weight = db.Column(db.Integer, default=1)  # 权重，用于排序
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    def to_dict(self):
        """转换为字典"""
        return super().to_dict()
    
    def __repr__(self):
        return f'<SearchSuggestion {self.term}: {self.source_type}>'


class SearchAnalytics(BaseModel):
    """搜索分析统计模型"""
    
    __tablename__ = 'search_analytics'
    
    date = db.Column(db.Date, nullable=False)
    total_searches = db.Column(db.Integer, default=0)
    unique_users = db.Column(db.Integer, default=0)
    no_results_count = db.Column(db.Integer, default=0)  # 无结果搜索次数
    avg_results_per_search = db.Column(db.Float, default=0.0)
    top_categories = db.Column(db.Text)  # JSON格式的热门分类统计
    
    # 添加唯一约束
    __table_args__ = (db.UniqueConstraint('date', name='unique_date'),)
    
    def get_top_categories(self):
        """获取热门分类统计"""
        if self.top_categories:
            return json.loads(self.top_categories)
        return {}
    
    def set_top_categories(self, categories_dict):
        """设置热门分类统计"""
        self.top_categories = json.dumps(categories_dict)
    
    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data['top_categories'] = self.get_top_categories()
        return data
    
    def __repr__(self):
        return f'<SearchAnalytics {self.date}: {self.total_searches} searches>'