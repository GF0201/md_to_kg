import json


def process_json_file(input_file, output_file):
    # 打开txt文件用于写入
    with open(output_file, 'w', encoding='utf-8') as txt_file:
        try:
            with open(input_file, 'r', encoding='utf-8') as json_file:
                data = json.load(json_file)

                # 调试输出：检查数据的类型
                print(f"数据类型: {type(data)}")

                # 如果data是列表类型，则处理每个元素
                if isinstance(data, list):
                    print(f"共有 {len(data)} 个三元组")
                    for triple in data:
                        # 确保每个元素是字典类型
                        if isinstance(triple, dict):
                            # 获取三元组中的头、关系和尾
                            head = triple.get('head')
                            relation = triple.get('relation')  # 将connect改为relation
                            tail = triple.get('tail')

                            # 调试输出：查看每个三元组
                            print(f"三元组: {head} {relation} {tail}")

                            if head and relation and tail:
                                # 将三元组转换为句子
                                sentence = f"{head} {relation} {tail}"
                                # 将句子写入txt文件，并换行
                                txt_file.write(f"{sentence}\n")
                            else:
                                print(f"跳过无效三元组: {triple}")
                        else:
                            print(f"跳过非字典元素: {triple}")
                else:
                    print(f"错误：JSON文件的根元素应该是列表类型，实际为：{type(data)}")
        except Exception as e:
            print(f"无法处理文件 {input_file}: {e}")


if __name__ == "__main__":
    # 指定输入JSON文件和输出txt文件路径
    input_file = 'D:/pythonProject/md_split/new_triple/无线局域网WLAN.json'  # 替换为你的JSON文件路径
    output_file = 'D:/pythonProject/md_split/无线局域网WLAN.txt'  # 输出的Markdown文件路径

    # 处理单个JSON文件
    process_json_file(input_file, output_file)
    print(f"结果已保存到 {output_file}")
