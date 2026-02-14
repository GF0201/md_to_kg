from neo4j_connector import Neo4jConnector
from llm_integration import LLMClient
import json


class QAApplication:
    def __init__(self):
        self.neo4j = Neo4jConnector()
        self.llm = LLMClient()

    def process_question(self, question):
        # 生成Cypher查询
        cypher = self.llm.generate_cypher(question)
        if not cypher:
            return "无法生成有效的查询语句，请尝试重新提问。"

        # 执行查询
        try:
            results = self.neo4j.execute_query(cypher)
        except Exception as e:
            return f"查询执行失败：{str(e)}"

        # 生成自然语言回答
        if not results:
            return "没有找到相关结果。"

        return self.llm.generate_answer(question, json.dumps(results, ensure_ascii=False))

    def run(self):
        print("计算机网络问答系统（输入exit退出）")
        while True:
            question = input("\n你的问题：")
            if question.lower() == 'exit':
                break
            print("\n处理中...")
            answer = self.process_question(question)
            print(f"\n答案：{answer}")


if __name__ == "__main__":
    app = QAApplication()
    app.run()