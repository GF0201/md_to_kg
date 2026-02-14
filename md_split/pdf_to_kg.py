import os
import re
import json
import requests
import pandas as pd

# PDF 操作
from PyPDF2 import PdfReader, PdfWriter

# Markdown 转换
from markitdown import MarkItDown

# Markdown 文本分块
from langchain.text_splitter import MarkdownTextSplitter

# Neo4j 操作
from py2neo import Graph, Node, Relationship

###############################################################################
#                             全局配置区                                      #
###############################################################################

# 1) PDF 原文件 & Excel 信息
PDF_FILE = r"D:\demo\your_original.pdf"             # 您的 PDF 文件路径
EXCEL_FILE = r"D:\demo\page_ranges.xlsx"            # 存储章节页码区间的 Excel
SPLIT_PDF_FOLDER = None  # 如果留空，脚本会自动在 PDF 同目录下创建与 PDF 同名的文件夹

# 2) PDF -> Markdown
#    - 本示例使用 markitdown，将生成的 .md 文件统一放入此文件夹
PDF_TO_MD_FOLDER = r"D:\demo\extracted_pdfs"

# 3) Markdown 格式清理
#    - 清理后保存的文件夹
CLEANED_MD_FOLDER = r"D:\demo\cleaned_mds"

# 4) Markdown 分块
#    - 分块后保存的文件夹
CHUNKED_MD_FOLDER = r"D:\demo\split_mds"
CHUNK_SIZE = 500        # 单块最大字符数
CHUNK_OVERLAP = 50      # 块与块之间的字符重叠数

# 5) 关键词提取
#    - 提取结果保存的文件夹
KEYWORDS_MD_FOLDER = r"D:\demo\extract_mds"

# 6) 合并关键词与原文分块
#    - 合并结果保存的文件夹
MERGED_MD_FOLDER = r"D:\demo\merged_mds"

# 7) 三元组提取
#    - 三元组提取结果（JSON）保存的文件夹
TRIPLE_JSON_FOLDER = r"D:\demo\kg_triple_extract"

# 8) 更新三元组 JSON 文件
#    - 更新后保存的文件夹
UPDATED_TRIPLE_FOLDER = r"D:\demo\new_triple"

# 9) Neo4j 连接信息 (示例)
NEO4J_BOLT_URL = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "00000000")  # 用户名、密码
ROOT_NODE_NAME = "计算机网络-谢希仁"  # 知识图谱根节点名称

###############################################################################
#                             具体函数实现区                                   #
###############################################################################

def split_pdf_by_chapters(pdf_file: str, excel_file: str, output_folder: str = None):
    """
    根据 excel_file 中的章节名与页码区间，
    将 pdf_file 拆分成多个子 PDF 并存放在 output_folder 中。
    如果 output_folder 未指定，则默认在 pdf_file 同目录下创建一个同名文件夹。
    """
    print(">>> 正在根据 Excel 提供的页码拆分 PDF ...")

    # 读取 Excel，假设三列分别为：name, start, end
    df = pd.read_excel(excel_file)

    # 创建输出文件夹（以原始 PDF 文件名命名）
    base_name = os.path.splitext(os.path.basename(pdf_file))[0]  # 去掉路径 & 扩展名
    if not output_folder:
        output_folder = os.path.join(os.path.dirname(pdf_file), base_name)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    with open(pdf_file, 'rb') as f:
        reader = PdfReader(f)
        for idx, row in df.iterrows():
            chapter_name = str(row['name'])
            start_page = int(row['start'])
            end_page = int(row['end'])

            writer = PdfWriter()
            # PyPDF2 以 0 为起始下标，所以要减 1
            for page_num in range(start_page - 1, end_page):
                writer.add_page(reader.pages[page_num])

            # 保存子 PDF
            output_file = os.path.join(output_folder, f"{chapter_name}.pdf")
            with open(output_file, 'wb') as out:
                writer.write(out)

    print(f"    拆分完成，输出文件夹: {output_folder}")
    return output_folder


def convert_pdf_to_md(input_folder: str, output_folder: str):
    """
    使用 markitdown 将指定文件夹下所有 PDF 批量转换为 Markdown。
    """
    print(">>> 正在将 PDF 批量转换为 Markdown ...")
    markitdown = MarkItDown()

    os.makedirs(output_folder, exist_ok=True)

    for file_name in os.listdir(input_folder):
        if file_name.endswith(".pdf"):
            pdf_path = os.path.join(input_folder, file_name)
            markdown_file_name = os.path.splitext(file_name)[0] + ".md"
            markdown_path = os.path.join(output_folder, markdown_file_name)

            try:
                pdf_result = markitdown.convert(pdf_path)
                with open(markdown_path, "w", encoding="utf-8") as md_file:
                    md_file.write(pdf_result.text_content)
                print(f"    成功转换: {file_name} -> {markdown_file_name}")
            except Exception as e:
                print(f"    转换失败: {file_name}，错误信息: {e}")


def clean_markdown_folder_with_proper_line_breaks(input_folder, output_folder):
    """
    批量清理文件夹中的所有 Markdown 文件，删除多余空格和换行符等。
    """
    print(">>> 正在清理 Markdown 文件格式 ...")
    os.makedirs(output_folder, exist_ok=True)

    for file_name in os.listdir(input_folder):
        if file_name.endswith(".md"):
            input_path = os.path.join(input_folder, file_name)
            output_path = os.path.join(output_folder, file_name)
            clean_markdown_file_with_proper_line_breaks(input_path, output_path)
    print("    清理完成。")


def clean_markdown_file_with_proper_line_breaks(input_path, output_path):
    """
    清理单个 Markdown 文件，删除多余空格、换行符等。
    仅作为示例，可根据需求自行调整。
    """
    with open(input_path, "r", encoding="utf-8") as file:
        content = file.read()

    # 1. 删除非标点符号后的换行符，并删除多个连续换行符
    content = re.sub(r"(?<![。！？])\n{2,}(?!\n)", " ", content)
    # 2. 标点符号后保留一个换行符
    content = re.sub(r"([。！？])\s*\n\s*", r"\1\n", content)
    # 3. 删除句子中多余空格
    content = re.sub(r"(?<!\n)[ \t]+(?!\n)", "", content)
    # 4. 清理段落间的多余空行，最多保留两个换行符
    content = re.sub(r"\n{3,}", "\n\n", content)

    with open(output_path, "w", encoding="utf-8") as file:
        file.write(content)


def split_md_files_by_paragraph(input_folder, output_folder, chunk_size=500, chunk_overlap=50):
    """
    对文件夹中的 Markdown 文件进行分块，并将结果保存到 output_folder。
    """
    print(">>> 正在对 Markdown 文件进行分块 ...")
    os.makedirs(output_folder, exist_ok=True)

    splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    for file_name in os.listdir(input_folder):
        if file_name.endswith(".md"):
            input_path = os.path.join(input_folder, file_name)
            output_path = os.path.join(output_folder, file_name)

            with open(input_path, "r", encoding="utf-8") as file:
                md_content = file.read()

            # 先以空行分段
            paragraphs = md_content.split("\n\n")
            cleaned_paragraphs = [p.strip() for p in paragraphs if p.strip()]

            chunks = []
            for paragraph in cleaned_paragraphs:
                # 使用 langchain 进一步分块
                chunks.extend(splitter.split_text(paragraph))

            with open(output_path, "w", encoding="utf-8") as output_file:
                for i, chunk in enumerate(chunks):
                    output_file.write(f"### 分块 {i + 1}\n")
                    output_file.write(chunk + "\n\n")

            print(f"    处理完成: {file_name}")
    print("    分块完成。")


def read_markdown_file(file_path):
    """
    读取 Markdown 文件，并根据分块标题（### 分块/关键词提取）切割。
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    # 假设以 ### 开头的行作为分块标识
    blocks = re.split(r'(?=\n###)', content)
    return blocks


###############################################################################
#                关键词提取（示例：调用本地 qwen2.5 模型 API）                  #
###############################################################################

def extract_keywords_with_llama(block):
    """
    调用本地大模型接口，根据 block 文本提取关键词。
    可根据自己实际的大模型 API 地址及提示词需求进行调整。
    """
    host = "http://localhost"
    port = "11434"
    model = "qwen2.5:latest"

    url = f"{host}:{port}/api/chat"
    headers = {"Content-Type": "application/json"}

    prompt_template = f"""
    给定以下文本，请提取其中所有与计算机网络相关的关键词，并以逗号分隔的方式返回（确保关键词是按完整词组提取，而不是逐字分割）：
    {block}
    只需要输出关键词列表，无需额外解释。
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
            answer = response.json().get("message", {}).get("content", "")
            keywords = process_keywords(answer)
            return keywords
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Exception occurred: {e}")
        return []


def process_keywords(raw_keywords):
    """
    根据需要对关键词做一些简单清理。
    """
    cleaned = re.sub(r"[,\s]+", " ", raw_keywords).strip()
    cleaned = re.sub(r"(?<=[\u4e00-\u9fa5])(?=[\u4e00-\u9fa5])", "", cleaned)
    return [k.strip() for k in re.split(r"[,、]", cleaned) if k.strip()]


def extract_keywords_from_md_files(input_folder, output_folder):
    """
    批量读取Markdown文件分块，提取关键词，并输出到新的 Markdown 文件。
    """
    print(">>> 正在提取关键词 ...")
    os.makedirs(output_folder, exist_ok=True)

    md_files = [f for f in os.listdir(input_folder) if f.endswith('.md')]
    for file_name in md_files:
        input_file_path = os.path.join(input_folder, file_name)
        blocks = read_markdown_file(input_file_path)

        keywords_by_block = []
        for block in blocks:
            kws = extract_keywords_with_llama(block)
            keywords_by_block.append(kws)

        # 保存关键词到新的 Markdown 文件
        output_file_path = os.path.join(output_folder, file_name.replace('.md', '_keywords.md'))
        with open(output_file_path, 'w', encoding='utf-8') as file:
            for i, block_kws in enumerate(keywords_by_block):
                file.write(f"### 关键词提取 - 分块 {i + 1}\n")
                file.write(f"**关键词**: {', '.join(block_kws)}\n\n")

        print(f"    已提取关键词: {file_name} -> {os.path.basename(output_file_path)}")
    print("    关键词提取完成。")


###############################################################################
#                    合并关键词与原文分块                                      #
###############################################################################

def merge_md_blocks(content_folder, keywords_folder, output_folder):
    """
    将内容分块与提取的关键词分块合并到同一个 Markdown 文件中。
    """
    print(">>> 正在合并关键词与原文分块 ...")

    content_files = [f for f in os.listdir(content_folder) if f.endswith('.md')]
    keywords_files = [f for f in os.listdir(keywords_folder) if f.endswith('.md')]

    os.makedirs(output_folder, exist_ok=True)

    for content_file_name in content_files:
        # 匹配对应的关键词文件（可按需修改匹配规则）
        matching_keywords_files = [
            f for f in keywords_files
            if f.startswith(os.path.splitext(content_file_name)[0])  # 同名
        ]

        for keywords_file_name in matching_keywords_files:
            content_file = os.path.join(content_folder, content_file_name)
            keywords_file = os.path.join(keywords_folder, keywords_file_name)
            output_file = os.path.join(output_folder, content_file_name)

            merge_two_md_files(content_file, keywords_file, output_file)
    print("    合并完成。")


def merge_two_md_files(content_file, keywords_file, output_file):
    """
    根据标题分块，将原内容和关键词内容合并。
    """
    with open(content_file, 'r', encoding='utf-8') as f:
        content_lines = f.readlines()
    with open(keywords_file, 'r', encoding='utf-8') as f:
        keywords_lines = f.readlines()

    content_blocks = parse_blocks(content_lines, r'^###\s*分块\s*\d+')
    keywords_blocks = parse_blocks(keywords_lines, r'^###\s*关键词提取\s*-\s*分块\s*\d+')

    merged_blocks = []
    for kw_title, kw_content in keywords_blocks:
        # 将标题中提取到的分块编号，如 “### 关键词提取 - 分块 1” -> “### 分块 1”
        content_title = kw_title.replace("关键词提取 - ", "")

        # 在内容分块中找同名标题
        matching_content = next((cnt for t, cnt in content_blocks if t == content_title), None)

        if matching_content:
            merged_block = f"{kw_title}\n{''.join(matching_content)}{''.join(kw_content)}"
            merged_blocks.append(merged_block)
        else:
            # 若找不到对应原文分块，直接把关键词块加进结果中
            merged_blocks.append(f"{kw_title}\n{''.join(kw_content)}")

    # 写入合并结果
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(merged_blocks))


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
            # 如果已经有一个块在收集，就先存起来
            if current_title:
                blocks.append((current_title, current_content))
            current_title = line.strip()
            current_content = []
        else:
            if current_title:
                current_content.append(line)

    if current_title:
        blocks.append((current_title, current_content))

    return blocks


###############################################################################
#                  提取三元组，并将其保存为 JSON 文件                           #
###############################################################################

def extract_triples_from_md_files(input_folder, output_folder):
    """
    读取 Markdown 分块内容，调用大模型 API 提取三元组，并保存到 JSON 文件中。
    """
    print(">>> 正在提取三元组 ...")

    os.makedirs(output_folder, exist_ok=True)
    md_files = [f for f in os.listdir(input_folder) if f.endswith('.md')]

    for md_file in md_files:
        input_file_path = os.path.join(input_folder, md_file)
        output_file_path = os.path.join(output_folder, f"{os.path.splitext(md_file)[0]}.json")

        print(f"    处理文件: {md_file}")
        blocks = read_markdown_file(input_file_path)

        triples_by_block = []
        for block in blocks:
            triples = extract_triples_with_llama(block)
            if triples:
                triples_by_block.append(triples)
            else:
                triples_by_block.append([])

        save_triples_to_json(output_file_path, triples_by_block)
    print("    三元组提取完成。")


def extract_triples_with_llama(block):
    """
    调用本地大模型接口，从文本中抽取三元组。
    此处以 qwen2.5 为例，需根据您的实际情况修改 host、port、model。
    """
    host = "http://localhost"
    port = "11434"
    model = "qwen2.5:latest"

    url = f"{host}:{port}/api/chat"
    headers = {"Content-Type": "application/json"}

    prompt_template = f"""
{block}

任务描述:
从上述计算机网络相关文本中提取知识图谱三元组，输出内容应简洁、不复杂。
输出要求:
- 使用 JSON 格式表示三元组，包含 head、relation、tail 三个字段。
- 关系谓词: 选择明确、简洁的技术关系动词。
- 仅提取与计算机网络核心相关的知识点。

如果没有可用三元组，返回空的 JSON 数组。
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
            answer = response.json().get("message", {}).get("content", "")
            return process_triples(answer)
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Exception occurred: {e}")
        return []


def process_triples(raw_triples):
    """
    将返回的 JSON 格式三元组字符串进行解析，返回三元组列表。
    """
    try:
        # 假设返回的数据直接是 JSON
        # 如果有 ```json 包裹，需要先剥离
        raw_triples = raw_triples.strip("```json").strip()
        triples = json.loads(raw_triples)
        if isinstance(triples, dict):
            # 如果返回的是单个对象，就放到列表里
            triples = [triples]
        return triples if isinstance(triples, list) else []
    except Exception as e:
        print(f"Error processing triples: {e}")
        return []


def save_triples_to_json(output_file_path, triples_by_block):
    """
    保存三元组列表到 JSON 文件。
    """
    try:
        with open(output_file_path, 'w', encoding='utf-8') as file:
            json.dump(triples_by_block, file, ensure_ascii=False, indent=4)
        print(f"    三元组提取结果已保存: {os.path.basename(output_file_path)}")
    except Exception as e:
        print(f"Error saving to JSON: {e}")


###############################################################################
#                  更新三元组 JSON 文件（示例：删除无效键等）                    #
###############################################################################

def update_triples_json_files(input_folder, output_folder):
    """
    读取指定文件夹下的 JSON 文件，对三元组中无效或错误的键进行更新或删除。
    并将结果保存到新的目录中。
    """
    print(">>> 正在更新三元组 JSON 文件 ...")
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            input_file_path = os.path.join(input_folder, filename)
            with open(input_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            updated_data = []
            # data 是一个二维结构：最外层的列表，对应各块
            for sublist in data:
                for triple in sublist:
                    # 可以在此执行一些自定义的清洗操作
                    # 例如将"关系"字段改为"relation"
                    if "关系" in triple:
                        triple["relation"] = triple.pop("关系")
                    # 可以判断是否为空
                    if triple.get("head") and triple.get("relation") and triple.get("tail"):
                        updated_data.append(triple)

            output_file_path = os.path.join(output_folder, filename)
            with open(output_file_path, "w", encoding="utf-8") as f:
                json.dump(updated_data, f, ensure_ascii=False, indent=4)

    print("    更新完成。")


###############################################################################
#             使用三元组 JSON 文件构建 Neo4j 知识图谱                          #
###############################################################################

def build_knowledge_graph_from_triples(
    triple_folder,
    bolt_url=NEO4J_BOLT_URL,
    auth=NEO4J_AUTH,
    root_name=ROOT_NODE_NAME
):
    """
    将指定文件夹下的三元组 JSON 文件写入 Neo4j 中，并在数据库中构建知识图谱。
    """
    print(">>> 正在构建 Neo4j 知识图谱 ...")

    graph = Graph(bolt_url, auth=auth)

    # 可选：清空已有图谱中的节点（示例中使用三个标签清空）
    graph.run("MATCH (n:Knowledge) DETACH DELETE n")
    graph.run("MATCH (n:Knowledge_section) DETACH DELETE n")
    graph.run("MATCH (n:Knowledge_node) DETACH DELETE n")

    # 创建根节点
    root_node = Node("Knowledge", name=root_name)
    graph.create(root_node)

    # 遍历 JSON 文件夹
    for file_name in os.listdir(triple_folder):
        if not file_name.endswith(".json"):
            continue

        file_path = os.path.join(triple_folder, file_name)
        section_label = "Knowledge_section"
        section_node = Node(section_label, name=os.path.splitext(file_name)[0])
        graph.create(section_node)

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            if isinstance(item, dict):
                head = item.get("head")
                relation = item.get("relation")
                tail = item.get("tail")

                # 如果三项都有值才进行写入
                if head and relation and tail:
                    # 创建节点
                    head_node = graph.nodes.match("Knowledge_node", name=head).first()
                    if not head_node:
                        head_node = Node("Knowledge_node", name=head)
                        graph.create(head_node)

                    tail_node = graph.nodes.match("Knowledge_node", name=tail).first()
                    if not tail_node:
                        tail_node = Node("Knowledge_node", name=tail)
                        graph.create(tail_node)

                    # 创建关系
                    relationship = Relationship(head_node, relation, tail_node)
                    relationship["name"] = relation
                    graph.create(relationship)

                    # 文件节点 -> 实体节点 (可选)
                    file_rel_1 = Relationship(section_node, "CONTAINS", head_node)
                    file_rel_2 = Relationship(section_node, "CONTAINS", tail_node)
                    graph.create(file_rel_1)
                    graph.create(file_rel_2)

        print(f"    处理完成: {file_name}")

    print("    知识图谱已完成构建。")


###############################################################################
#                                  主流程                                     #
###############################################################################

def main():
    # 1. PDF 按章节拆分
    pdf_split_folder = split_pdf_by_chapters(PDF_FILE, EXCEL_FILE, SPLIT_PDF_FOLDER)

    # 2. 将拆分后的 PDF 转为 Markdown
    convert_pdf_to_md(pdf_split_folder, PDF_TO_MD_FOLDER)

    # 3. 清理 Markdown 格式
    clean_markdown_folder_with_proper_line_breaks(PDF_TO_MD_FOLDER, CLEANED_MD_FOLDER)

    # 4. 对 Markdown 分块
    split_md_files_by_paragraph(CLEANED_MD_FOLDER, CHUNKED_MD_FOLDER, CHUNK_SIZE, CHUNK_OVERLAP)

    # 5. 提取关键词
    extract_keywords_from_md_files(CHUNKED_MD_FOLDER, KEYWORDS_MD_FOLDER)

    # 6. 将关键词与原文分块合并
    merge_md_blocks(CHUNKED_MD_FOLDER, KEYWORDS_MD_FOLDER, MERGED_MD_FOLDER)

    # 7. 三元组提取
    extract_triples_from_md_files(MERGED_MD_FOLDER, TRIPLE_JSON_FOLDER)

    # 8. 更新三元组 JSON
    update_triples_json_files(TRIPLE_JSON_FOLDER, UPDATED_TRIPLE_FOLDER)

    # 9. 构建知识图谱
    build_knowledge_graph_from_triples(UPDATED_TRIPLE_FOLDER)

    print("\n>>> 全部流程执行完毕！请查看 Neo4j 中的知识图谱。")


# 如果作为脚本运行，则执行主函数
if __name__ == "__main__":
    main()
