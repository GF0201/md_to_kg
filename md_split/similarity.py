import difflib


def compute_diff_similarity(text1, text2):
    # 使用difflib的SequenceMatcher来计算相似度
    seq_matcher = difflib.SequenceMatcher(None, text1, text2)
    # 获取相似度分数
    similarity = seq_matcher.ratio()
    return similarity


if __name__ == "__main__":
    # 输入两个文本
    text1 = """路由器凡时，路由器R1先收下它，接着把TTL的值减1 把P1丢弃，并向源主机发送一个ICMP时间超过差错报告报文。
由千TTL等千零了，因此凡就源主机接着发送第二个数据报P2,并把TTL设置为2。贮先到达路由器R1,R1收下后把TTL减l再转发给路由
器R2。民收到P2时TTL为1,但减l后TTL变为零了。民就丢 弃P2,并向源主机发送一个ICMP时间超过差错报告报文。这样一直继续下去
。当最后一 个数据报刚刚到达目的主机时，数据报的TTL是1。主机不转发数据报，也不把TTL值减l。但因IP数据报中封装的是无法
交付的运输层的UDP用户数据报，因此目的主机要向源主机发送ICMP终点不可达差错报告报文（见5.2.2(cid:7188)）。 这样，源主
机达到了(cid:7151)己的目的，因为这些路由器和最后目的主机发来的ICMP报文正 好给出了源主机想知道的路由信息一一到达目的
主机所经过的路由器的IP地址，以及到达 其中的每一个路由器的往返时间。图4-31是从南京的一个PC向新浪网的邮件服务器"""

    text2 = """路由器R1接收并减TTL值数据报P1。源主机发送ICMP时间超过差错报告报文。路由器R2接收并减TTL值后丢弃数据报P2。目的主机发送ICMP终点不可达差错报告报文。源主机收到路由信息。IP数据报封装UDP用户数据报。"""

    # 计算相似度
    similarity = compute_diff_similarity(text1, text2)
    print(f"文本相似度（difflib）：{similarity}")
