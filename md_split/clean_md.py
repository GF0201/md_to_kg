# 对转换后的md文件进行格式清理 删除多余空格以及换行符
import os
import re

def clean_markdown_file_with_proper_line_breaks(input_path, output_path):
    """
    清理 Markdown 文件，确保换行符只出现在标点符号（句号、问号、感叹号）后面，并删除多个连续的换行符。

    参数:
        input_path (str): 原始 Markdown 文件路径。
        output_path (str): 清理后的 Markdown 文件保存路径。
    """
    with open(input_path, "r", encoding="utf-8") as file:
        content = file.read()

    # 1. 删除非标点符号后的换行符，并删除多个连续换行符
    content = re.sub(r"(?<![。！？])\n{2,}(?!\n)", " ", content)

    # 2. 标点符号后保留一个换行符（确保格式正确）
    content = re.sub(r"([。！？])\s*\n\s*", r"\1\n", content)

    # 3. 删除句子中所有的多余空格
    content = re.sub(r"(?<!\n)[ \t]+(?!\n)", "", content)

    # 4. 清理段落间的多余空行，最多保留两个换行符
    content = re.sub(r"\n{3,}", "\n\n", content)

    # 保存清理后的内容
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(content)

    print(f"文件已清理并保存到: {output_path}")


def clean_markdown_folder_with_proper_line_breaks(input_folder, output_folder):
    """
    批量清理文件夹中的所有 Markdown 文件，确保换行符只出现在标点符号后，并删除多个连续的换行符。

    参数:
        input_folder (str): 包含原始 Markdown 文件的文件夹路径。
        output_folder (str): 清理后的 Markdown 文件保存路径。
    """
    os.makedirs(output_folder, exist_ok=True)

    for file_name in os.listdir(input_folder):
        if file_name.endswith(".md"):  # 只处理 Markdown 文件
            input_path = os.path.join(input_folder, file_name)
            output_path = os.path.join(output_folder, file_name)
            clean_markdown_file_with_proper_line_breaks(input_path, output_path)


# 示例使用
input_folder = "D:\\pythonProject\\md_split\\mds"  # 输入文件夹路径
output_folder = "D:\\pythonProject\\md_split\\new_mds_1.2"  # 输出文件夹路径
clean_markdown_folder_with_proper_line_breaks(input_folder, output_folder)
