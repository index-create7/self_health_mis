#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI调用测试模块（简化版）
测试简化后的百炼适配器功能
"""

import unittest
from unittest import mock
import json
import os
import sys
import requests

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.bailian_adapter import (
    BaiLianAdapter,
    ask_bailian
)


class TestBaiLianAdapter(unittest.TestCase):
    """
    测试简化版百炼适配器的基本功能
    """

    def setUp(self):
        """
        设置测试环境
        """
        # 初始化默认适配器
        self.adapter = BaiLianAdapter()

    def test_adapter_initialization(self):
        """
        测试适配器初始化
        """
        # 检查适配器是否正确初始化
        self.assertIsInstance(self.adapter, BaiLianAdapter)
        self.assertEqual(self.adapter.app_id, "f7f17875f8094d66bf3fa4af4f5d51cd")
        self.assertEqual(self.adapter.endpoint, "https://bailian.aliyun.com/api/v1/chat/completions")
        
        # 测试自定义参数初始化
        adapter = BaiLianAdapter(api_key="test_key", app_id="test_app_id")
        self.assertEqual(adapter.api_key, "test_key")
        self.assertEqual(adapter.app_id, "test_app_id")

    @mock.patch('requests.post')
    def test_ask_method(self, mock_post):
        """
        测试ask方法
        """
        # 模拟响应
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "测试响应内容"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # 测试字符串输入
        result = self.adapter.ask("测试消息")
        self.assertEqual(result, "测试响应内容")
        
        # 测试消息列表输入
        messages = [{"role": "user", "content": "测试消息"}]
        result = self.adapter.ask(messages)
        self.assertEqual(result, "测试响应内容")

    @mock.patch('requests.post')
    def test_ask_method_error(self, mock_post):
        """
        测试ask方法错误处理
        """
        # 模拟请求失败
        mock_post.side_effect = Exception("测试错误")
        
        # 测试错误情况下返回空字符串
        result = self.adapter.ask("测试消息")
        self.assertEqual(result, "")


class TestHelperFunctions(unittest.TestCase):
    """
    测试辅助函数
    """

    @mock.patch('ai.bailian_adapter.BaiLianAdapter')
    def test_ask_bailian(self, mock_adapter_class):
        """
        测试ask_bailian便捷函数
        """
        # 创建模拟适配器和设置返回值
        mock_adapter = mock_adapter_class.return_value
        mock_adapter.ask.return_value = "测试响应"
        
        # 测试调用便捷函数
        result = ask_bailian("测试消息", api_key="test_key", app_id="test_app_id")
        self.assertEqual(result, "测试响应")
        
        # 检查是否正确创建了适配器
        mock_adapter_class.assert_called_once()
        
        # 检查是否调用了ask方法
        mock_adapter.ask.assert_called_once_with("测试消息")


class TestIntegrationWithBaiLian(unittest.TestCase):
    """
    与百炼API的集成测试（简化版）
    """

    def setUp(self):
        """
        设置集成测试环境
        """
        # 创建适配器实例
        self.adapter = BaiLianAdapter()

    def test_integration_with_bailian(self):
        """
        测试与百炼API的集成
        """
        # 主动跳过测试，避免实际API调用
        self.skipTest("集成测试已主动跳过，避免实际API调用")


def run_tests():
    """
    运行所有测试
    """
    # 创建测试加载器
    loader = unittest.TestLoader()
    
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加测试类
    suite.addTests(loader.loadTestsFromTestCase(TestBaiLianAdapter))
    suite.addTests(loader.loadTestsFromTestCase(TestHelperFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegrationWithBaiLian))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回测试结果
    return result


if __name__ == '__main__':
    # 运行测试
    print("=" * 50)
    print("开始运行AI调用测试（简化版）")
    print("=" * 50)
    
    # 执行测试
    test_result = run_tests()
    
    # 输出测试结果摘要
    print("\n测试结果摘要:")
    print(f"运行测试数: {test_result.testsRun}")
    print(f"失败数: {len(test_result.failures)}")
    print(f"错误数: {len(test_result.errors)}")
    print(f"跳过数: {len(test_result.skipped)}")
    
    # 退出码设置
    if test_result.wasSuccessful():
        sys.exit(0)
    else:
        sys.exit(1)

    print("\n" + "=" * 50)
    print("测试结束")
    print("=" * 50)