import math
from time import sleep, time
import grpc 
import threading
from concurrent import futures
import comm_pb2 as raftpb2
import comm_pb2_grpc as raft_grpc
import uuid
import socket
import random 
import sys
import os
import signal



class client():
    def __init__(self,ports,lid):
        self.ports=ports
        self.leader=lid
    def getv(self,k):
        # print("hi")
        gm=raftpb2.getmsg(key=k)
        with grpc.insecure_channel(f'{self.ports[self.leader]}:50051') as channel:
            stub=raft_grpc.svr_cltStub(channel)
            res=stub.get(gm) 
            print(res)
        if (res.success==False and res.data=="DN"):
            return "key does not exist",False
        while(res.success==False and res.data!="DN  "):
            sleep(0.5)
            self.leader=res.lID
            print(res.lID)
            with grpc.insecure_channel(f'{self.ports[self.leader]}:50051') as channel:
                stub=raft_grpc.svr_cltStub(channel)
                res=stub.get(gm)  
                if (res.success==False and res.data=="DN"):
                    return "key does not exist",False
        return res.data,res.success
            
    def setv(self,k,v):
        print("his")
        gm=raftpb2.setmsg(key=k,value=v)
        try:
            with grpc.insecure_channel(f'{self.ports[self.leader]}:50051') as channel:
                stub=raft_grpc.svr_cltStub(channel)
                res=stub.set(gm)  
            while(res.success==False):
                self.leader=res.lID
                sleep(0.5)
                with grpc.insecure_channel(f'{self.ports[self.leader]}:50051') as channel:
                    stub=raft_grpc.svr_cltStub(channel)
                    res=stub.set(gm)  
            return res.lID,res.success
        except Exception as e:
            print(e)

if __name__=='__main__':
    id_ads=["35.202.71.182","35.202.36.67","104.154.194.207","34.66.221.193","34.133.14.103"]
    id_ads=["10.128.0.5","10.128.0.6","10.128.0.2","10.128.0.3","10.128.0.4"]
    # id_ads = ["50051", "50052", "50053"]


    c=client(id_ads,0)
    # c.setv("0","0")
    while(True):
        q=input("""Enter Query by given format
1) Get key
2) Set key value
                """)
        q=q.split()
        if(q[0]=="Set"):
            print(c.setv(q[1],q[2]))
        elif (q[0]=="Get"): 
            print(c.getv(q[1]))
        elif (q[0]=="CL"):
            c.leader=int(input())