import ollama
import json
from dotenv import load_dotenv
import os

load_dotenv()


class LLMClient:
    def __init__(self):
        self.client = ollama.Client(host=os.getenv("OLLAMA_HOST"))

    def generate_cypher(self, question):
        prompt = f"""
        你是一个计算机网络知识图谱专家，请根据以下知识图谱结构将用户的问题转换为Cypher查询语句。

        知识图谱结构：
        - 节点类型：Protocol, Device, NetworkLayer
        - 协议属性：name, description, layer, reliability
        - 设备属性：name, type, layer
        - 关系：BELONGS_TO（协议属于某层）, USES（设备使用协议）

        示例：
        问题：HTTP协议属于哪一层？
        CYPHER: MATCH (p:Protocol {name: 'HTTP'}) RETURN p.layer

        当前问题：{question}
        """

        response = self.client.generate(
            model='qwen2:7b',
            prompt=prompt,
            format='json',
            options={'temperature': 0.1}
        )

        try:
            return json.loads(response['response'])['cypher']
        except:
            return None

    def generate_answer(self, question, context):
        prompt = f"""
        根据以下上下文信息，用中文回答用户的问题。
        保持回答专业但易懂，使用适当的网络术语。

        问题：{question}
        上下文：{context}
        """

        response = self.client.generate(
            model='qwen2.5:latest',
            prompt=prompt,
            options={'temperature': 0.5}
        )

        return response['response']