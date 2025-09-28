import asyncio
from PhotonGame import net

# --- simple callback to handle incoming messages ---
counter = 0

async def handle_message(msg: str):
    global counter
    print(f"[GAME] Received event: {msg}")

    # Example: parse shooter:victim or shooter:base
    try:
        shooter, target = msg.split(":")
    except ValueError:
        shooter, target = msg, None

    # Send back a simple ACK for each message
    await send_queue.put("This")

    # After 15 events, tell tester we're done
    counter += 1
    if counter >= 15:
        await send_queue.put("221")
        print("[GAME] Sent 221, shutting down soon…")
        # Cancel loop after a short delay
        await asyncio.sleep(1)
        for task in asyncio.all_tasks():
            task.cancel()

# --- driver entry point ---
async def main():
    global send_queue
    send_queue = asyncio.Queue()

    # kick off sender & receiver
    sender_task = asyncio.create_task(net.udp_sender(send_queue))
    receiver_task = asyncio.create_task(net.udp_receiver(handle_message))

    # Initial handshake: tell tester we're ready
    await send_queue.put("202")
    print("[GAME] Sent 202, waiting for tester events…")

    await asyncio.gather(sender_task, receiver_task)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except asyncio.CancelledError:
        print("[GAME] Finished.")
