from markitdown import MarkItDown

# 初始化转换器
markitdown = MarkItDown()

# 转换不同类型的文件
# PDF文档
pdf_result = markitdown.convert("IPv6.pdf")
print(pdf_result.text_content)
