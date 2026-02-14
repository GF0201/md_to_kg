# PDF到知识图谱自动化流水线

将PDF文档自动转换为知识图谱三元组，并导入Neo4j数据库。

## 文件说明

| 文件 | 功能 |
|------|------|
| `pdf_to_triple.py` | PDF → Markdown → 分块 → 三元组JSON |
| `triple_to_kg.py` | JSON三元组 → Neo4j知识图谱 |
| `requirements.txt` | Python依赖清单 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 pdf_to_triple.py

编辑文件顶部的配置区：

```python
# API配置
API_KEY = "你的API密钥"
BASE_URL = "https://tb.api.mkeai.com/v1"
MODEL_NAME = "deepseek-v3.2"

# 路径配置
PDF_INPUT = r"D:\demo\pdfs"        # PDF文件或文件夹
EXCEL_CONFIG = None                 # 章节配置Excel（可选）
OUTPUT_ROOT = r"D:\demo\output"    # 输出目录
```

### 3. 运行三元组提取

```bash
python pdf_to_triple.py
```

输出目录结构：
```
output/
├── 1_split_pdfs/      # 切分后的PDF（如果使用Excel配置）
├── 2_raw_mds/         # 原始Markdown
├── 3_cleaned_mds/     # 清理后的Markdown
├── 4_chunked_mds/     # 分块后的Markdown
├── 5_keywords_mds/    # 关键词提取结果
├── 6_merged_mds/      # 合并后的Markdown
└── 7_triples_json/    # 最终三元组JSON ⭐
```

### 4. 配置 triple_to_kg.py

```python
# Neo4j配置
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "00000000"

# 输入配置
TRIPLES_FOLDER = r"D:\demo\output\7_triples_json"
```

### 5. 导入Neo4j

```bash
python triple_to_kg.py
```

## 高级配置

### PDF章节切分

如需按章节切分PDF，准备Excel文件（包含以下列）：

| name | start | end |
|------|-------|-----|
| 第1章-概述 | 1 | 20 |
| 第2章-物理层 | 21 | 50 |
| ... | ... | ... |

然后设置：
```python
EXCEL_CONFIG = r"D:\demo\chapters.xlsx"
```

### 关闭关键词提取

如需加快处理速度，可关闭关键词提取：
```python
ENABLE_KEYWORD_EXTRACTION = False
```

### 增量导入Neo4j

如需保留现有数据进行增量导入：
```python
CLEAR_EXISTING = False
```

## 三元组JSON格式

```json
[
    {
        "head": "TCP",
        "relation": "属于",
        "tail": "传输层"
    },
    {
        "head": "HTTP",
        "relation": "基于",
        "tail": "TCP"
    }
]
```

## 依赖说明

- **PyPDF2**: PDF文件拆分
- **markitdown**: PDF转Markdown（微软开源）
- **langchain**: Markdown分块
- **openai**: 大模型API调用
- **pandas/openpyxl**: Excel读取
- **py2neo**: Neo4j数据库操作
