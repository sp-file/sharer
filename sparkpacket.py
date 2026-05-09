import asyncio
import hashlib
import json
import os
import pathlib
import shutil
import time


import aiofiles
import websockets
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


# =========================================================
# CONFIG
# =========================================================


BASE_DIR = "/Users/Shared/secret"
SYNC_DIR = os.path.join(BASE_DIR, "sparkpacket")
PORT = 8765


# Add peers here
PEERS = [
    # "ws://192.168.1.50:8765",
    # "ws://192.168.1.51:8765",
]


# Prevent sync loops
RECENT_CHANGES = {}
CHANGE_TIMEOUT = 3


# =========================================================
# UTILITIES
# =========================================================




def ensure_directories():
    os.makedirs(SYNC_DIR, exist_ok=True)




def relative_path(path):
    return os.path.relpath(path, SYNC_DIR)




def absolute_path(rel_path):
    return os.path.join(SYNC_DIR, rel_path)




def file_hash(path):
    h = hashlib.sha256()


    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)


    return h.hexdigest()




def mark_recent(path):
    RECENT_CHANGES[path] = time.time()




def is_recent(path):
    if path not in RECENT_CHANGES:
        return False


    return time.time() - RECENT_CHANGES[path] < CHANGE_TIMEOUT




# =========================================================
# FILE WATCHER
# =========================================================


class SyncHandler(FileSystemEventHandler):
    def __init__(self, loop):
        self.loop = loop


    def on_created(self, event):
        if event.is_directory:
            return


        if is_recent(event.src_path):
            return


        asyncio.run_coroutine_threadsafe(
            broadcast_file(event.src_path),
            self.loop,
        )


    def on_modified(self, event):
        if event.is_directory:
            return


        if is_recent(event.src_path):
            return


        asyncio.run_coroutine_threadsafe(
            broadcast_file(event.src_path),
            self.loop,
        )


    def on_deleted(self, event):
        if event.is_directory:
            return


        rel = relative_path(event.src_path)


        asyncio.run_coroutine_threadsafe(
            broadcast_delete(rel),
            self.loop,
        )




# =========================================================
# NETWORKING
# =========================================================


connected_clients = set()




async def send_json(ws, data):
    await ws.send(json.dumps(data))




async def recv_json(ws):
    data = await ws.recv()
    return json.loads(data)




async def broadcast_to_peers(message):
    for peer in PEERS:
        try:
            async with websockets.connect(peer) as ws:
                await send_json(ws, message)
        except Exception as e:
            print(f"Peer error {peer}: {e}")




async def broadcast_file(path):
    try:
        rel = relative_path(path)


        async with aiofiles.open(path, "rb") as f:
            content = await f.read()


        message = {
            "type": "file",
            "path": rel,
            "content": content.hex(),
            "hash": file_hash(path),
        }


        print(f"Broadcasting file update: {rel}")


        await broadcast_to_peers(message)


    except Exception as e:
        print(f"Broadcast file error: {e}")




async def broadcast_delete(rel_path):
    message = {
        "type": "delete",
        "path": rel_path,
    }


    print(f"Broadcasting delete: {rel_path}")


    await broadcast_to_peers(message)




# =========================================================
# SERVER
# =========================================================


async def handle_connection(ws):
    connected_clients.add(ws)


    try:
        async for raw in ws:
            data = json.loads(raw)
            await handle_message(data)


    except Exception as e:
        print(f"Connection error: {e}")


    finally:
        connected_clients.remove(ws)




async def handle_message(data):
    msg_type = data.get("type")


    if msg_type == "file":
        rel = data["path"]
        content = bytes.fromhex(data["content"])


        target = absolute_path(rel)


        os.makedirs(os.path.dirname(target), exist_ok=True)


        mark_recent(target)


        async with aiofiles.open(target, "wb") as f:
            await f.write(content)


        print(f"Updated from peer: {rel}")


    elif msg_type == "delete":
        rel = data["path"]
        target = absolute_path(rel)


        if os.path.exists(target):
            mark_recent(target)
            os.remove(target)


        print(f"Deleted from peer: {rel}")




# =========================================================
# FOLDER SELF-HEALING
# =========================================================


async def ensure_sync_folder_forever():
    while True:
        if not os.path.exists(SYNC_DIR):
            print("sparkpacket folder missing — recreating")
            os.makedirs(SYNC_DIR, exist_ok=True)


        await asyncio.sleep(2)




# =========================================================
# MAIN
# =========================================================


async def main():
    ensure_directories()


    loop = asyncio.get_running_loop()


    observer = Observer()
    handler = SyncHandler(loop)


    observer.schedule(handler, SYNC_DIR, recursive=True)
    observer.start()


    server = await websockets.serve(handle_connection, "0.0.0.0", PORT)


    print("SparkPacket running")
    print(f"Watching: {SYNC_DIR}")
    print(f"Listening on port: {PORT}")


    asyncio.create_task(ensure_sync_folder_forever())


    try:
        while True:
            await asyncio.sleep(1)


    except KeyboardInterrupt:
        observer.stop()
        observer.join()
        server.close()
        await server.wait_closed()




if __name__ == "__main__":
    asyncio.run(main())
