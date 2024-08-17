import grpc
import time
from concurrent import futures
import comm_pb2 as pb2
import comm_pb2_grpc as pb2_grpc
from enum import Enum

cats=["ELECTRONICS", "FASHION","OTHERS"]

import socket

# def get_ip_address():
#     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#     try:
#         s.connect(("8.8.8.8", 80))
#         ip_address = s.getsockname()[0]
#     finally:
#         s.close()
#     return ip_address
# print("IP Address:", get_ip_address())

class Item:
    def __init__(self,id, product_name, category, quantity, description, seller_address, price_per_unit, seller_uuid):
        self.item_id = id  
        self.product_name = product_name
        self.category = category
        self.quantity = quantity
        self.description = description
        self.seller_address = seller_address
        self.price_per_unit = price_per_unit
        self.seller_uuid = seller_uuid
        self.num_rating = 0
        self.ratings = 0
        self.rated_buyers=[]

class Seller:
    def __init__(self, port, uuid):
        self.port = port
        self.uuid = uuid
        

class market(pb2_grpc.buyer_marketServicer):
    id_cnt = 0
    def __init__(self,*args,**kwargs):
        self.sellers = {}
        self.items = {}
        self.subscribers={}

    def register(self,request,context):
        print(f"Seller join request from {request.port}[ip:port], uuid = {request.uuid}")
        if(request.uuid in self.sellers.keys()):
            res={'status':"FAILURE! UUID Already Exists"}
        else:
            self.sellers[request.uuid]=[]
            res={'status':"SUCCESS"}
        return pb2.reg_status(**res)
    
    def sellitem(self,itm,context):
        print(f"Sell Item request from{itm.uuid}")
        if(itm.uuid in self.sellers.keys() ):
            self.items[self.id_cnt] = Item(self.id_cnt,itm.name,itm.category,itm.qty,itm.desc,itm.address,itm.price,itm.uuid)
            self.sellers[itm.uuid].append(self.items[self.id_cnt])
            self.subscribers[self.id_cnt]=[]
            self.id_cnt+=1
            res={'status':"SUCCESS"}
        else:
            res={'status':"FAILURE! Seller Not Registered"}
        return pb2.reg_status(**res)
    
    def buy_item(self, req, context):
        print(f"Buy Item {req.itemid} request from {req.buyer_address}")
        if req.itemid in self.items.keys():
            item = self.items[req.itemid]
            if item.quantity >= req.qty:
                item.quantity -= req.qty
                # send notification to seller 
                self.notify((self.items[req.itemid].seller_address),self.items[req.itemid])
                res = {'status': "SUCCESS"}
            else:
                res = {'status': "FAILURE! Insufficient Quantity"}
        else:
            res = {'status': "FAILURE! ItemNo. does not exist"}
        return pb2.reg_status(**res)

    def notify(self,seller_port,item):
        print(f"Sending noitification to {seller_port}")
        with grpc.insecure_channel(f'{seller_port}') as channel:
            notify_stub = pb2_grpc.notifStub(channel)
            r=0
            if(item.num_rating != 0):
                r=item.ratings/item.num_rating
            t = pb2.search_itms(Itemid=item.item_id, price=item.price_per_unit, name=item.product_name,
                    category=item.category, desc=item.description, qty=item.quantity,
                    address=str(item.seller_address), rating=str(r))
            notify_stub.notify(t)
            

    def updateitem(self,upd_itm,context):
        print(f"Update Item {upd_itm.itemid} request from {upd_itm.address}")
        if(upd_itm.itemid in self.items.keys()):
            t=self.items[upd_itm.itemid]
            t.quantity=upd_itm.qty
            t.price=upd_itm.price
            for sub_address in self.subscribers[upd_itm.itemid]: #send noitifications to wishlister buyers
                self.notify(sub_address,self.items[upd_itm.itemid])
            res={'status':"SUCCESS"}
            
        else:
            res={'status':"FAILURE! ItemNo. does not exist"}
        return pb2.reg_status(**res)
    

    def deleteitem(self,ditem,context):
        print(f"Delete Item {ditem.itemid} request from {ditem.address}")
        # print(self.items[ditem.item_id].keys())
        res={'status':"FAILURE!"}
        # res={'status':"FAILURE! ItemNo. does not exist"}
        if(ditem.itemid in self.items.keys()):
            self.items.pop(ditem.itemid)
            self.sellers[ditem.uuid].pop(ditem.itemid)
            res={'status':"SUCCESS"}
        return pb2.reg_status(**res)

    def display_items(self, seller, context):
        print(f"Display items request from {seller.port}")
        for item in self.sellers[seller.uuid]:
            try:
                r=0
                if(item.num_rating != 0):
                    r=item.ratings/item.num_rating
                t = pb2.display_itms(
                Itemid=item.item_id,
                price=int(item.price_per_unit),
                name=item.product_name,
                category=item.category,
                qty=int(item.quantity),
                address=item.seller_address,
                rating=str(r)  
            )
                yield t
            except Exception as e:
                print(f"Error serializing item: {e}")
    
        res = {'status': "SUCCESS"}
        return pb2.reg_status(**res)

    def search(self, search_req, context):
        print(f"Search request for Item name: {search_req.name}, Category: {search_req.cat}")
        for item in self.items.values():
            if (item.product_name.lower().startswith(search_req.name) and item.category.lower().startswith(search_req.cat)):
                r=0
                if(item.num_rating != 0):
                    r=item.ratings/item.num_rating
                t = pb2.search_itms(Itemid=item.item_id, price=item.price_per_unit, name=item.product_name,
                    category=item.category, desc=item.description, qty=item.quantity,
                    address=str(item.seller_address), rating=str(r))
                yield t
        
    def add_to_wishlist(self, req, context):
        print(f"Add to Wishlist {req.itemid} request from {req.buyer_address}")
        if req.itemid in self.items.keys():
            # seller_uuid = req.buyer_address
            self.subscribers[req.itemid].append(req.buyer_address)
            res = {'status': "SUCCESS"}
        else:
            res = {'status': "FAILURE! ItemNo. does not exist"}
   
        return pb2.reg_status(**res)

    def rate_item(self, req, context):
        print(f"Rate Item {req.itemid} request from {req.buyer_address}")
        if req.itemid in self.items.keys() :
            item = self.items[req.itemid]
            if req.buyer_address not in item.rated_buyers:
                item.num_rating+=1
                item.ratings += req.rating
                item.rated_buyers.append(req.buyer_address)
                res = {'status': "SUCCESS"}
            else :
                res={'status':"FAILURE! Buyer already rated this item"}
        else:
            res = {'status': "FAILURE! ItemNo. does not exist"}
        return pb2.reg_status(**res)




def serve():
    server=grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    pb2_grpc.add_buyer_marketServicer_to_server(market(),server)
    server.add_insecure_port('[::]:50051')
    print("Server Starting")
    server.start()
    print("Server Running")
    server.wait_for_termination()

if __name__=='__main__':
    serve()

