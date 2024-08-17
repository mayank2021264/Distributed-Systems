from __future__ import print_function
from concurrent import futures
import grpc
import threading
import comm_pb2 as pb2
import comm_pb2_grpc as pb2_grpc
import uuid


import socket

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
    finally:
        s.close()
    return ip_address

# print("IP Address:", get_ip_address())
class Buyer:
    def __init__(self): 
        self.host = f"{get_ip_address()}:50053"
        print(self.host)
        # self.prt ="localhost:50051"
        self.prt = "34.170.100.50:50051"  #hardcode market address
        # print(prt)
        self.uid = str(uuid.uuid1())
        self.channel = grpc.insecure_channel(self.prt)
        self.stub = pb2_grpc.buyer_marketStub(self.channel)

    def search_items(self):
        itmnam=input("Enter Item Name : ")
        itmcat=input("Enter Item Category : ")
        msg = pb2.search_req(name=itmnam,cat=itmcat)
        response_stream = self.stub.search(msg)
        for item in response_stream:
            print(f"Search Result - Item ID: {item.Itemid} Name: {item.name} Category: {item.category}\n Description: {item.desc}\n Price: {item.price}\n Quantity: {item.qty}\n Seller Address: {item.address}\n Rating: {item.rating}")

    def buy_item_req(self):
        item_id=int(input("Enter Item_id : "))
        qunty=int(input("Enter Quantity : "))
        buyer_address=self.host
        msg = pb2.buy_req(itemid=item_id, qty=qunty, buyer_address=buyer_address)
        
        return self.stub.buy_item(msg)
    
    def add_to_wishlist(self):
        item_id=int(input("Enter Item_id : "))
        buyer_address=self.host
        msg = pb2.add_wish(itemid=item_id, buyer_address=buyer_address)
        return self.stub.add_to_wishlist(msg)

    def rate_item(self):
        item_id=int(input("Enter Item_id : "))
        itmr=int(input("Enter rating(1-5) : "))
        buyer_address=self.host
        msg = pb2.item_rate(itemid=item_id, buyer_address=buyer_address,rating=itmr)
        return self.stub.rate_item(msg)
    

# class notifier():
#     def __init__(self):
#         pass
#     def notify(self,notif):
#         print(f"""The Following Item has been updated:
# Item ID: {notif.Itemid}, Price: {notif.price}, Name: {notif.name}, Category: {notif.category},
# Description: {notif.desc}
# Quantity Remaining: {notif.qty}
# Rating: {notif.rating} / 5  |  Seller: {notif.address})
#         """)
#         res={'status':"SUCCESS"}
#         return pb2.reg_status(res)



def buyer_interface():
    buyer = Buyer()
    while True:
        choice = input("""BUYER GUI
1) Search
2) Buy Item
3) Add to wishlist
4) rate item
""")
        if choice == "1":
            buyer.search_items()
        elif choice == "2":
            print(buyer.buy_item_req())
        elif choice == "3":
            print(buyer.add_to_wishlist())
        elif choice == "4":
            print(buyer.rate_item())
        elif choice == "5":
            print("Exiting")
            break
        else:
            print("Continue")
    
    

class notifier():
    def __init__(self):
        pass
    def notify(self,notif,context):
        print(f"""The Following Item has been updated:
Item ID: {notif.Itemid}, Price: {notif.price}, Name: {notif.name}, Category: {notif.category},
Description: {notif.desc}
Quantity Remaining: {notif.qty}
Rating: {notif.rating} / 5  |  Seller: {notif.address})
        """)
        
        res={'status':"SUCCESS"}
        return pb2.reg_status(**res)
    

    
if __name__ == '__main__':
    
    seller_thread = threading.Thread(target=buyer_interface)
    seller_thread.start()
    svr_notifier=grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_notifServicer_to_server(notifier(),svr_notifier)
    svr_notifier.add_insecure_port('[::]:50053')
    # # print("Server Starting")
    svr_notifier.start()
    print("Buyer notification Server Running")
    svr_notifier.wait_for_termination()
