import unittest
import json
import os
import datetime
from unittest.mock import patch, mock_open
from memory_mcp_server import update_user_preference

class TestUpdateUserPreference(unittest.TestCase):
    def setUp(self):
        # 测试前删除可能存在的user_preference.json文件
        if os.path.exists("user_preference.json"):
            os.remove("user_preference.json")
    
    def tearDown(self):
        # 测试后删除可能存在的user_preference.json文件
        if os.path.exists("user_preference.json"):
            os.remove("user_preference.json")
    
    def test_update_user_preference_new_file(self):
        """测试当文件不存在时创建新文件并保存偏好数据"""
        preferences = [
            {
                "dimension": "回答风格-长度",
                "value": "concise",
                "confidence": "high",
                "evidence": "用户说：'长话短说，告诉我关键点就行。'"
            }
        ]
        
        result = update_user_preference(preferences)
        
        # 验证返回消息
        self.assertEqual(result, "成功保存 1 条用户偏好数据")
        
        # 验证文件是否创建并包含正确的数据
        self.assertTrue(os.path.exists("user_preference.json"))
        
        with open("user_preference.json", "r", encoding='utf-8') as f:
            saved_data = json.load(f)
        
        # 验证保存的数据
        self.assertEqual(len(saved_data), 1)
        self.assertEqual(saved_data[0]["dimension"], "回答风格-长度")
        self.assertEqual(saved_data[0]["value"], "concise")
        self.assertEqual(saved_data[0]["confidence"], "high")
        self.assertEqual(saved_data[0]["evidence"], "用户说：'长话短说，告诉我关键点就行。'")
        self.assertIn("create_time", saved_data[0])
    
    def test_update_user_preference_existing_file(self):
        """测试当文件已存在时追加新的偏好数据"""
        # 首先创建一些初始数据
        initial_preferences = [
            {
                "dimension": "技术背景-编程语言",
                "value": ["Python"],
                "confidence": "medium",
                "evidence": "用户提供了Python代码片段"
            }
        ]
        
        # 保存初始数据
        with open("user_preference.json", "w", encoding='utf-8') as f:
            json.dump(initial_preferences, f, ensure_ascii=False, indent=2)
        
        # 添加新的偏好数据
        new_preferences = [
            {
                "dimension": "回答风格-长度",
                "value": "concise",
                "confidence": "high",
                "evidence": "用户说：'长话短说，告诉我关键点就行。'"
            }
        ]
        
        result = update_user_preference(new_preferences)
        
        # 验证返回消息
        self.assertEqual(result, "成功保存 1 条用户偏好数据")
        
        # 验证文件是否包含合并后的数据
        with open("user_preference.json", "r", encoding='utf-8') as f:
            saved_data = json.load(f)
        
        # 验证保存的数据
        self.assertEqual(len(saved_data), 2)
        self.assertEqual(saved_data[0]["dimension"], "技术背景-编程语言")
        self.assertEqual(saved_data[1]["dimension"], "回答风格-长度")
        self.assertIn("create_time", saved_data[1])
    
    def test_update_user_preference_empty_list(self):
        """测试传入空列表的情况"""
        preferences = []
        
        result = update_user_preference(preferences)
        
        # 验证返回消息
        self.assertEqual(result, "成功保存 0 条用户偏好数据")
        
        # 验证文件是否创建
        self.assertTrue(os.path.exists("user_preference.json"))
        
        # 验证文件内容为空列表
        with open("user_preference.json", "r", encoding='utf-8') as f:
            saved_data = json.load(f)
        
        self.assertEqual(saved_data, [])
    
    @patch('builtins.open', new_callable=mock_open, read_data='[{"dimension": "test", "value": "test"}]')
    @patch('os.path.exists', return_value=True)
    def test_update_user_preference_read_error(self, mock_exists, mock_file):
        """测试读取文件时发生错误的情况"""
        # 模拟文件读取错误
        mock_file.side_effect = IOError("模拟文件读取错误")
        
        preferences = [
            {
                "dimension": "回答风格-长度",
                "value": "concise",
                "confidence": "high",
                "evidence": "测试证据"
            }
        ]
        
        result = update_user_preference(preferences)
        
        # 验证返回消息 - 修正预期结果
        self.assertEqual(result, "保存用户偏好数据失败: 模拟文件读取错误")
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.path.exists', return_value=True)
    def test_update_user_preference_write_error(self, mock_exists, mock_file):
        """测试写入文件时发生错误的情况"""
        # 模拟文件写入错误
        mock_file.side_effect = IOError("模拟文件写入错误")
        
        preferences = [
            {
                "dimension": "回答风格-长度",
                "value": "concise",
                "confidence": "high",
                "evidence": "测试证据"
            }
        ]
        
        result = update_user_preference(preferences)
        
        # 验证返回错误消息
        self.assertEqual(result, "保存用户偏好数据失败: 模拟文件写入错误")

if __name__ == '__main__':
    unittest.main() 