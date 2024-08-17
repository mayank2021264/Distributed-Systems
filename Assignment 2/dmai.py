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
from threading import Event
import sys
import os
import signal
import json

class nodes:
    def __init__(self,id,stub):
        self.id=id
        self.stub=stub
        self.port

import socket

def is_port_open(host,port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.2)  
        s.connect((host, port))
        return True
    except (socket.timeout, ConnectionRefusedError):
        return False
    finally:
        s.close()


class log_entry:
    def __init__(self,t,key,value,term):
        self.t=t
        if t=="NO-OP":
            self.key=None
            self.value=None
            self.term=int(term)
        elif t=="SET":
            self.key=key
            self.value=value
            self.term=int(term)
    def to_dict(self):
        if self.t == "NO-OP":
            return {
                "t": self.t,
                "term": self.term
            }
        elif self.t == "SET":
            return {
                "t": self.t,
                "key": self.key,
                "value": self.value,
                "term": self.term
            }
        
class client(raft_grpc.svr_cltServicer):
    def __init__(self,rt):
        self.rt=rt
    
    def set(self,msg,context):
        rt.write(rt.dumpfile,f"Set : Node {self.rt.nodeid} {self.rt.current_leader} received  {msg} request")    
        print(time()," :  ",f"Node {self.rt.nodeid} {self.rt.current_leader} received  {msg} request")    
        if(self.rt.current_role=="leader")  and (self.rt.lease > time()):
            lentry=log_entry("SET",msg.key,msg.value,self.rt.curr_term)
            t=self.rt.broadcast_msgs(lentry)
            # self.write(self.dumpfile,"REPLY  ---> entry :", t)
            # self.write(self.dumpfile,"set success")
            return raftpb2.reply(data=None,lID=self.rt.current_leader,success=t)
        else:
            rt.write(rt.dumpfile,"Failure : I am not leader")
            return raftpb2.reply(data=None,lID=self.rt.current_leader,success=False)

    def get(self,msg,context):
        rt.write(rt.dumpfile,f"GEt : Node {self.rt.nodeid} {self.rt.current_leader} received {msg} request")    
        print(time()," :  ",f"Node {self.rt.nodeid} {self.rt.current_leader} received {msg} request")    
        if(self.rt.current_role=="leader") and (self.rt.lease > time()):
            for i in reversed(self.rt.logs):
                if i.key==msg.key and (self.rt.lease > time()):
                    return raftpb2.reply(data=i.value,lID=self.rt.current_leader,success=True)
            return raftpb2.reply(data="DN",lID=self.rt.current_leader,success=False)
        else:
            rt.write(rt.dumpfile,"Failure : I am not leader")
            return raftpb2.reply(data="NL",lID=self.rt.current_leader,success=False)

class raftc(raft_grpc.raftServicer):
    def __init__(self,id,id_port):
        self.nodeid,self.host = id,id_port[id]
        self.node_ads=[]
        self.curr_term=0
        self.votedfor=None
        self.logs=[]
        self.commit_length=0
        self.current_role="follower"
        self.current_leader=None
        self.votes_rcvd=set()
        self.sent_length=[0]*(len(id_port))
        self.acked_length=[0]*(len(id_port))
        self.eto = time() + round(random.uniform(5,10),6) 
        self.logfile=f"./log_node_{self.nodeid}/log.txt."
        self.dumpfile=f"./log_node_{self.nodeid}/dump.txt."
        self.leaderlease=0
        self.lease=0 
        self.lb=False
        self.noop=0
        self.rpcid=0
        self.leaseacks=0
        self.leasenum=0
        for id,port in enumerate(id_port):
            if(id!=self.nodeid):
                self.node_ads.append([id,port])    
        try:
            os.mkdir(f"./log_node_{self.nodeid}")    
        except FileExistsError as e:
            pass
        except Exception as e:
            print(time()," :  ","log Error : " ,e)
        
        self.write(self.dumpfile,f"{time()}Initilisation for node {self.nodeid} done  {len(self.node_ads)}")
        
    def write(self,fi,s):
        try:
            with open(fi,"a") as f:
                f.write(s+"\n")
        except Exception as e:
            print(time()," :  ","w-->file Error : " ,e,s)

    def update(self):
        print(time()," :  ",f" --------------------> {self.nodeid} : {self.current_role} , {self.commit_length}, {len(self.logs)} , {self.curr_term} \n {self.leaderlease , self.eto , self.lease , time()}\n ")
        self.write(self.dumpfile,f"{time()} <====> {self.rpcid} {self.lb} {self.nodeid}  \n: {self.current_role} : {self.commit_length} , {len(self.logs)} , {self.curr_term} \n {self.leaderlease} , {self.eto} , {self.lease}   ")
        # if(type(self.curr_term)==str):
        #     print(time()," :  ","str self.curr-term              ",self.curr_term)
        if self.current_role=="leader":
            if time()>=self.leaderlease and  time()<self.lease  :
                self.leaseacks=1
                self.leasenum=1
                self.lb=False
                self.rpcid+=1
                for follower,prt in self.node_ads:
                    try:
                        print(time()," :  ",f"sending heartbeat and renew request from {self.nodeid} to {follower}  : {self.leasenum} : {self.leaseacks}")
                        self.write(self.dumpfile,f"{time()}sending heartbeat and renew request from {self.nodeid} to {follower}")
                        self.leasenum+=1
                        self.replicate_log(self.nodeid,follower,prt)
                    except grpc.RpcError as e:
                        self.write(self.dumpfile,f"{time()}sending heartbeat and renew request from {self.nodeid} to {follower}")
                        print(time()," :  ",f"sending heartbeat and renew request from {self.nodeid} to {follower}")
                        print(time()," :  ",f"ReqVote RPC Error to {follower} ")
                        self.write(self.dumpfile,e)
                
            elif(time() > self.lease):
               self.write(self.dumpfile,f"{time()}{self.nodeid} not able to renew lease , stepping down")
               print(time()," :  ",f"{self.nodeid} not able to renew lease , stepping down")
               self.current_leader=None
               self.current_role='follower'
               self.eto=time()+round(random.uniform(5,10),6)



        if (time() > self.eto ):
            if (self.current_role == 'follower'):
                self.current_role="candidate"
                self.write(self.dumpfile,f"{time()}Node {self.nodeid} election timer timed out, becoming cadidate ")
            if(self.current_role=='candidate'):
                print(time()," :  ",f" Starting election {time()} , {self.eto}\n" )
                self.write(self.dumpfile,f"time()  :   Starting election {time()} , {self.eto}" )
                self.try_leader()
        # self.save(f"C:/Users/Vianshu/Desktop/117_A2/log_node_{self.nodeid}/metadata")

    def try_leader(self):
        # self.write(self.dumpfile,"Trying to become leader")
        self.curr_term+=1
        self.current_role = 'candidate'
        self.votedfor=self.nodeid
        self.votes_rcvd.add(self.nodeid)
        self.lastterm=0
        if(len(self.logs) >0 ):
            self.lastterm=self.logs[-1].term
            print(time()," :  ",self.lastterm)
        try:
            req_vote_msg=raftpb2.req_vote(cterm=self.curr_term,
                                      cID=self.nodeid,
                                      cloglen=len(self.logs),
                                      clogterm=int(self.lastterm))
        except Exception as e:
            print(time()," :  ",e,"  ----------------- ",type(self.curr_term))
            print(time()," :  ",e,"  ----------------- ",type(self.nodeid))
            print(time()," :  ",e,f"  ----------{self.lastterm}------- ",type(self.lastterm))

        for id,prt in self.node_ads:
            if id!=self.nodeid:    
                try:        
                    # h,p=prt.split(':')
                    if(is_port_open(prt,50051)):
                        with grpc.insecure_channel(f"{prt}:50051") as channel:
                            stub=raft_grpc.raftStub(channel)
                            response=stub.RequestVote(req_vote_msg)
                            self.collecting_votes(response)
                    else:
                        self.write(self.dumpfile,f"{time()} COLLECTVOTE: (INACTIVE) Error occurred while sending RPC to Node {id}")

                except Exception as e:
                    print(time()," :  ",f" COLLECTVOTE: Error occurred while sending RPC to Node {id}. \n")
                    self.write(self.dumpfile,f"{time()} COLLECTVOTE: Error occurred while sending RPC to Node {id}")
        self.eto=time()+round(random.uniform(5,10),6)
            
    def RequestVote(self,c,context):
        self.write(self.dumpfile,f"{time()}Vote request recieved from {c.cID}")
        print(time()," :  ",f"Vote request recieved from {c.cID}")
        try:
            if(c.cterm > self.curr_term):
                self.write(self.dumpfile,f"{time()} candidates term was greater {c.cterm,self.curr_term}")
                print(time()," :  "," candidates term was greater ")
                self.curr_term=c.cterm
                self.current_role="follower"
                self.votedfor=None
                self.eto=time()+round(random.uniform(5,10),6)

            self.lastterm=0
            if len(self.logs) > 0:
                self.lastterm=self.logs[-1].term

            logOK=(c.clogterm > self.lastterm) or (c.clogterm == self.lastterm and c.cloglen >= len(self.logs))

            if c.cterm == self.curr_term and logOK and  self.votedfor in [c.cID,None]:
                self.votedfor=c.cID
                self.write(self.dumpfile,f"{time()}Vote granted for Node {c.cID} in term {c.cterm}.")
                print(time()," :  ",f"Vote granted for Node {c.cID} in term {c.cterm}.")
                vote_response=raftpb2.req_vote_result(term=int(self.curr_term),ID=self.nodeid,granted=True,pltime=self.leaderlease)
            else:
                self.write(self.dumpfile,f"{time()}Vote rejected for Node {c.cID} in term {c.cterm}.")
                print(time()," :  ",f"Vote rejected for Node {c.cID} in term {c.cterm}.")
                vote_response=raftpb2.req_vote_result(term=int(self.curr_term),ID=self.nodeid,granted=False,pltime=self.leaderlease)
            return vote_response
        except Exception as e:
            self.write(self.dumpfile,f"{time()}  REQVOTE RPC ERROR F :  ")
            print(time()," :  ",f" REQVOTE RPC ERROR F :  ")
          
    def collecting_votes(self,recv):
        self.write(self.dumpfile,f"{time()} vote recieved from {recv.ID},{recv.term},{recv.granted} {recv.pltime}")
        if self.current_role== "candidate" and recv.term == self.curr_term and recv.granted:
            self.votes_rcvd.add(recv.ID)
            # self.write(self.dumpfile,len(self.votes_rcvd),math.ceil((len(self.node_ads)+1)/2))
            if(len(self.votes_rcvd)  >= math.ceil((len(self.node_ads)+1)/2)):
                self.write(self.dumpfile,f"{time()}Node {self.nodeid} became the leader for term {self.curr_term}.")
                print(time()," :  ",f"Node {self.nodeid} became the leader for term {self.curr_term}.")
                self.current_role="leader"
                self.current_leader=self.nodeid
                self.votes_rcvd=set()
                self.leaderlease=max(self.leaderlease,recv.pltime)
                self.eto=time()+round(random.uniform(5,10),6)
                chk=0
                while(time()<self.leaderlease):
                    if(not chk):
                        print(f"{time(), self.lease ,self.leaderlease} New Leader waiting for Old Leader Lease to timeout.")
                        self.write(self.dumpfile,f"{time(), self.lease ,self.leaderlease} New Leader waiting for Old Leader Lease to timeout.")
                        chk=1
                print(f"{time(), self.lease ,self.leaderlease} Old Leader lease ended")
                self.write(self.dumpfile,f"{time(), self.lease ,self.leaderlease} Old Leader lease ended ")
                
                self.lease=time()+10
                noop_entry=log_entry("NO-OP",-1,-1,self.curr_term)
                self.broadcast_msgs(noop_entry)

        elif recv.term > self.curr_term:
            self.curr_term=recv.term 
            self.current_role="follower"
            self.votedfor=None
            self.eto=time()+round(random.uniform(5,10),6)
            print(time()," :  ",f"{self.nodeid} Stepping down my term was less")
            self.write(self.dumpfile,f"{time()}{self.nodeid} Stepping down my term was less")

    def broadcast_msgs(self,entry):
        if self.current_role=="leader" and time()<self.lease and time()>self.leaderlease :
            self.logs.append(entry)
            self.acked_length[self.nodeid]=len(self.logs)
            print(time()," :  ",f"leader appended Got Entry from client sending to other nodes {entry.t,entry.key,entry.value,entry.term}")
            self.write(self.dumpfile,f"{time()} leader appended Got Entry from client sending to other nodes {entry.t,entry.key,entry.value,entry.term}")
            temp=len(self.logs)
            for fid,prt in self.node_ads:
                if fid != self.nodeid:
                    try:
                        self.replicate_log(self.nodeid,fid,prt)
                    except Exception as e:
                        self.write(self.dumpfile,e)
            # self.write(self.dumpfile,"commit check before",temp," --- ",self.commit_length)
            if self.commit_length >= temp:
                return True
            else:
                return False
            
    def replicate_log(self,leaderid,followerid,prt): #called periodically and when there is a new message
        prefixlen=self.sent_length[followerid]
        suffix=[]
        for i in self.logs[prefixlen:]:
            if(i.t=="NO-OP"):
                suffix.append(f"{i.t} {i.term}")
            else:
                suffix.append(f"{i.t} {i.key} {i.value} {i.term}")
        prefixterm=0
        if prefixlen > 0 :
            prefixterm = self.logs[prefixlen-1].term
        logm=raftpb2.log_m(lid=self.current_leader,cterm=int(self.curr_term),pfxlen=prefixlen,pfxterm=prefixterm,commitlength=self.commit_length,lease=self.lease,type="RLL",suffix=suffix)
        try:
            # h,p=prt.split(':')
            if(is_port_open(prt,50051)):
                with grpc.insecure_channel(f"{prt}:50051") as channel:
                    self.write(self.dumpfile,f"{time()} : sending log request to {followerid}\n {suffix} ")
                    stub=raft_grpc.raftStub(channel)
                    self.handle_log_response(stub.LogReq(logm))   
            else:
                self.write(self.dumpfile,f"{time()} False : {followerid}.\n")
                    
        except Exception as e:
            self.write(self.dumpfile,f"{time()} RPLOG GRPC Error : occurred while sending RPC to Node {followerid}.\n{e} \n")
        
        # except Exception as e:
            # self.write(self.dumpfile,f"{time()} RPLOG GRPC Error : occurred while sending RPC to Node {followerid}.\n{e} \n")
        

    def LogReq(self,ldr,context):
        try:
            
            if(ldr.cterm > self.curr_term):
                self.write(self.dumpfile,f"{time()} : first Recieved heartbeat from {ldr.lid}")
                print(time()," :  ",f"++>Recieved heartbeat from {ldr.lid}")
                self.curr_term=ldr.cterm
                self.votedfor=None
                # self.eto=time()+round(random.uniform(5,10),6)
                

            if (ldr.cterm==self.curr_term):
                self.eto=time()+round(random.uniform(5,10),6)
                if self.current_role=="candidate":
                    print(time()," :  ",f"{self.nodeid} Stepping down ----- lobreq")
                self.write(self.dumpfile,f"{time()}  : Recieved heartbeat from {ldr.lid}")
                print(time()," :  ",f"-->Recieved heartbeat from {ldr.lid} || et0 increased")
                self.current_role="follower"
                self.current_leader=ldr.lid

            lt=""
            if(ldr.type=="ILL") : #increase leader lease (ILL) as leader got quorom of acks
                self.leaderlease=time()+10
                self.write(self.dumpfile,f"{time()}{self.nodeid} : Leader {self.current_leader } renewed lease ")     #                                                 leader lease updated
                print(time()," :  ",f"{self.nodeid} : Leader {self.current_leader } renewed lease ")     #leader lease updated
            
            elif (ldr.type=="RLL"):
                print(time()," :  ",f"{self.nodeid} : Leader requested lease renewed") #                                          Lease renewal accepted
                lt="LRA"
                # self.write(self.dumpfile,f"{time()}{self.nodeid} Stepping down")
            # self.write(self.dumpfile,"check        -----------",ldr.cterm,self.curr_term)

            logOK = (len(self.logs)>=ldr.pfxlen) and (ldr.pfxlen==0 or self.logs[ldr.pfxlen-1].term==ldr.pfxterm)

            if(ldr.cterm==self.curr_term and logOK):
                try:
                    self.AppendEntries(ldr.pfxlen,ldr.commitlength,ldr.suffix)
                except Exception as e:
                    self.write(self.dumpfile,f"{time()}Append Error : --> {e}  ")
                
                ack=ldr.pfxlen + len(ldr.suffix)

                # if(len(ldr.suffix)>0):
                self.write(self.dumpfile,f"{time()}Node {self.nodeid} accepted AppendEntries RPC from {self.current_leader}.")
                print(time()," :  ",f"Node {self.nodeid} accepted AppendEntries RPC from {self.current_leader}.")
                return raftpb2.log_r(id=self.nodeid,term=self.curr_term,ack=ack,type=lt,success=True)
            else:
                self.write(self.dumpfile,f"{time()}Node {self.nodeid} rejected AppendEntries RPC from {self.current_leader}.")
                # if(len(ldr.suffix)>0):
                print(time()," :  ",f" Node {self.nodeid} rejected AppendEntries RPC from {self.current_leader}.")
                return raftpb2.log_r(id=self.nodeid,term=self.curr_term,ack=0,type=lt,success=False)
        except Exception as e:
            self.write(self.dumpfile,f"{time()}REQLOG ---> : {e}")
            print(time()," :  ",f"REQLOG : {e}")

            
    def AppendEntries(self,prefixlen,leadercommit,suffix): #called by follower to extend its log with entries rcvd from leader
        try:
            if(len(suffix)!=0):
                self.write(self.dumpfile,f"\n Append entry ---> {prefixlen} : {leadercommit} \n{suffix}  ")
                
            if len(suffix) > 0 and len(self.logs) >  prefixlen:
                index=min(len(self.logs),prefixlen+len(suffix))-1
                # print(time()," :  ","idx - pfx  ",index-prefixlen)
                # self.write(self.dumpfile,f"{time()} idx - pfx  {index-prefixlen}")
                ct=suffix[index-prefixlen].split()[-1]
                if(self.logs[index].term != ct):
                    self.logs=self.logs[:prefixlen]   
            if prefixlen+len(suffix) > len(self.logs):
                for i in range(len(self.logs)-prefixlen,len(suffix)):
                    self.write(self.dumpfile,f"{time()}Node {self.nodeid} (follower) Appended the entry {suffix[i]} to the state machine.")
                    if(suffix[i].split()[0]=="NO-OP"):
                        t,ct=suffix[i].split()
                        self.logs.append(log_entry(t,0,0,ct))
                    else:
                        t,k,v,ct=suffix[i].split()
                        self.logs.append(log_entry(t,k,v,ct))
            if leadercommit > self.commit_length :
                self.write(self.dumpfile,f"{time()} trying commiting {self.commit_length,leadercommit,len(self.logs),suffix}")
                for i in range(self.commit_length,leadercommit):
                    # self.write(self.dumpfile,f"{time()}Node {self.nodeid} (follower) committed the entry {i} to the state machine.")
                    self.write(self.dumpfile,f"{time()}Node {self.nodeid} (follower) committed the entry {self.logs[i].t ,self.logs[i].key ,self.logs[i].value ,self.logs[i].term} to the state machine.")
                    # self.write(self.logfile,f"{self.logs[i].t } {self.logs[i].key} {self.logs[i].value} {self.logs[i].term}")
                    
                self.commit_length=leadercommit
                print(time()," :  ",f"commited : {self.commit_length}")
                self.write(self.dumpfile,f"{time()} : commited : {self.commit_length}")
        except Exception as e:
            print(time()," :  ",f"Exception append 3  : {e}  : {len(suffix)} : {leadercommit} : {self.commit_length}")
            self.write(self.dumpfile,f"{time()}Exception append 3 : {e} : {len(suffix)} : {leadercommit} : {self.commit_length}")
            

    def handle_log_response(self,flr):
        # try:
        if (flr.type== "LRA"):
            self.write(self.dumpfile,f"{time()} : {self.rpcid}  : {self.lb}  :  Got lease ack from {flr.id})")
            print(time()," :  ",f"Got lease ack from {flr.id})")
            self.leaseacks+=1
            if (self.leaseacks >= math.ceil((len(self.node_ads)+1)/2)): 
                    self.lease=time()+10
                    self.write(self.dumpfile,f"{time()} : {self.nodeid} {self.leaseacks} : Leader lease renewed")
                    for i,prt in self.node_ads:
                        logm=raftpb2.log_m(lid=self.current_leader,cterm=int(self.curr_term),pfxlen=0,pfxterm=0,commitlength=self.commit_length,lease=self.lease,type="ILL",suffix=[])
                        try:
                            with grpc.insecure_channel(f"{prt}:50051") as channel:
                                stub=raft_grpc.raftStub(channel)
                                stub.LogReq(logm)   
                        except grpc.RpcError as e:
                            self.write(self.dumpfile,f"{time()}handle log RPC ERROR F : node {i} ")
                            print(time()," :  ",f"handle log RPC ERROR F : node {i} ")
                        
        if flr.term == self.curr_term and self.current_role=="leader":
            if flr.success and flr.ack >= self.acked_length[flr.id]:
                try:    
                    self.write(self.dumpfile,f"{time()}updating sent length for {flr.id},{flr.ack} |||||||||||||||")
                    self.sent_length[flr.id] = flr.ack
                    self.acked_length[flr.id] = flr.ack
                    self.CommitLogEntries()
                except Exception as e:
                    self.write(self.dumpfile,f"{time()}handlelr log1: {e}" f"\nflr :{flr}")
                    print(time()," :  ",f"handlelr log1: {e}" "\nflr :{flr}")
            elif self.sent_length[flr.id]>0:
                print(time()," :  ",f"tryin again for node{flr.id}  ---> {flr.success}  :  {flr.ack} : {self.acked_length[flr.id]}")
                self.sent_length[flr.id]=self.sent_length[flr.id]-1
                
                # self.write(self.dumpfile,f"{time()}handlelr log2: {e}" f"\nflr :{flr}")
                # print(time()," :  ",f"handlelr \nlog2: {e} \nflr :{flr}  \n{self.node_ads[flr.id][1]} ")
                # try:
                fprt=""
                for i,prt in self.node_ads:
                    if(i==flr.id):
                        fprt=prt
                self.replicate_log(self.nodeid,flr.term,fprt)
                # except Exception as e:
                    # self.write(self.dumpfile,f"{time()}handlelr log2: {e}" f"\nflr :{flr}")
                    # print(time()," :  ",f"handlelr \nlog2: {e} \nflr :{flr}  \n{self.node_ads[flr.id][1]} ")

        elif flr.term > self.curr_term :
            self.curr_term=int(flr.term)
            print(time()," :  ","Stepping down handle log response")
            self.current_role="follower"
            #    self.write(self.dumpfile,f"{time()}{self.nodeid} Stepping down")
            self.eto=time()+round(random.uniform(5,10),6)
            self.votedfor=None
        # except Exception as e:
            # self.write(self.dumpfile,f"{time()}handlelr log: {e}" f"\nflr :{flr}")

    def acks(self,length):
        return sum(i>=length for i in self.acked_length)

    def CommitLogEntries(self):
        try:
            minacks=math.ceil((len(self.node_ads)+1)/2)
            ready=[]
            for i in range(1,len(self.logs)+1):
                if(self.acks(i)>= minacks):
                    ready.append(i)
            # self.write(self.dumpfile,f"{time()}Trying commit {ready}")
            # self.write(self.dumpfile,f"{time()}Trying commit {ready}")
            if len(ready)!=0 and max(ready)>self.commit_length and self.logs[max(ready)-1].term == self.curr_term:
                for i in range(self.commit_length,max(ready)):
                    ent=self.logs[i]
                    # self.write(self.logfile,f"{ent.t} {ent.key} {ent.value} {ent.term}")   
                    self.write(self.dumpfile,f"{time()}Node {self.nodeid} (leader) committed the entry {self.logs[i]} to the state machine.")
                    print(time()," :  ",f"Node {self.nodeid} (leader) committed the entry {self.logs[i]} to the state machine.")
                self.commit_length=max(ready)
        except Exception as e:
            print(time()," :  ",f"Commiting error : {e} ")
            self.write(self.dumpfile,f"{time()}Commiting error : {e}")
    
    def restore(self, filename, n):
        with open(filename, 'r') as file:
            data = json.load(file)
    
        self.logs = []
        for entry_data in data.get('logs', []):
            t = entry_data['t']
            term = entry_data['term'] 
            if(t=="NO-OP"):
                key=None
                value=None
            else:
                key = entry_data['key']
                value = entry_data['value']
            entry = log_entry(t, key, value, term)
            self.logs.append(entry)

        for attr, value in data.items():
            if not attr.startswith("__") and attr not in ["logs", "votes_rcvd"]:
                setattr(self, attr, value)

        self.current_role = "follower"
        self.current_leader = None
        self.votes_rcvd = set()
        self.eto = time() + round(random.uniform(5, 10), 6)
        self.leaderlease = 0
        self.lease = 0
        self.noop = 0
        self.leaseacks = 0
        self.sent_length = [0] * n
        self.acked_length = [0] * n

        try:
            with open(self.dumpfile, "a") as f:
                f.write(f"\n\n RESTARTING NODE\n\n")
                f.write(f"\n{self.logs}  \n{self.commit_length} \n")
        except Exception as e:
            print(time(), " :  ", "<---file Error : ", e)

        try:
            with open(self.logfile, "w") as f:
                for ent in self.logs:
                    f.write(f"{ent.t} {ent.key} {ent.value} {ent.term}" + "\n")
        except Exception as e:
            print(time(), " :  ", "--->file Error : ", e)
    
    def save(self, filename):
        data = {}
        # Serialize the log entries into dictionaries
        log_entries_as_dicts = [entry.to_dict() for entry in self.logs]
        data['logs'] = log_entries_as_dicts

        with open(self.logfile,'w') as f:
            for ent in self.logs:
                f.write(f"{ent.t} {ent.key} {ent.value} {ent.term}\n")   

        # Serialize other attributes of the class
        for attr, value in vars(self).items():
            if not attr.startswith("__") and attr not in["logs","votes_rcvd"]:
                data[attr] = value

        # Write serialized data to file
        with open(filename, 'w') as file:
            json.dump(data, file)

def serve(rt,event,addr):
    server=grpc.server(futures.ThreadPoolExecutor(10))
    raft_grpc.add_raftServicer_to_server(rt,server)
    raft_grpc.add_svr_cltServicer_to_server(client(rt),server)
    # self.write(self.dumpfile,rt.host)
    server.add_insecure_port(f"{addr}:50051")
    # print(time()," :  ","Server Starting")
    server.start()
    # print(time()," :  ","Server Running")
    try:
        while (True):
            server.wait_for_termination(1)
            if event.is_set():
                rt.save(f"./log_node_{rt.nodeid}/metadata")
                sys.exit(0)

    except KeyboardInterrupt as k:
        sys.exit(0)

def upd(rt,event):
    # sleep(2)
    try:
        while True:        
            sleep(1)
            rt.update()
            if event.is_set():
                # rt.save(f"C:/Users/Vianshu/Desktop/117_A2/log_node_{rt.nodeid}/metadata")
                sys.exit(0)
    except KeyboardInterrupt as k:
        sys.exit(0)
if __name__=='__main__':

    id = sys.argv[1]
    # id_ads = ["50051", "50052", "50053", "50054"]
    # id_ads = ["50051", "50052", "50053","50054","50055"]
    if(len(sys.argv)!=7):
        print("INVALID TRY AGAIN")
        sys.exit(0)
    id_ads=[]
    for i in sys.argv[2:]:
        id_ads.append(i)
    
    rt = raftc(int(id), id_ads)    
    print(id_ads[int(id)])
    if (os.path.exists(f"./log_node_{rt.nodeid}/metadata")):
        rt.write(rt.dumpfile,"   ----------      RESTARTING NODE  ------------ ")
        rt.restore(f"./log_node_{rt.nodeid}/metadata",5)
    else:
        rt.write(rt.dumpfile," STARTING NODE FOR FIRST TIME ")
    
    event = Event()
    client_thrd = threading.Thread(target=upd, args=(rt,event))
    svr_thrd = threading.Thread(target=serve, args=(rt,event,id_ads[int(id)]))
    client_thrd.start()
    svr_thrd.start()
    # try:
    #     client_thrd.start()
    #     svr_thrd.start()
    #     client_thrd.join()
    #     svr_thrd.join()
    # except KeyboardInterrupt as a:
    #     print("ENDING")
    #     client_thrd.join()
    #     svr_thrd.join()
    #     sleep(2)
    #     event.set()
    try:
        while client_thrd.is_alive() and svr_thrd.is_alive():
            client_thrd.join(1)
            svr_thrd.join(1) 
    except (KeyboardInterrupt, SystemExit):  
        print ('\n! Received keyboard interrupt, quitting threads.\n')
        event.set()
        rt.save(f"./log_node_{rt.nodeid}/metadata")
        sys.exit(0)