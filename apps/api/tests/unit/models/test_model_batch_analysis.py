#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量分析模型单元测试
覆盖批量分析相关模型的所有功能
"""
import pytest
from datetime import datetime, timedelta
from src.models.batch_analysis import (
    BatchAnalysisJob, BatchAnalysisFile, BatchProcessingSummary,
    BatchStatus, FileStatus
)


class TestBatchAnalysisJob:
    """测试BatchAnalysisJob模型"""

    @pytest.mark.unit
    @pytest.mark.models
    @pytest.mark.batch
    def test_create_batch_job(self, db_session, test_user):
        """测试创建批量分析任务"""
        job = BatchAnalysisJob(
            job_id='test_job_123',
            job_name='测试任务',
            user_id=test_user.id,
            total_files=5,
            settings={'analysis_type': 'customer_requirements'},
            status=BatchStatus.PENDING
        )
        job.save()
        
        assert job.id is not None
        assert job.job_id == 'test_job_123'
        assert job.job_name == '测试任务'
        assert job.user_id == test_user.id
        assert job.total_files == 5
        assert job.status == BatchStatus.PENDING
        assert job.created_at is not None

    @pytest.mark.unit
    @pytest.mark.models
    @pytest.mark.batch
    def test_batch_job_status_transitions(self, db_session, test_user):
        """测试批量任务状态转换"""
        job = BatchAnalysisJob(
            job_id='test_job_status',
            job_name='状态测试任务',
            user_id=test_user.id,
            total_files=3,
            status=BatchStatus.PENDING
        )
        job.save()
        
        # 测试开始处理
        job.start_processing()
        assert job.status == BatchStatus.PROCESSING
        assert job.start_time is not None
        
        # 测试完成处理
        job.complete_processing()
        assert job.status == BatchStatus.COMPLETED
        assert job.end_time is not None
        
        # 测试取消处理
        job.status = BatchStatus.PROCESSING
        job.cancel_processing()
        assert job.status == BatchStatus.CANCELLED

    @pytest.mark.unit
    @pytest.mark.models
    @pytest.mark.batch
    def test_batch_job_progress_update(self, db_session, test_user):
        """测试批量任务进度更新"""
        job = BatchAnalysisJob(
            job_id='test_job_progress',
            job_name='进度测试任务',
            user_id=test_user.id,
            total_files=10
        )
        job.save()
        
        # 更新进度
        job.update_progress(processed=5, successful=4, failed=1)
        assert job.processed_files == 5
        assert job.successful_files == 4
        assert job.failed_files == 1
        assert job.progress_percentage == 50.0

    @pytest.mark.unit
    @pytest.mark.models
    @pytest.mark.batch
    def test_batch_job_duration_calculation(self, db_session, test_user):
        """测试批量任务时长计算"""
        job = BatchAnalysisJob(
            job_id='test_job_duration',
            job_name='时长测试任务',
            user_id=test_user.id,
            total_files=3
        )
        job.save()
        
        # 设置开始和结束时间
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=5)
        job.start_time = start_time
        job.end_time = end_time
        job.save()
        
        duration = job.get_actual_duration()
        assert duration == 300.0  # 5分钟 = 300秒

    @pytest.mark.unit
    @pytest.mark.models
    @pytest.mark.batch
    def test_get_active_jobs(self, db_session, test_user):
        """测试获取活跃任务"""
        # 创建不同状态的任务
        job1 = BatchAnalysisJob(
            job_id='active_job_1',
            user_id=test_user.id,
            total_files=3,
            status=BatchStatus.PROCESSING
        )
        job2 = BatchAnalysisJob(
            job_id='active_job_2',
            user_id=test_user.id,
            total_files=3,
            status=BatchStatus.PENDING
        )
        job3 = BatchAnalysisJob(
            job_id='completed_job',
            user_id=test_user.id,
            total_files=3,
            status=BatchStatus.COMPLETED
        )
        
        for job in [job1, job2, job3]:
            job.save()
        
        # 获取活跃任务
        active_jobs = BatchAnalysisJob.get_active_jobs()
        active_job_ids = [job.job_id for job in active_jobs]
        
        assert len(active_jobs) == 2
        assert 'active_job_1' in active_job_ids
        assert 'active_job_2' in active_job_ids
        assert 'completed_job' not in active_job_ids

    @pytest.mark.unit
    @pytest.mark.models
    @pytest.mark.batch
    def test_get_active_jobs_by_user(self, db_session, test_user, admin_user):
        """测试按用户获取活跃任务"""
        # 为不同用户创建任务
        job1 = BatchAnalysisJob(
            job_id='user_job_1',
            user_id=test_user.id,
            total_files=3,
            status=BatchStatus.PROCESSING
        )
        job2 = BatchAnalysisJob(
            job_id='admin_job_1',
            user_id=admin_user.id,
            total_files=3,
            status=BatchStatus.PROCESSING
        )
        
        for job in [job1, job2]:
            job.save()
        
        # 获取指定用户的活跃任务
        user_jobs = BatchAnalysisJob.get_active_jobs(user_id=test_user.id)
        assert len(user_jobs) == 1
        assert user_jobs[0].job_id == 'user_job_1'

    @pytest.mark.unit
    @pytest.mark.models
    @pytest.mark.batch
    def test_batch_job_to_dict(self, db_session, test_user):
        """测试批量任务转换为字典"""
        job = BatchAnalysisJob(
            job_id='test_dict_job',
            job_name='字典测试任务',
            user_id=test_user.id,
            total_files=5,
            settings={'analysis_type': 'customer_requirements'},
            status=BatchStatus.PENDING
        )
        job.save()
        
        job_dict = job.to_dict()
        
        assert job_dict['job_id'] == 'test_dict_job'
        assert job_dict['job_name'] == '字典测试任务'
        assert job_dict['total_files'] == 5
        assert job_dict['status'] == 'pending'
        assert 'created_at' in job_dict
        assert job_dict['settings']['analysis_type'] == 'customer_requirements'


class TestBatchAnalysisFile:
    """测试BatchAnalysisFile模型"""

    @pytest.mark.unit
    @pytest.mark.models
    @pytest.mark.batch
    def test_create_batch_file(self, db_session, test_batch_job):
        """测试创建批量文件记录"""
        file = BatchAnalysisFile(
            job_id=test_batch_job.job_id,
            file_id='test_file_123',
            filename='test_document.txt',
            original_filename='original_test.txt',
            file_size=1024,
            file_type='txt',
            status=FileStatus.QUEUED
        )
        file.save()
        
        assert file.id is not None
        assert file.job_id == test_batch_job.job_id
        assert file.file_id == 'test_file_123'
        assert file.filename == 'test_document.txt'
        assert file.original_filename == 'original_test.txt'
        assert file.file_size == 1024
        assert file.file_type == 'txt'
        assert file.status == FileStatus.QUEUED

    @pytest.mark.unit
    @pytest.mark.models
    @pytest.mark.batch
    def test_batch_file_status_transitions(self, db_session, test_batch_job):
        """测试批量文件状态转换"""
        file = BatchAnalysisFile(
            job_id=test_batch_job.job_id,
            file_id='status_test_file',
            filename='status_test.txt',
            original_filename='original_status_test.txt',
            file_size=1024,
            file_type='txt',
            status=FileStatus.QUEUED
        )
        file.save()
        
        # 测试开始处理
        file.start_processing()
        assert file.status == FileStatus.PROCESSING
        assert file.processing_start_time is not None
        
        # 测试完成处理
        result = {'extracted_data': 'test'}
        file.complete_processing(result)
        assert file.status == FileStatus.COMPLETED
        assert file.processing_end_time is not None
        assert file.analysis_result == result
        
        # 测试处理失败
        file.status = FileStatus.PROCESSING
        error_msg = 'Processing failed'
        file.fail_processing(error_msg)
        assert file.status == FileStatus.FAILED
        assert file.error_message == error_msg

    @pytest.mark.unit
    @pytest.mark.models
    @pytest.mark.batch
    def test_batch_file_processing_duration(self, db_session, test_batch_job):
        """测试批量文件处理时长"""
        file = BatchAnalysisFile(
            job_id=test_batch_job.job_id,
            file_id='duration_test_file',
            filename='duration_test.txt',
            original_filename='original_duration_test.txt',
            file_size=1024,
            file_type='txt'
        )
        file.save()
        
        # 设置处理时间
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(seconds=30)
        file.processing_start_time = start_time
        file.processing_end_time = end_time
        file.save()
        
        duration = file.get_processing_duration()
        assert duration == 30.0

    @pytest.mark.unit
    @pytest.mark.models
    @pytest.mark.batch
    def test_get_job_files(self, db_session, test_batch_job):
        """测试获取任务的所有文件"""
        # 创建多个文件
        files = []
        for i in range(3):
            file = BatchAnalysisFile(
                job_id=test_batch_job.job_id,
                file_id=f'job_file_{i}',
                filename=f'file_{i}.txt',
                original_filename=f'original_file_{i}.txt',
                file_size=1024 * i,
                file_type='txt'
            )
            file.save()
            files.append(file)
        
        # 获取任务文件
        job_files = BatchAnalysisFile.get_job_files(test_batch_job.job_id)
        assert len(job_files) == 3
        
        # 验证文件顺序（按创建时间）
        for i, file in enumerate(job_files):
            assert file.file_id == f'job_file_{i}'

    @pytest.mark.unit
    @pytest.mark.models
    @pytest.mark.batch
    def test_batch_file_to_dict(self, db_session, test_batch_job):
        """测试批量文件转换为字典"""
        file = BatchAnalysisFile(
            job_id=test_batch_job.job_id,
            file_id='dict_test_file',
            filename='dict_test.txt',
            original_filename='original_dict_test.txt',
            file_size=2048,
            file_type='txt',
            status=FileStatus.COMPLETED,
            confidence_score=0.85,
            analysis_result={'test': 'data'}
        )
        file.save()
        
        file_dict = file.to_dict()
        
        assert file_dict['file_id'] == 'dict_test_file'
        assert file_dict['filename'] == 'dict_test.txt'
        assert file_dict['original_filename'] == 'original_dict_test.txt'
        assert file_dict['file_size'] == 2048
        assert file_dict['file_type'] == 'txt'
        assert file_dict['status'] == 'completed'
        assert file_dict['confidence_score'] == 0.85
        assert file_dict['has_result'] == True  # The to_dict method returns has_result instead of analysis_result


class TestBatchProcessingSummary:
    """测试BatchProcessingSummary模型"""

    @pytest.mark.unit
    @pytest.mark.models
    @pytest.mark.batch
    def test_create_processing_summary(self, db_session, test_batch_job):
        """测试创建处理摘要"""
        summary = BatchProcessingSummary(
            job_id=test_batch_job.job_id,
            total_files=5,
            successful_files=4,
            failed_files=1,
            total_processing_time=120.0,
            average_confidence=0.85,
            average_file_time=24.0
        )
        summary.save()
        
        assert summary.id is not None
        assert summary.job_id == test_batch_job.job_id
        assert summary.total_files == 5
        assert summary.successful_files == 4
        assert summary.failed_files == 1
        assert summary.success_rate == 80.0
        assert summary.total_processing_time == 120.0
        assert summary.average_processing_time == 24.0
        assert summary.average_confidence == 0.85

    @pytest.mark.unit
    @pytest.mark.models
    @pytest.mark.batch
    def test_create_from_job(self, db_session, test_batch_job, test_batch_files):
        """测试从任务创建摘要"""
        # 更新任务状态
        test_batch_job.processed_files = 3
        test_batch_job.successful_files = 2
        test_batch_job.failed_files = 1
        test_batch_job.save()
        
        # 更新文件状态
        test_batch_files[0].status = FileStatus.COMPLETED
        test_batch_files[0].confidence_score = 0.8
        test_batch_files[0].processing_duration = 15.0
        test_batch_files[0].save()
        
        test_batch_files[1].status = FileStatus.COMPLETED
        test_batch_files[1].confidence_score = 0.9
        test_batch_files[1].processing_duration = 20.0
        test_batch_files[1].save()
        
        test_batch_files[2].status = FileStatus.FAILED
        test_batch_files[2].error_message = 'Processing failed'
        test_batch_files[2].save()
        
        # 创建摘要
        summary = BatchProcessingSummary.create_from_job(test_batch_job.job_id)
        
        assert summary is not None
        assert summary.job_id == test_batch_job.job_id
        assert summary.total_files == 3
        assert summary.successful_files == 2
        assert summary.failed_files == 1
        assert summary.success_rate == 66.67
        assert abs(summary.average_confidence - 0.85) < 0.001  # Use floating point comparison

    @pytest.mark.unit
    @pytest.mark.models
    @pytest.mark.batch
    def test_summary_to_dict(self, db_session, test_user):
        """测试摘要转换为字典"""
        # Create a unique test job for this test
        job = BatchAnalysisJob(
            job_id='dict_test_job_unique',
            job_name='字典测试任务',
            user_id=test_user.id,
            total_files=5
        )
        job.save()
        
        summary = BatchProcessingSummary(
            job_id=job.job_id,
            total_files=5,
            successful_files=4,
            failed_files=1,
            total_processing_time=100.0,
            average_confidence=0.75,
            average_file_time=20.0
        )
        summary.save()
        
        summary_dict = summary.to_dict()
        
        assert summary_dict['job_id'] == job.job_id
        assert summary_dict['total_files'] == 5
        assert summary_dict['successful_files'] == 4
        assert summary_dict['failed_files'] == 1
        assert summary_dict['success_rate'] == 80.0
        assert summary_dict['total_processing_time'] == 100.0
        assert summary_dict['average_file_time'] == 20.0
        assert summary_dict['average_confidence'] == 0.75
        # summary_data is a computed property, so check the constituent parts
        assert summary_dict['file_type_stats'] is None
        assert summary_dict['common_errors'] is None
        assert summary_dict['error_categories'] is None


class TestBatchStatusEnum:
    """测试批量状态枚举"""

    @pytest.mark.unit
    @pytest.mark.models
    @pytest.mark.batch
    def test_batch_status_values(self):
        """测试批量状态值"""
        assert BatchStatus.PENDING.value == 'pending'
        assert BatchStatus.PROCESSING.value == 'processing'
        assert BatchStatus.COMPLETED.value == 'completed'
        assert BatchStatus.FAILED.value == 'failed'
        assert BatchStatus.CANCELLED.value == 'cancelled'

    @pytest.mark.unit
    @pytest.mark.models
    @pytest.mark.batch
    def test_file_status_values(self):
        """测试文件状态值"""
        assert FileStatus.QUEUED.value == 'queued'
        assert FileStatus.PROCESSING.value == 'processing'
        assert FileStatus.COMPLETED.value == 'completed'
        assert FileStatus.FAILED.value == 'failed'
        assert FileStatus.SKIPPED.value == 'skipped'


class TestBatchAnalysisIntegration:
    """测试批量分析模型集成"""

    @pytest.mark.unit
    @pytest.mark.models
    @pytest.mark.batch
    def test_job_file_relationship(self, db_session, test_user):
        """测试任务和文件的关系"""
        # 创建任务
        job = BatchAnalysisJob(
            job_id='integration_test_job',
            job_name='集成测试任务',
            user_id=test_user.id,
            total_files=2
        )
        job.save()
        
        # 创建相关文件
        file1 = BatchAnalysisFile(
            job_id=job.job_id,
            file_id='integration_file_1',
            filename='integration_test_1.txt',
            original_filename='original_integration_test_1.txt',
            file_size=1024,
            file_type='txt'
        )
        file1.save()
        
        file2 = BatchAnalysisFile(
            job_id=job.job_id,
            file_id='integration_file_2',
            filename='integration_test_2.txt',
            original_filename='original_integration_test_2.txt',
            file_size=2048,
            file_type='txt'
        )
        file2.save()
        
        # 验证关系
        job_files = BatchAnalysisFile.get_job_files(job.job_id)
        assert len(job_files) == 2
        assert job_files[0].job_id == job.job_id
        assert job_files[1].job_id == job.job_id

    @pytest.mark.unit
    @pytest.mark.models
    @pytest.mark.batch
    def test_complete_workflow(self, db_session, test_user):
        """测试完整的批量分析工作流"""
        # 1. 创建任务
        job = BatchAnalysisJob(
            job_id='workflow_test_job',
            job_name='工作流测试任务',
            user_id=test_user.id,
            total_files=2,
            status=BatchStatus.PENDING
        )
        job.save()
        
        # 2. 创建文件
        files = []
        for i in range(2):
            file = BatchAnalysisFile(
                job_id=job.job_id,
                file_id=f'workflow_file_{i}',
                filename=f'workflow_test_{i}.txt',
                original_filename=f'original_workflow_test_{i}.txt',
                file_size=1024 * (i + 1),
                file_type='txt',
                status=FileStatus.QUEUED
            )
            file.save()
            files.append(file)
        
        # 3. 开始处理
        job.start_processing()
        assert job.status == BatchStatus.PROCESSING
        
        # 4. 处理文件
        for i, file in enumerate(files):
            file.start_processing()
            assert file.status == FileStatus.PROCESSING
            
            # 模拟处理结果
            result = {'analysis': f'result_{i}'}
            file.complete_processing(result, confidence_score=0.8 + i * 0.1)
            assert file.status == FileStatus.COMPLETED
            assert file.confidence_score == 0.8 + i * 0.1
        
        # 5. 更新任务进度
        job.update_progress(processed=2, successful=2, failed=0)
        assert job.processed_files == 2
        assert job.successful_files == 2
        assert job.progress_percentage == 100.0
        
        # 6. 完成任务
        job.complete_processing()
        assert job.status == BatchStatus.COMPLETED
        
        # 7. 创建摘要
        summary = BatchProcessingSummary.create_from_job(job.job_id)
        assert summary is not None
        assert summary.total_files == 2
        assert summary.successful_files == 2
        assert summary.success_rate == 100.0