from mcp import ClientSession, types
from mcp.client.sse import sse_client
import asyncio
import json

async def run():
    # 创建SSE连接到服务器，端口6688，路径/sse
    async with sse_client("http://localhost:6688/sse") as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化连接
            print("初始化连接...")
            await session.initialize()
            print("连接初始化完成")

            # result = await session.get_prompt("user_preference_extract_prompt", {
            #         "message":json.dumps([
            #             {"role": "user", "content": "用户消息1"},
            #             {"role": "assistant", "content": "助手回复1"},
            #             {"role": "user", "content": "用户消息2"}
            #         ],ensure_ascii=False,indent=2) 
            # })
            # print(f"用户偏好prompt: {result}")

            # 测试 update_user_preference 工具
            # print("\n测试 update_user_preference...")
            # preferences = [
            #     {
            #         "dimension": "回答风格-长度",
            #         "value": "concise", 
            #         "confidence": "high",
            #         "evidence": "用户说：'长话短说，告诉我关键点就行。'"
            #     },
            #     {
            #         "dimension": "技术背景-编程语言",
            #         "value": ["Python", "JavaScript"],
            #         "confidence": "medium",
            #         "evidence": "用户多次询问关于Python和React的问题。"
            #     },
            #     {
            #         "dimension": "语言与语气-语言风格",
            #         "value": "casual_with_emoji",
            #         "confidence": "medium",
            #         "evidence": "用户在对话中经常使用表情符号。"
            #     }
            # ]
            # result = await session.call_tool("update_user_preference", {"preferences": preferences})
            # print(f"更新用户偏好结果: {result}")
            
            # 测试 get_user_preference 工具
            print("\n测试 get_user_preference...")
            # 获取所有偏好
            result = await session.call_tool("get_user_preference", { 
            })
            print(result)
            
            # 测试限制数量的参数
            print("\n测试限制偏好数量...")
            result = await session.call_tool("get_user_preference", {"count": 1})
            print(result)
            
            # 注：如果需要测试日期筛选功能，可以使用以下代码
            # 需要将DATE替换为实际的日期前缀(例如"2023-10-24")
            print("\n测试按日期筛选偏好...")
            result = await session.call_tool("get_user_preference", {"create_time": "DATE"})
            print(f"按日期筛选的用户偏好:\n{result[:300]}...(内容较长，省略部分显示)")

            # # 列出可用工具
            # print("\n获取可用工具列表...")
            # tools = await session.list_tools()
            # print(f"可用工具: {tools}")

            # # 创建实体
            # print("\n创建实体...")
            # entities = [
            #     {
            #         "name": "张三",
            #         "entityType": "人物",
            #         "observations": ["喜欢打篮球", "是一名软件工程师"]
            #     },
            #     {
            #         "name": "李四",
            #         "entityType": "人物",
            #         "observations": ["喜欢读书", "是一名教师"]
            #     }
            # ]
            # result = await session.call_tool("create_entities", {"entities": entities})
            # print(f"创建实体结果: {result}")

            # # 创建关系
            # print("\n创建关系...")
            # relations = [
            #     {
            #         "from": "张三",
            #         "to": "李四",
            #         "relationType": "朋友"
            #     }
            # ]
            # result = await session.call_tool("create_relations", {"relations": relations})
            # print(f"创建关系结果: {result}")

            # # 添加观察
            # print("\n添加观察...")
            # observations = [
            #     {
            #         "entityName": "张三",
            #         "contents": ["住在北京", "今年35岁"]
            #     }
            # ]
            # result = await session.call_tool("add_observations", {"observations": observations})
            # print(f"添加观察结果: {result}")

            # # 读取整个图谱
            # print("\n读取整个知识图谱...")
            # result = await session.call_tool("read_graph", {})
            # print(f"知识图谱内容: {result}")

            # # 搜索节点
            # print("\n搜索节点...")
            # result = await session.call_tool("search_nodes", {"query": "软件"})
            # print(f"搜索结果: {result}")

            # # 打开特定节点
            # print("\n打开特定节点...")
            # result = await session.call_tool("open_nodes", {"names": ["张三"]})
            # print(f"节点内容: {result}")

            # # 删除观察
            # print("\n删除观察...")
            # deletions = [
            #     {
            #         "entityName": "张三",
            #         "observations": ["今年35岁"]
            #     }
            # ]
            # result = await session.call_tool("delete_observations", {"deletions": deletions})
            # print(f"删除观察结果: {result}")

            # # 删除关系
            # print("\n删除关系...")
            # result = await session.call_tool("delete_relations", {"relations": relations})
            # print(f"删除关系结果: {result}")

            # # 删除实体
            # print("\n删除实体...")
            # result = await session.call_tool("delete_entities", {"entity_names": ["李四"]})
            # print(f"删除实体结果: {result}")

            # # 再次读取图谱确认更改
            # print("\n再次读取知识图谱...")
            # result = await session.call_tool("read_graph", {})
            # print(f"更新后的知识图谱内容: {result}")

if __name__ == "__main__":
    asyncio.run(run())