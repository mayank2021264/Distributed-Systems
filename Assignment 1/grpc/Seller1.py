
from __future__ import print_function

import logging
from concurrent import futures
import uuid
import threading
import socket
import grpc
import comm_pb2 as pb2
import comm_pb2_grpc as pb2_grpc



def get_ip_address():
    # Create a socket object
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to a known server (Google's DNS server)
        s.connect(("8.8.8.8", 80))
        # Get the IP address
        ip_address = s.getsockname()[0]
    finally:
        s.close()
    return ip_address


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



server=grpc.server(futures.ThreadPoolExecutor(max_workers=10))
pb2_grpc.add_notifServicer_to_server(notifier(),server)
server.add_insecure_port('[::]:50052')

class Seller():
    def __init__(self):
        self.host = f"{get_ip_address()}:50052"
        print(self.host)
        self.prt ="localhost:50051"
        # self.prt = "34.170.100.50:50051" #hardcode market address
        self.uid=str(uuid.uuid1())
        self.channel = grpc.insecure_channel(self.prt)
        self.stub = pb2_grpc.buyer_marketStub(self.channel)
    
    def send(self):
        message = pb2.reg_req(port=str(self.host),uuid=self.uid)
        print(f'{message}')
        return self.stub.register(message)
    
    def item_req(self):
        nme = input("Enter the item name: ")
        cat = input("Enter the category ( Electronics, Fashion, Others): ")
        if( cat not in ["Electronics","Fashion","Others"]):
            print("Invalid! Try again")
            self.item_req()
        q = int(input("Enter the quantity: "))
        dsc = input("Enter the item description: ")
        p = float(input("Enter the price per unit: "))
        seller_address = self.host
        ud = self.uid
        msg=pb2.item(name=str(nme),category=str(cat),qty=int(q),desc=str(dsc),address=str(seller_address),price=int(p),uuid=str(ud))
        return self.stub.sellitem(msg)

    def upd_itm(self):
        id = input("Enter the item id: ")
        q = int(input("Enter the quantity: "))
        p = float(input("Enter the price per unit: "))
        sa= self.prt
        ud = self.uid
        msg=pb2.item_upd(itemid=int(id),qty=int(q),price=int(p),address=str(sa),uuid=str(ud))
        return self.stub.updateitem(msg)
    
    def del_item(self):
        id = input("Enter the item id: ")
        sa= self.prt
        ud = self.uid
        msg=pb2.del_itm(itemid=int(id),address=str(sa),uuid=str(ud))
        return self.stub.deleteitem(msg)
    
    def dis_items(self):
        sa = self.prt
        ud = self.uid
        msg = pb2.reg_req(port=str(sa), uuid=str(ud))

        response_stream = self.stub.display_items(msg)
        for item in response_stream:
            print("▀▀▀▀")
            print(f"Item ID: {item.Itemid}, Price: {item.price}, Name: {item.name}, Category: {item.category}\nQuantity: {item.qty}\nSeller: {item.address}\nRating: {item.rating}")
            # print("▀▀▀▀")


def cli():
    seler1= Seller()
    while True:
        si=input("""
SELLER INTERFACE
1) Register
2) Sell item 
3) Update item
4) Delete item
5) Display item
""")
        if(si == "1"):
            print(seler1.send())
        elif(si =="2"):
            print(seler1.item_req())
        elif(si =="3"):
            print(seler1.upd_itm())
        elif(si =="4"):
            print(seler1.del_item())
        elif(si == "5"):
            seler1.dis_items()
        else:
            print("Continue")

    
def notif_srv():
    
    # print("Server Starting")
    server.start()
    # print("seller notification Server Running")
    server.wait_for_termination()
    
if __name__ == '__main__':
    # notif_srv()
    seller_thread = threading.Thread(target=notif_srv)
    seller_thread.start()
    cli()
