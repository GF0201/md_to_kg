# 对md文本进行分块（按照段落）
import os
from langchain.text_splitter import MarkdownTextSplitter


def split_md_files_by_paragraph(input_folder, output_folder, chunk_size=500, chunk_overlap=50):
    """
    对文件夹中的 Markdown 文件进行段落分块，并将结果保存到另一个文件夹中。

    参数:
        input_folder (str): 包含原始 Markdown 文件的文件夹路径。
        output_folder (str): 保存分块结果的文件夹路径。
        chunk_size (int): 每块的最大字符数（超过此长度的段落将被进一步分块）。
        chunk_overlap (int): 块之间的重叠字符数，用于上下文连续性。
    """
    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)

    # 初始化 LangChain 的 Markdown 分块工具
    splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    # 遍历输入文件夹中的所有 Markdown 文件
    for file_name in os.listdir(input_folder):
        if file_name.endswith(".md"):  # 只处理 Markdown 文件
            input_path = os.path.join(input_folder, file_name)
            output_path = os.path.join(output_folder, file_name)

            # 读取 Markdown 文件内容
            with open(input_path, "r", encoding="utf-8") as file:
                md_content = file.read()

            # 按段落分块
            # 1. 首先以两个换行符分段
            paragraphs = md_content.split("\n\n")
            cleaned_paragraphs = [p.strip() for p in paragraphs if p.strip()]

            # 2. 使用 LangChain 进一步按字符数限制分块
            chunks = []
            for paragraph in cleaned_paragraphs:
                chunks.extend(splitter.split_text(paragraph))

            # 保存分块结果到新的 Markdown 文件
            with open(output_path, "w", encoding="utf-8") as output_file:
                for i, chunk in enumerate(chunks):
                    output_file.write(f"### 分块 {i + 1}\n")
                    output_file.write(chunk + "\n\n")

            print(f"处理完成: {file_name}, 分块结果已保存到: {output_path}")


# 示例使用
input_folder = "D:\\pythonProject\\md_split\\new_mds_1.2"  # 输入文件夹路径
output_folder = "D:\\pythonProject\\md_split\\split_mds_1.2"  # 输出文件夹路径
split_md_files_by_paragraph(input_folder, output_folder, chunk_size=500, chunk_overlap=50)


