"""
三元组导入Neo4j知识图谱
=======================
功能：
1. 批量读取JSON格式的三元组文件
2. 创建Neo4j图数据库中的节点和关系
3. 支持增量导入和清空重建

作者：整合自 md_split 项目
"""

import os
import json
from py2neo import Graph, Node, Relationship

###############################################################################
#                             全局配置区                                      #
###############################################################################

# ========== Neo4j配置 ==========
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "00000000"

# ========== 输入配置 ==========
# 三元组JSON文件夹路径（通常是 pdf_to_triple.py 的输出目录）
TRIPLES_FOLDER = r"D:\demo\output\7_triples_json"

# ========== 图谱配置 ==========
ROOT_NODE_NAME = "计算机网络知识图谱"  # 根节点名称
CLEAR_EXISTING = True  # 是否清空现有图谱（False=增量导入）

# ========== 节点标签 ==========
LABEL_ROOT = "Knowledge"           # 根节点标签
LABEL_SECTION = "Knowledge_section"  # 章节/文件节点标签
LABEL_ENTITY = "Knowledge_node"    # 实体节点标签

###############################################################################
#                             Neo4j 连接与操作                                #
###############################################################################

class KnowledgeGraphBuilder:
    """知识图谱构建器"""
    
    def __init__(self, uri: str, user: str, password: str):
        """
        初始化Neo4j连接
        
        Args:
            uri: Neo4j Bolt协议地址
            user: 用户名
            password: 密码
        """
        self.graph = Graph(uri, auth=(user, password))
        self.entity_cache = {}  # 缓存已创建的实体节点，避免重复查询
        print(f">>> 已连接到Neo4j: {uri}")
    
    def clear_graph(self):
        """清空现有知识图谱"""
        print(">>> 正在清空现有图谱...")
        self.graph.run(f"MATCH (n:{LABEL_ROOT}) DETACH DELETE n")
        self.graph.run(f"MATCH (n:{LABEL_SECTION}) DETACH DELETE n")
        self.graph.run(f"MATCH (n:{LABEL_ENTITY}) DETACH DELETE n")
        self.entity_cache.clear()
        print("    清空完成。")
    
    def create_root_node(self, name: str) -> Node:
        """创建根节点"""
        root = Node(LABEL_ROOT, name=name)
        self.graph.create(root)
        print(f">>> 已创建根节点: {name}")
        return root
    
    def create_section_node(self, name: str, root_node: Node = None) -> Node:
        """
        创建章节/文件节点
        
        Args:
            name: 章节名称
            root_node: 根节点（可选，用于建立层级关系）
        
        Returns:
            创建的章节节点
        """
        section = Node(LABEL_SECTION, name=name)
        self.graph.create(section)
        
        # 如果提供了根节点，创建关联关系
        if root_node:
            rel = Relationship(root_node, "CONTAINS", section)
            self.graph.create(rel)
        
        return section
    
    def get_or_create_entity(self, name: str) -> Node:
        """
        获取或创建实体节点（带缓存）
        
        Args:
            name: 实体名称
        
        Returns:
            实体节点
        """
        if not name or not name.strip():
            return None
        
        name = name.strip()
        
        # 先检查缓存
        if name in self.entity_cache:
            return self.entity_cache[name]
        
        # 查询数据库
        node = self.graph.nodes.match(LABEL_ENTITY, name=name).first()
        
        if not node:
            # 创建新节点
            node = Node(LABEL_ENTITY, name=name)
            self.graph.create(node)
        
        # 加入缓存
        self.entity_cache[name] = node
        return node
    
    def create_triple_relationship(self, head: str, relation: str, tail: str, 
                                    section_node: Node = None) -> bool:
        """
        根据三元组创建节点和关系
        
        Args:
            head: 头实体名称
            relation: 关系名称
            tail: 尾实体名称
            section_node: 所属章节节点（可选）
        
        Returns:
            是否创建成功
        """
        if not head or not relation or not tail:
            return False
        
        # 获取或创建头尾实体节点
        head_node = self.get_or_create_entity(head)
        tail_node = self.get_or_create_entity(tail)
        
        if not head_node or not tail_node:
            return False
        
        # 创建三元组关系
        rel = Relationship(head_node, relation, tail_node)
        rel["name"] = relation
        self.graph.create(rel)
        
        # 如果提供了章节节点，创建包含关系
        if section_node:
            # 头实体与章节的关系
            section_rel_head = Relationship(section_node, "CONTAINS", head_node)
            self.graph.create(section_rel_head)
            
            # 尾实体与章节的关系
            section_rel_tail = Relationship(section_node, "CONTAINS", tail_node)
            self.graph.create(section_rel_tail)
        
        return True
    
    def import_triples_from_json(self, json_path: str, section_node: Node = None) -> int:
        """
        从JSON文件导入三元组
        
        Args:
            json_path: JSON文件路径
            section_node: 所属章节节点
        
        Returns:
            成功导入的三元组数量
        """
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        count = 0
        
        # 处理可能的嵌套结构
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    # 单个三元组
                    if self.create_triple_relationship(
                        item.get("head"),
                        item.get("relation"),
                        item.get("tail"),
                        section_node
                    ):
                        count += 1
                elif isinstance(item, list):
                    # 嵌套列表（分块结构）
                    for triple in item:
                        if isinstance(triple, dict):
                            if self.create_triple_relationship(
                                triple.get("head"),
                                triple.get("relation"),
                                triple.get("tail"),
                                section_node
                            ):
                                count += 1
        
        return count
    
    def build_from_folder(self, folder_path: str, root_name: str = ROOT_NODE_NAME,
                          clear_existing: bool = CLEAR_EXISTING):
        """
        从文件夹批量导入三元组构建知识图谱
        
        Args:
            folder_path: JSON文件夹路径
            root_name: 根节点名称
            clear_existing: 是否清空现有图谱
        """
        print("=" * 60)
        print("三元组导入Neo4j知识图谱")
        print("=" * 60)
        
        # 清空现有图谱
        if clear_existing:
            self.clear_graph()
        
        # 创建根节点
        root_node = self.create_root_node(root_name)
        
        # 获取所有JSON文件
        json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
        
        if not json_files:
            print(">>> 未找到JSON文件!")
            return
        
        print(f">>> 找到 {len(json_files)} 个JSON文件")
        
        total_triples = 0
        total_entities = 0
        
        for json_file in json_files:
            json_path = os.path.join(folder_path, json_file)
            section_name = os.path.splitext(json_file)[0]
            
            print(f"    处理: {json_file}")
            
            # 创建章节节点
            section_node = self.create_section_node(section_name, root_node)
            
            # 导入三元组
            count = self.import_triples_from_json(json_path, section_node)
            total_triples += count
            
            print(f"      导入 {count} 个三元组")
        
        total_entities = len(self.entity_cache)
        
        print("=" * 60)
        print("导入完成！")
        print(f"  - 章节数: {len(json_files)}")
        print(f"  - 实体数: {total_entities}")
        print(f"  - 三元组数: {total_triples}")
        print("=" * 60)
        
        # 输出一些统计查询示例
        print("\n可以在Neo4j浏览器中执行以下查询查看结果:")
        print(f"  - 查看所有节点: MATCH (n) RETURN n LIMIT 100")
        print(f"  - 查看根节点: MATCH (n:{LABEL_ROOT}) RETURN n")
        print(f"  - 查看章节: MATCH (n:{LABEL_SECTION}) RETURN n")
        print(f"  - 查看实体关系: MATCH (h)-[r]->(t) RETURN h,r,t LIMIT 50")


###############################################################################
#                             辅助函数                                        #
###############################################################################

def validate_json_files(folder_path: str) -> dict:
    """
    验证文件夹中的JSON文件格式
    
    Args:
        folder_path: JSON文件夹路径
    
    Returns:
        验证结果字典
    """
    results = {
        "valid": [],
        "invalid": [],
        "total_triples": 0
    }
    
    json_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    
    for json_file in json_files:
        json_path = os.path.join(folder_path, json_file)
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # 统计三元组数量
            count = 0
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and all(k in item for k in ['head', 'relation', 'tail']):
                        count += 1
                    elif isinstance(item, list):
                        for t in item:
                            if isinstance(t, dict) and all(k in t for k in ['head', 'relation', 'tail']):
                                count += 1
            
            results["valid"].append({
                "file": json_file,
                "triples": count
            })
            results["total_triples"] += count
            
        except Exception as e:
            results["invalid"].append({
                "file": json_file,
                "error": str(e)
            })
    
    return results


def print_validation_results(results: dict):
    """打印验证结果"""
    print("=" * 60)
    print("JSON文件验证结果")
    print("=" * 60)
    
    print(f"\n有效文件 ({len(results['valid'])} 个):")
    for item in results['valid']:
        print(f"  - {item['file']}: {item['triples']} 个三元组")
    
    if results['invalid']:
        print(f"\n无效文件 ({len(results['invalid'])} 个):")
        for item in results['invalid']:
            print(f"  - {item['file']}: {item['error']}")
    
    print(f"\n总计三元组数: {results['total_triples']}")
    print("=" * 60)


###############################################################################
#                             入口                                            #
###############################################################################

def main():
    """主函数"""
    
    # 验证JSON文件
    if os.path.exists(TRIPLES_FOLDER):
        results = validate_json_files(TRIPLES_FOLDER)
        print_validation_results(results)
        
        if not results['valid']:
            print("没有有效的JSON文件，退出。")
            return
        
        # 询问是否继续
        user_input = input("\n是否继续导入到Neo4j? (y/n): ").strip().lower()
        if user_input != 'y':
            print("已取消。")
            return
    else:
        print(f"错误: 文件夹不存在: {TRIPLES_FOLDER}")
        return
    
    # 构建知识图谱
    builder = KnowledgeGraphBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    builder.build_from_folder(
        folder_path=TRIPLES_FOLDER,
        root_name=ROOT_NODE_NAME,
        clear_existing=CLEAR_EXISTING
    )


def import_without_confirmation():
    """不需要确认的导入函数（用于自动化脚本）"""
    builder = KnowledgeGraphBuilder(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    builder.build_from_folder(
        folder_path=TRIPLES_FOLDER,
        root_name=ROOT_NODE_NAME,
        clear_existing=CLEAR_EXISTING
    )


if __name__ == "__main__":
    main()
