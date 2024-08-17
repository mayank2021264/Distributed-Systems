import zmq

class MessageServer:
    def __init__(self, port):
        self.port = port
        self.groups = {}

    def register_group(self, name, group_uuid, ip_address):
        self.groups[group_uuid] = {"name": name, "ip_address": ip_address}

    def get_group_list(self):
        return self.groups

    def start(self):
        context = zmq.Context()
        socket = context.socket(zmq.REP)
        socket.bind(f"tcp://*:{self.port}")

        print("Message Server is running...")

        while True:
            message = socket.recv_json()
            if message["action"] == "register_group":
                name = message["name"]
                group_uuid = message["group_uuid"]
                ip_address = message["ip_address"]
                self.register_group(name, group_uuid, ip_address)
                print(f"Group '{name}' with UUID '{group_uuid}' registered from {ip_address}")
                socket.send_string("SUCCESS")
            elif message["action"] == "get_group_list":
                groups = self.get_group_list()
                print(f"GROUP LIST REQUEST FROM {message["user_uuid"]}")
                socket.send_json(groups)
            else:
                socket.send_string("Unknown action")


if __name__ == "__main__":
    server = MessageServer(5555)
    server.start()
