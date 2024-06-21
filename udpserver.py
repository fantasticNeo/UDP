import socket
import time
import random

# 服务器的IP地址和端口号
SERVER_IP = "192.168.228.128"
SERVER_PORT = 2605

def main():
    # 创建UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # 绑定IP地址和端口号
    server_socket.bind(('', SERVER_PORT))
    
    print(f"UDP服务器正在监听")

    handshake_stage = 0  # 三次握手阶段
    expected_seq_no = 1  # 期望收到的序列号
    data_transfer = False  # 数据传输阶段
    fin_stage = False  # 四次挥手阶段

    while True:
        # 接收客户端发来的数据和客户端地址
        data, client_addr = server_socket.recvfrom(2048)
        print(f"从 {client_addr} 收到消息: {data.decode()}")

        # 解析客户端请求数据
        seq_no, ver = parse_udp_data(data.decode())

        # 检查序列号和版本号是否符合预期
        if ver == 2:
            if handshake_stage == 0 and seq_no == expected_seq_no:  # SYN阶段
                response_seq = seq_no + 1
                response_data = f"Seq no: {response_seq}, Ver: 2"
                server_socket.sendto(response_data.encode(), client_addr)
                print(f"向 {client_addr} 发送响应: {response_data}")
                expected_seq_no = 3  # 期望收到的序列号更新为3
                handshake_stage += 1  # 更新握手阶段

            elif handshake_stage == 1 and seq_no == expected_seq_no:  # ACK阶段
                # 三次握手结束，进入数据传输阶段
                print("三次握手完成，进入数据传输阶段")
                handshake_stage += 1  # 更新握手阶段
                expected_seq_no = 5  # 设置数据传输阶段的期望序列号
                data_transfer = True

            elif data_transfer and seq_no >= 5 and seq_no < 100:  # 数据传输阶段
                # 构造响应数据包
                response_seq = seq_no + 1
                response_data = f"Seq no: {response_seq}, Ver: 2"
                
                # 模拟30%的丢包概率
                if random.random() > 0.3:
                    time.sleep(random.uniform(0.05, 0.2))
                    server_socket.sendto(response_data.encode(), client_addr)
                    print(f"向 {client_addr} 发送响应: {response_data}")
                    expected_seq_no = seq_no + 2  # 期望序列号加2

                # 检测是否发送完第十二个数据包
                if seq_no == 27:
                    print("数据传输完成，进入四次挥手阶段")
                    data_transfer = False
                    fin_stage = True
                    expected_seq_no = 100  # 设置四次挥手阶段的期望序列号

            elif fin_stage and seq_no == 100:  # FIN阶段，开始四次挥手
                response_data_101 = f"Seq no: 101, Ver: 2"
                response_data_102 = f"Seq no: 102, Ver: 2"
                server_socket.sendto(response_data_101.encode(), client_addr)
                print(f"向 {client_addr} 发送响应: {response_data_101}")
                server_socket.sendto(response_data_102.encode(), client_addr)
                print(f"向 {client_addr} 发送报文: {response_data_102}")
                expected_seq_no = 103  # 设置挥手阶段的期望序列号

            elif fin_stage and seq_no == expected_seq_no:  # 最终ACK阶段
                print("四次挥手完成，连接关闭")
                break

            else:
                print("收到的请求数据包参数不符合预期设定，终止连接。")
                break
        else:
            print("收到的请求数据包版本不符合预期设定，终止连接。")
            break

def parse_udp_data(data):
    # 解析UDP报文中的序列号和版本号
    parts = data.split(', ')
    seq_no = int(parts[0].split(': ')[1])
    ver = int(parts[1].split(': ')[1])
    return seq_no, ver

if __name__ == "__main__":
    main()