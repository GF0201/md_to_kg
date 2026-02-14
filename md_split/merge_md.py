import os
import re


def merge_md_blocks(content_file, keywords_file, output_file):
    # 读取文件内容
    with open(content_file, 'r', encoding='utf-8') as f:
        content_lines = f.readlines()

    with open(keywords_file, 'r', encoding='utf-8') as f:
        keywords_lines = f.readlines()

    # 将内容分块
    content_blocks = parse_blocks(content_lines, r'^###\s*分块\s*\d+')
    keywords_blocks = parse_blocks(keywords_lines, r'^###\s*关键词提取\s*-\s*分块\s*\d+')

    # 合并内容和关键词
    merged_blocks = []
    for keyword_block_title, keyword_block_content in keywords_blocks:
        # 从内容分块中查找对应的标题
        content_block = next(
            (content for title, content in content_blocks if title == keyword_block_title.replace("关键词提取 - ", "")),
            None)

        if content_block:
            # 添加内容块到关键词块前面
            merged_block = f"{keyword_block_title}\n{''.join(content_block)}{''.join(keyword_block_content)}"
            merged_blocks.append(merged_block)
        else:
            # 如果没有对应内容块，保留原关键词块
            merged_blocks.append(f"{keyword_block_title}\n{''.join(keyword_block_content)}")

    # 写入合并后的文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(merged_blocks))

    # 输出合并成功的信息
    print(f'{output_file} 合并成功！')


def parse_blocks(lines, title_pattern):
    """
    将文件行分块，基于指定的标题正则表达式。
    返回一个列表，每个元素是 (标题, 内容) 的元组。
    """
    blocks = []
    current_title = None
    current_content = []

    for line in lines:
        if re.match(title_pattern, line):
            if current_title:
                blocks.append((current_title, current_content))
            current_title = line.strip()
            current_content = []
        elif current_title:
            current_content.append(line)

    if current_title:
        blocks.append((current_title, current_content))

    return blocks


def process_all_files(content_folder, keywords_folder, output_folder):
    """
    批量处理两个文件夹中的md文件，最终合并的结果保存到输出文件夹。
    """
    # 遍历content_folder和keywords_folder中的所有.md文件
    content_files = [f for f in os.listdir(content_folder) if f.endswith('.md')]
    keywords_files = [f for f in os.listdir(keywords_folder) if f.endswith('.md')]

    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 遍历所有内容文件并进行处理
    for content_file_name in content_files:
        # 在keywords_folder中找到相应的关键词文件
        matching_keywords_files = [f for f in keywords_files if f.startswith(content_file_name.split('.')[0])]

        for keywords_file_name in matching_keywords_files:
            # 获取文件路径
            content_file = os.path.join(content_folder, content_file_name)
            keywords_file = os.path.join(keywords_folder, keywords_file_name)
            output_file = os.path.join(output_folder, content_file_name)

            # 合并md文件
            merge_md_blocks(content_file, keywords_file, output_file)


# 示例使用
content_folder = 'D:\\pythonProject\\md_split\\split_mds'  # 第一个文件夹
keywords_folder = 'D:\\pythonProject\\md_split\\extract_mds'  # 第二个文件夹
output_folder = 'D:\\pythonProject\\md_split\\merged_mds'  # 输出文件夹

process_all_files(content_folder, keywords_folder, output_folder)
