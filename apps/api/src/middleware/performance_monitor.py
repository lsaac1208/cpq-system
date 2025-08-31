# -*- coding: utf-8 -*-
"""
性能监控中间件
提供请求性能监控、资源使用监控和健康检查功能
"""
import time
import logging
import threading
from typing import Dict, Any, Optional
from functools import wraps
from flask import request, g, current_app, jsonify
import gc
from collections import deque, defaultdict
from datetime import datetime, timedelta

# Optional import for system monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available - system metrics monitoring disabled")

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.request_metrics = deque(maxlen=1000)  # 保持最近1000个请求的指标
        self.ai_analysis_metrics = deque(maxlen=100)  # AI分析专用指标
        self.endpoint_stats = defaultdict(lambda: {
            'count': 0,
            'total_time': 0,
            'avg_time': 0,
            'max_time': 0,
            'min_time': float('inf'),
            'error_count': 0,
            'last_error': None
        })
        self.system_metrics = {
            'cpu_usage': [],
            'memory_usage': [],
            'disk_usage': [],
            'connections': [],
            'timestamp': []
        }
        self.alerts = deque(maxlen=50)  # 警告信息
        self.start_time = time.time()
        self._lock = threading.Lock()
        
        # 性能阈值配置
        self.thresholds = {
            'request_time_warning': 5.0,      # 请求时间警告阈值
            'request_time_critical': 15.0,    # 请求时间危险阈值
            'ai_analysis_time_warning': 60.0, # AI分析时间警告阈值
            'ai_analysis_time_critical': 120.0, # AI分析时间危险阈值
            'memory_usage_warning': 80.0,     # 内存使用警告阈值
            'memory_usage_critical': 90.0,    # 内存使用危险阈值
            'cpu_usage_warning': 80.0,        # CPU使用警告阈值
            'cpu_usage_critical': 95.0,       # CPU使用危险阈值
            'error_rate_warning': 5.0,        # 错误率警告阈值
            'error_rate_critical': 10.0       # 错误率危险阈值
        }
        
        logger.info("性能监控器初始化完成")
    
    def record_request(self, endpoint: str, method: str, duration: float, 
                      status_code: int, error_msg: Optional[str] = None):
        """记录请求指标"""
        with self._lock:
            # 记录请求指标
            metric = {
                'endpoint': endpoint,
                'method': method,
                'duration': duration,
                'status_code': status_code,
                'timestamp': time.time(),
                'error': error_msg,
                'is_ai_analysis': '/ai-analysis/' in endpoint
            }
            self.request_metrics.append(metric)
            
            # 更新端点统计
            key = f"{method} {endpoint}"
            stats = self.endpoint_stats[key]
            stats['count'] += 1
            stats['total_time'] += duration
            stats['avg_time'] = stats['total_time'] / stats['count']
            stats['max_time'] = max(stats['max_time'], duration)
            stats['min_time'] = min(stats['min_time'], duration)
            
            if status_code >= 400:
                stats['error_count'] += 1
                stats['last_error'] = error_msg
            
            # AI分析专用指标
            if metric['is_ai_analysis']:
                self.ai_analysis_metrics.append(metric)
            
            # 检查性能阈值
            self._check_performance_thresholds(metric)
    
    def _check_performance_thresholds(self, metric: Dict[str, Any]):
        """检查性能阈值并生成警告"""
        duration = metric['duration']
        endpoint = metric['endpoint']
        
        # 检查请求时间阈值
        if metric['is_ai_analysis']:
            if duration > self.thresholds['ai_analysis_time_critical']:
                self._add_alert('critical', f"AI分析超时严重: {endpoint} 耗时 {duration:.2f}s")
            elif duration > self.thresholds['ai_analysis_time_warning']:
                self._add_alert('warning', f"AI分析耗时较长: {endpoint} 耗时 {duration:.2f}s")
        else:
            if duration > self.thresholds['request_time_critical']:
                self._add_alert('critical', f"请求响应严重超时: {endpoint} 耗时 {duration:.2f}s")
            elif duration > self.thresholds['request_time_warning']:
                self._add_alert('warning', f"请求响应较慢: {endpoint} 耗时 {duration:.2f}s")
        
        # 检查错误率
        if metric['status_code'] >= 500:
            self._add_alert('error', f"服务器错误: {endpoint} 返回 {metric['status_code']}")
    
    def record_system_metrics(self):
        """记录系统指标"""
        if not PSUTIL_AVAILABLE:
            # 如果 psutil 不可用，记录基本时间戳
            with self._lock:
                timestamp = time.time()
                self.system_metrics['timestamp'].append(timestamp)
                # 保持最近100个数据点
                max_points = 100
                for key in self.system_metrics:
                    if len(self.system_metrics[key]) > max_points:
                        self.system_metrics[key] = self.system_metrics[key][-max_points:]
            return
        
        try:
            with self._lock:
                # CPU使用率 - 捕获具体异常
                try:
                    cpu_percent = psutil.cpu_percent(interval=None)
                except Exception as cpu_err:
                    logger.debug(f"CPU指标收集失败: {cpu_err}")
                    cpu_percent = 0.0
                
                # 内存使用率
                try:
                    memory = psutil.virtual_memory()
                    memory_percent = memory.percent
                except Exception as mem_err:
                    logger.debug(f"内存指标收集失败: {mem_err}")
                    memory_percent = 0.0
                
                # 磁盘使用率
                try:
                    disk = psutil.disk_usage('/')
                    disk_percent = disk.percent
                except Exception as disk_err:
                    logger.debug(f"磁盘指标收集失败: {disk_err}")
                    disk_percent = 0.0
                
                # 网络连接数 - 这个可能有权限问题
                try:
                    connections = len(psutil.net_connections())
                except Exception as net_err:
                    logger.debug(f"网络连接指标收集失败: {net_err}")
                    connections = 0
                
                timestamp = time.time()
                
                # 记录指标
                self.system_metrics['cpu_usage'].append(cpu_percent)
                self.system_metrics['memory_usage'].append(memory_percent)
                self.system_metrics['disk_usage'].append(disk_percent)
                self.system_metrics['connections'].append(connections)
                self.system_metrics['timestamp'].append(timestamp)
                
                # 保持最近100个数据点
                max_points = 100
                for key in self.system_metrics:
                    if len(self.system_metrics[key]) > max_points:
                        self.system_metrics[key] = self.system_metrics[key][-max_points:]
                
                # 检查系统阈值（仅在有有效数据时）
                if memory_percent > 0:
                    if memory_percent > self.thresholds['memory_usage_critical']:
                        self._add_alert('critical', f"内存使用率危险: {memory_percent:.1f}%")
                    elif memory_percent > self.thresholds['memory_usage_warning']:
                        self._add_alert('warning', f"内存使用率较高: {memory_percent:.1f}%")
                
                if cpu_percent > 0:
                    if cpu_percent > self.thresholds['cpu_usage_critical']:
                        self._add_alert('critical', f"CPU使用率危险: {cpu_percent:.1f}%")
                    elif cpu_percent > self.thresholds['cpu_usage_warning']:
                        self._add_alert('warning', f"CPU使用率较高: {cpu_percent:.1f}%")
                
        except Exception as e:
            # 减少日志级别，避免大量错误日志
            logger.debug(f"记录系统指标失败: {str(e)}")
    
    def _add_alert(self, level: str, message: str):
        """添加警告"""
        alert = {
            'level': level,
            'message': message,
            'timestamp': time.time(),
            'datetime': datetime.now().isoformat()
        }
        self.alerts.append(alert)
        
        # 记录到日志
        if level == 'critical':
            logger.error(f"性能警告[{level.upper()}]: {message}")
        elif level == 'warning':
            logger.warning(f"性能警告[{level.upper()}]: {message}")
        else:
            logger.info(f"性能信息[{level.upper()}]: {message}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        with self._lock:
            now = time.time()
            uptime = now - self.start_time
            
            # 基础统计
            total_requests = len(self.request_metrics)
            ai_requests = len(self.ai_analysis_metrics)
            
            # 计算平均响应时间
            if total_requests > 0:
                avg_response_time = sum(m['duration'] for m in self.request_metrics) / total_requests
                
                # 最近5分钟的请求
                recent_threshold = now - 300  # 5分钟前
                recent_requests = [m for m in self.request_metrics if m['timestamp'] > recent_threshold]
                recent_avg = sum(m['duration'] for m in recent_requests) / len(recent_requests) if recent_requests else 0
                
                # 错误率
                error_count = sum(1 for m in self.request_metrics if m['status_code'] >= 400)
                error_rate = (error_count / total_requests) * 100 if total_requests > 0 else 0
            else:
                avg_response_time = 0
                recent_avg = 0
                error_rate = 0
            
            # AI分析统计
            if ai_requests > 0:
                ai_avg_time = sum(m['duration'] for m in self.ai_analysis_metrics) / ai_requests
                ai_success_rate = sum(1 for m in self.ai_analysis_metrics if m['status_code'] < 400) / ai_requests * 100
            else:
                ai_avg_time = 0
                ai_success_rate = 0
            
            # 系统资源 (仅在 psutil 可用时)
            if PSUTIL_AVAILABLE:
                current_cpu = self.system_metrics['cpu_usage'][-1] if self.system_metrics['cpu_usage'] else 0
                current_memory = self.system_metrics['memory_usage'][-1] if self.system_metrics['memory_usage'] else 0
                current_connections = self.system_metrics['connections'][-1] if self.system_metrics['connections'] else 0
            else:
                current_cpu = 0
                current_memory = 0
                current_connections = 0
            
            # 最近的警告
            recent_alerts = [a for a in self.alerts if now - a['timestamp'] < 3600]  # 最近1小时
            critical_alerts = [a for a in recent_alerts if a['level'] == 'critical']
            
            return {
                'uptime_seconds': uptime,
                'uptime_human': self._format_uptime(uptime),
                'requests': {
                    'total': total_requests,
                    'ai_analysis': ai_requests,
                    'avg_response_time': round(avg_response_time, 3),
                    'recent_avg_response_time': round(recent_avg, 3),
                    'error_rate': round(error_rate, 2)
                },
                'ai_analysis': {
                    'count': ai_requests,
                    'avg_time': round(ai_avg_time, 2),
                    'success_rate': round(ai_success_rate, 2)
                },
                'system': {
                    'cpu_usage': round(current_cpu, 1),
                    'memory_usage': round(current_memory, 1),
                    'connections': current_connections
                },
                'alerts': {
                    'total': len(recent_alerts),
                    'critical': len(critical_alerts),
                    'recent': list(recent_alerts)[-5:]  # 最近5个警告
                },
                'health_status': self._calculate_health_status()
            }
    
    def get_detailed_metrics(self) -> Dict[str, Any]:
        """获取详细指标"""
        with self._lock:
            return {
                'endpoint_stats': dict(self.endpoint_stats),
                'system_metrics': {
                    'cpu_usage': self.system_metrics['cpu_usage'][-20:],  # 最近20个点
                    'memory_usage': self.system_metrics['memory_usage'][-20:],
                    'disk_usage': self.system_metrics['disk_usage'][-20:],
                    'connections': self.system_metrics['connections'][-20:],
                    'timestamps': self.system_metrics['timestamp'][-20:]
                },
                'recent_requests': list(self.request_metrics)[-50:],  # 最近50个请求
                'ai_analysis_metrics': list(self.ai_analysis_metrics)[-20:],  # 最近20个AI分析
                'alerts': list(self.alerts)[-20:],  # 最近20个警告
                'thresholds': self.thresholds
            }
    
    def _calculate_health_status(self) -> str:
        """计算健康状态"""
        # 检查最近的关键警告
        now = time.time()
        recent_critical = [a for a in self.alerts if a['level'] == 'critical' and now - a['timestamp'] < 300]
        
        if recent_critical:
            return 'critical'
        
        # 检查系统资源 (仅在 psutil 可用时)
        if PSUTIL_AVAILABLE and self.system_metrics['memory_usage']:
            current_memory = self.system_metrics['memory_usage'][-1]
            current_cpu = self.system_metrics['cpu_usage'][-1] if self.system_metrics['cpu_usage'] else 0
            
            if current_memory > self.thresholds['memory_usage_critical'] or current_cpu > self.thresholds['cpu_usage_critical']:
                return 'critical'
            elif current_memory > self.thresholds['memory_usage_warning'] or current_cpu > self.thresholds['cpu_usage_warning']:
                return 'warning'
        
        # 检查错误率
        if self.request_metrics:
            recent_requests = [m for m in self.request_metrics if now - m['timestamp'] < 300]
            if recent_requests:
                error_rate = sum(1 for m in recent_requests if m['status_code'] >= 400) / len(recent_requests) * 100
                if error_rate > self.thresholds['error_rate_critical']:
                    return 'critical'
                elif error_rate > self.thresholds['error_rate_warning']:
                    return 'warning'
        
        return 'healthy'
    
    def _format_uptime(self, seconds: float) -> str:
        """格式化运行时间"""
        days = int(seconds // 86400)
        hours = int((seconds % 86400) // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {secs}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"
    
    def force_garbage_collection(self):
        """强制垃圾回收"""
        collected = gc.collect()
        logger.info(f"强制垃圾回收完成，回收对象数: {collected}")
        return collected

# 全局性能监控实例
performance_monitor = PerformanceMonitor()

def monitor_performance(f):
    """性能监控装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        error_msg = None
        status_code = 200
        
        try:
            # 记录请求开始时间
            g.start_time = start_time
            
            # 执行原函数
            result = f(*args, **kwargs)
            
            # 检查返回结果的状态码
            if hasattr(result, 'status_code'):
                status_code = result.status_code
            elif isinstance(result, tuple) and len(result) >= 2:
                status_code = result[1]
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            status_code = 500
            raise
            
        finally:
            # 记录性能指标
            duration = time.time() - start_time
            endpoint = request.endpoint or request.path
            method = request.method
            
            performance_monitor.record_request(
                endpoint=endpoint,
                method=method,
                duration=duration,
                status_code=status_code,
                error_msg=error_msg
            )
    
    return decorated_function

def init_performance_monitoring(app):
    """初始化性能监控"""
    
    @app.before_request
    def before_request():
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        # 记录请求性能
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            endpoint = request.endpoint or request.path
            method = request.method
            
            performance_monitor.record_request(
                endpoint=endpoint,
                method=method,
                duration=duration,
                status_code=response.status_code
            )
        
        return response
    
    # 添加性能监控端点
    @app.route('/api/v1/system/performance', methods=['GET'])
    def get_performance_summary():
        """获取性能摘要"""
        try:
            summary = performance_monitor.get_performance_summary()
            return jsonify({
                'success': True,
                'data': summary
            })
        except Exception as e:
            logger.error(f"获取性能摘要失败: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/v1/system/metrics', methods=['GET'])
    def get_detailed_metrics():
        """获取详细指标"""
        try:
            metrics = performance_monitor.get_detailed_metrics()
            return jsonify({
                'success': True,
                'data': metrics
            })
        except Exception as e:
            logger.error(f"获取详细指标失败: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/v1/system/health', methods=['GET'])
    def health_check():
        """健康检查端点"""
        try:
            # 记录系统指标
            performance_monitor.record_system_metrics()
            
            # 获取健康状态
            summary = performance_monitor.get_performance_summary()
            health_status = summary['health_status']
            
            # 进行内存管理
            if summary['system']['memory_usage'] > 85:
                collected = performance_monitor.force_garbage_collection()
                logger.info(f"高内存使用触发垃圾回收: {collected}")
            
            return jsonify({
                'status': health_status,
                'timestamp': datetime.now().isoformat(),
                'uptime': summary['uptime_human'],
                'system': summary['system'],
                'requests': summary['requests'],
                'ai_analysis': summary['ai_analysis'],
                'alerts_count': summary['alerts']['total']
            })
            
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return jsonify({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
    
    # 启动后台任务定期记录系统指标
    import threading
    
    def record_metrics_periodically():
        import time
        while True:
            try:
                performance_monitor.record_system_metrics()
                time.sleep(30)  # 每30秒记录一次
            except Exception as e:
                logger.error(f"定期记录系统指标失败: {str(e)}")
                time.sleep(60)  # 出错时等待更长时间
    
    thread = threading.Thread(target=record_metrics_periodically, daemon=True)
    thread.start()
    
    logger.info("性能监控系统初始化完成")