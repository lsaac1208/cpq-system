# -*- coding: utf-8 -*-
"""
AI服务管理器
提供AI服务的连接池管理、请求队列、降级服务和负载均衡功能
"""
import time
import logging
import threading
from typing import Dict, Any, Optional, List, Callable
from queue import Queue, Empty
from collections import deque
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import random

logger = logging.getLogger(__name__)

class ServiceStatus(Enum):
    """服务状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"

@dataclass
class RequestContext:
    """请求上下文"""
    request_id: str
    user_id: int
    priority: int  # 1-10, 10为最高优先级
    timeout: float
    created_at: float
    file_size: int
    file_type: str
    callback: Optional[Callable] = None

class AIServiceManager:
    """AI服务管理器"""
    
    def __init__(self, max_concurrent_requests: int = 3, queue_size: int = 50):
        self.max_concurrent_requests = max_concurrent_requests
        self.queue_size = queue_size
        
        # 请求队列和处理
        self.request_queue = Queue(maxsize=queue_size)
        self.processing_requests = {}  # request_id -> context
        self.completed_requests = deque(maxlen=100)  # 完成的请求历史
        
        # 服务状态管理
        self.service_status = ServiceStatus.HEALTHY
        self.last_health_check = time.time()
        self.health_check_interval = 60  # 60秒
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
        
        # 性能统计
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'queued_requests': 0,
            'dropped_requests': 0,
            'avg_processing_time': 0,
            'max_processing_time': 0,
            'min_processing_time': float('inf')
        }
        
        # 降级服务配置
        self.degradation_thresholds = {
            'queue_size_warning': 30,      # 队列长度警告阈值
            'queue_size_critical': 45,     # 队列长度危险阈值
            'avg_time_warning': 60.0,      # 平均处理时间警告阈值
            'avg_time_critical': 120.0,    # 平均处理时间危险阈值
            'failure_rate_warning': 20.0,  # 失败率警告阈值
            'failure_rate_critical': 50.0  # 失败率危险阈值
        }
        
        # 线程控制
        self._lock = threading.Lock()
        self._shutdown = False
        
        # 启动工作线程
        self._start_worker_threads()
        
        logger.info(f"AI服务管理器初始化完成，最大并发: {max_concurrent_requests}, 队列大小: {queue_size}")
    
    def submit_analysis_request(self, context: RequestContext) -> bool:
        """
        提交AI分析请求
        
        Args:
            context: 请求上下文
            
        Returns:
            bool: 是否成功添加到队列
        """
        with self._lock:
            self.stats['total_requests'] += 1
            
            # 检查队列是否已满
            if self.request_queue.full():
                # 根据优先级决定是否丢弃请求
                if context.priority >= 8:  # 高优先级请求
                    # 尝试丢弃低优先级的请求
                    if self._try_drop_low_priority_request():
                        logger.info(f"为高优先级请求 {context.request_id} 腾出队列空间")
                    else:
                        logger.warning(f"队列已满，丢弃高优先级请求: {context.request_id}")
                        self.stats['dropped_requests'] += 1
                        return False
                else:
                    logger.warning(f"队列已满，丢弃请求: {context.request_id}")
                    self.stats['dropped_requests'] += 1
                    return False
            
            # 检查服务状态
            if self.service_status == ServiceStatus.UNAVAILABLE:
                logger.error(f"AI服务不可用，拒绝请求: {context.request_id}")
                self.stats['failed_requests'] += 1
                return False
            
            # 添加到队列
            try:
                self.request_queue.put(context, block=False)
                self.stats['queued_requests'] += 1
                logger.info(f"请求已加入队列: {context.request_id}, 优先级: {context.priority}, 队列长度: {self.request_queue.qsize()}")
                return True
            except:
                logger.error(f"添加请求到队列失败: {context.request_id}")
                self.stats['failed_requests'] += 1
                return False
    
    def _try_drop_low_priority_request(self) -> bool:
        """尝试丢弃低优先级请求"""
        # 这里简化实现，实际可以维护一个优先级队列
        # 当前只是记录尝试，实际的队列重排需要更复杂的数据结构
        return False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        with self._lock:
            queue_size = self.request_queue.qsize()
            processing_count = len(self.processing_requests)
            
            # 计算失败率
            total = self.stats['total_requests']
            failed = self.stats['failed_requests']
            failure_rate = (failed / total * 100) if total > 0 else 0
            
            return {
                'queue_size': queue_size,
                'processing_count': processing_count,
                'max_concurrent': self.max_concurrent_requests,
                'service_status': self.service_status.value,
                'stats': {
                    **self.stats,
                    'failure_rate': round(failure_rate, 2),
                    'queue_utilization': round(queue_size / self.queue_size * 100, 1),
                    'processing_utilization': round(processing_count / self.max_concurrent_requests * 100, 1)
                },
                'last_health_check': datetime.fromtimestamp(self.last_health_check).isoformat(),
                'consecutive_failures': self.consecutive_failures
            }
    
    def get_processing_requests(self) -> List[Dict[str, Any]]:
        """获取正在处理的请求信息"""
        with self._lock:
            requests_info = []
            current_time = time.time()
            
            for request_id, context in self.processing_requests.items():
                processing_time = current_time - context.created_at
                requests_info.append({
                    'request_id': request_id,
                    'user_id': context.user_id,
                    'priority': context.priority,
                    'processing_time': round(processing_time, 2),
                    'timeout': context.timeout,
                    'file_size': context.file_size,
                    'file_type': context.file_type,
                    'status': 'processing'
                })
            
            return requests_info
    
    def _start_worker_threads(self):
        """启动工作线程"""
        for i in range(self.max_concurrent_requests):
            thread = threading.Thread(target=self._worker_loop, args=(i,), daemon=True)
            thread.start()
            logger.info(f"启动AI服务工作线程 {i}")
    
    def _worker_loop(self, worker_id: int):
        """工作线程循环"""
        logger.info(f"AI服务工作线程 {worker_id} 开始运行")
        
        while not self._shutdown:
            try:
                # 从队列获取请求
                context = self.request_queue.get(timeout=1.0)
                
                # 检查请求是否超时
                current_time = time.time()
                if current_time - context.created_at > context.timeout:
                    logger.warning(f"请求超时，丢弃: {context.request_id}")
                    self.stats['failed_requests'] += 1
                    continue
                
                # 开始处理请求
                with self._lock:
                    self.processing_requests[context.request_id] = context
                
                logger.info(f"工作线程 {worker_id} 开始处理请求: {context.request_id}")
                
                # 实际处理请求（这里需要调用AI分析服务）
                success = self._process_request(context, worker_id)
                
                # 更新统计
                processing_time = time.time() - context.created_at
                with self._lock:
                    if context.request_id in self.processing_requests:
                        del self.processing_requests[context.request_id]
                    
                    if success:
                        self.stats['successful_requests'] += 1
                        self.consecutive_failures = 0
                    else:
                        self.stats['failed_requests'] += 1
                        self.consecutive_failures += 1
                    
                    # 更新处理时间统计
                    self._update_processing_time_stats(processing_time)
                    
                    # 添加到完成历史
                    self.completed_requests.append({
                        'request_id': context.request_id,
                        'user_id': context.user_id,
                        'processing_time': processing_time,
                        'success': success,
                        'completed_at': time.time(),
                        'worker_id': worker_id
                    })
                
                # 检查是否需要更新服务状态
                self._update_service_status()
                
            except Empty:
                # 队列为空，继续循环
                continue
            except Exception as e:
                logger.error(f"工作线程 {worker_id} 处理请求时出错: {str(e)}")
                if 'context' in locals():
                    with self._lock:
                        if context.request_id in self.processing_requests:
                            del self.processing_requests[context.request_id]
                        self.stats['failed_requests'] += 1
                        self.consecutive_failures += 1
    
    def _process_request(self, context: RequestContext, worker_id: int) -> bool:
        """
        处理单个请求
        
        Args:
            context: 请求上下文
            worker_id: 工作线程ID
            
        Returns:
            bool: 处理是否成功
        """
        try:
            # 这里应该调用实际的AI分析服务
            # 为了演示，我们模拟处理时间
            
            # 根据文件大小和服务状态模拟处理时间
            base_time = min(context.file_size / 100000, 10)  # 基础时间，最大10秒
            
            if self.service_status == ServiceStatus.DEGRADED:
                base_time *= 1.5  # 降级状态下处理时间增加50%
            
            # 添加随机因素
            processing_time = base_time + random.uniform(1, 5)
            
            logger.info(f"模拟处理请求 {context.request_id}，预计耗时: {processing_time:.2f}s")
            time.sleep(processing_time)
            
            # 模拟成功率（根据服务状态）
            if self.service_status == ServiceStatus.HEALTHY:
                success_rate = 0.95
            elif self.service_status == ServiceStatus.DEGRADED:
                success_rate = 0.80
            else:
                success_rate = 0.20
            
            success = random.random() < success_rate
            
            if success:
                logger.info(f"请求处理成功: {context.request_id}")
            else:
                logger.warning(f"请求处理失败: {context.request_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"处理请求 {context.request_id} 时出错: {str(e)}")
            return False
    
    def _update_processing_time_stats(self, processing_time: float):
        """更新处理时间统计"""
        total_requests = self.stats['successful_requests'] + self.stats['failed_requests']
        if total_requests > 0:
            # 更新平均处理时间
            current_avg = self.stats['avg_processing_time']
            self.stats['avg_processing_time'] = (current_avg * (total_requests - 1) + processing_time) / total_requests
        
        # 更新最大和最小处理时间
        self.stats['max_processing_time'] = max(self.stats['max_processing_time'], processing_time)
        self.stats['min_processing_time'] = min(self.stats['min_processing_time'], processing_time)
    
    def _update_service_status(self):
        """更新服务状态"""
        current_time = time.time()
        
        # 定期进行健康检查
        if current_time - self.last_health_check > self.health_check_interval:
            self._perform_health_check()
            self.last_health_check = current_time
        
        # 根据统计数据调整服务状态
        queue_size = self.request_queue.qsize()
        avg_time = self.stats['avg_processing_time']
        
        # 计算失败率
        total = self.stats['successful_requests'] + self.stats['failed_requests']
        failure_rate = (self.stats['failed_requests'] / total * 100) if total > 0 else 0
        
        # 确定新的服务状态
        new_status = ServiceStatus.HEALTHY
        
        # 检查关键指标
        if (self.consecutive_failures >= self.max_consecutive_failures or
            queue_size >= self.degradation_thresholds['queue_size_critical'] or
            avg_time >= self.degradation_thresholds['avg_time_critical'] or
            failure_rate >= self.degradation_thresholds['failure_rate_critical']):
            new_status = ServiceStatus.UNAVAILABLE
        elif (queue_size >= self.degradation_thresholds['queue_size_warning'] or
              avg_time >= self.degradation_thresholds['avg_time_warning'] or
              failure_rate >= self.degradation_thresholds['failure_rate_warning']):
            new_status = ServiceStatus.DEGRADED
        
        # 更新状态
        if new_status != self.service_status:
            old_status = self.service_status
            self.service_status = new_status
            logger.warning(f"AI服务状态变更: {old_status.value} -> {new_status.value}")
            
            # 根据状态变更调整策略
            if new_status == ServiceStatus.DEGRADED:
                logger.info("服务进入降级模式，将采用简化处理策略")
            elif new_status == ServiceStatus.UNAVAILABLE:
                logger.error("服务不可用，将拒绝新请求")
            elif new_status == ServiceStatus.HEALTHY:
                logger.info("服务恢复正常")
    
    def _perform_health_check(self):
        """执行健康检查"""
        try:
            # 这里可以添加实际的健康检查逻辑
            # 例如：调用AI服务的健康检查端点
            
            # 简化的健康检查：检查是否有工作线程在正常工作
            active_workers = len(self.processing_requests)
            queue_size = self.request_queue.qsize()
            
            logger.info(f"健康检查 - 活跃工作线程: {active_workers}, 队列长度: {queue_size}")
            
            # 如果有积压但没有工作线程在处理，可能有问题
            if queue_size > 0 and active_workers == 0:
                logger.warning("检测到队列积压但无活跃工作线程，可能存在问题")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            return False
    
    def get_service_recommendations(self) -> List[str]:
        """获取服务优化建议"""
        recommendations = []
        
        # 分析当前状态并给出建议
        queue_size = self.request_queue.qsize()
        avg_time = self.stats['avg_processing_time']
        
        if queue_size > self.degradation_thresholds['queue_size_warning']:
            recommendations.append(f"队列积压严重 ({queue_size}个请求)，建议增加并发处理能力或优化处理逻辑")
        
        if avg_time > self.degradation_thresholds['avg_time_warning']:
            recommendations.append(f"平均处理时间过长 ({avg_time:.2f}s)，建议优化AI模型或增加缓存")
        
        total = self.stats['successful_requests'] + self.stats['failed_requests']
        if total > 0:
            failure_rate = self.stats['failed_requests'] / total * 100
            if failure_rate > self.degradation_thresholds['failure_rate_warning']:
                recommendations.append(f"失败率过高 ({failure_rate:.1f}%)，建议检查AI服务稳定性")
        
        if self.consecutive_failures > 1:
            recommendations.append(f"连续失败 {self.consecutive_failures} 次，建议检查AI服务配置")
        
        if not recommendations:
            recommendations.append("服务运行正常，无需特殊优化")
        
        return recommendations
    
    def shutdown(self):
        """关闭服务管理器"""
        self._shutdown = True
        logger.info("AI服务管理器正在关闭...")

# 全局AI服务管理器实例
ai_service_manager = AIServiceManager()