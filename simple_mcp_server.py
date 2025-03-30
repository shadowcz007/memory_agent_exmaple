import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

import uvicorn
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# 知识图谱层：简单使用JSON文件存储
DATA_FILE = "memory_data.json"

def load_data() -> Dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"conversations": {}, "memories": {}}

def save_data(data: Dict) -> None:
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

# 记忆模块
class MemoryManager:
    @staticmethod
    def generate_memory(message: str) -> Dict:
        # 简化实现：从消息中提取关键信息作为记忆
        return {
            "id": str(uuid.uuid4()),
            "content": message,
            "created_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def retrieve_memories(conversation_id: str, query: str) -> List[Dict]:
        # 简化实现：检索与当前对话相关的记忆
        data = load_data()
        return data.get("memories", {}).get(conversation_id, [])
    
    @staticmethod
    def store_memory(conversation_id: str, memory: Dict) -> None:
        data = load_data()
        if conversation_id not in data["memories"]:
            data["memories"][conversation_id] = []
        data["memories"][conversation_id].append(memory)
        save_data(data)

# MCP服务器层
class MCPServer:
    @staticmethod
    async def process_message(conversation_id: str, message: str) -> str:
        # 加载数据
        data = load_data()
        
        # 创建新对话或更新现有对话
        if conversation_id not in data["conversations"]:
            data["conversations"][conversation_id] = []
        
        # 存储用户消息
        data["conversations"][conversation_id].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # 生成记忆
        memory = MemoryManager.generate_memory(message)
        MemoryManager.store_memory(conversation_id, memory)
        
        # 检索相关记忆
        relevant_memories = MemoryManager.retrieve_memories(conversation_id, message)
        
        # 生成回复（简化实现）
        response = f"收到消息: {message}"
        if relevant_memories:
            response += f"\n我记得: {relevant_memories[-1]['content']}"
        
        # 存储助手回复
        data["conversations"][conversation_id].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        save_data(data)
        return response

# SSE服务层
async def sse_endpoint(request):
    # 在实际实现中，这里应该建立SSE连接
    # 简化实现，直接返回成功消息
    return JSONResponse({"status": "connected"})

async def message_endpoint(request):
    data = await request.json()
    conversation_id = data.get("conversation_id", str(uuid.uuid4()))
    message = data.get("message", "")
    
    response = await MCPServer.process_message(conversation_id, message)
    
    return JSONResponse({
        "conversation_id": conversation_id,
        "response": response
    })

# 路由配置
routes = [
    Route("/", endpoint=sse_endpoint, methods=["GET"]),
    Route("/messages", endpoint=message_endpoint, methods=["POST"]),
]

# 中间件配置
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
]

# 创建应用
app = Starlette(routes=routes, middleware=middleware)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)


'''
// 发送消息到服务器
async function sendMessage(message, conversationId = null) {
  try {
    const response = await fetch('http://localhost:8000/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        conversation_id: conversationId,
        message: message
      }),
    });
    
    const data = await response.json();
    console.log('收到回复:', data.response);
    
    // 保存会话ID以便后续使用
    return data.conversation_id;
  } catch (error) {
    console.error('发送消息出错:', error);
  }
}

// 使用示例
async function chatExample() {
  // 第一条消息，不提供conversationId
  const conversationId = await sendMessage('你好，我是用户');
  
  // 后续消息使用相同的conversationId
  await sendMessage('我想了解更多关于记忆功能', conversationId);
}

// 运行示例
chatExample();
'''