from py2neo import Graph, Node, Relationship
import os
import json

# 连接到 Neo4j 数据库
graph = Graph("bolt://localhost:7687", auth=("neo4j", "00000000"))

# 删除知识图谱相关的所有节点
graph.run("MATCH (n:Knowledge) DETACH DELETE n")
graph.run("MATCH (n:Knowledge_section) DETACH DELETE n")
graph.run("MATCH (n:Knowledge_node) DETACH DELETE n")

# 创建根节点
root_node = Node("Knowledge", name="计算机网络-谢希仁")
graph.create(root_node)

# 指定三元组 JSON 文件夹路径
base_dir = r"D:\\pythonProject\\md_split\\new_triple"

# 遍历文件夹中的所有文件
for file_name in os.listdir(base_dir):
    # 构建文件完整路径
    file_path = os.path.join(base_dir, file_name)

    # 跳过非 JSON 文件
    if not file_name.endswith(".json"):
        continue

    # 使用固定的标签 Knowledge_section，而不是文件名
    section_label = "Knowledge_section"

    # 创建 Knowledge_section 节点，并将文件名作为属性
    section_node = Node(section_label, name=file_name.split(".")[0])  # 只取文件名，不包含扩展名
    graph.create(section_node)

    # 打开并读取 JSON 文件内容
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 遍历 JSON 文件中的三元组
    for item in data:
        # 确保 item 是字典并且包含 'head', 'relation', 'tail' 键
        if isinstance(item, dict):
            head = item.get("head", None)
            relation = item.get("relation", None)
            tail = item.get("tail", None)

            # 检查是否提取到值并避免空值
            if head and relation and tail:
                print(f"Head: {head}, Relation: {relation}, Tail: {tail}")
            else:
                print("Missing expected values in item:", item)
        else:
            print("Item is not a valid dictionary:", item)

        # 检查并创建头实体节点
        head_node = graph.nodes.match("Knowledge_node", name=head).first()
        if not head_node:
            head_node = Node("Knowledge_node", name=head)
            graph.create(head_node)

        # 检查并创建尾实体节点
        tail_node = graph.nodes.match("Knowledge_node", name=tail).first()
        if not tail_node:
            tail_node = Node("Knowledge_node", name=tail)
            graph.create(tail_node)

        # 创建头节点到尾节点的关系
        relationship = Relationship(head_node, relation, tail_node)
        relationship["name"] = relation
        graph.create(relationship)

        # 创建文件到实体的关系
        file_relationship = Relationship(section_node, "CONTAINS", head_node)
        graph.create(file_relationship)

        file_relationship = Relationship(section_node, "CONTAINS", tail_node)
        graph.create(file_relationship)

    print(f"Processed file: {file_name}")

print("All JSON files processed and knowledge graph updated.")
