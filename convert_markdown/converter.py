import os
from markitdown import MarkItDown

markitdown = MarkItDown()

def convert_pdf_to_markdown(pdf_path, output_path):
    """将单个 PDF 转换为 Markdown 文件。"""

    try:
        pdf_result = markitdown.convert(pdf_path)
        with open(output_path, "w", encoding="utf-8") as md_file:
            md_file.write(pdf_result.text_content)
        print(f"成功转换: {os.path.basename(pdf_path)} -> {os.path.basename(output_path)}")
    except Exception as e:
        print(f"转换失败: {os.path.basename(pdf_path)}，错误信息: {e}")

def batch_convert_pdfs(input_folder, output_folder):
    """批量转换文件夹中的所有 PDF 文件。"""
    os.makedirs(output_folder, exist_ok=True)
    for file_name in os.listdir(input_folder):
        if file_name.endswith(".pdf"):
            pdf_path = os.path.join(input_folder, file_name)
            markdown_file_name = os.path.splitext(file_name)[0] + ".md"
            markdown_path = os.path.join(output_folder, markdown_file_name)
            convert_pdf_to_markdown(pdf_path, markdown_path)
