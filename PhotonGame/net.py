import asyncio, socket, os

SEND_ADDR = os.getenv("PHOTON_SEND_ADDR", "127.0.0.1")
SEND_PORT = int(os.getenv("PHOTON_SEND_PORT", "7500"))
RECV_ADDR = os.getenv("PHOTON_BIND_ADDR", "0.0.0.0")
RECV_PORT = int(os.getenv("PHOTON_RECV_PORT", "7501"))

def make_tx():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.setblocking(False)
    return s

async def udp_sender(q: asyncio.Queue):
    sock = make_tx()
    loop = asyncio.get_running_loop()
    while True:
        msg = await q.get()
        data = str(int(msg)).encode("ascii")
        await loop.run_in_executor(None, sock.sendto, data, (SEND_ADDR, SEND_PORT))

async def udp_receiver(on_line):
    loop = asyncio.get_running_loop()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((RECV_ADDR, RECV_PORT))
    sock.setblocking(False)
    while True:
        data, _ = await loop.run_in_executor(None, sock.recvfrom, 4096)
        await on_line(data.decode("ascii").strip())
