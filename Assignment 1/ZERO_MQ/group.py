import zmq
import threading
import uuid
import time
import socket

def find_empty_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # sock.bind(("", 0))
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    
    return port

class Group:
    def __init__(self, message_server_ip, message_server_port, name):
        self.port = None
        self.users = []
        self.messages = []
        self.message_server_ip = message_server_ip
        self.message_server_port = message_server_port
        self.name = name
        self.uuid = uuid.uuid1()

    def join_group(self, user_uuid):
        if user_uuid not in self.users:
            self.users.append(user_uuid)
            return "SUCCESS"
        else:
            return "User already in group"

    def leave_group(self, user_uuid):
        print()
        print(self.users)
        print()
        if user_uuid in self.users:
            self.users.remove(user_uuid)
            return "SUCCESS"
        else:
            return "User not found in group"

    def get_messages(self, timestamp=None):
        if timestamp:
            filtered_messages = [msg["message"] for msg in self.messages if msg["timestamp"] >= timestamp]
            return filtered_messages
        else:
            return [msg["message"] for msg in self.messages]

    def send_message(self, message):
        timestamp = time.time()  
        self.messages.append({"timestamp": timestamp, "message": message})
        socket.send_json({"response": "SUCCESS"})
    
    def register_with_message_server(self):
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.connect(f"tcp://{self.message_server_ip}:{self.message_server_port}")

        message = {"action": "register_group", "name": self.name, "group_uuid": str(self.uuid), "ip_address": f"{self.message_server_ip}:{self.port}"}
        socket.send_json(message)
        response = socket.recv_string()
        print("Registration response:", response)

    def handle_client(self, socket):
        message = socket.recv_json()
        action = message["action"]
        
            
        if action == "send_message":
            try:
                send_thread=threading.Thread(target=self.send_message(message["message"]))
                send_thread.start()
            except:
                socket.send_json({"response": "FAILURE"})
            return
        if action == "join_group":
            user_uuid = message["user_uuid"]
            print(f"Join Request from {user_uuid} ")
            response = self.join_group(user_uuid)

        elif action == "leave_group":
            user_uuid = message["user_uuid"]
            print(f"Leave Request from {user_uuid} ")
            response = self.leave_group(user_uuid)

        elif action == "get_messages":
            timestamp = message["timestamp"]
            response = self.get_messages(timestamp)
        else:
            response = "Unknown action"

        socket.send_json({"response": response})


    def start(self, port):
        self.port = port
        self.register_with_message_server()

        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind(f"tcp://*:{self.port}")

        print(f"Group Server '{self.name}' with UUID '{self.uuid}' is running...")

        while True:
            self.handle_client(socket)


if __name__ == "__main__":
    group = Group("localhost", 5555, input("Enter Group name : "))
    group.start(find_empty_port())
