import asyncio
import json
from typing import List, Dict
from mcp import ClientSession, types
from mcp.client.sse import sse_client
import httpx
import json_repair

# LLM API配置
API_KEY = "sk-你的key"  # 替换为您的API密钥
API_BASE = "https://api.siliconflow.cn/v1"
MODEL = "Qwen/Qwen2.5-7B-Instruct"

# 知识提取的function schema
KNOWLEDGE_EXTRACTION_FUNCTIONS = [
    {
        "type": "function",
        "function": {
            "name": "extract_knowledge",
            "description": "从文本中提取知识实体和关系",
            "parameters": {
                "type": "object",
                "properties": {
                    "entities": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "实体名称"},
                                "entityType": {"type": "string", "description": "实体类型"},
                                "observations": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "关于实体的观察/属性"
                                }
                            },
                            "required": ["name", "entityType", "observations"]
                        }
                    },
                    "relations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "from": {"type": "string", "description": "关系起点实体"},
                                "to": {"type": "string", "description": "关系终点实体"},
                                "relationType": {"type": "string", "description": "关系类型"}
                            },
                            "required": ["from", "to", "relationType"]
                        }
                    }
                },
                "required": ["entities", "relations"]
            }
        }
    }
]

async def call_llm(content: str) -> Dict:
    """调用LLM API提取知识"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一个知识提取助手。请从用户输入中提取关键实体、实体类型、实体属性和实体间的关系。"
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                "tools": KNOWLEDGE_EXTRACTION_FUNCTIONS,
                "temperature": 0.6
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"LLM API调用失败: {response.text}")
            
        result = response.json()
        
        # 添加调试信息
        print("LLM 原始响应:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if "choices" not in result or not result["choices"]:
            raise Exception("LLM响应中没有choices字段")
            
        if "message" not in result["choices"][0]:
            raise Exception("LLM响应中没有message字段")
            
        message = result["choices"][0]["message"]
        if "tool_calls" not in message or not message["tool_calls"]:
            raise Exception("LLM未返回tool_calls")
            
        tool_call = message["tool_calls"][0]
        if "function" not in tool_call or "arguments" not in tool_call["function"]:
            raise Exception("tool_calls格式不正确")
            
        try:
            arguments = tool_call["function"]["arguments"]
            try:
                # 使用 json_repair 来修复和解析 JSON
                return json_repair.loads(arguments)
            except Exception as e:
                print("JSON修复和解析错误，原始内容:")
                print(arguments)
                raise Exception(f"JSON修复和解析失败: {str(e)}")
                
        except Exception as e:
            print("获取参数失败，原始响应:")
            print(tool_call)
            raise Exception(f"处理tool_calls失败: {str(e)}")

async def save_to_memory(session: ClientSession, extracted_knowledge: Dict):
    """将提取的知识保存到记忆库"""
    # 保存实体
    if extracted_knowledge["entities"]:
        await session.call_tool("create_entities", {"entities": extracted_knowledge["entities"]})
        print("实体保存成功")

    # 保存关系
    if extracted_knowledge["relations"]:
        await session.call_tool("create_relations", {"relations": extracted_knowledge["relations"]})
        print("关系保存成功")

async def main():
    # 连接到记忆服务器
    async with sse_client("http://localhost:6688/sse") as (read, write):
        async with ClientSession(read, write) as session:
            print("已连接到记忆服务器")
            await session.initialize()

            while True:
                try:
                    # 获取用户输入
                    user_input = input("\n请输入要保存的知识(输入'quit'退出):\n")
                    if user_input.lower() == 'quit':
                        break

                    # 使用LLM提取知识
                    print("正在提取知识...")
                    extracted_knowledge = await call_llm(user_input)
                    print("\n提取的知识:")
                    print(json.dumps(extracted_knowledge, ensure_ascii=False, indent=2))

                    # 确认是否保存
                    confirm = input("\n是否保存这些知识？(y/n): ")
                    if confirm.lower() == 'y':
                        # 保存到记忆库
                        await save_to_memory(session, extracted_knowledge)
                        print("知识已成功保存到记忆库")
                    else:
                        print("已取消保存")

                except Exception as e:
                    print(f"错误: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())