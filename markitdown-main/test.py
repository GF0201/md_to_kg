import os
from markitdown import MarkItDown

markitdown = MarkItDown()
# 定义输入文件夹路径和输出文件夹路径
input_folder = "D:\\pythonProject\\markitdown-main\\extracted_pdfs"  # 替换为你的 PDF 文件夹路径
output_folder = "D:\\pythonProject\\mds"  # 替换为保存 Markdown 的文件夹路径

# 确保输出文件夹存在
os.makedirs(output_folder, exist_ok=True)

# 遍历文件夹中的所有 PDF 文件
for file_name in os.listdir(input_folder):
    if file_name.endswith(".pdf"):  # 检查是否是 PDF 文件
        pdf_path = os.path.join(input_folder, file_name)
        markdown_file_name = os.path.splitext(file_name)[0] + ".md"  # 将扩展名改为 .md
        markdown_path = os.path.join(output_folder, markdown_file_name)

        try:
            # 使用 markitdown 进行转换
            pdf_result = markitdown.convert(pdf_path)

            # 将转换后的内容保存为 Markdown 文件
            with open(markdown_path, "w", encoding="utf-8") as md_file:
                md_file.write(pdf_result.text_content)

            print(f"成功转换: {file_name} -> {markdown_file_name}")
        except Exception as e:
            print(f"转换失败: {file_name}，错误信息: {e}")
