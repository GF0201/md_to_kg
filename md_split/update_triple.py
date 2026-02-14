#更新检测json文件
import os
import json


def update_triples(input_folder, output_folder):
    # 遍历输入文件夹中的所有文件
    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            input_file_path = os.path.join(input_folder, filename)

            # 读取 JSON 文件
            with open(input_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            updated_data = []

            # 遍历文件中的列表
            for sublist in data:
                for triple in sublist:
                    # 检查字典中的键，并修改"关系"为"relation"
                    if "关系" in triple:
                        triple["relation"] = triple.pop("关系")
                    updated_data.append(triple)

            # 创建输出文件夹路径（如果不存在则创建）
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            # 保存更新后的数据到新文件
            output_file_path = os.path.join(output_folder, filename)
            with open(output_file_path, "w", encoding="utf-8") as f:
                json.dump(updated_data, f, ensure_ascii=False, indent=4)


# 设置输入和输出文件夹路径
input_folder = "D:\\pythonProject\\md_split\\kg_triple_extract"  # 输入文件夹路径
output_folder = "D:\\pythonProject\\md_split\\new_triple"  # 输出文件夹路径

# 执行更新操作
update_triples(input_folder, output_folder)
