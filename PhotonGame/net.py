import asyncio, socket, os
SEND_ADDR=os.getenv("PHOTON_SEND_ADDR","127.0.0.1")
SEND_PORT=int(os.getenv("PHOTON_SEND_PORT","7500"))
RECV_ADDR=os.getenv("PHOTON_BIND_ADDR","0.0.0.0")
RECV_PORT=int(os.getenv("PHOTON_RECV_PORT","7501"))

def _tx_sock():
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.setblocking(False)
    return s

async def udp_sender(q:asyncio.Queue):
    s=_tx_sock(); loop=asyncio.get_running_loop()
    while True:
        val=int(await q.get())
        await loop.run_in_executor(None, s.sendto, str(val).encode("ascii"), (SEND_ADDR,SEND_PORT))

async def udp_receiver(on_line):
    loop=asyncio.get_running_loop()
    r=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); r.bind((RECV_ADDR,RECV_PORT)); r.setblocking(False)
    while True:
        data,_=await loop.run_in_executor(None, r.recvfrom, 4096)
        await on_line(data.decode("ascii").strip())
