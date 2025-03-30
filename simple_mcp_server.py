from starlette.applications import Starlette
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route
from starlette.background import BackgroundTask
import uvicorn
import json
import os
from datetime import datetime
from typing import Dict, List

# 知识图谱层
class KnowledgeGraph:
    def __init__(self, storage_file: str = "memory.json"):
        self.storage_file = storage_file
        self.memories = self._load_memories()

    def _load_memories(self) -> List[Dict]:
        if not os.path.exists(self.storage_file):
            return []
        with open(self.storage_file, "r") as f:
            return json.load(f)

    def save_memory(self, memory: Dict):
        self.memories.append(memory)
        with open(self.storage_file, "w") as f:
            json.dump(self.memories, f)

    def search_memories(self, query: str) -> List[Dict]:
        return [m for m in self.memories if query.lower() in m["content"].lower()]

# MCP Server 层
class MCPServer:
    def __init__(self):
        self.kg = KnowledgeGraph()
        self.conversation_history = []

    def generate_memory(self, conversation: Dict) -> Dict:
        # 简化版记忆生成器
        return {
            "content": conversation["user_input"][-100:],  # 截取最后100字符
            "timestamp": datetime.now().isoformat(),
            "context": conversation["context"][:3]  # 只保留前3条上下文
        }

    def process_conversation(self, user_input: str, context: List[str]) -> Dict:
        # 简化版对话处理
        conversation = {"user_input": user_input, "context": context}
        
        # 记忆生成与存储
        memory = self.generate_memory(conversation)
        self.kg.save_memory(memory)
        
        # 记忆检索
        relevant_memories = self.kg.search_memories(user_input)
        
        # 更新对话历史
        self.conversation_history.append(conversation)
        
        return {
            "response": f"Echo: {user_input}",
            "memories": relevant_memories[:2]  # 最多返回2条相关记忆
        }

# SSE 服务层
app = Starlette()
mcp = MCPServer()

async def sse_stream(request):
    async def event_stream():
        data = await request.json()
        result = mcp.process_conversation(
            data.get("user_input", ""),
            data.get("context", [])
        )
        yield f"data: {json.dumps(result)}\n\n"
    
    return StreamingResponse(event_stream(), media_type="text/event-stream")

async def http_handler(request):
    data = await request.json()
    result = mcp.process_conversation(
        data.get("user_input", ""),
        data.get("context", [])
    )
    return JSONResponse(result)

app.add_route("/sse", sse_stream, methods=["POST"])
app.add_route("/http", http_handler, methods=["POST"])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)