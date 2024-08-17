import mprd_pb2 as mpb2
import mprd_pb2_grpc as mpb2_grpc
import grpc
from concurrent import futures
import sys,os
import math
import random
from time import time,sleep
class Mapper:
    def __init__(self,port) -> None:
        self.mapping={}
        self.nc=0
        self.port=port
        self.f=f"Data/dumps/Mapper_{port}_dump.txt"
        # with open(self.f,"w") as f:
        #     f.write("")

    def write(self,txt):
        try:
            with open(self.f,"a") as f:
                f.write(txt)
        except Exception as e:
            print(f"ERROR WRITING DUMP : {e}")

    def k_means_map(self, x, centroids):
        min_distance = math.inf
        closest_centroid = None
        # self.write(x,centroids)
        # print(x,centroids)
        for centroid in centroids:
            distance = math.sqrt((x[0] - centroid[0]) ** 2 + (x[1] - centroid[1]) ** 2)
            if distance < min_distance:
                min_distance = distance
                closest_centroid = centroid
        return [closest_centroid,x,1]

    def Mapper(self,msg,context):
        # sleep(5)
        k=random.random() 
        if k> 0.5:
            self.write(" Mapper Failed \n")
            # print(str(k))
            return mpb2.DataResponse(result="NO")
        self.write(f"----------------------------------------{msg.iterno}---------------------------------\n")
        print(f"----------------------------------------{msg.iterno}---------------------------------")
        self.write(f"DETAILS RECIEVED : {msg.si}->{msg.ei} ,{msg.nl} ,{msg.nr}\n")
        print(f"DETAILS RECIEVED : {msg.si}->{msg.ei} ,{msg.nl} ,{msg.nr}")
        
        # initiliazation for data
        # sleep(5)
        centroids=[]
        self.mapping.clear()
        for i in range(msg.nr):
            self.mapping[i]=[]
        for c in msg.centroid:
            centroids.append([i for i in c.points])
        self.nc=len(centroids)
        # self.write("Centroids : ",centroids)
        # print("Centroids : ",centroids)
        
        for ind,i in enumerate(centroids):
            self.write(f"cid: {ind} , x : {i[0]} , y : {i[1]}\n")
            print(f"cid: {ind} , x : {i[0]} , y : {i[1]}")
        self.write("\n")
        print()
        with open(f"Data/inputs/{msg.data}.txt", 'r') as file:
            for line_number, line in enumerate(file):
                if line_number >= msg.si:
                    try:
                        # Mapping
                        t=self.k_means_map([float(num_str) for num_str in line.strip().split(",")],centroids)
                        # Partitioning
                        self.mapping[centroids.index(t[0])%msg.nr].append(mpb2.data(cid=str(centroids.index(t[0])),point=t[1]))
                    except Exception as e:
                        self.write(f"<--<>--> {e}")
                        print("<--<>--> ",e)
                if line_number == msg.ei-1 or line_number>msg.nl:
                    break  
        self.write("\n")
        print("\n")
        for k in self.mapping.keys():
            self.write(f"FOR REDUCER {k} \n")
            print(f"FOR REDUCER {k}",end="\n")
            for i in self.mapping[k]:
                # self.write(i,end=" | ")
                # print(i,end=" | ")
                self.write(f"{i.cid} ,{round(i.point[0],2)} ,{round(i.point[1],2)} \n")
                print(f"{i.cid} ,{round(i.point[0],2)} ,{round(i.point[1],2)}" , end = "\n")
            self.write("\n")
            print("\n")
        
        base_dir = "Data/Mappers"
        
        for k in self.mapping.keys():
            reducer_dir = os.path.join(base_dir, f"M_{self.port}")
            os.makedirs(reducer_dir, exist_ok=True)

            file_path = os.path.join(reducer_dir, f"partition_{k}.txt")

            with open(file_path, "w") as im_f:
                im_f.write(f"FOR REDUCER {k}\n")
                for i in self.mapping[k]:
                    im_f.write(f"{i.cid}, {round(i.point[0], 2)}, {round(i.point[1], 2)}\n")
                im_f.write("\n")
        
        return mpb2.DataResponse(result="OK")
    
    
    def get_data(self, msg,context):
        alld=[]
        self.write(f"data req from {msg.cid}\n")
        print(f"data req from {msg.cid}")
        for i in self.mapping[int(msg.cid)]:
            try:
                alld.append(i)
            except Exception as e:
                self.write(f"----> {e}\n")
                print("----> ",e)
        # self.write(alld)
        # print(alld)
        return mpb2.alldata(d=alld)

        
def start_mapper_server(port):
    print("MAPPEPR")
    try:
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        mpb2_grpc.add_MapperServicer_to_server(Mapper(port), server)
        server.add_insecure_port(f"localhost:{port}")
        server.start()
        print(f"{port} Mapper And its server started ")
        server.wait_for_termination()
    except Exception as t:
        print("hiki")
if __name__ == "__main__":
    start_mapper_server(sys.argv[1])