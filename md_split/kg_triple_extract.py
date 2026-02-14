import os
import requests
import re
import json


# 读取Markdown文件，按分块处理
def read_markdown_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    # 假设文件按以 '#' 为标记的标题分块
    blocks = re.split(r'(?=\n###)', content)
    return blocks


# 调用 Llama 3.1 API 提取知识图谱三元组
def extract_triples_with_llama(block):
    host = "http://localhost"
    port = "11434"
    model = "qwen2.5:latest"

    url = f"{host}:{port}/api/chat"
    headers = {"Content-Type": "application/json"}

    # 填充提示模板
    prompt_template = f"""
    {block}

    任务描述:
    从提供的计算机网络相关文本中提取知识图谱三元组，输出内容应简洁、不复杂，并有代表性，能够用于增强大语言模型在计算机网络领域的对话能力。
    输出要求:
    数据格式: 使用 JSON 格式表示三元组，包含 head、relation、tail 三个字段。
    关系谓词: 选择明确、简洁的技术关系动词，以增强语义清晰度。
    信息筛选: 仅提取内容中与计算机网络核心相关的知识点，忽略冗余信息。
    """

    data = {
        "model": model,
        "options": {
            "temperature": 0.0
        },
        "stream": False,
        "messages": [{"role": "system", "content": prompt_template}]
    }

    try:
        response = requests.post(url, json=data, headers=headers, timeout=60)
        if response.status_code == 200:
            # 获取返回的三元组
            answer = response.json().get("message", {}).get("content", "")

            # 示例: 输出返回内容
            #print(f"Raw output from model: {answer}")

            triples = process_triples(answer)
            return triples
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception occurred: {e}")
        return None


# 处理返回的三元组字符串
def process_triples(raw_triples):
    # 确保返回有效的三元组列表
    try:
        # 假设返回格式为 JSON 格式的字符串
        triples = json.loads(raw_triples.strip("```json").strip())
        # 返回一个三元组的列表
        return triples
    except Exception as e:
        print(f"Error processing triples: {e}")
        return []


# 保存三元组提取结果到JSON文件
def save_triples_to_json(output_file_path, triples_by_block):
    # 确保保存的格式正确，打印数据调试
    try:
        with open(output_file_path, 'w', encoding='utf-8') as file:
            # 检查数据内容
            print(f"Saving the following data to {output_file_path}: {triples_by_block}")
            json.dump(triples_by_block, file, ensure_ascii=False, indent=4)
        print(f"三元组提取结果已保存至 {output_file_path}")
    except Exception as e:
        print(f"Error saving to JSON: {e}")


# 批量处理多个Markdown文件
def process_multiple_files(input_folder, output_folder):
    # 获取指定文件夹中的所有 Markdown 文件
    md_files = [f for f in os.listdir(input_folder) if f.endswith('.md')]

    for md_file in md_files:
        input_file_path = os.path.join(input_folder, md_file)
        output_file_path = os.path.join(output_folder, f"{os.path.splitext(md_file)[0]}.json")

        print(f"Processing file: {input_file_path}")

        # 读取Markdown文件并分块
        blocks = read_markdown_file(input_file_path)

        # 存储每个分块的三元组提取结果
        triples_by_block = []
        for block in blocks:
            triples = extract_triples_with_llama(block)
            if triples:
                triples_by_block.append(triples)
            else:
                triples_by_block.append([])  # 如果没有提取到三元组，保留空列表

        # 将三元组提取结果保存为JSON文件
        save_triples_to_json(output_file_path, triples_by_block)


# 主程序
def main():
    input_folder = "D:\\pythonProject\\md_split\\merged_mds"  # 替换为实际文件夹路径
    output_folder = "D:\\pythonProject\\md_split\\kg_triple_extract"  # 替换为保存结果的文件夹路径

    # 创建输出文件夹（如果不存在）
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 批量处理 Markdown 文件
    process_multiple_files(input_folder, output_folder)


# 执行主程序
if __name__ == "__main__":
    main()
