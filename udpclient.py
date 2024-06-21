import sys
import socket
import time
import statistics

# 服务器的IP地址和端口号从命令行参数中获取
if len(sys.argv) != 3:
    print("Usage: python udpclient.py <server_ip> <server_port>")
    sys.exit(1)

SERVER_IP = sys.argv[1]
SERVER_PORT = int(sys.argv[2])
# 报文大小
PACKET_SIZE = 2048
# 发送的请求次数
NUM_REQUESTS = 12
# 超时时间
TIMEOUT = 0.5  # 500ms

class Client:
    def __init__(self):
        # 创建UDP socket
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 设置超时时间
        self.client_socket.settimeout(TIMEOUT)
        # 统计信息
        self.received_packets = 0
        self.rtt_list = []
        self.first_response_time = None
        self.last_response_time = None
        self.total_packets_sent = 0
        self.data_packets_sent = 0  # 只统计数据传输期间的发送报文数
        self.data_packets_received = 0  # 只统计数据传输期间的接收报文数

    def send_request(self, seq_no, wait_for_response=True):
        # 构造请求数据包
        message = f"Seq no: {seq_no}, Ver: 2"
        start = time.time()

        # 发送请求报文
        self.client_socket.sendto(message.encode(), (SERVER_IP, SERVER_PORT))
        self.total_packets_sent += 1  # 统计总的发送报文数
        if seq_no >= 5 and seq_no < 100:  # 只统计数据传输阶段的发送报文数
            self.data_packets_sent += 1

        if wait_for_response:
            # 接收响应或处理超时
            try:
                data, server_addr = self.client_socket.recvfrom(PACKET_SIZE)
                end = time.time()
                # 解析服务器响应数据包
                response_seq, ver = parse_udp_data(data.decode())
                if response_seq == seq_no + 1 and ver == 2:
                    rtt = (end - start) * 1000  # 计算RTT
                    self.rtt_list.append(rtt)
                    self.received_packets += 1
                    if seq_no >= 5 and seq_no < 100:  # 只统计数据传输阶段的接收报文数
                        self.data_packets_received += 1
                    print(f"从 {server_addr} 收到响应: {data.decode()}. RTT: {rtt:.2f} ms")
                    if self.first_response_time is None:
                        self.first_response_time = end
                    self.last_response_time = end
                    return True
                else:
                    print("收到的响应数据包参数不符合预期设定，终止连接.")
                    return False
            except socket.timeout:
                print(f"Seq no: {seq_no}, request time out.")
                return False
        else:
            # 三次握手的第三次和四次挥手的第四次
            print(f"发送报文: {message}")
            return True

    def run(self):
        # 记录开始时间
        self.start_time = time.time()

        # 模拟TCP三次握手
        print("进行TCP“三次握手”连接建立：")
        if not self.send_request(1):  # SYN
            return
        if not self.send_request(3, wait_for_response=False):  # ACK
            return

        # 开始数据传输
        print("\n开始发送数据包：")
        seq_no = 5
        for _ in range(NUM_REQUESTS):
            retry_count = 0  # 初始化重传次数
            while retry_count < 3:  # 最多重传两次
                if self.send_request(seq_no):
                    seq_no += 2
                    break
                retry_count += 1
                time.sleep(TIMEOUT)

        # 记录结束时间
        self.end_time = time.time()

        # 打印汇总信息
        self.print_summary()

        # 模拟TCP四次挥手（连接释放）
        print("\n进行TCP“四次挥手”连接释放：")
        if not self.send_request(100):  # FIN
            return
        if not self.send_request(103, wait_for_response=False):  # FINAL ACK
            return

    def print_summary(self):
        sent_packets = self.data_packets_sent
        received_packets = self.data_packets_received
        lost_packets = sent_packets - received_packets
        loss_rate = (lost_packets / sent_packets) * 100 if sent_packets > 0 else 0
        max_rtt = max(self.rtt_list) if self.rtt_list else 0
        min_rtt = min(self.rtt_list) if self.rtt_list else 0
        avg_rtt = sum(self.rtt_list) / len(self.rtt_list) if self.rtt_list else 0
        stddev_rtt = statistics.stdev(self.rtt_list) if len(self.rtt_list) > 1 else 0
        total_response_time = (self.last_response_time - self.first_response_time) if self.last_response_time and self.first_response_time else 0

        print("\n【汇总】")
        print(f"发送的UDP报文数目: {sent_packets}")
        print(f"接收到的UDP报文数目: {received_packets}")
        print(f"丢包率: {loss_rate:.2f}%")
        print(f"最大RTT: {max_rtt:.2f} ms")
        print(f"最小RTT: {min_rtt:.2f} ms")
        print(f"平均RTT: {avg_rtt:.2f} ms")
        print(f"RTT的标准差: {stddev_rtt:.2f} ms")
        print(f"服务器整体响应时间: {total_response_time:.2f} 秒")

def parse_udp_data(data):
    # 解析UDP报文中的序列号和版本号
    parts = data.split(', ')
    seq_no = int(parts[0].split(': ')[1])
    ver = int(parts[1].split(': ')[1])
    return seq_no, ver

if __name__ == "__main__":
    client = Client()
    client.run()