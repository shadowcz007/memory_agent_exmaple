from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any
import json
import os

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
                with open(self.memory_file_path, "r") as f:
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
            lines.append(json.dumps(entity))
        for relation in graph["relations"]:
            lines.append(json.dumps(relation))
            
        with open(self.memory_file_path, "w") as f:
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

# 创建 MCP 服务器
mcp = FastMCP("KnowledgeGraph", port=6688 )
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

if __name__ == "__main__":
    mcp.run(transport='sse')