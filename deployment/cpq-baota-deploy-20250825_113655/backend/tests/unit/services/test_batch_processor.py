#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理器服务单元测试
覆盖批量处理器的所有功能
"""
import pytest
import tempfile
import time
from unittest.mock import Mock, patch, MagicMock
from src.services.batch_processor import BatchProcessor, BatchStatus, BatchJob
from src.services.ai_analyzer import AIAnalyzer


class TestBatchProcessor:
    """测试BatchProcessor服务"""

    @pytest.fixture
    def batch_processor(self):
        """创建批量处理器实例"""
        return BatchProcessor(max_workers=2, max_concurrent_batches=2)

    @pytest.fixture
    def mock_files(self, temp_test_files):
        """创建模拟文件对象"""
        files = []
        for doc_type, file_path in temp_test_files.items():
            mock_file = Mock()
            mock_file.filename = f'{doc_type}.txt'
            mock_file.content_length = 1024
            mock_file.read.return_value = b'test content'
            with open(file_path, 'rb') as f:
                mock_file.stream = f
            files.append(mock_file)
        return files

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_batch_processor_initialization(self, batch_processor):
        """测试批量处理器初始化"""
        assert batch_processor.max_workers == 2
        assert batch_processor.max_concurrent_batches == 2
        assert len(batch_processor.active_jobs) == 0
        assert batch_processor.executor is not None

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_validate_files_success(self, batch_processor, mock_files):
        """测试文件验证成功"""
        validated_files = batch_processor._validate_files(mock_files)
        
        assert len(validated_files) == len(mock_files)
        for file_info in validated_files:
            assert 'file_id' in file_info
            assert 'filename' in file_info
            assert 'content' in file_info
            assert 'size' in file_info

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_validate_files_empty(self, batch_processor):
        """测试空文件列表验证"""
        with pytest.raises(ValueError, match="No files provided"):
            batch_processor._validate_files([])

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_validate_files_too_many(self, batch_processor):
        """测试文件数量过多"""
        # 创建超过限制的文件
        mock_files = [Mock() for _ in range(51)]
        for i, mock_file in enumerate(mock_files):
            mock_file.filename = f'file_{i}.txt'
            mock_file.content_length = 1024
        
        with pytest.raises(ValueError, match="Too many files"):
            batch_processor._validate_files(mock_files)

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_validate_files_too_large(self, batch_processor):
        """测试文件过大"""
        mock_file = Mock()
        mock_file.filename = 'large_file.txt'
        mock_file.content_length = 20 * 1024 * 1024  # 20MB
        
        with pytest.raises(ValueError, match="File too large"):
            batch_processor._validate_files([mock_file])

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_validate_files_unsupported_format(self, batch_processor):
        """测试不支持的文件格式"""
        mock_file = Mock()
        mock_file.filename = 'test.exe'  # 不支持的格式
        mock_file.content_length = 1024
        
        with pytest.raises(ValueError, match="Unsupported file format"):
            batch_processor._validate_files([mock_file])

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_create_batch_job_success(self, batch_processor, mock_files):
        """测试成功创建批量任务"""
        job_id = batch_processor.create_batch_job(
            files=mock_files,
            user_id=1,
            settings={'analysis_type': 'customer_requirements'}
        )
        
        assert job_id is not None
        assert job_id.startswith('batch_')
        assert job_id in batch_processor.active_jobs
        
        job = batch_processor.active_jobs[job_id]
        assert job.user_id == 1
        assert job.status == BatchStatus.PENDING
        assert len(job.files) == len(mock_files)

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_create_batch_job_invalid_files(self, batch_processor):
        """测试创建批量任务时文件无效"""
        with pytest.raises(ValueError):
            batch_processor.create_batch_job(
                files=[],
                user_id=1,
                settings={}
            )

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_start_batch_processing_success(self, batch_processor, mock_files):
        """测试成功启动批量处理"""
        # 创建任务
        job_id = batch_processor.create_batch_job(
            files=mock_files,
            user_id=1,
            settings={'analysis_type': 'customer_requirements'}
        )
        
        # 创建进度回调
        progress_callback = Mock()
        
        # 启动处理
        result = batch_processor.start_batch_processing(job_id, progress_callback)
        
        assert result == True
        assert job_id in batch_processor.progress_callbacks
        assert batch_processor.active_jobs[job_id].status == BatchStatus.PROCESSING

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_start_batch_processing_job_not_found(self, batch_processor):
        """测试启动不存在的任务"""
        with pytest.raises(ValueError, match="Batch job .* not found"):
            batch_processor.start_batch_processing('nonexistent_job')

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_start_batch_processing_not_pending(self, batch_processor, mock_files):
        """测试启动非待处理状态的任务"""
        # 创建任务
        job_id = batch_processor.create_batch_job(
            files=mock_files,
            user_id=1,
            settings={}
        )
        
        # 修改状态为已处理
        batch_processor.active_jobs[job_id].status = BatchStatus.PROCESSING
        
        with pytest.raises(ValueError, match="not in pending status"):
            batch_processor.start_batch_processing(job_id)

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_concurrent_batch_limit(self, batch_processor, mock_files):
        """测试并发批量限制"""
        # 创建并启动最大数量的任务
        job_ids = []
        for i in range(batch_processor.max_concurrent_batches):
            job_id = batch_processor.create_batch_job(
                files=mock_files,
                user_id=1,
                settings={}
            )
            batch_processor.start_batch_processing(job_id)
            job_ids.append(job_id)
        
        # 尝试启动第三个任务（应该失败）
        job_id_3 = batch_processor.create_batch_job(
            files=mock_files,
            user_id=1,
            settings={}
        )
        
        with pytest.raises(ValueError, match="Maximum concurrent batches"):
            batch_processor.start_batch_processing(job_id_3)

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_get_batch_status_success(self, batch_processor, mock_files):
        """测试获取批量任务状态"""
        job_id = batch_processor.create_batch_job(
            files=mock_files,
            user_id=1,
            settings={}
        )
        
        status = batch_processor.get_batch_status(job_id)
        
        assert status['job_id'] == job_id
        assert status['status'] == 'pending'
        assert status['progress_percentage'] == 0
        assert 'files_status' in status
        assert len(status['files_status']) == len(mock_files)

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_get_batch_status_not_found(self, batch_processor):
        """测试获取不存在任务的状态"""
        with pytest.raises(ValueError, match="Batch job .* not found"):
            batch_processor.get_batch_status('nonexistent_job')

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_cancel_batch_job_success(self, batch_processor, mock_files):
        """测试成功取消批量任务"""
        job_id = batch_processor.create_batch_job(
            files=mock_files,
            user_id=1,
            settings={}
        )
        
        result = batch_processor.cancel_batch_job(job_id)
        
        assert result == True
        assert batch_processor.active_jobs[job_id].status == BatchStatus.CANCELLED

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_cancel_batch_job_not_found(self, batch_processor):
        """测试取消不存在的任务"""
        result = batch_processor.cancel_batch_job('nonexistent_job')
        assert result == False

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_get_batch_results_success(self, batch_processor, mock_files):
        """测试获取批量任务结果"""
        job_id = batch_processor.create_batch_job(
            files=mock_files,
            user_id=1,
            settings={}
        )
        
        # 模拟任务完成
        job = batch_processor.active_jobs[job_id]
        job.status = BatchStatus.COMPLETED
        job.processed_files = len(mock_files)
        job.successful_files = len(mock_files)
        
        results = batch_processor.get_batch_results(job_id)
        
        assert results['job_id'] == job_id
        assert results['status'] == 'completed'
        assert results['total_files'] == len(mock_files)
        assert 'results' in results

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_get_batch_results_not_found(self, batch_processor):
        """测试获取不存在任务的结果"""
        with pytest.raises(ValueError, match="Batch job .* not found"):
            batch_processor.get_batch_results('nonexistent_job')

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_cleanup_completed_jobs(self, batch_processor, mock_files):
        """测试清理已完成的任务"""
        # 创建一个完成的任务
        job_id = batch_processor.create_batch_job(
            files=mock_files,
            user_id=1,
            settings={}
        )
        
        job = batch_processor.active_jobs[job_id]
        job.status = BatchStatus.COMPLETED
        job.end_time = time.time() - 3600  # 1小时前完成
        
        # 清理任务
        cleaned_count = batch_processor.cleanup_completed_jobs(older_than_hours=0.5)
        
        assert cleaned_count == 1
        assert job_id not in batch_processor.active_jobs

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_get_processing_statistics(self, batch_processor, mock_files):
        """测试获取处理统计"""
        # 创建一些任务
        for i in range(2):
            job_id = batch_processor.create_batch_job(
                files=mock_files,
                user_id=1,
                settings={}
            )
            if i == 0:
                # 第一个任务设为已完成
                job = batch_processor.active_jobs[job_id]
                job.status = BatchStatus.COMPLETED
                job.processed_files = len(mock_files)
                job.successful_files = len(mock_files)
        
        stats = batch_processor.get_processing_statistics()
        
        assert 'total_jobs' in stats
        assert 'active_jobs' in stats
        assert 'completed_jobs' in stats
        assert 'success_rate' in stats
        assert 'average_file_time' in stats
        assert stats['total_jobs'] == 2
        assert stats['active_jobs'] == 2  # 包括pending和completed


class TestBatchJob:
    """测试BatchJob类"""

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_batch_job_creation(self):
        """测试批量任务创建"""
        files = [
            {'file_id': 'file_1', 'filename': 'test1.txt', 'content': 'content1'},
            {'file_id': 'file_2', 'filename': 'test2.txt', 'content': 'content2'}
        ]
        
        job = BatchJob(
            job_id='test_job',
            user_id=1,
            total_files=2,
            status=BatchStatus.PENDING,
            files=files,
            settings={'analysis_type': 'customer_requirements'}
        )
        
        assert job.job_id == 'test_job'
        assert job.user_id == 1
        assert job.total_files == 2
        assert job.status == BatchStatus.PENDING
        assert len(job.files) == 2
        assert job.processed_files == 0
        assert job.successful_files == 0
        assert job.failed_files == 0

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_batch_job_progress_calculation(self):
        """测试批量任务进度计算"""
        job = BatchJob(
            job_id='progress_test',
            user_id=1,
            total_files=10,
            status=BatchStatus.PROCESSING,
            files=[],
            settings={}
        )
        
        # 更新进度
        job.processed_files = 5
        assert job.get_progress_percentage() == 50.0
        
        job.processed_files = 10
        assert job.get_progress_percentage() == 100.0
        
        # 避免除零错误
        job.total_files = 0
        assert job.get_progress_percentage() == 0.0

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_batch_job_to_dict(self):
        """测试批量任务转换为字典"""
        files = [{'file_id': 'file_1', 'filename': 'test1.txt'}]
        
        job = BatchJob(
            job_id='dict_test',
            user_id=1,
            total_files=1,
            status=BatchStatus.PROCESSING,
            files=files,
            settings={'analysis_type': 'customer_requirements'}
        )
        
        job_dict = job.to_dict()
        
        assert job_dict['job_id'] == 'dict_test'
        assert job_dict['user_id'] == 1
        assert job_dict['total_files'] == 1
        assert job_dict['status'] == 'processing'
        assert job_dict['progress_percentage'] == 0.0
        assert 'start_time' in job_dict
        assert job_dict['settings']['analysis_type'] == 'customer_requirements'


class TestBatchProcessorIntegration:
    """测试批量处理器集成功能"""

    @pytest.fixture
    def batch_processor_with_mock_analyzer(self):
        """创建带模拟分析器的批量处理器"""
        processor = BatchProcessor(max_workers=1, max_concurrent_batches=1)
        
        # 模拟AI分析器
        with patch('src.services.batch_processor.AIAnalyzer') as mock_analyzer_class:
            mock_analyzer = Mock()
            mock_analyzer.analyze_document.return_value = {
                'analysis_type': 'customer_requirements',
                'business_insights': {
                    'customer_requirements': {
                        'raw_analysis': '{"test": "result"}',
                        'risk_assessment': {'technical_risk': 'low'}
                    }
                },
                'confidence_scores': {'overall': 0.85},
                'processing_time': 10.0
            }
            mock_analyzer_class.return_value = mock_analyzer
            yield processor, mock_analyzer

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    @pytest.mark.slow
    def test_end_to_end_processing(self, batch_processor_with_mock_analyzer, temp_test_files):
        """测试端到端批量处理"""
        processor, mock_analyzer = batch_processor_with_mock_analyzer
        
        # 创建测试文件
        mock_files = []
        for doc_type, file_path in temp_test_files.items():
            mock_file = Mock()
            mock_file.filename = f'{doc_type}.txt'
            mock_file.content_length = 1024
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            mock_file.read.return_value = content.encode('utf-8')
            mock_files.append(mock_file)
        
        # 创建任务
        job_id = processor.create_batch_job(
            files=mock_files,
            user_id=1,
            settings={'analysis_type': 'customer_requirements'}
        )
        
        # 启动处理
        progress_calls = []
        def progress_callback(job_id, progress_data):
            progress_calls.append((job_id, progress_data))
        
        success = processor.start_batch_processing(job_id, progress_callback)
        assert success == True
        
        # 等待处理完成（在实际环境中会异步进行）
        time.sleep(0.1)  # 短暂等待
        
        # 检查状态
        status = processor.get_batch_status(job_id)
        assert status['job_id'] == job_id
        
        # 验证分析器被调用
        assert mock_analyzer.analyze_document.called

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_error_handling_in_processing(self, batch_processor_with_mock_analyzer, temp_test_files):
        """测试处理过程中的错误处理"""
        processor, mock_analyzer = batch_processor_with_mock_analyzer
        
        # 配置分析器抛出异常
        mock_analyzer.analyze_document.side_effect = Exception("Analysis failed")
        
        # 创建测试文件
        mock_file = Mock()
        mock_file.filename = 'error_test.txt'
        mock_file.content_length = 1024
        mock_file.read.return_value = b'test content'
        
        # 创建和启动任务
        job_id = processor.create_batch_job(
            files=[mock_file],
            user_id=1,
            settings={'analysis_type': 'customer_requirements'}
        )
        
        success = processor.start_batch_processing(job_id)
        assert success == True
        
        # 检查任务状态（应该正常启动，错误在处理过程中处理）
        status = processor.get_batch_status(job_id)
        assert status['status'] == 'processing'

    @pytest.mark.unit
    @pytest.mark.services
    @pytest.mark.batch
    def test_progress_callback_triggering(self, batch_processor, mock_files):
        """测试进度回调触发"""
        job_id = batch_processor.create_batch_job(
            files=mock_files,
            user_id=1,
            settings={}
        )
        
        # 创建进度回调
        progress_calls = []
        def progress_callback(job_id, progress_data):
            progress_calls.append((job_id, progress_data))
        
        # 启动处理
        batch_processor.start_batch_processing(job_id, progress_callback)
        
        # 手动触发进度回调
        job = batch_processor.active_jobs[job_id]
        job.processed_files = 1
        batch_processor._trigger_progress_callbacks(job_id, job)
        
        # 验证回调被调用
        assert len(progress_calls) == 1
        assert progress_calls[0][0] == job_id
        assert progress_calls[0][1]['processed_files'] == 1