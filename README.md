# SparkPacket – Peer-to-Peer Folder Sync for macOS

A lightweight, local-network sync tool for macOS that watches a shared folder and automatically syncs changes across multiple computers.

## Features

- **Automatic folder watching** – Detects file creation, edits, and deletions in real-time
- **Peer-to-peer sync** – Shares updates directly between computers on the same network
- **Self-healing** – Automatically recreates the sync folder if it's deleted
- **Local network only** – Runs on your MacBooks without exposing to the public internet
- **Educational prototype** – Perfect for learning about file watchers and WebSocket networking

## Quick Start

### 1. Install Dependencies

```bash
pip3 install watchdog websockets aiofiles
```

### 2. Run the Program

```bash
python3 sparkpacket.py
```

### 3. Connect Multiple Computers

Edit the `PEERS` list in `sparkpacket.py` with the IP addresses of other computers:

```python
PEERS = [
    "ws://192.168.1.50:8765",
    "ws://192.168.1.51:8765",
]
```

## Files

- **sparkpacket.py** – Main sync program
- **com.sparkpacket.sync.plist** – macOS launchd auto-start configuration
- **spfile.txt** – Full documentation with detailed code comments

## Auto-Start on macOS

To run SparkPacket automatically on login:

```bash
cp com.sparkpacket.sync.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.sparkpacket.sync.plist
```

## Security Note

Only connect computers that explicitly agree to participate. This is a local-network prototype—do not expose the server port to the public internet without adding authentication and encryption.

## Future Enhancements

For production use, consider adding:
- Encryption & TLS
- Authentication
- Conflict resolution
- Version history
- Peer discovery
- File locking
- Database-backed metadata
