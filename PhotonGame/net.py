import asyncio, socket, os
from dataclasses import dataclass

@dataclass
class Endpoints:
    send_addr: str
    send_port: int
    recv_addr: str
    recv_port: int

def endpoints_from_env() -> Endpoints:
    return Endpoints(
        send_addr=os.getenv("PHOTON_SEND_ADDR", "127.0.0.1"),
        send_port=int(os.getenv("PHOTON_SEND_PORT", "7500")),
        recv_addr=os.getenv("PHOTON_BIND_ADDR", "0.0.0.0"),
        recv_port=int(os.getenv("PHOTON_RECV_PORT", "7501")),
    )

async def udp_sender(q: asyncio.Queue, ep: Endpoints, stop: asyncio.Event):
    loop = asyncio.get_running_loop()
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setblocking(False)
    s.connect((ep.send_addr, ep.send_port))
    try:
        while not stop.is_set():
            val = await q.get()
            msg = str(val)
            await loop.sock_sendall(s, msg.encode("ascii"))
    finally:
        s.close()

async def udp_receiver(on_line, ep: Endpoints, stop: asyncio.Event):
    loop = asyncio.get_running_loop()
    r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    r.bind((ep.recv_addr, ep.recv_port))
    r.setblocking(False)
    try:
        while not stop.is_set():
            data = await loop.sock_recv(r, 4096)
            await on_line(data.decode("ascii").strip())
    finally:
        r.close()
