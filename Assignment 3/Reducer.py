import mprd_pb2 as mpb2
import mprd_pb2_grpc as mpb2_grpc
import grpc
from concurrent import futures
import sys
import os
import numpy as np
import random
from time import sleep
class Reducer:
    def __init__(self,port) -> None:
        self.data={}
        self.id=0
        self.f=f"Data/dumps/Reducer_{port}_dump.txt"
        # with open(self.f,"w") as fd:
        #     fd.write("")
    # def reduce(points)
    def get_data(self,p):
        try:
            with grpc.insecure_channel(f"localhost:{p}") as channel:
                stub = mpb2_grpc.MapperStub(channel)
                response = stub.get_data(mpb2.data(cid=f"{self.id}"))
                self.sort_shuffle(response.d)
        except Exception as e:
            self.write(f"REspof--> {e}\n")
            print("REspof-->",e)
    
    def write(self,txt):
        try:
            with open(self.f,"a") as df:
                df.write(txt+"\n")
        except Exception as e:
            print(f"ERROR WRITING DUMP : {e}, {txt} ,{type(txt)}")


    def sort_shuffle(self,data):
        for i in data:
            self.data[int(i.cid)].append([i.point[0],i.point[1]]) 
            
    def Reducer(self,msg,context):
        # sleep(5)
        k=random.random() 
        if k> 0.5:
            self.write(" Reducer Failed ")
            # print(str(k))
            return mpb2.DataResponse(result="NO")
        self.write(f"----------------------------------------{msg.iterno}---------------------------------\n")
        print(f"----------------------------------------{msg.iterno}---------------------------------")
        self.write(f"DATA RECIEVED FROM MASTER : {msg.id} {msg.mapper_ports} {msg.C}\n\n")
        print(f"DATA RECIEVED FROM MASTER : {msg.id} {msg.mapper_ports} {msg.C}")
        self.id=msg.id
        self.data.clear()
        self.mapper_ports=msg.mapper_ports
        for i in range(msg.C):
            self.data[i]=[]

        self.write("GETTING DATA FROM MAPPERS")
        for i in self.mapper_ports:
            try:
                self.get_data(i)
            except Exception as e:
                self.write(f"  :   {e}\n")
                print("  :   ",e)
        self.write("GOT DATA FROM MAPPERS AND ALSO SORTED,SHUFFLED")
        
        base_dir = "Data/Reducers"
        
        reducer_dir = os.path.join(base_dir,"")
        os.makedirs(reducer_dir, exist_ok=True)

        file_path = os.path.join(reducer_dir, f"R{self.id}.txt")
        
                
        temp=[]
        with open(file_path, "w") as im_f:
            for centroid_id, points  in self.data.items():
                cx,cy=0,0
                if(len(points)):
                    for p in points:
                        cx+=p[0]
                        cy+=p[1]
                    self.data[centroid_id]=(mpb2.points(points=[cx/len(points),cy/len(points)]))
                    temp.append(mpb2.cent_p(cid=str(centroid_id),x=self.data[centroid_id].points[0],y=self.data[centroid_id].points[1]))
                    self.write(f"CENTROID ID : {centroid_id}\n")
                    im_f.write(f"--> centroid : {centroid_id} : \n" )
                    im_f.write(f"{round(self.data[centroid_id].points[0], 2)}, {round(self.data[centroid_id].points[1], 2)}\n")
                    print(f"CENTROID ID :{centroid_id}")
                    print(self.data[centroid_id])
            im_f.write("\n")
        
        return mpb2.DataResponse(result="OK",d=temp)


def start_reducer_server(port):
    print("REDUCERRR")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    mpb2_grpc.add_ReducerServicer_to_server(Reducer(port), server)
    server.add_insecure_port(f"localhost:{port}")
    server.start()
    print(f"{port} : Reducer Server started")
    server.wait_for_termination()

if __name__ == "__main__":
    start_reducer_server(sys.argv[1])