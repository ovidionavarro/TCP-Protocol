import socket
from package import Package
from utils import parse_address, get_host_ip
import time
import random
import math as m

PKG_SIZE = 30
WINDOW_SIZE = 5
SYN = 1<<7
ACK = 1<<4
FIN = 1<<8
RST = 1<<6

class Conn:
    def __init__(self, src: str, dest=None, sock=None):
        if sock is None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_RAW,
                                 socket.IPPROTO_RAW)
            #sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
        self.socket = sock
        self.src = src
        self.dest = dest
        self.ack=0
        self.numseq=0
        self.buff = b''
    def __repr__(self) -> str:
        return f'source:{self.src}\n dest:{self.dest}'

class ConnException(Exception):
    pass

def listen(address: str) -> Conn:
    conn: Conn = Conn(src=address)
    host, port = parse_address(address)
    tuple_addr = (host, port)
    conn.socket.bind(tuple_addr)
    print(f'Listening on {address}')
    return conn


def accept(conn) -> Conn:
    conn = hand_shake(conn)
    return conn


def dial(address) -> Conn:
    #se crea pakt syn y se envia a la direeccion de destino
    hostD,portD=parse_address(address)
    
    ip="127.0.0.1"#get_host_ip()

    print("ip: ",ip)
    conn = Conn(f'{ip}:{portD}') 
    conn.numseq = random.randint(1,100)
    pkg = Package(ip, hostD, portD, portD, conn.numseq,0,130,255,b'').build_pck()
    # conn.socket.sendto(pkg,parse_address(address))
    send(conn,b'', address)
    time.sleep(1)
    conn = listen(f'{ip}:{portD}')
    print("esperando data")
    data, _ = conn.socket.recvfrom(255)
    data = data[20:]
    print(Package.unzip(data))

    print("Conexion establecida")

    return conn


def send(conn: Conn, data: bytes, address) -> int:
    #conn.socket.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    data_len = len(data)
    max_data=PKG_SIZE-28
    if(data_len<=max_data):
       hostD,portD=parse_address(conn.src)
       hostS, portS = parse_address(address)
       pkg = Package(hostD,hostS,portD,portS,conn.numseq,conn.ack, ACK, WINDOW_SIZE, data ).build_pck()
       print (pkg)
       return conn.socket.sendto(pkg,parse_address(address))

    
    
    data_list = []
    index = 0
    cant=1
    num_pkg = m.ceil(data_len / (max_data))
    while cant<=num_pkg:
        data_list.append(data[index:max_data+index])
        cant+=1
        index+=max_data

    for i in data_list:
        send(conn, i, address)


    
    return len(data)


def recv(conn: Conn, length: int) -> bytes:
    pass


def close(conn: Conn):
    pass



#### Flagsss -->>> 0:NS 1:CWR 2:ECE 3:URG 4:ACK 5:PSH 6:RST 7:SYN 8:FIN
####pakt
def hand_shake(conn:Conn):
    print("waiting data")
    data, _ = conn.socket.recvfrom(65565)
    data=data[20:]
    pkg=Package.unzip(data)
    print(pkg[8])

    if(pkg[8]==Package.check_sum(data[:24]+data[28:])):
        
        print("PKG recivido")
        if (pkg[6] & SYN):
            print("PKG SYN recivido")
            print(pkg)
            conn.dest=f'{pkg[1]:}:{pkg[3]}'
            hostS,portS=parse_address(conn.src)
            hostD,portD=parse_address(conn.dest)
            packSINACK=Package(hostS,hostD,portS,portD,pkg[5]+1,pkg[4]+1,144,255,b'').build_pck()
            time.sleep(1.5)
            print("enviando ack/syn")
            conn.socket.sendto(packSINACK,parse_address(conn.dest))
        else:
            return
             #else aceptar la conexion primro 

    return conn
