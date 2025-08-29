#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量分析路由单元测试
覆盖批量分析API的所有功能
"""
import pytest
import json
import io
from unittest.mock import patch, Mock
from src.models.batch_analysis import BatchStatus, FileStatus

class TestBatchAnalysisSubmit:
    """测试批量分析任务提交"""

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_submit_batch_analysis_success(self, client, engineer_auth_headers, temp_test_files, mock_batch_processor):
        """测试成功提交批量分析任务"""
        # 准备测试数据
        settings = {
            'analysis_type': 'customer_requirements',
            'auto_start': False,
            'business_context': {
                'industry': 'technology',
                'project_type': 'development'
            }
        }
        
        with open(temp_test_files['customer_requirements'], 'rb') as f:
            data = {
                'batch_name': '测试批量分析',
                'settings': json.dumps(settings),
                'priority': 5,
                'files': (f, 'customer_requirements.txt')
            }
            
            response = client.post(
                '/api/v1/batch-analysis/submit',
                headers=engineer_auth_headers,
                data=data,
                content_type='multipart/form-data'
            )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] == True
        assert 'job_id' in data
        assert 'estimated_duration' in data

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_submit_batch_analysis_no_files(self, client, engineer_auth_headers):
        """测试提交无文件的批量分析任务"""
        settings = {
            'analysis_type': 'customer_requirements',
            'auto_start': False
        }
        
        data = {
            'batch_name': '测试批量分析',
            'settings': json.dumps(settings),
            'priority': 5
        }
        
        response = client.post(
            '/api/v1/batch-analysis/submit',
            headers=engineer_auth_headers,
            data=data
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'msg' in data or 'error' in data
        assert 'No files provided' in data['error']

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_submit_batch_analysis_too_many_files(self, client, engineer_auth_headers, temp_test_files):
        """测试提交过多文件的批量分析任务"""
        settings = {
            'analysis_type': 'customer_requirements',
            'auto_start': False
        }
        
        # 创建51个文件（超过限制）
        files_list = []
        for i in range(51):
            files_list.append(('files', (io.BytesIO(b'test content'), f'test_{i}.txt')))
        
        data = {
            'batch_name': '测试批量分析',
            'settings': json.dumps(settings),
            'priority': 5
        }
        data.update(files_list)
        
        response = client.post(
            '/api/v1/batch-analysis/submit',
            headers=engineer_auth_headers,
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'msg' in data or 'error' in data
        assert 'Too many files' in data['error']

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_submit_batch_analysis_invalid_settings(self, client, engineer_auth_headers, temp_test_files):
        """测试无效设置的批量分析任务"""
        with open(temp_test_files['customer_requirements'], 'rb') as f:
            data = {
                'batch_name': '测试批量分析',
                'settings': 'invalid json',  # 无效的JSON
                'priority': 5,
                'files': (f, 'customer_requirements.txt')
            }
            
            response = client.post(
                '/api/v1/batch-analysis/submit',
                headers=engineer_auth_headers,
                data=data,
                content_type='multipart/form-data'
            )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'msg' in data or 'error' in data
        assert 'Invalid settings JSON format' in data['error']

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_submit_batch_analysis_unauthorized(self, client, temp_test_files):
        """测试未授权的批量分析任务提交"""
        settings = {
            'analysis_type': 'customer_requirements',
            'auto_start': False
        }
        
        with open(temp_test_files['customer_requirements'], 'rb') as f:
            data = {
                'batch_name': '测试批量分析',
                'settings': json.dumps(settings),
                'files': (f, 'customer_requirements.txt')
            }
            
            response = client.post(
                '/api/v1/batch-analysis/submit',
                data=data,
                content_type='multipart/form-data'
            )
        
        assert response.status_code == 401


class TestBatchAnalysisStart:
    """测试批量分析任务启动"""

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_start_batch_job_success(self, client, engineer_auth_headers, test_batch_job, mock_batch_processor):
        """测试成功启动批量分析任务"""
        response = client.post(
            f'/api/v1/batch-analysis/jobs/{test_batch_job.job_id}/start',
            headers=engineer_auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert data['job_id'] == test_batch_job.job_id

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_start_batch_job_not_found(self, client, engineer_auth_headers):
        """测试启动不存在的批量分析任务"""
        response = client.post(
            '/api/v1/batch-analysis/jobs/nonexistent-job/start',
            headers=engineer_auth_headers
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'msg' in data or 'error' in data

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_start_batch_job_already_running(self, client, engineer_auth_headers, test_batch_job):
        """测试启动已经运行的批量分析任务"""
        # 模拟任务已经在运行
        with patch('src.routes.batch_analysis.batch_processor.get_batch_status') as mock_status:
            mock_status.return_value = {'status': 'processing'}
            
            response = client.post(
                f'/api/v1/batch-analysis/jobs/{test_batch_job.job_id}/start',
                headers=engineer_auth_headers
            )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'already running' in data['message']

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_start_batch_job_unauthorized(self, client, test_batch_job):
        """测试未授权启动批量分析任务"""
        response = client.post(
            f'/api/v1/batch-analysis/jobs/{test_batch_job.job_id}/start'
        )
        
        assert response.status_code == 401


class TestBatchAnalysisStatus:
    """测试批量分析状态查询"""

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_get_batch_job_status_success(self, client, engineer_auth_headers, test_batch_job, test_batch_files, mock_batch_processor):
        """测试成功获取批量分析任务状态"""
        response = client.get(
            f'/api/v1/batch-analysis/jobs/{test_batch_job.job_id}/status',
            headers=engineer_auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'status' in data
        assert data['status']['job_id'] == test_batch_job.job_id

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_get_batch_job_status_not_found(self, client, engineer_auth_headers):
        """测试获取不存在任务的状态"""
        response = client.get(
            '/api/v1/batch-analysis/jobs/nonexistent-job/status',
            headers=engineer_auth_headers
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'msg' in data or 'error' in data

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_get_batch_job_status_unauthorized_user(self, client, auth_headers, test_batch_job):
        """测试其他用户获取任务状态（权限不足）"""
        response = client.get(
            f'/api/v1/batch-analysis/jobs/{test_batch_job.job_id}/status',
            headers=auth_headers
        )
        
        assert response.status_code == 403
        data = response.get_json()
        assert 'msg' in data or 'error' in data


class TestBatchAnalysisResults:
    """测试批量分析结果获取"""

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_get_batch_job_results_success(self, client, engineer_auth_headers, test_batch_job, mock_batch_processor):
        """测试成功获取批量分析结果"""
        response = client.get(
            f'/api/v1/batch-analysis/jobs/{test_batch_job.job_id}/results',
            headers=engineer_auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'results' in data

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_get_batch_job_results_not_found(self, client, engineer_auth_headers):
        """测试获取不存在任务的结果"""
        response = client.get(
            '/api/v1/batch-analysis/jobs/nonexistent-job/results',
            headers=engineer_auth_headers
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'msg' in data or 'error' in data


class TestBatchAnalysisHistory:
    """测试批量分析历史记录"""

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_get_batch_history_success(self, client, engineer_auth_headers, test_batch_job):
        """测试成功获取批量分析历史"""
        response = client.get(
            '/api/v1/batch-analysis/history',
            headers=engineer_auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'records' in data
        assert 'pagination' in data
        assert 'statistics' in data

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_get_batch_history_with_filters(self, client, engineer_auth_headers, test_batch_job):
        """测试带过滤条件的历史记录查询"""
        response = client.get(
            '/api/v1/batch-analysis/history?status=pending&page=1&page_size=10',
            headers=engineer_auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'records' in data

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_clear_batch_history_success(self, client, engineer_auth_headers, test_batch_job):
        """测试成功清空批量分析历史"""
        response = client.delete(
            '/api/v1/batch-analysis/history/clear',
            headers=engineer_auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'deleted_count' in data

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_delete_batch_record_success(self, client, engineer_auth_headers, test_batch_job):
        """测试成功删除批量分析记录"""
        response = client.delete(
            f'/api/v1/batch-analysis/record/{test_batch_job.id}',
            headers=engineer_auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True


class TestBatchAnalysisSystem:
    """测试批量分析系统功能"""

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_get_system_status_success(self, client, engineer_auth_headers, mock_batch_processor):
        """测试成功获取系统状态"""
        response = client.get(
            '/api/v1/batch-analysis/system/status',
            headers=engineer_auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'status' in data
        assert 'environment' in data['status']
        assert 'processing_capacity' in data['status']
        assert 'user_limits' in data['status']

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_get_batch_settings_success(self, client, engineer_auth_headers):
        """测试成功获取批量处理设置"""
        response = client.get(
            '/api/v1/batch-analysis/settings',
            headers=engineer_auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'settings' in data
        assert 'max_files_per_batch' in data['settings']
        assert 'supported_formats' in data['settings']

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_cancel_batch_job_success(self, client, engineer_auth_headers, test_batch_job, mock_batch_processor):
        """测试成功取消批量分析任务"""
        mock_batch_processor.cancel_batch_job.return_value = True
        
        response = client.post(
            f'/api/v1/batch-analysis/jobs/{test_batch_job.job_id}/cancel',
            headers=engineer_auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_simulate_complete_job_success(self, client, engineer_auth_headers, test_batch_job):
        """测试成功模拟完成批量分析任务"""
        response = client.post(
            f'/api/v1/batch-analysis/jobs/{test_batch_job.job_id}/simulate_complete',
            headers=engineer_auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert data['status'] == 'completed'


class TestBatchAnalysisAdmin:
    """测试批量分析管理功能"""

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_get_batch_statistics_admin(self, client, admin_auth_headers, mock_batch_processor):
        """测试管理员获取批量处理统计"""
        response = client.get(
            '/api/v1/batch-analysis/statistics',
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'statistics' in data

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_get_batch_statistics_non_admin(self, client, engineer_auth_headers):
        """测试非管理员获取统计（权限不足）"""
        response = client.get(
            '/api/v1/batch-analysis/statistics',
            headers=engineer_auth_headers
        )
        
        assert response.status_code == 403

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_cleanup_batch_jobs_admin(self, client, admin_auth_headers, mock_batch_processor):
        """测试管理员清理批量任务"""
        response = client.post(
            '/api/v1/batch-analysis/cleanup',
            headers=admin_auth_headers,
            json={'hours': 24}
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True

    @pytest.mark.unit
    @pytest.mark.api
    @pytest.mark.batch
    def test_debug_batch_jobs(self, client, engineer_auth_headers, test_batch_job):
        """测试调试批量任务"""
        response = client.get(
            '/api/v1/batch-analysis/debug/jobs',
            headers=engineer_auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'jobs' in data
        assert 'total_jobs' in data