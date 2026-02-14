"""
PDF 到三元组自动化提取流水线
=============================
功能：
1. 按章节切分PDF（基于Excel配置）
2. PDF转Markdown
3. 清理Markdown格式
4. 分块处理
5. 关键词提取（可选）
6. 三元组提取并保存为JSON

作者：整合自 md_split 项目
"""

import os
import re
import json
import time
from openai import OpenAI

# PDF 操作
from PyPDF2 import PdfReader, PdfWriter

# Markdown 转换
from markitdown import MarkItDown

# Markdown 文本分块
from langchain_text_splitters import MarkdownTextSplitter

# Excel 读取
import pandas as pd

###############################################################################
#                             全局配置区                                      #
###############################################################################

# ========== API配置 ==========
API_KEY = "sk-ENQjRCfsEGJDkgNy0wXU6u3AThPIClxFbFVpplVkL2uFTM7T"
BASE_URL = "https://tb.api.mkeai.com/v1"
MODEL_NAME = "deepseek-v3.2"

# ========== 路径配置 ==========
# PDF输入：可以是单个PDF文件，也可以是包含多个PDF的文件夹
PDF_INPUT = r"D:\pythonProject\book"  # 修改为你的PDF文件或文件夹路径

# Excel章节配置文件（如果需要按章节切分PDF，请提供此文件）
# Excel应包含三列：name（章节名）、start（起始页）、end（结束页）
# 如果不需要切分，设为 None
EXCEL_CONFIG = None  # 例如: r"D:\demo\chapters.xlsx"

# 输出根目录（所有中间文件和最终结果都会保存在这里）
OUTPUT_ROOT = r"D:\pythonProject\md_to_kg\triple_kg"

# ========== 分块参数 ==========
CHUNK_SIZE = 500        # 单块最大字符数
CHUNK_OVERLAP = 50      # 块与块之间的字符重叠数

# ========== 处理选项 ==========
ENABLE_KEYWORD_EXTRACTION = False  # 是否启用关键词提取（测试时关闭以加快速度）
API_CALL_INTERVAL = 1.0            # API调用间隔（秒），避免限流
MAX_RETRIES = 3                    # API调用最大重试次数

# ========== 测试模式 ==========
TEST_MODE = True                   # 测试模式：只处理部分页面
MAX_PAGES = None                   # 最大处理页数（None=自动计算1/4，或指定具体数字如50）

###############################################################################
#                             初始化OpenAI客户端                              #
###############################################################################

client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

###############################################################################
#                             工具函数                                        #
###############################################################################

def ensure_dir(path):
    """确保目录存在，不存在则创建"""
    os.makedirs(path, exist_ok=True)
    return path


def call_llm(prompt: str, max_retries: int = MAX_RETRIES) -> str:
    """
    调用大模型API，带重试机制
    """
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "你是一个专业的计算机网络知识图谱构建助手。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4096
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"    API调用失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
            else:
                raise e
    return ""


###############################################################################
#                             PDF处理函数                                     #
###############################################################################

def split_pdf_by_chapters(pdf_file: str, excel_file: str, output_folder: str) -> str:
    """
    根据 Excel 中的章节名与页码区间，将 PDF 拆分成多个子 PDF。
    
    Args:
        pdf_file: PDF文件路径
        excel_file: Excel配置文件路径（包含name, start, end三列）
        output_folder: 输出文件夹路径
    
    Returns:
        输出文件夹路径
    """
    print(">>> 正在根据 Excel 配置拆分 PDF ...")
    
    df = pd.read_excel(excel_file)
    ensure_dir(output_folder)
    
    with open(pdf_file, 'rb') as f:
        reader = PdfReader(f)
        total_pages = len(reader.pages)
        
        for idx, row in df.iterrows():
            chapter_name = str(row['name']).strip()
            start_page = int(row['start'])
            end_page = int(row['end'])
            
            # 验证页码范围
            if start_page < 1 or end_page > total_pages:
                print(f"    警告: 章节 '{chapter_name}' 页码范围 ({start_page}-{end_page}) 超出PDF总页数 ({total_pages})")
                continue
            
            writer = PdfWriter()
            # PyPDF2 以 0 为起始下标
            for page_num in range(start_page - 1, end_page):
                writer.add_page(reader.pages[page_num])
            
            # 清理文件名中的非法字符
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', chapter_name)
            output_file = os.path.join(output_folder, f"{safe_name}.pdf")
            
            with open(output_file, 'wb') as out:
                writer.write(out)
            
            print(f"    已拆分: {chapter_name} (第{start_page}-{end_page}页)")
    
    print(f"    拆分完成，输出文件夹: {output_folder}")
    return output_folder


def convert_pdf_to_md(input_path: str, output_folder: str, max_pages: int = None) -> str:
    """
    将PDF文件或文件夹中的所有PDF转换为Markdown。
    
    Args:
        input_path: PDF文件或文件夹路径
        output_folder: 输出文件夹路径
        max_pages: 最大处理页数（None=全部处理）
    
    Returns:
        输出文件夹路径
    """
    print(">>> 正在将 PDF 转换为 Markdown ...")
    
    ensure_dir(output_folder)
    markitdown = MarkItDown()
    
    # 获取所有PDF文件
    if os.path.isfile(input_path):
        pdf_files = [input_path]
    else:
        pdf_files = [os.path.join(input_path, f) for f in os.listdir(input_path) if f.endswith('.pdf')]
    
    for pdf_path in pdf_files:
        file_name = os.path.basename(pdf_path)
        md_name = os.path.splitext(file_name)[0] + ".md"
        md_path = os.path.join(output_folder, md_name)
        
        try:
            # 如果指定了最大页数，先提取部分页面
            if max_pages:
                temp_pdf_path = os.path.join(output_folder, f"_temp_{file_name}")
                reader = PdfReader(pdf_path)
                total_pages = len(reader.pages)
                pages_to_extract = min(max_pages, total_pages)
                
                writer = PdfWriter()
                for i in range(pages_to_extract):
                    writer.add_page(reader.pages[i])
                
                with open(temp_pdf_path, 'wb') as f:
                    writer.write(f)
                
                print(f"    提取前 {pages_to_extract}/{total_pages} 页用于测试")
                result = markitdown.convert(temp_pdf_path)
                os.remove(temp_pdf_path)  # 删除临时文件
            else:
                result = markitdown.convert(pdf_path)
            
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(result.text_content)
            print(f"    已转换: {file_name} -> {md_name}")
        except Exception as e:
            print(f"    转换失败: {file_name}, 错误: {e}")
    
    return output_folder


###############################################################################
#                             Markdown处理函数                                #
###############################################################################

def clean_markdown_content(content: str) -> str:
    """
    清理Markdown内容，删除多余空格和换行符。
    """
    # 1. 删除非标点符号后的多余换行
    content = re.sub(r"(?<![。！？])\n{2,}(?!\n)", " ", content)
    # 2. 标点符号后保留一个换行符
    content = re.sub(r"([。！？])\s*\n\s*", r"\1\n", content)
    # 3. 删除句子中多余空格
    content = re.sub(r"(?<!\n)[ \t]+(?!\n)", "", content)
    # 4. 最多保留两个换行符
    content = re.sub(r"\n{3,}", "\n\n", content)
    
    return content


def clean_markdown_folder(input_folder: str, output_folder: str) -> str:
    """
    批量清理Markdown文件。
    """
    print(">>> 正在清理 Markdown 格式 ...")
    
    ensure_dir(output_folder)
    
    for file_name in os.listdir(input_folder):
        if file_name.endswith(".md"):
            input_path = os.path.join(input_folder, file_name)
            output_path = os.path.join(output_folder, file_name)
            
            with open(input_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            cleaned = clean_markdown_content(content)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(cleaned)
    
    print("    清理完成。")
    return output_folder


def split_markdown_to_chunks(input_folder: str, output_folder: str, 
                              chunk_size: int = CHUNK_SIZE, 
                              chunk_overlap: int = CHUNK_OVERLAP) -> str:
    """
    对Markdown文件进行分块处理。
    """
    print(">>> 正在对 Markdown 进行分块 ...")
    
    ensure_dir(output_folder)
    splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    for file_name in os.listdir(input_folder):
        if file_name.endswith(".md"):
            input_path = os.path.join(input_folder, file_name)
            output_path = os.path.join(output_folder, file_name)
            
            with open(input_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 先按空行分段
            paragraphs = content.split("\n\n")
            cleaned_paragraphs = [p.strip() for p in paragraphs if p.strip()]
            
            # 使用LangChain进一步分块
            chunks = []
            for paragraph in cleaned_paragraphs:
                chunks.extend(splitter.split_text(paragraph))
            
            # 保存分块结果
            with open(output_path, "w", encoding="utf-8") as f:
                for i, chunk in enumerate(chunks):
                    f.write(f"### 分块 {i + 1}\n")
                    f.write(chunk + "\n\n")
            
            print(f"    已分块: {file_name} ({len(chunks)} 个分块)")
    
    print("    分块完成。")
    return output_folder


###############################################################################
#                             关键词提取                                      #
###############################################################################

def extract_keywords(text: str) -> list:
    """
    使用大模型提取文本中的关键词。
    """
    prompt = f"""请从以下计算机网络相关文本中提取关键词，要求：
1. 提取与计算机网络核心概念相关的专业术语
2. 以逗号分隔的方式返回
3. 只输出关键词列表，不要其他解释

文本：
{text}

关键词："""
    
    try:
        result = call_llm(prompt)
        # 解析关键词
        keywords = [k.strip() for k in re.split(r'[,，、]', result) if k.strip()]
        return keywords
    except Exception as e:
        print(f"    关键词提取失败: {e}")
        return []


def extract_keywords_from_folder(input_folder: str, output_folder: str) -> str:
    """
    批量提取Markdown文件中的关键词。
    """
    print(">>> 正在提取关键词 ...")
    
    ensure_dir(output_folder)
    
    for file_name in os.listdir(input_folder):
        if file_name.endswith(".md"):
            input_path = os.path.join(input_folder, file_name)
            output_path = os.path.join(output_folder, file_name.replace('.md', '_keywords.md'))
            
            with open(input_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 按分块标题分割
            blocks = re.split(r'(?=###\s*分块)', content)
            blocks = [b.strip() for b in blocks if b.strip()]
            
            keywords_result = []
            for i, block in enumerate(blocks):
                print(f"    处理 {file_name} 分块 {i + 1}/{len(blocks)}...")
                keywords = extract_keywords(block)
                keywords_result.append({
                    'block_num': i + 1,
                    'keywords': keywords
                })
                time.sleep(API_CALL_INTERVAL)
            
            # 保存关键词结果
            with open(output_path, "w", encoding="utf-8") as f:
                for item in keywords_result:
                    f.write(f"### 关键词提取 - 分块 {item['block_num']}\n")
                    f.write(f"**关键词**: {', '.join(item['keywords'])}\n\n")
            
            print(f"    已提取关键词: {file_name}")
    
    print("    关键词提取完成。")
    return output_folder


def merge_content_and_keywords(content_folder: str, keywords_folder: str, output_folder: str) -> str:
    """
    将原文分块与关键词合并。
    """
    print(">>> 正在合并原文与关键词 ...")
    
    ensure_dir(output_folder)
    
    content_files = [f for f in os.listdir(content_folder) if f.endswith('.md')]
    
    for content_file in content_files:
        base_name = os.path.splitext(content_file)[0]
        keywords_file = f"{base_name}_keywords.md"
        keywords_path = os.path.join(keywords_folder, keywords_file)
        
        if not os.path.exists(keywords_path):
            # 如果没有对应的关键词文件，直接复制原文
            import shutil
            shutil.copy(
                os.path.join(content_folder, content_file),
                os.path.join(output_folder, content_file)
            )
            continue
        
        # 读取原文和关键词
        with open(os.path.join(content_folder, content_file), "r", encoding="utf-8") as f:
            content_text = f.read()
        
        with open(keywords_path, "r", encoding="utf-8") as f:
            keywords_text = f.read()
        
        # 解析分块
        content_blocks = re.split(r'(###\s*分块\s*\d+)', content_text)
        keywords_blocks = re.split(r'(###\s*关键词提取\s*-\s*分块\s*\d+)', keywords_text)
        
        # 构建关键词字典
        keywords_dict = {}
        for i in range(1, len(keywords_blocks), 2):
            if i + 1 < len(keywords_blocks):
                block_num = re.search(r'分块\s*(\d+)', keywords_blocks[i])
                if block_num:
                    keywords_dict[int(block_num.group(1))] = keywords_blocks[i + 1].strip()
        
        # 合并结果
        merged_content = []
        for i in range(1, len(content_blocks), 2):
            if i + 1 < len(content_blocks):
                block_num = re.search(r'分块\s*(\d+)', content_blocks[i])
                if block_num:
                    num = int(block_num.group(1))
                    merged_content.append(content_blocks[i])  # 标题
                    merged_content.append(content_blocks[i + 1])  # 原文内容
                    if num in keywords_dict:
                        merged_content.append(f"\n{keywords_dict[num]}\n")
        
        # 保存合并结果
        output_path = os.path.join(output_folder, content_file)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(''.join(merged_content))
    
    print("    合并完成。")
    return output_folder


###############################################################################
#                             三元组提取                                      #
###############################################################################

def extract_triples(text: str) -> list:
    """
    使用大模型从文本中提取知识图谱三元组。
    """
    prompt = f"""请从以下计算机网络相关文本中提取知识图谱三元组。

要求：
1. 使用JSON格式输出，每个三元组包含 head（头实体）、relation（关系）、tail（尾实体）三个字段
2. 关系谓词应选择明确、简洁的动词或动词短语
3. 仅提取与计算机网络核心知识相关的内容
4. 如果没有可提取的三元组，返回空数组 []
5. 直接输出JSON数组，不要添加其他解释文字

文本：
{text}

JSON输出："""
    
    try:
        result = call_llm(prompt)
        triples = parse_triples_response(result)
        return triples
    except Exception as e:
        print(f"    三元组提取失败: {e}")
        return []


def parse_triples_response(response: str) -> list:
    """
    解析大模型返回的三元组JSON。
    """
    try:
        # 移除可能的markdown代码块标记
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        # 尝试解析JSON
        triples = json.loads(response)
        
        # 确保返回列表格式
        if isinstance(triples, dict):
            triples = [triples]
        
        # 验证三元组格式并标准化字段名
        valid_triples = []
        for t in triples:
            if isinstance(t, dict):
                # 处理可能的中文字段名
                head = t.get('head') or t.get('头实体') or t.get('主体')
                relation = t.get('relation') or t.get('关系') or t.get('谓词')
                tail = t.get('tail') or t.get('尾实体') or t.get('客体')
                
                if head and relation and tail:
                    valid_triples.append({
                        'head': str(head).strip(),
                        'relation': str(relation).strip(),
                        'tail': str(tail).strip()
                    })
        
        return valid_triples
    except json.JSONDecodeError as e:
        print(f"    JSON解析失败: {e}")
        return []


def extract_triples_from_folder(input_folder: str, output_folder: str) -> str:
    """
    批量从Markdown文件中提取三元组并保存为JSON。
    """
    print(">>> 正在提取三元组 ...")
    
    ensure_dir(output_folder)
    
    md_files = [f for f in os.listdir(input_folder) if f.endswith('.md')]
    
    for file_name in md_files:
        input_path = os.path.join(input_folder, file_name)
        output_path = os.path.join(output_folder, os.path.splitext(file_name)[0] + '.json')
        
        print(f"    处理文件: {file_name}")
        
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 按分块标题分割
        blocks = re.split(r'(?=###\s*分块)', content)
        blocks = [b.strip() for b in blocks if b.strip()]
        
        all_triples = []
        for i, block in enumerate(blocks):
            print(f"      提取分块 {i + 1}/{len(blocks)}...")
            triples = extract_triples(block)
            all_triples.extend(triples)
            time.sleep(API_CALL_INTERVAL)
        
        # 保存三元组
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_triples, f, ensure_ascii=False, indent=4)
        
        print(f"    已保存: {os.path.basename(output_path)} ({len(all_triples)} 个三元组)")
    
    print("    三元组提取完成。")
    return output_folder


###############################################################################
#                             主流程                                          #
###############################################################################

def run_pipeline(
    pdf_input: str = PDF_INPUT,
    excel_config: str = EXCEL_CONFIG,
    output_root: str = OUTPUT_ROOT,
    enable_keywords: bool = ENABLE_KEYWORD_EXTRACTION,
    test_mode: bool = TEST_MODE,
    max_pages: int = MAX_PAGES
):
    """
    运行完整的PDF到三元组处理流水线。
    
    Args:
        pdf_input: PDF文件或文件夹路径
        excel_config: Excel章节配置文件路径（可选）
        output_root: 输出根目录
        enable_keywords: 是否启用关键词提取
        test_mode: 是否为测试模式（只处理部分页面）
        max_pages: 最大处理页数（None=自动计算1/4）
    """
    print("=" * 60)
    print("PDF 到三元组自动化提取流水线")
    if test_mode:
        print("【测试模式】只处理部分页面")
    print("=" * 60)
    
    # 计算测试模式下的页数
    pages_limit = None
    if test_mode:
        if max_pages:
            pages_limit = max_pages
        else:
            # 自动计算1/4页数
            if os.path.isfile(pdf_input):
                pdf_path = pdf_input
            else:
                pdf_files = [f for f in os.listdir(pdf_input) if f.endswith('.pdf')]
                if pdf_files:
                    pdf_path = os.path.join(pdf_input, pdf_files[0])
                else:
                    pdf_path = None
            
            if pdf_path:
                reader = PdfReader(pdf_path)
                total_pages = len(reader.pages)
                pages_limit = max(10, total_pages // 4)  # 至少10页，最多1/4
                print(f">>> 自动计算：处理 {pages_limit}/{total_pages} 页 (约1/4)")
    
    # 创建输出目录结构
    ensure_dir(output_root)
    
    split_pdf_folder = os.path.join(output_root, "1_split_pdfs")
    md_folder = os.path.join(output_root, "2_raw_mds")
    cleaned_folder = os.path.join(output_root, "3_cleaned_mds")
    chunked_folder = os.path.join(output_root, "4_chunked_mds")
    keywords_folder = os.path.join(output_root, "5_keywords_mds")
    merged_folder = os.path.join(output_root, "6_merged_mds")
    triples_folder = os.path.join(output_root, "7_triples_json")
    
    # Step 1: PDF章节切分（可选）
    if excel_config and os.path.exists(excel_config):
        if os.path.isfile(pdf_input):
            split_pdf_by_chapters(pdf_input, excel_config, split_pdf_folder)
            current_input = split_pdf_folder
        else:
            print(">>> 跳过PDF切分（输入为文件夹）")
            current_input = pdf_input
    else:
        print(">>> 跳过PDF切分（未提供Excel配置）")
        current_input = pdf_input
    
    # Step 2: PDF转Markdown
    convert_pdf_to_md(current_input, md_folder, max_pages=pages_limit)
    
    # Step 3: 清理Markdown
    clean_markdown_folder(md_folder, cleaned_folder)
    
    # Step 4: 分块
    split_markdown_to_chunks(cleaned_folder, chunked_folder)
    
    # Step 5 & 6: 关键词提取与合并（可选）
    if enable_keywords:
        extract_keywords_from_folder(chunked_folder, keywords_folder)
        merge_content_and_keywords(chunked_folder, keywords_folder, merged_folder)
        final_input = merged_folder
    else:
        print(">>> 跳过关键词提取")
        final_input = chunked_folder
    
    # Step 7: 三元组提取
    extract_triples_from_folder(final_input, triples_folder)
    
    print("=" * 60)
    print("处理完成！")
    print(f"三元组JSON文件保存在: {triples_folder}")
    print("=" * 60)
    
    return triples_folder


###############################################################################
#                             入口                                            #
###############################################################################

if __name__ == "__main__":
    # 运行完整流水线
    run_pipeline()
