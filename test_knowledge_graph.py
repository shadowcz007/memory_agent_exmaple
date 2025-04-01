from memory_mcp_server import KnowledgeGraphManager
import json

def test_knowledge_graph():
    # 初始化知识图谱管理器
    kg = KnowledgeGraphManager("test_memory.json")
    
    # 测试用例1：创建一个简单的星形图
    print("\n测试用例1: 星形图")
    entities = [
        {"name": "张三", "entityType": "人物"},
        {"name": "足球", "entityType": "运动"},
        {"name": "篮球", "entityType": "运动"},
        {"name": "游泳", "entityType": "运动"}
    ]
    kg.create_entities(entities)
    
    relations = [
        {"from": "张三", "to": "足球", "relationType": "喜欢"},
        {"from": "张三", "to": "篮球", "relationType": "喜欢"},
        {"from": "张三", "to": "游泳", "relationType": "喜欢"}
    ]
    kg.create_relations(relations)
    
    result = kg.find_nearest_farthest_nodes("张三")
    print("星形图结果:", json.dumps(result, ensure_ascii=False, indent=2))
    # 预期：所有运动都是最近的节点（深度1），没有最远节点
    
    # 测试用例2：创建一个链式图
    print("\n测试用例2: 链式图")
    entities = [
        {"name": "北京", "entityType": "城市"},
        {"name": "上海", "entityType": "城市"},
        {"name": "广州", "entityType": "城市"},
        {"name": "深圳", "entityType": "城市"}
    ]
    kg.create_entities(entities)
    
    relations = [
        {"from": "北京", "to": "上海", "relationType": "连接"},
        {"from": "上海", "to": "广州", "relationType": "连接"},
        {"from": "广州", "to": "深圳", "relationType": "连接"}
    ]
    kg.create_relations(relations)
    
    result = kg.find_nearest_farthest_nodes("北京")
    print("链式图结果:", json.dumps(result, ensure_ascii=False, indent=2))
    # 预期：上海是最近的节点，深圳是最远的节点
    
    # 测试用例3：创建一个环形图
    print("\n测试用例3: 环形图")
    entities = [
        {"name": "春天", "entityType": "季节"},
        {"name": "夏天", "entityType": "季节"},
        {"name": "秋天", "entityType": "季节"},
        {"name": "冬天", "entityType": "季节"}
    ]
    kg.create_entities(entities)
    
    relations = [
        {"from": "春天", "to": "夏天", "relationType": "转换"},
        {"from": "夏天", "to": "秋天", "relationType": "转换"},
        {"from": "秋天", "to": "冬天", "relationType": "转换"},
        {"from": "冬天", "to": "春天", "relationType": "转换"}
    ]
    kg.create_relations(relations)
    
    result = kg.find_nearest_farthest_nodes("春天")
    print("环形图结果:", json.dumps(result, ensure_ascii=False, indent=2))
    # 预期：夏天是最近的节点，秋天和冬天是最远的节点
    
    # 测试用例4：带有最大深度限制
    print("\n测试用例4: 带深度限制的图")
    result = kg.find_nearest_farthest_nodes("春天", max_depth=1)
    print("深度限制结果:", json.dumps(result, ensure_ascii=False, indent=2))
    # 预期：只显示深度1的节点
    
    # 测试用例5：孤立节点
    print("\n测试用例5: 孤立节点")
    entities = [
        {"name": "孤岛", "entityType": "地点"}
    ]
    kg.create_entities(entities)
    
    result = kg.find_nearest_farthest_nodes("孤岛")
    print("孤立节点结果:", json.dumps(result, ensure_ascii=False, indent=2))
    # 预期：没有最近和最远的节点
    
    # 清理测试文件
    import os
    if os.path.exists("test_memory.json"):
        os.remove("test_memory.json")

if __name__ == "__main__":
    test_knowledge_graph()