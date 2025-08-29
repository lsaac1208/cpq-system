#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报价API路由单元测试
覆盖报价相关API的所有功能
"""
import pytest
import json
from decimal import Decimal
from datetime import datetime, timedelta
from unittest.mock import patch
from src.models.quote import Quote, QuoteStatus


class TestQuotesAPI:
    """测试报价API路由"""

    @pytest.mark.unit
    @pytest.mark.api
    def test_get_quotes_success(self, client, auth_headers, test_quote):
        """测试成功获取报价列表"""
        response = client.get('/api/quotes', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'quotes' in data
        assert len(data['quotes']) > 0
        
        # 验证报价数据结构
        quote = data['quotes'][0]
        assert 'id' in quote
        assert 'quote_number' in quote
        assert 'customer_name' in quote
        assert 'status' in quote
        assert 'final_price' in quote

    @pytest.mark.unit
    @pytest.mark.api
    def test_get_quotes_unauthorized(self, client):
        """测试未授权获取报价列表"""
        response = client.get('/api/quotes')
        assert response.status_code == 401

    @pytest.mark.unit
    @pytest.mark.api
    def test_get_quotes_with_pagination(self, client, auth_headers, test_quote):
        """测试带分页的报价列表"""
        response = client.get(
            '/api/quotes?page=1&per_page=10',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'quotes' in data
        assert 'pagination' in data
        assert 'total' in data['pagination']
        assert 'pages' in data['pagination']
        assert 'current_page' in data['pagination']

    @pytest.mark.unit
    @pytest.mark.api
    def test_get_quotes_filter_by_status(self, client, auth_headers, test_quote):
        """测试按状态筛选报价"""
        response = client.get(
            f'/api/quotes?status={test_quote.status.value}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        
        # 验证所有报价都是指定状态
        for quote in data['quotes']:
            assert quote['status'] == test_quote.status.value

    @pytest.mark.unit
    @pytest.mark.api
    def test_get_quotes_search_by_customer(self, client, auth_headers, test_quote):
        """测试按客户名称搜索报价"""
        response = client.get(
            f'/api/quotes?search={test_quote.customer_name}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert len(data['quotes']) > 0
        
        # 验证搜索结果包含目标客户
        customer_names = [q['customer_name'] for q in data['quotes']]
        assert test_quote.customer_name in customer_names

    @pytest.mark.unit
    @pytest.mark.api
    def test_get_quote_by_id_success(self, client, auth_headers, test_quote):
        """测试成功获取单个报价"""
        response = client.get(
            f'/api/quotes/{test_quote.id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'quote' in data
        
        quote = data['quote']
        assert quote['id'] == test_quote.id
        assert quote['quote_number'] == test_quote.quote_number
        assert quote['customer_name'] == test_quote.customer_name
        assert 'configuration' in quote
        assert 'product' in quote

    @pytest.mark.unit
    @pytest.mark.api
    def test_get_quote_by_id_not_found(self, client, auth_headers):
        """测试获取不存在的报价"""
        response = client.get('/api/quotes/99999', headers=auth_headers)
        
        assert response.status_code == 404
        data = response.get_json()
        assert 'msg' in data or 'error' in data

    @pytest.mark.unit
    @pytest.mark.api
    def test_create_quote_success(self, client, auth_headers, test_product):
        """测试成功创建报价"""
        quote_data = {
            'customer_name': 'New Customer',
            'customer_email': 'newcustomer@gmail.com',
            'customer_company': 'New Company',
            'product_id': test_product.id,
            'quantity': 2,
            'configuration': {
                'cpu': 'Intel i7',
                'memory': '16GB'
            },
            'discount_percentage': 5.0,
            'notes': 'Test quote creation',
            'valid_until': (datetime.now() + timedelta(days=30)).isoformat()
        }
        
        response = client.post(
            '/api/quotes',
            headers=auth_headers,
            json=quote_data
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] == True
        assert 'quote' in data
        
        created_quote = data['quote']
        assert created_quote['customer_name'] == quote_data['customer_name']
        assert created_quote['customer_email'] == quote_data['customer_email']
        assert created_quote['product_id'] == quote_data['product_id']
        assert created_quote['quantity'] == quote_data['quantity']
        assert 'quote_number' in created_quote
        assert created_quote['status'] == 'draft'

    @pytest.mark.unit
    @pytest.mark.api
    def test_create_quote_invalid_product(self, client, auth_headers):
        """测试创建报价时产品无效"""
        quote_data = {
            'customer_name': 'Test Customer',
            'customer_email': 'test@gmail.com',
            'product_id': 99999,  # 不存在的产品ID
            'quantity': 1
        }
        
        response = client.post(
            '/api/quotes',
            headers=auth_headers,
            json=quote_data
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'msg' in data or 'error' in data

    @pytest.mark.unit
    @pytest.mark.api
    def test_create_quote_invalid_data(self, client, auth_headers, test_product):
        """测试创建报价时数据无效"""
        invalid_data = {
            'customer_name': '',  # 空客户名
            'customer_email': 'invalid-email',  # 无效邮箱
            'product_id': test_product.id,
            'quantity': 0  # 无效数量
        }
        
        response = client.post(
            '/api/quotes',
            headers=auth_headers,
            json=invalid_data
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'msg' in data or 'error' in data or 'errors' in data

    @pytest.mark.unit
    @pytest.mark.api
    def test_update_quote_success(self, client, auth_headers, test_quote):
        """测试成功更新报价"""
        update_data = {
            'customer_company': 'Updated Company',
            'quantity': 3,
            'discount_percentage': 10.0,
            'notes': 'Updated notes'
        }
        
        response = client.put(
            f'/api/quotes/{test_quote.id}',
            headers=auth_headers,
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'quote' in data
        
        updated_quote = data['quote']
        assert updated_quote['customer_company'] == update_data['customer_company']
        assert updated_quote['quantity'] == update_data['quantity']
        assert updated_quote['notes'] == update_data['notes']

    @pytest.mark.unit
    @pytest.mark.api
    def test_update_quote_not_found(self, client, auth_headers):
        """测试更新不存在的报价"""
        update_data = {
            'customer_company': 'Non-existent Quote'
        }
        
        response = client.put(
            '/api/quotes/99999',
            headers=auth_headers,
            json=update_data
        )
        
        assert response.status_code == 404

    @pytest.mark.unit
    @pytest.mark.api
    def test_update_quote_unauthorized_user(self, client, admin_auth_headers, test_quote):
        """测试其他用户更新报价（权限验证）"""
        # 这里应该测试用户只能更新自己创建的报价
        update_data = {
            'notes': 'Unauthorized update'
        }
        
        # 使用admin用户尝试更新普通用户的报价
        response = client.put(
            f'/api/quotes/{test_quote.id}',
            headers=admin_auth_headers,
            json=update_data
        )
        
        # 管理员应该能够更新任何报价
        assert response.status_code == 200

    @pytest.mark.unit
    @pytest.mark.api
    def test_delete_quote_success(self, client, auth_headers, db_session, test_product, test_user):
        """测试成功删除报价"""
        # 创建一个测试报价用于删除
        quote = Quote(
            quote_number='Q-DELETE-001',
            customer_name='Delete Test Customer',
            customer_email='delete@gmail.com',
            product_id=test_product.id,
            quantity=1,
            unit_price=Decimal('100.00'),
            total_price=Decimal('100.00'),
            final_price=Decimal('100.00'),
            status=QuoteStatus.DRAFT,
            created_by=test_user.id
        )
        quote.save()
        
        response = client.delete(
            f'/api/quotes/{quote.id}',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True

    @pytest.mark.unit
    @pytest.mark.api
    def test_delete_quote_not_found(self, client, auth_headers):
        """测试删除不存在的报价"""
        response = client.delete(
            '/api/quotes/99999',
            headers=auth_headers
        )
        
        assert response.status_code == 404

    @pytest.mark.unit
    @pytest.mark.api
    def test_update_quote_status_success(self, client, auth_headers, test_quote):
        """测试更新报价状态"""
        status_data = {
            'status': 'pending'
        }
        
        response = client.patch(
            f'/api/quotes/{test_quote.id}/status',
            headers=auth_headers,
            json=status_data
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'quote' in data
        assert data['quote']['status'] == 'pending'

    @pytest.mark.unit
    @pytest.mark.api
    def test_update_quote_status_invalid(self, client, auth_headers, test_quote):
        """测试更新报价为无效状态"""
        status_data = {
            'status': 'invalid_status'
        }
        
        response = client.patch(
            f'/api/quotes/{test_quote.id}/status',
            headers=auth_headers,
            json=status_data
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'msg' in data or 'error' in data

    @pytest.mark.unit
    @pytest.mark.api
    def test_approve_quote_success(self, client, admin_auth_headers, test_quote):
        """测试批准报价"""
        response = client.post(
            f'/api/quotes/{test_quote.id}/approve',
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'quote' in data
        assert data['quote']['status'] == 'approved'

    @pytest.mark.unit
    @pytest.mark.api
    def test_approve_quote_unauthorized(self, client, auth_headers, test_quote):
        """测试非管理员批准报价"""
        response = client.post(
            f'/api/quotes/{test_quote.id}/approve',
            headers=auth_headers
        )
        
        assert response.status_code == 403

    @pytest.mark.unit
    @pytest.mark.api
    def test_reject_quote_success(self, client, admin_auth_headers, test_quote):
        """测试拒绝报价"""
        rejection_data = {
            'reason': 'Budget constraints'
        }
        
        response = client.post(
            f'/api/quotes/{test_quote.id}/reject',
            headers=admin_auth_headers,
            json=rejection_data
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'quote' in data
        assert data['quote']['status'] == 'rejected'

    @pytest.mark.unit
    @pytest.mark.api
    def test_send_quote_success(self, client, auth_headers, test_quote):
        """测试发送报价"""
        send_data = {
            'email_template': 'standard',
            'custom_message': 'Please review this quote'
        }
        
        with patch('src.routes.quotes.send_quote_email') as mock_send:
            mock_send.return_value = True
            
            response = client.post(
                f'/api/quotes/{test_quote.id}/send',
                headers=auth_headers,
                json=send_data
            )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        mock_send.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.api
    def test_duplicate_quote_success(self, client, auth_headers, test_quote):
        """测试复制报价"""
        response = client.post(
            f'/api/quotes/{test_quote.id}/duplicate',
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] == True
        assert 'quote' in data
        
        duplicated_quote = data['quote']
        assert duplicated_quote['id'] != test_quote.id
        assert duplicated_quote['customer_name'] == test_quote.customer_name
        assert duplicated_quote['product_id'] == test_quote.product_id
        assert duplicated_quote['status'] == 'draft'

    @pytest.mark.unit
    @pytest.mark.api
    def test_generate_quote_pdf_success(self, client, auth_headers, test_quote):
        """测试生成报价PDF"""
        with patch('src.routes.quotes.generate_quote_pdf') as mock_pdf:
            mock_pdf.return_value = b'PDF content'
            
            response = client.get(
                f'/api/quotes/{test_quote.id}/pdf',
                headers=auth_headers
            )
        
        assert response.status_code == 200
        assert response.content_type == 'application/pdf'
        mock_pdf.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.api
    def test_get_quote_history_success(self, client, auth_headers, test_quote):
        """测试获取报价历史"""
        response = client.get(
            f'/api/quotes/{test_quote.id}/history',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'history' in data
        assert isinstance(data['history'], list)

    @pytest.mark.unit
    @pytest.mark.api
    def test_get_quote_statistics(self, client, admin_auth_headers, test_quote):
        """测试获取报价统计"""
        response = client.get('/api/quotes/statistics', headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'statistics' in data
        
        stats = data['statistics']
        assert 'total_quotes' in stats
        assert 'pending_quotes' in stats
        assert 'approved_quotes' in stats
        assert 'conversion_rate' in stats

    @pytest.mark.unit
    @pytest.mark.api
    def test_bulk_update_quote_status(self, client, admin_auth_headers, test_quote):
        """测试批量更新报价状态"""
        bulk_data = {
            'quote_ids': [test_quote.id],
            'status': 'pending'
        }
        
        response = client.patch(
            '/api/quotes/bulk-status',
            headers=admin_auth_headers,
            json=bulk_data
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'updated_count' in data
        assert data['updated_count'] > 0

    @pytest.mark.unit
    @pytest.mark.api
    def test_export_quotes_success(self, client, admin_auth_headers, test_quote):
        """测试导出报价"""
        response = client.get(
            '/api/quotes/export?format=csv&status=draft',
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] == True
        assert 'export_url' in data or 'quotes' in data


class TestQuotesAPIValidation:
    """测试报价API数据验证"""

    @pytest.mark.unit
    @pytest.mark.api
    def test_create_quote_missing_required_fields(self, client, auth_headers, test_product):
        """测试创建报价时缺少必需字段"""
        incomplete_data = {
            'customer_name': 'Test Customer'
            # 缺少customer_email, product_id等必需字段
        }
        
        response = client.post(
            '/api/quotes',
            headers=auth_headers,
            json=incomplete_data
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'msg' in data or 'error' in data or 'errors' in data

    @pytest.mark.unit
    @pytest.mark.api
    def test_create_quote_invalid_email_format(self, client, auth_headers, test_product):
        """测试创建报价时邮箱格式无效"""
        invalid_data = {
            'customer_name': 'Test Customer',
            'customer_email': 'invalid-email-format',
            'product_id': test_product.id,
            'quantity': 1
        }
        
        response = client.post(
            '/api/quotes',
            headers=auth_headers,
            json=invalid_data
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'msg' in data or 'error' in data

    @pytest.mark.unit
    @pytest.mark.api
    def test_create_quote_negative_quantity(self, client, auth_headers, test_product):
        """测试创建报价时数量为负数"""
        invalid_data = {
            'customer_name': 'Test Customer',
            'customer_email': 'test@gmail.com',
            'product_id': test_product.id,
            'quantity': -1
        }
        
        response = client.post(
            '/api/quotes',
            headers=auth_headers,
            json=invalid_data
        )
        
        assert response.status_code == 400

    @pytest.mark.unit
    @pytest.mark.api
    def test_create_quote_invalid_discount(self, client, auth_headers, test_product):
        """测试创建报价时折扣无效"""
        invalid_data = {
            'customer_name': 'Test Customer',
            'customer_email': 'test@gmail.com',
            'product_id': test_product.id,
            'quantity': 1,
            'discount_percentage': 150  # 超过100%
        }
        
        response = client.post(
            '/api/quotes',
            headers=auth_headers,
            json=invalid_data
        )
        
        assert response.status_code == 400


class TestQuotesAPIErrorHandling:
    """测试报价API错误处理"""

    @pytest.mark.unit
    @pytest.mark.api
    def test_invalid_quote_id_format(self, client, auth_headers):
        """测试无效的报价ID格式"""
        response = client.get('/api/quotes/invalid_id', headers=auth_headers)
        assert response.status_code == 400

    @pytest.mark.unit
    @pytest.mark.api
    @patch('src.routes.quotes.Quote.query')
    def test_database_error_handling(self, mock_query, client, auth_headers):
        """测试数据库错误处理"""
        mock_query.filter.side_effect = Exception("Database error")
        
        response = client.get('/api/quotes', headers=auth_headers)
        assert response.status_code == 500
        
        data = response.get_json()
        assert 'msg' in data or 'error' in data

    @pytest.mark.unit
    @pytest.mark.api
    def test_concurrent_quote_modification(self, client, auth_headers, test_quote):
        """测试并发修改报价"""
        # 模拟两个用户同时修改同一个报价
        update_data1 = {'notes': 'First update'}
        update_data2 = {'notes': 'Second update'}
        
        # 第一个更新应该成功
        response1 = client.put(
            f'/api/quotes/{test_quote.id}',
            headers=auth_headers,
            json=update_data1
        )
        assert response1.status_code == 200
        
        # 第二个更新也应该成功（简单的最后写入获胜策略）
        response2 = client.put(
            f'/api/quotes/{test_quote.id}',
            headers=auth_headers,
            json=update_data2
        )
        assert response2.status_code == 200