import zmq
import uuid
import random 

import socket

def find_empty_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock.bind(("", 0))
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    
    return port


class User:
    def __init__(self, message_server_ip, message_server_port):
        self.message_server_ip = message_server_ip
        self.message_server_port = message_server_port
        self.uuid=str(uuid.uuid1())

    def request_group_list(self):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect(f"tcp://{self.message_server_ip}:{self.message_server_port}")

        socket.send_json({"action": "get_group_list","user_uuid":self.uuid})
        groups = socket.recv_json()
        return groups

    def join_group(self, group_name, user_uuid):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)

        for group_uuid, group_info in self.request_group_list().items():
            if group_info["name"] == group_name:
                group_ip, group_port = group_info["ip_address"].split(":")
                socket.connect(f"tcp://{group_ip}:{group_port}")
                socket.send_json({"action": "join_group", "user_uuid": user_uuid})
                response = socket.recv_string()
                # print(f"Join group '{group_name}' response:", response)
                print(response)
                break
        else:
            print("FAILURE")

    def leave_group(self, group_name, user_uuid):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        for group_uuid, group_info in self.request_group_list().items():
            if group_info["name"] == group_name:
                group_ip, group_port = group_info["ip_address"].split(":")
                socket.connect(f"tcp://{group_ip}:{group_port}")
                socket.send_json({"action": "leave_group", "user_uuid": user_uuid})
                response = socket.recv_string()
                # print(f"Leave group '{group_name}' response:", response)
                print(response)
                break
        else:
            print("FAILURE")

    def get_messages(self, group_name, user_uuid, timestamp=None):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)

        for group_uuid, group_info in self.request_group_list().items():
            if group_info["name"] == group_name:
                group_ip, group_port = group_info["ip_address"].split(":")
                socket.connect(f"tcp://{group_ip}:{group_port}")

                message = {"action": "get_messages", "user_uuid": user_uuid,"timestamp":timestamp}

                socket.send_json(message)
                messages = socket.recv_json()
                # print(messages)
                for msgs in messages['response']:
                    print(msgs)
                # print()
                # print("Received messages from group", group_name, ":", messages)
                break
        else:
            print("FAILURE")
    
    def send_message(self, group_name, user_uuid, message_content):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)

        for group_uuid, group_info in self.request_group_list().items():
            if group_info["name"] == group_name:
                group_ip, group_port = group_info["ip_address"].split(":")
                socket.connect(f"tcp://{group_ip}:{group_port}")

                socket.send_json({"action": "send_message", "user_uuid": user_uuid, "message": message_content})
                response = socket.recv_string()
                print()
                break
        else:
            print(f"Group '{group_name}' not found.")
                

def menu():
    
    user = User("localhost", 5555)
    while True:
        m=int(input("""
1) Get Groups
2) Join Group
3) Leave Group
4) Get Message 
5) Send Message
6) Exit
             """))
        if m == 1:
            groups = user.request_group_list()
            print("The user prints:")
            for server_name, server_address in groups.items():
                print(f"    {server_name} - {server_address}")
        elif m == 2:
            group_name = input("Enter group name to join: ")
            user.join_group(group_name, user.uuid)
        elif m == 3:
            group_name = input("Enter group name to leave: ")
            user.leave_group(group_name, user.uuid)
        elif m == 4:
            group_name = input("Enter group name to get messages from: ")
            user.get_messages(group_name, user.uuid)
        elif m == 5:
            group_name = input("Enter group name to send message to: ")
            message_content = input("Enter message content: ")
            user.send_message(group_name, user.uuid, message_content)
        elif m == 6:
            break
        else:
            print("Invalid option. Please choose a number between 1 and 6.")

if __name__ == "__main__":
    menu()
