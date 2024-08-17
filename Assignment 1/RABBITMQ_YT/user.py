import sys,pika,os,uuid
# we can use json to serialize and deserialize if we want to send data in dictionnarty format 

import json
#!/usr/bin/env python
import uuid
import sys
import pika


class user_req():
    def __init__(self,name,sub_req,req):
        self.name=f"usr.{name}"
        # intiliaizins queue for updatesubscriptions requests
        self.cnc = pika.BlockingConnection(
            pika.ConnectionParameters(host="localhost"),
        )

        self.channel = self.cnc.channel()

        
        self.channel.queue_declare(queue="usr_reqs")
        # self.callback_queue = result.method.queue

        # self.chnl.basic_consume(
            # queue=self.callback_queue,
            # on_message_callback=self.on_response,
            # auto_ack=True,
        # )
        self.channel.queue_declare(queue=f"{self.name}")
        if(sub_req==True):
            self.sub_upd(req)
        # self.response = None
        # self.corr_id = None
            
        self.rcv_notifs()
        try:
            print("recieving notifications")
            self.channel.start_consuming()
        except Exception as e:
            print("Error :",e)
            print("Exiting")
            self.channel.close()


    def temp(self,ch, method, properties, body):
        print(f"{body.decode()}") 

    def rcv_notifs(self):
        self.channel.basic_consume(queue=self.name, on_message_callback=self.temp, auto_ack=True)
    
    def sub_upd(self,req):
        self.channel.basic_publish(exchange='',routing_key='usr_reqs',body=str(req))
        # print("Request send to subscribe")
    

if __name__ =="__main__":
    try: 
        print(" [x] sending a user_reqs")
        if(len(sys.argv)>2):
            print(sys.argv)
            sub_req={}
            if(sys.argv[2]=='s'):
                sub_req=json.dumps({
            "name": str(sys.argv[1]),
            "yt": str(sys.argv[3]),
            "sub": True
            })
            elif (sys.argv[2]=='u'):
                sub_req=json.dumps({
            "name": str(sys.argv[1]),
            "yt": str(sys.argv[3]),
            "sub": False
            })  
            user_rpc=user_req(sys.argv[1],True,sub_req)
        else:
            user_rpc=user_req(sys.argv[1],False,"")
    except:
        print("Exiting")

    