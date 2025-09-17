import asyncio, socket
from .config import SEND_ADDR, SEND_PORT, RECV_ADDR, RECV_PORT

def make_tx_socket():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # local broadcast not needed on 127.0.0.1, but leave option:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.setblocking(False)
    return s

async def udp_sender(queue: asyncio.Queue):
    sock = make_tx_socket()
    loop = asyncio.get_running_loop()
    while True:
        msg = await queue.get()
        data = str(msg).encode("ascii")
        await loop.run_in_executor(None, sock.sendto, data, (SEND_ADDR, SEND_PORT))

async def udp_receiver(on_line):
    loop = asyncio.get_running_loop()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((RECV_ADDR, RECV_PORT))   # allow any
    sock.setblocking(False)
    while True:
        data, _addr = await loop.run_in_executor(None, sock.recvfrom, 4096)
        line = data.decode("ascii").strip()
        await on_line(line)             # e.g., "12:7" or "53" or "43"
