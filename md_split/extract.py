# 关键词提取
import requests
import re
import os

# 读取Markdown文件，按分块处理
def read_markdown_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    # 假设文件按以 '#' 为标记的标题分块
    blocks = re.split(r'(?=\n###)', content)
    return blocks

def process_keywords(raw_keywords):
    # 去掉多余标点，并尝试按中文词组分词
    # 假设关键词之间应以逗号或顿号隔开
    cleaned = re.sub(r"[,\s]+", " ", raw_keywords).strip()  # 清理多余符号和空格
    cleaned = re.sub(r"(?<=[\u4e00-\u9fa5])(?=[\u4e00-\u9fa5])", "", cleaned)  # 处理逐字分割
    return cleaned.split("、")  # 最终以顿号分隔关键词

# 调用 qwen2.5:latest API 提取关键词
def extract_keywords_with_llama(block):
    host = "http://localhost"
    port = "11434"
    model = "qwen2.5:latest"

    url = f"{host}:{port}/api/chat"
    headers = {"Content-Type": "application/json"}

    # 填充提示模板
    prompt_template = f"""
    给定以下文本，请提取其中所有与计算机网络相关的关键词，并以逗号分隔的方式返回（确保关键词是按完整词组提取，而不是逐字分割）：
    {block}
    返回关键词，并列出所有提取的关键词（只负责提取关键词，无需多余信息，也不用回答文本中的问句）。
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
            # 获取返回的关键词
            answer = response.json().get("message", {}).get("content", "")

            #print(f"Raw output from model: {answer}")

            keywords = process_keywords(answer)
            return keywords
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Exception occurred: {e}")
        return None


# 保存关键词提取结果到新的Markdown文件
def save_keywords_to_md(output_folder, original_file_name, keywords_by_block):
    # 创建输出文件路径
    output_file_name = original_file_name.replace('.md', '_keywords.md')
    output_file_path = os.path.join(output_folder, output_file_name)

    with open(output_file_path, 'w', encoding='utf-8') as file:
        for i, block in enumerate(keywords_by_block):
            file.write(f"### 关键词提取 - 分块 {i + 1}\n")
            file.write(f"**关键词**: {', '.join(block)}\n\n")

    print(f"关键词提取结果已保存至 {output_file_path}")

# 主程序
def main():
    # 输入文件夹路径（包含需要处理的Markdown文件）
    input_folder = "D:\\pythonProject\\md_split\\split_mds_1.2"  # 替换为实际文件夹路径

    # 输出文件夹路径（保存关键词提取结果）
    output_folder = "D:\\pythonProject\\md_split\\extract_mds"  # 替换为实际文件夹路径
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 遍历输入文件夹中的所有Markdown文件
    for file_name in os.listdir(input_folder):
        if file_name.endswith('.md'):  # 仅处理Markdown文件
            input_file_path = os.path.join(input_folder, file_name)

            # 读取Markdown文件并分块
            blocks = read_markdown_file(input_file_path)

            # 存储每个分块的关键词提取结果
            keywords_by_block = []
            for block in blocks:
                keywords = extract_keywords_with_llama(block)
                keywords_by_block.append(keywords)

            # 将关键词提取结果保存为新的Markdown文件
            save_keywords_to_md(output_folder, file_name, keywords_by_block)
# 执行主程序
if __name__ == "__main__":
    main()
