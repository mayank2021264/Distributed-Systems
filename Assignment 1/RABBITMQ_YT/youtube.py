import sys,pika,os,uuid

import uuid
import sys
import pika


class yt_req():
    def __init__(self,req):
        self.cnc = pika.BlockingConnection(
            pika.ConnectionParameters(host="localhost"),
        )
        self.chnl = self.cnc.channel()
        self.chnl.queue_declare(queue="upload_reqs")
        try:
            print(req)
            self.chnl.basic_publish(exchange='',routing_key='upload_reqs',body=req)
            print("Request Send")
        except:
            print("Error")

if __name__ == "__main__":
    print(" [x] sending a youtuber_reqs")
    req=f"{sys.argv[1]} {''.join(sys.argv[2:])}"
    youtuber_rpc=yt_req(req)