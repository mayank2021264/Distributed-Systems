import sys,os,subprocess
import grpc
import mprd_pb2 as mpb2
import mprd_pb2_grpc as mpb2_grpc
import random 
from concurrent import futures
from time import time,sleep
import threading
import shutil
import socket

# def is_port_open(host, port):
#     try:
#         # Create a socket object
#         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#         # Set a timeout in seconds
#         sock.settimeout(2)
#         # Attempt to connect to the host and port
#         sock.connect((host, port))
#         # Close the socket
#         sock.close()
#         return True
#     except (socket.timeout, ConnectionRefusedError):
#         # Connection timed out or refused
#         return False

# 0  :  1.4302438497543335 2.4735968112945557
# 1  :  -6.464229583740234 -3.25716233253479  takinf first 2 input data points as starting centroids

def del_dirs(dir):
    if os.path.exists(dir):
        # Delete the directory and its contents
        shutil.rmtree(dir)
        print(f"Directory '{dir}' and its contents deleted successfully.")
    else:
        print(f"Directory '{dir}' does not exist.")


class Master:
    # def __init__(self, num_mappers, num_reducers, num_centroids, num_iterations, input_location, port=50051) -> None:
    #     self.M = num_mappers
    #     self.R = num_reducers
    #     self.C = num_centroids
    #     self.I = num_iterations
    #     self.input = input_location
    def __init__(self):
        
        self.M = int(input("Enter Number of Mappers : "))
        self.R = int(input("Enter Number of Reducers : "))
        self.C = int(input("Enter Number of Centroids : "))
        self.I = int(input("Enter Number of Iterations : "))
        self.input = input("Enter Number of Input filename (W/o .txt) : ")
        
        if not os.path.isfile(f"Data/Inputs/{self.input}.txt"):
            print("INVALID FILE ! TRY AGAIN")
            return 
    # Deleting directories for previos run
        del_dirs("Data/dumps")
        del_dirs("Data/Mappers")
        del_dirs("Data/Reducers")
        # self.mf=
        self.centroids=[]
        os.makedirs("Data/dumps", exist_ok=True)
        self.f="Data/dumps/master_dump.txt"
        with open(self.f,"w") as f:
            f.write("MASTER INITILIAZED\n")
        print("MASTER INITILIAZED")
        self.mapper_ports=[]
        self.reducer_ports=[]
        prt=50052

        try:# Spawning M mappers
            for i in range(self.M):
                self.mapper_ports.append(prt)

                with open(f"Data/dumps/Mapper_{prt}_dump.txt","w") as mf:
                    mf.write("")
                self.write(f"{time()} : STARTED MAPPER {prt} \n")
                print(f"STARTED MAPPER {prt} ")
                subprocess.Popen(['cmd.exe', '/c', 'start', 'cmd.exe', '/k', 'python', "C:/Users/Vianshu/Desktop/117_A3/Mapper.py",f"{prt}"])
                prt+=1 

            # Spawning R reducers
            for i in range(self.R):
                self.reducer_ports.append(prt)
                with open(f"Data/dumps/Reducer_{prt}_dump.txt","w") as rf:
                    rf.write("")
                self.write(f"{time()} : STARTED REDUCER {prt} \n")
                print(f"STARTED REDUCER {prt} ")
                subprocess.Popen(['cmd.exe', '/c', 'start', 'cmd.exe', '/k', 'python', "C:/Users/Vianshu/Desktop/117_A3/Reducer.py",f"{prt}"])
                prt+=1
        except Exception as e:
            self.write(f"Try again : {e}\n")
            print("Try Again "+ e)
        # return
        # Getting Random C centroids
        with open(f"Data/inputs/{self.input}.txt", 'r') as file:
            data=file.readlines()
            self.num_points=len(data)
            self.centroids=random.sample(data,self.C)
            self.centroids= [mpb2.points(points=[float(k) for k in i.strip().split(',')]) for i in self.centroids]
        
        self.write(f"{time()} : RANDOM CENTROIDS : \n")
        for ind,i in enumerate(self.centroids):
            self.write(f"{time()} : cid: {ind} , x : {i.points[0]} , y : {i.points[1]}\n")
        #waiting to start all mappers and reducers , might need to change according to number of mappers and reducer
        sleep(2)

        self.iters()
        self.write(f"{time()} : FINAL CENTROIDS : \n")
        with open("Data/FINAL_CENTROIDS.txt","w") as cf:
            for cid,i in enumerate(self.centroids):
                # print(i)
                self.write(f"{cid} : {i.points[0]},{i.points[1]}\n")
                cf.write(f"{cid}: {i.points[0]},{i.points[1]}\n")
    

    def write(self,txt):        
        with open(self.f,"a") as f:
            f.write(txt)

    def start_mapper_thread(self,si, ppm, mapper_port,iternum,mapper):
        while True:
            try:
                self.write(f"{time()} : {self.mapper_ports[mapper]} : {si} -> {si+ppm}\n")
                response = self.start_mapper(si, si + ppm, mapper_port,iternum)
                if response == "OK":
                    # mapper_acks += 1
                    self.write(f"{time()} : {self.mapper_ports[mapper]} : Mapper returned successful \n")
                    print(f"{self.mapper_ports[mapper]} : Mapper returned successful \n")
                    return
                else:
                    self.write(f"{time()} : {self.mapper_ports[mapper]}: Mapper returned unsuccessful Starting Again \n")
                    print(f"{self.mapper_ports[mapper]}: Mapper returned unsuccessful Starting Again \n")
            except Exception as e:
                self.write(f"{time()} : {self.mapper_ports[mapper]}:  Mapper Failed Spawning it again {e}\n")
                print(f"{self.mapper_ports[mapper]}:  Mapper Failed Spawning it again {e} \n")
                try:
                    # if(is_port_open("localhost",{self.mapper_ports[mapper]}==False)):
                    subprocess.Popen(['cmd.exe', '/c', 'start', 'cmd.exe', '/k', 'python', "C:/Users/Vianshu/Desktop/117_A3/Mapper.py",f"{self.mapper_ports[mapper]}"])
                except Exception as e:
                    self.write(f"{time()} :  Unable to start the mapper {e}\n")
                    print(" Unable to start the mapper")
    
    def start_reducer_thread(self,mapper_ports, reducer, reducer_port,iternum):
        while True:
            self.write(f"{time()} : {self.reducer_ports[reducer]} : Sending GRPC to Reducer {reducer}\n")
            try:
                response = self.start_reducers(mapper_ports, reducer, reducer_port,iternum)
                if response.result == "OK":
                    self.write(f"{time()} : {self.reducer_ports[reducer]} : Reducer returned successful \n")
                    print(f"{reducer_port} : Reducer returned successful \n")
                    self.merge(response.d)
                    return
                else:
                    self.write(f"{time()} : {self.reducer_ports[reducer]} : Reducer returned unsuccessful Sending req Again \n")
                    print(f"{reducer_port} : Reducer returned unsuccessful Sending req Again \n")
            except Exception as e:
                self.write(f"{time()} : {self.reducer_ports[reducer]} :  Reducer grpc Failed Starting Again \n")
                print(f"{reducer_port} : Reducer grpc Failed Starting Again \n")
                try:
                    subprocess.Popen(['cmd.exe', '/c', 'start', 'cmd.exe', '/k', 'python', "C:/Users/Vianshu/Desktop/117_A3/Reducer.py",f"{self.reducer_ports[reducer]}"])
                except Exception as e:
                    self.write(f"{time()} :  Unable to start the reducer\n")
                    print(" Unable to start the reducer")

    def iters(self):
        # self.start_time=time()
        for i in range(self.I):
            self.write(f"{time()} : <----------------ITERATION NUMBER : {i} -------------------->\n")
            print(f"ITERATION NUMBER --> {i}")
            if(self.assign_mappers(str(i))):
                # print("done")
                if(self.centroids==self.newcents):
                    self.write("Ending Iterations before : Centroids Converged \n")
                    return
                self.centroids=self.newcents
                
                for cid,i in enumerate(self.centroids):
                # print(i)
                    self.write(f"{cid} : {i.points[0]},{i.points[1]}\n")
            else:
                self.write("Failure")
                print("Failure")
            # break
        self.write(" ITERATIONS ENDED \n")
    
    def assign_mappers(self,iternum):
        # if(self.num_points%self.M==0):
        ppm=int(self.num_points/self.M)+1  
        si = 0
        self.write(f"{time()} : SENDING DATA TO MAPPERS\n")
        print("\n SENDING DATA TO MAPPERS \n ")
        # mapper_acks=0
        # Start mapper threads
        mapper_threads = []
        for mapper in range(self.M):
            print(f"{self.mapper_ports[mapper]} : {si} -> {si+ppm}")
            mapper_thread = threading.Thread(target=self.start_mapper_thread, args=(si, ppm, self.mapper_ports[mapper],iternum,mapper))
            mapper_threads.append(mapper_thread)
            mapper_thread.start()
            si += ppm

        # Wait for mapper threads to complete
        for thread in mapper_threads:
            thread.join()
        # All mapppers completed


        self.write(f"{time()} : MAPPERS TASK COMPLETED STARTING REDUCERS\n")
        print("\n MAPPERS TASK COMPLETED STARTING REDUCERS")
    # REDUCER PART -------------------------------------------
        
        self.newcents=[0]*self.C
        reducer_threads = []
        print("\n\n MAPPERS TASK COMPLETED STARTING REDUCERS")
        for reducer in range(self.R):
            reducer_thread = threading.Thread(target=self.start_reducer_thread, args=(self.mapper_ports, reducer, self.reducer_ports[reducer],iternum))
            reducer_thread.start()
            reducer_threads.append(reducer_thread)

        # Wait for reducer threads to complete
        for thread in reducer_threads:
            thread.join()
        # All reducers completed
        return True 
        

    def start_reducers(self,mappers_prt,id,p,iternum):
        with grpc.insecure_channel(f"localhost:{p}") as channel:
            stub=mpb2_grpc.ReducerStub(channel)
            response=stub.Reducer(mpb2.red_req(id=id,mapper_ports=mappers_prt,C=self.C,iterno=iternum))
            # self.write(f"{time()} : \nHIIII\n")
            # print("\nHIIII\n")
            return response

    def merge(self,data):
        for i in data:
            self.newcents[int(i.cid)]=mpb2.points(points=[i.x,i.y])

    def start_mapper(self,si,ei,p,iternum):
        with grpc.insecure_channel(f"localhost:{p}") as channel:
            stub=mpb2_grpc.MapperStub(channel)
            response=stub.Mapper(mpb2.DataRequest(data=self.input,si=int(si),ei=int(ei),nl=int(self.num_points),nr=int(self.R),centroid=self.centroids,iterno=iternum))
            return response.result

if __name__ == "__main__":
    # master=Master(num_mappers=7, num_reducers=2, num_centroids=2, num_iterations=10, input_location="input")
    # master=Master(num_mappers=2, num_reducers=2, num_centroids=3, num_iterations=10, input_location="points2")
    # master=Master(num_mappers=4, num_reducers=3, num_centroids=2, num_iterations=10, input_location="points3")
    while True:
        master=Master()