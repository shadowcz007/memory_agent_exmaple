from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any
import json
import os
import datetime

from starlette.middleware.cors import CORSMiddleware
import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from mcp.server.sse import SseServerTransport

# 创建 FastMCP 的子类并重写方法


class CustomMCP(FastMCP):
    def sse_app(self) -> Starlette:
        
        """Return an instance of the SSE server app."""
        message_path = getattr(self.settings, "message_path", "/messages/")
        sse = SseServerTransport(message_path)
    
        async def handle_sse(request: Request) -> None:
            async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,  # type: ignore[reportPrivateUsage]
            ) as streams:
                await self._mcp_server.run(
                    streams[0],
                    streams[1],
                    self._mcp_server.create_initialization_options(),
                )

        sse_path=getattr(self.settings, "sse_path", "/sse")
        app = Starlette(
            debug=self.settings.debug,
            routes=[
                Route(sse_path, endpoint=handle_sse),
                Mount(message_path, app=sse.handle_post_message),
            ],
        )
        
        # 添加 CORS 中间件
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # 调整此列表以允许特定来源
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        return app
        
    async def run_sse_async(self) -> None:
        """Run the server using SSE transport."""
        starlette_app = self.sse_app()

        config = uvicorn.Config(
            starlette_app,
            host=self.settings.host,
            port=self.settings.port,
            log_level=self.settings.log_level.lower(),
        )
        server = uvicorn.Server(config)
        await server.serve()

host= "0.0.0.0"
port = 8000
sse_path= "/sse"
message_path = "/messages/"


# 定义知识图谱的数据结构
class Entity:
    def __init__(self, name: str, entity_type: str, observations: List[str] = None):
        self.name = name
        self.entity_type = entity_type
        self.observations = observations or []
        
    def to_dict(self):
        return {
            "type": "entity",
            "name": self.name,
            "entityType": self.entity_type,
            "observations": self.observations
        }

class Relation:
    def __init__(self, from_entity: str, to_entity: str, relation_type: str):
        self.from_entity = from_entity
        self.to_entity = to_entity
        self.relation_type = relation_type
        
    def to_dict(self):
        return {
            "type": "relation",
            "from": self.from_entity,
            "to": self.to_entity,
            "relationType": self.relation_type
        }

class KnowledgeGraphManager:
    def __init__(self, memory_file_path: str = "memory.json"):
        self.memory_file_path = memory_file_path
        
    def load_graph(self):
        entities = []
        relations = []
        
        try:
            if os.path.exists(self.memory_file_path):
                with open(self.memory_file_path, "r", encoding='utf-8') as f:
                    lines = f.read().split("\n")
                    for line in lines:
                        if line.strip():
                            item = json.loads(line)
                            if item.get("type") == "entity":
                                entities.append(item)
                            elif item.get("type") == "relation":
                                relations.append(item)
        except Exception as e:
            print(f"Error loading graph: {e}")
            
        return {"entities": entities, "relations": relations}
    
    def save_graph(self, graph):
        lines = []
        for entity in graph["entities"]:
            lines.append(json.dumps(entity, ensure_ascii=False))
        for relation in graph["relations"]:
            lines.append(json.dumps(relation, ensure_ascii=False))
            
        with open(self.memory_file_path, "w", encoding='utf-8') as f:
            f.write("\n".join(lines))
    
    def create_entities(self, entities: List[Dict[str, Any]]):
        graph = self.load_graph()
        new_entities = []
        
        for entity in entities:
            if not any(e["name"] == entity["name"] for e in graph["entities"]):
                entity_dict = {
                    "type": "entity",
                    "name": entity["name"],
                    "entityType": entity["entityType"],
                    "observations": entity.get("observations", [])
                }
                graph["entities"].append(entity_dict)
                new_entities.append(entity_dict)
                
        self.save_graph(graph)
        return new_entities
    
    def create_relations(self, relations: List[Dict[str, Any]]):
        graph = self.load_graph()
        new_relations = []
        
        for relation in relations:
            if not any(r["from"] == relation["from"] and 
                      r["to"] == relation["to"] and 
                      r["relationType"] == relation["relationType"] 
                      for r in graph["relations"]):
                relation_dict = {
                    "type": "relation",
                    "from": relation["from"],
                    "to": relation["to"],
                    "relationType": relation["relationType"]
                }
                graph["relations"].append(relation_dict)
                new_relations.append(relation_dict)
                
        self.save_graph(graph)
        return new_relations
    
    def add_observations(self, observations: List[Dict[str, Any]]):
        graph = self.load_graph()
        results = []
        
        for obs in observations:
            entity_name = obs["entityName"]
            contents = obs["contents"]
            
            entity = next((e for e in graph["entities"] if e["name"] == entity_name), None)
            if not entity:
                raise ValueError(f"Entity with name {entity_name} not found")
                
            if "observations" not in entity:
                entity["observations"] = []
                
            new_observations = [content for content in contents if content not in entity["observations"]]
            entity["observations"].extend(new_observations)
            
            results.append({
                "entityName": entity_name,
                "addedObservations": new_observations
            })
            
        self.save_graph(graph)
        return results
    
    def delete_entities(self, entity_names: List[str]):
        graph = self.load_graph()
        
        graph["entities"] = [e for e in graph["entities"] if e["name"] not in entity_names]
        graph["relations"] = [r for r in graph["relations"] 
                             if r["from"] not in entity_names and r["to"] not in entity_names]
        
        self.save_graph(graph)
        return "Entities deleted successfully"
    
    def delete_observations(self, deletions: List[Dict[str, Any]]):
        graph = self.load_graph()
        
        for deletion in deletions:
            entity_name = deletion["entityName"]
            observations_to_delete = deletion["observations"]
            
            entity = next((e for e in graph["entities"] if e["name"] == entity_name), None)
            if entity:
                entity["observations"] = [o for o in entity["observations"] 
                                         if o not in observations_to_delete]
                
        self.save_graph(graph)
        return "Observations deleted successfully"
    
    def delete_relations(self, relations: List[Dict[str, Any]]):
        graph = self.load_graph()
        
        for relation in relations:
            graph["relations"] = [r for r in graph["relations"] 
                                if not (r["from"] == relation["from"] and 
                                       r["to"] == relation["to"] and 
                                       r["relationType"] == relation["relationType"])]
            
        self.save_graph(graph)
        return "Relations deleted successfully"
    
    def read_graph(self):
        return self.load_graph()
    
    def search_nodes(self, query: str):
        graph = self.load_graph()
        results = []
        
        query = query.lower()
        for entity in graph["entities"]:
            if (query in entity["name"].lower() or 
                query in entity["entityType"].lower() or 
                any(query in obs.lower() for obs in entity["observations"])):
                results.append(entity)
                
        return results
    
    def open_nodes(self, names: List[str]):
        graph = self.load_graph()
        results = []
        
        for name in names:
            entity = next((e for e in graph["entities"] if e["name"] == name), None)
            if entity:
                results.append(entity)
                
        return results
        
    def find_nearest_farthest_nodes(self, start_node: str, max_depth: int = None):
        """
        使用BFS查找与给定节点最近和最远的节点
        
        参数:
        - start_node: 起始节点名称
        - max_depth: 最大搜索深度（可选）
        
        返回:
        包含最近和最远节点的字典
        """
        graph = self.load_graph()
        
        # 检查起始节点是否存在
        if not any(e["name"] == start_node for e in graph["entities"]):
            raise ValueError(f"起始节点 {start_node} 不存在")
            
        # 构建邻接表
        adjacency = {}
        for entity in graph["entities"]:
            adjacency[entity["name"]] = set()
            
        for relation in graph["relations"]:
            from_node = relation["from"]
            to_node = relation["to"]
            adjacency[from_node].add(to_node)
            adjacency[to_node].add(from_node)  # 假设关系是双向的
            
        # BFS实现
        queue = [(start_node, 0)]  # (节点, 深度)
        visited = {start_node}
        nearest_nodes = []
        farthest_nodes = []
        current_depth = 0
        max_depth_found = 0
        
        while queue:
            node, depth = queue.popleft() if hasattr(queue, 'popleft') else queue.pop(0)
            
            # 更新最近和最远节点
            if depth == 1:  # 最近的节点（深度为1）
                nearest_nodes.append(node)
            if depth > max_depth_found:  # 发现更远的节点
                max_depth_found = depth
                farthest_nodes = [node]
            elif depth == max_depth_found:  # 同样远的节点
                farthest_nodes.append(node)
                
            # 如果达到最大深度，停止继续搜索
            if max_depth and depth >= max_depth:
                continue
                
            # 遍历邻居节点
            for neighbor in adjacency[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))
        
        return {
            "nearest_nodes": nearest_nodes,
            "farthest_nodes": farthest_nodes,
            "max_depth": max_depth_found
        }
# 创建 MCP 服务器
# mcp = FastMCP("KnowledgeGraph", port=6688)
# 使用自定义的 MCP 类替代原来的 FastMCP
mcp = CustomMCP("KnowledgeGraph",port=6688,message_path=message_path,host=host,sse_path=sse_path)

kg_manager = KnowledgeGraphManager()

@mcp.tool()
def create_entities(entities: List[Dict[str, Any]]) -> str:
    """
    创建新实体
    
    参数:
    - entities: 要创建的实体列表，每个实体包含 name, entityType 和可选的 observations
    """
    result = kg_manager.create_entities(entities)
    return json.dumps(result, indent=2)

@mcp.tool()
def create_relations(relations: List[Dict[str, Any]]) -> str:
    """
    创建新关系
    
    参数:
    - relations: 要创建的关系列表，每个关系包含 from, to 和 relationType
    """
    result = kg_manager.create_relations(relations)
    return json.dumps(result, indent=2)

@mcp.tool()
def add_observations(observations: List[Dict[str, Any]]) -> str:
    """
    为实体添加观察内容
    
    参数:
    - observations: 要添加的观察列表，每项包含 entityName 和 contents(字符串列表)
    """
    result = kg_manager.add_observations(observations)
    return json.dumps(result, indent=2)

@mcp.tool()
def delete_entities(entity_names: List[str]) -> str:
    """
    删除实体
    
    参数:
    - entity_names: 要删除的实体名称列表
    """
    return kg_manager.delete_entities(entity_names)

@mcp.tool()
def delete_observations(deletions: List[Dict[str, Any]]) -> str:
    """
    删除实体的观察内容
    
    参数:
    - deletions: 要删除的观察列表，每项包含 entityName 和 observations(字符串列表)
    """
    return kg_manager.delete_observations(deletions)

@mcp.tool()
def delete_relations(relations: List[Dict[str, Any]]) -> str:
    """
    删除关系
    
    参数:
    - relations: 要删除的关系列表，每个关系包含 from, to 和 relationType
    """
    return kg_manager.delete_relations(relations)

@mcp.tool()
def read_graph() -> str:
    """
    读取整个知识图谱
    """
    result = kg_manager.read_graph()
    return json.dumps(result, indent=2)

@mcp.tool()
def search_nodes(query: str) -> str:
    """
    搜索知识图谱中的节点
    
    参数:
    - query: 搜索查询字符串，将匹配实体名称、类型和观察内容
    """
    result = kg_manager.search_nodes(query)
    return json.dumps(result, indent=2)

@mcp.tool()
def open_nodes(names: List[str]) -> str:
    """
    通过名称打开特定节点
    
    参数:
    - names: 要检索的实体名称列表
    """
    result = kg_manager.open_nodes(names)
    return json.dumps(result, indent=2)

@mcp.tool()
def find_nearest_farthest_nodes(start_node: str, max_depth: int = None) -> str:
    """
    查找与给定节点最近和最远的节点
    
    参数:
    - start_node: 起始节点名称
    - max_depth: 最大搜索深度（可选）
    """
    result = kg_manager.find_nearest_farthest_nodes(start_node, max_depth)
    return json.dumps(result, indent=2)

@mcp.tool()
def update_user_preference(preferences: List[Dict[str, Any]]) -> str:
    """
    接收并存储用户偏好数据
    
    参数:
    - preferences: 用户偏好列表，每个偏好包含 dimension, value, confidence 和 evidence
    """
    preference_file = "user_preference.json"
    current_time = datetime.datetime.now().isoformat()
    
    # 为每个偏好添加时间戳
    for pref in preferences:
        pref["create_time"] = current_time
    
    # 读取现有偏好数据（如果存在）
    existing_preferences = []
    if os.path.exists(preference_file):
        try:
            with open(preference_file, "r", encoding='utf-8') as f:
                existing_preferences = json.load(f)
        except Exception as e:
            print(f"读取用户偏好文件错误: {e}")
    
    # 合并新的偏好数据
    existing_preferences.extend(preferences)
    
    # 保存更新后的偏好数据
    try:
        with open(preference_file, "w", encoding='utf-8') as f:
            json.dump(existing_preferences, f, ensure_ascii=False, indent=2)
        return f"成功保存 {len(preferences)} 条用户偏好数据"
    except Exception as e:
        return f"保存用户偏好数据失败: {e}"

@mcp.tool()
def get_user_preference(create_time: str = None, count: int = None) -> str:
    """
    获取用户偏好数据并拼接到chat_prompt中返回
    
    参数:
    - create_time: 筛选偏好的日期时间（可选）
    - count: 返回的偏好数量（可选）
    """
    preference_file = "user_preference.json"
  
    # 读取用户偏好数据
    if not os.path.exists(preference_file):
        return "未找到用户偏好数据"
    
    try:
        with open(preference_file, "r", encoding='utf-8') as f:
            preferences = json.load(f)
    except Exception as e:
        return f"读取用户偏好数据失败: {e}"
    
    # 根据create_time筛选
    if create_time:
        filtered_prefs = [p for p in preferences if p.get("create_time", "").startswith(create_time)]
    else:
        filtered_prefs = preferences
    
    # 根据count限制数量
    if count and count > 0:
        filtered_prefs = filtered_prefs[:min(count, len(filtered_prefs))]
    
    # 如果没有符合条件的偏好数据
    if not filtered_prefs:
        return "没有找到符合条件的用户偏好数据"
    
    # 将偏好数据转换为JSON字符串
    user_preferences_json = json.dumps(filtered_prefs, ensure_ascii=False, indent=2)
    
    # 拼接chat_prompt
    chat_prompt = f"""
你是一个智能且善于适应的 AI 助手。在与用户交互时，请务必参考并应用以下提供的用户偏好信息。这些信息反映了用户的习惯和需求，遵循它们能提供更个性化、更贴心的服务。

当前用户偏好 (JSON 格式):

{user_preferences_json}

应用指南:

1 解读偏好:

- 仔细阅读 dimension 和 value 字段，理解用户的具体偏好。例如，"回答风格-长度": "concise" 意味着用户喜欢简短的回答；"技术背景-编程语言": ["JavaScript"] 表示用户熟悉 JavaScript。

- confidence 字段（如果存在）表示该偏好的可信度。对于 low 置信度的偏好，请谨慎参考；对于 high 或 medium 置信度的偏好，应优先考虑。

- evidence 字段提供了推断该偏好的依据，有助于你理解偏好的背景。

2 调整回答:

风格适应: 根据 "回答风格" (长度、深度、正式度) 和 "语言与语气" (风格、表情符号使用) 调整你的措辞和表达方式。

3 内容定制:

- 根据 "学习与解释方式" 选择最适合用户的解释方法（如代码示例、类比）。

- 根据 "技术背景与工具" 调整技术内容的深度，使用用户熟悉的语言或工具进行举例。

- 在涉及相关领域时，务必考虑 "领域特定偏好"（如推荐食谱时考虑素食偏好）。

4 格式选择: 如果用户有 "格式偏好"（如列表、表格），尽量满足。

5 优先级:

- 当前指令优先: 如果用户在当前问题中明确提出了与已存偏好不同的要求（例如，偏好简短回答的用户这次要求"请详细解释"），请优先遵循用户的当前指令。

- 高置信度优先: 在没有明确指令冲突时，优先应用置信度高的偏好。

6 处理缺失/冲突:

- 偏好缺失: 如果某个维度的偏好没有记录，请使用通用的最佳实践（清晰、中立、适度详细）来回应。

- 偏好冲突 (理论上不应由该 Prompt 处理，应在生成偏好时解决): 如果遇到内部冲突的偏好，请尝试理解用户意图或使用最通用、最安全的选项。

你的目标: 像一个了解用户习惯的朋友一样进行交流，提供精准、贴心且高效的帮助。
"""
    
    return chat_prompt

@mcp.prompt()
def user_preference_extract_prompt(message: str) -> str:
    """
    从对话历史中提取用户偏好的提示词
    
    参数:
    - message: 包含对话历史的字符串
    """
    return """
你是一个精密的分析助手，擅长从人类对话中识别和推断用户偏好。

任务: 分析以下用户与 AI 助手的对话记录，识别并提取潜在的用户偏好。请关注用户的提问方式、语气、反馈、明确要求以及对话中隐含的线索。

输入: {
  "conversation_history": [
    {"role": "user", "content": "用户第一句话"},
    {"role": "assistant", "content": "助手第一句话"},
    {"role": "user", "content": "用户第二句话"},
    {"role": "assistant", "content": "助手第二句话"},
    // ... 更多对话轮次
  ]
}

需要分析和提取的偏好维度 (请尽可能全面地考虑以下方面):

1. 回答风格 (Content Style):
   - 长度 (Length): 用户是倾向于简短、核心的回答 (concise)，还是详细、全面的解释 (detailed)？（例如：用户是否经常说"简单点说"或"能再详细点吗？"）
   - 深度/专业性 (Depth/Professionalism): 用户是需要基础入门的解释 (beginner)，还是能理解专业术语和复杂概念 (expert)？（例如：用户是否频繁询问基础定义，或直接使用专业术语？）
   - 正式度 (Formality): 用户倾向于正式 (formal) 还是非正式/随意 (casual) 的交流？

2. 语言与语气 (Language & Tone):
   - 语言风格 (Language Style): 用户是否使用或偏好特定的语言风格，如幽默、严谨、带有表情符号 (use_emoji) 等？
   - 翻译需求 (Translation Needs): 用户是否提及或暗示需要其他语言的翻译？（例如："preferred_language_translation": "Spanish"）

3. 学习与解释方式 (Learning & Explanation):
   - 偏好方式 (Preferred Method): 用户更喜欢通过代码示例 (code_examples)、理论解释 (theory)、生活类比 (analogy) 还是图表/视觉化 (visuals) 来理解信息？（例如：用户是否经常要求"给个例子看看"或"有没有图表？"）

4. 技术背景与工具 (Technical Background & Tools):
   - 编程语言 (Programming Languages): 用户熟悉或偏好哪些编程语言？（例如："programming_languages": ["Python", "JavaScript"]）
   - 软件/工具 (Software/Tools): 用户是否提及常用的软件或工具？
   - 技术水平 (Technical Level): 用户在特定领域（如编程、设计）的整体技术水平是初学者、中级还是专家？

5. 领域特定偏好 (Domain-Specific Preferences):
   - 饮食习惯 (Dietary): 如素食 (vegetarian)、无麸质 (gluten_free) 等
   - 兴趣爱好 (Interests): 如特定类型的音乐、电影、书籍、运动等
   - 预算/成本敏感度 (Budget Sensitivity): 在讨论购物、旅行等话题时是否关注价格？
   - 可访问性需求 (Accessibility Needs): 是否提及视觉、听觉或其他方面的辅助需求？

6. 交互模式 (Interaction Patterns):
   - 主动性 (Proactivity): 用户是否喜欢 AI 主动提供建议或扩展信息？
   - 澄清频率 (Clarification Frequency): 用户是否经常需要 AI 澄清回答？这可能暗示需要更清晰或简单的表达。

7. 格式偏好 (Format Preferences):
   - 用户是否偏好特定的信息组织格式，如列表 (list)、表格 (table)、段落 (paragraph)？

输出格式: 请将提取到的偏好以 JSON 格式输出。对于每个识别出的偏好，请包含以下字段：
- dimension: 偏好所属的维度 (例如: "回答风格-长度", "技术背景-编程语言")
- value: 推断出的偏好值 (例如: "concise", ["Python", "JavaScript"], "beginner")
- confidence: 你对这个推断的置信度（可选，例如: "high", "medium", "low"）
- evidence: 对话中支持该推断的具体证据或用户语句（引用原文）

示例输出: [
  {
    "dimension": "回答风格-长度",
    "value": "concise",
    "confidence": "high",
    "evidence": "用户说：'长话短说，告诉我关键点就行。'"
  },
  {
    "dimension": "技术背景-编程语言",
    "value": ["JavaScript"],
    "confidence": "medium",
    "evidence": "用户多次询问关于 React 和 Node.js 的问题，并提供了 JS 代码片段。"
  },
  {
    "dimension": "语言与语气-语言风格",
    "value": "casual_with_emoji",
    "confidence": "high",
    "evidence": "用户在对话中多次使用 😊 和 👍 等表情符号，语言风格较为随意。"
  },
  {
    "dimension": "领域特定偏好-饮食习惯",
    "value": ["vegetarian"],
    "confidence": "high",
    "evidence": "用户明确提到：'我是素食主义者，请推荐一些不含肉的食谱。'"
  }
]

注意事项:
- 如果对话数据不足以推断某个维度的偏好，请不要强行输出
- 专注于从对话中直接或间接反映出来的偏好
- 置信度可以帮助后续系统判断偏好的可靠性
- 提供的证据应尽可能具体

"""+f"分析以下对话记录: {message}"

if __name__ == "__main__":
    mcp.run(transport='sse')