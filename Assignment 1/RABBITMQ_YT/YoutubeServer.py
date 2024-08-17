
import os
import sys
import json
import pika



class YT_SERVER:
    def __init__(self):
        self.cnc = pika.BlockingConnection(
        pika.ConnectionParameters(host="localhost"),
        )
        self.chnl = self.cnc.channel()
        queues={}

        self.subscribers_dict={}
        self.users=set()
        # notify_user_queues=[]
        self.chnl.queue_declare(queue="upload_reqs")
        self.chnl.queue_declare(queue="usr_reqs")

    def on_request(self,ch, method, props, body):
        print(body.decode())
        req=str(body.decode()).split(' ')
        yt_name=req[0]
        if yt_name in self.subscribers_dict.keys():
            print(self.subscribers_dict[yt_name])
        if(yt_name not in self.subscribers_dict.keys()):
            self.subscribers_dict[yt_name]=set()
        vdo_name=''.join(req[1:])
        self.send_notifs(yt_name,vdo_name)
        # response = "SUCCESS"
        # self.chnl.basic_consume()

    def usr_req(self,ch, method, props, body):
        # print(body.decode())
        req=json.loads(body.decode())
        print(req)
        if req['name'] in self.users :
            print(f"starting {req['name']}")
        else:
            print(f"Adding user {req['name']}")
            self.users.add(req['name'])
        if req['yt'] in self.subscribers_dict.keys() :
            if(req['sub']==True):
                print(f"{req['name']} subscribing to {req['yt']} ")
                self.subscribers_dict[req['yt']].add(req['name'])
                print("Done")
            else:
                print(f"{req['name']} subscribing to {req['yt']} ")
                self.subscribers_dict[req['yt']].remove(req['name'])
        else:
            print(f"youtuber : {req['yt']} does not exist")

    def send_notifs(self,ytname,vdo):
        # print("hi")
        # print(len(self.subscribers_dict[ytname]))
        for i in self.subscribers_dict[ytname]:
           notif=f"New Notification: {ytname} uploaded {vdo}."
           print(notif)
           self.chnl.basic_publish(exchange='',routing_key=f"usr.{i}",body=str(notif))
    
svr=YT_SERVER()
try:
    print(" [x] Awaiting user requests")
    svr.chnl.basic_consume(queue="usr_reqs", on_message_callback=svr.usr_req,auto_ack=True)
    svr.chnl.basic_consume(queue="upload_reqs", on_message_callback=svr.on_request,auto_ack=True)
    svr.chnl.start_consuming()
except Exception as e:
    print("error:",e)
    print('Ending Server')
    svr.chnl.close()



