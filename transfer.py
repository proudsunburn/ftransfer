#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import secrets
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import tempfile
import blosc

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# Constants
TRANSFER_PORT = 15820

# Configure Blosc for optimal performance with LZ4
blosc.set_nthreads(4)  # Use 4 threads for compression
blosc.set_releasegil(True)  # Release GIL during compression
# Use LZ4 compressor (fastest option) with level 1 for maximum speed
BLOSC_COMPRESSOR = 'lz4'
BLOSC_LEVEL = 1

# Virtual environment and cache directory patterns to exclude
VENV_PATTERNS = [
    'venv', '.venv', 'env', '.env', 'virtualenv',
    '__pycache__', '.pytest_cache', '.tox',
    'node_modules', '.npm', '.yarn',
    '.git', '.svn', '.hg',
    'conda-env', '.conda',
    '.mypy_cache', '.coverage'
]

def detect_tailscale_userspace_mode():
    """Detect if Tailscale is running in userspace proxy mode (containers)
    
    Returns:
        bool: True if Tailscale is running in userspace mode (no TUN interface),
              False if running in kernel TUN mode (normal)
    """
    try:
        # Try using netifaces if available
        import netifaces
        interfaces = netifaces.interfaces()
        
        # Check for Tailscale TUN interfaces
        tailscale_interfaces = [
            iface for iface in interfaces 
            if 'tailscale' in iface.lower() or 
               iface.startswith('tun') or
               iface.startswith('utun')  # macOS TUN interfaces
        ]
        
        # No TUN interface = userspace proxy mode
        return len(tailscale_interfaces) == 0
        
    except ImportError:
        # Fallback without netifaces dependency
        try:
            # Check /proc/net/dev for Linux systems
            with open('/proc/net/dev', 'r') as f:
                interfaces_data = f.read()
                # Look for tailscale interface
                return 'tailscale' not in interfaces_data and 'tun' not in interfaces_data
        except (FileNotFoundError, PermissionError):
            # macOS or other systems - try alternative detection
            try:
                # Use ifconfig as fallback
                result = subprocess.run(['ifconfig'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return 'tailscale' not in result.stdout and 'tun' not in result.stdout
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Ultimate fallback - assume kernel mode
            return False

# Utility functions
def recv_all(socket, n):
    """Receive exactly n bytes from socket"""
    data = b''
    while len(data) < n:
        packet = socket.recv(n - len(data))
        if not packet:
            raise ConnectionError("Socket connection broken")
        data += packet
    return data

def validate_files(file_paths: List[str]) -> List[Path]:
    """Validate that all file paths exist and are accessible"""
    validated_files = []
    
    for file_path_str in file_paths:
        file_path = Path(file_path_str)
        if not file_path.exists():
            print(f"Error: File or directory does not exist: {file_path}")
            sys.exit(1)
        validated_files.append(file_path)
    
    return validated_files

def collect_files_recursive(file_paths: List[Path], exclude_venv: bool = False) -> List[Tuple[Path, str]]:
    """Collect all files recursively from directories
    
    Args:
        file_paths: List of file/directory paths to process
        exclude_venv: If True, exclude virtual environment and cache directories
    
    Returns:
        List of (absolute_path, relative_path) tuples
    """
    collected_files = []
    excluded_dirs = []
    
    def should_exclude_dir(dir_name: str) -> bool:
        """Check if directory should be excluded based on venv patterns"""
        if not exclude_venv:
            return False
        return dir_name.lower() in [pattern.lower() for pattern in VENV_PATTERNS]
    
    def collect_from_directory(base_path: Path, current_path: Path):
        """Recursively collect files from directory, excluding venv folders"""
        try:
            for item in current_path.iterdir():
                if item.is_file():
                    # Calculate relative path from the base directory being sent
                    relative_path = item.relative_to(base_path.parent)
                    collected_files.append((item, str(relative_path)))
                elif item.is_dir():
                    # Check if this directory should be excluded
                    if should_exclude_dir(item.name):
                        excluded_dirs.append(str(item.relative_to(base_path.parent)))
                    else:
                        # Recursively process subdirectory
                        collect_from_directory(base_path, item)
        except PermissionError:
            print(f"Warning: Permission denied accessing {current_path}")
    
    for path in file_paths:
        if path.is_file():
            collected_files.append((path, path.name))
        elif path.is_dir():
            collect_from_directory(path, path)
        else:
            print(f"Warning: Skipping {path} (not a regular file or directory)")
    
    # Show excluded directories if any
    if excluded_dirs and exclude_venv:
        print(f"Excluded {len(excluded_dirs)} virtual environment/cache directories:")
        for excluded_dir in sorted(set(excluded_dirs))[:10]:  # Show first 10
            print(f"  - {excluded_dir}")
        if len(excluded_dirs) > 10:
            print(f"  ... and {len(excluded_dirs) - 10} more")
    
    return collected_files

def calculate_speed(bytes_transferred: int, elapsed_time: float) -> float:
    """Calculate transfer speed in bytes per second"""
    if elapsed_time <= 0:
        return 0.0
    return bytes_transferred / elapsed_time

def format_speed(speed: float) -> str:
    """Format speed for display"""
    if speed < 1024:
        return f"{speed:.1f} B/s"
    elif speed < 1024 * 1024:
        return f"{speed / 1024:.1f} KB/s"
    elif speed < 1024 * 1024 * 1024:
        return f"{speed / (1024 * 1024):.1f} MB/s"
    else:
        return f"{speed / (1024 * 1024 * 1024):.1f} GB/s"

def calculate_eta(remaining_bytes: int, current_speed: float) -> int:
    """Calculate estimated time to completion in seconds"""
    if current_speed <= 0 or remaining_bytes <= 0:
        return 0
    return int(remaining_bytes / current_speed)

def format_eta(seconds: int) -> str:
    """Format ETA for display as MM:SS or HH:MM:SS"""
    if seconds <= 0:
        return "00:00"
    elif seconds < 3600:  # Less than 1 hour
        minutes, secs = divmod(seconds, 60)
        return f"{minutes:02d}:{secs:02d}"
    else:  # 1 hour or more
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def format_size(size: int) -> str:
    """Format file size for display"""
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    else:
        return f"{size / (1024 * 1024 * 1024):.1f} GB"

def get_current_file_info(stream_position: int, files_metadata: List[Dict]) -> Optional[Dict]:
    """Get information about the file currently being processed at stream position"""
    for file_info in files_metadata:
        file_start = file_info['offset']
        file_end = file_info['offset'] + file_info['size']
        if file_start <= stream_position < file_end:
            return file_info
    return None

def print_transfer_progress(filename: str, file_size: int, progress_percent: float, 
                           speed_str: str, eta_str: str, is_first_update: bool, 
                           action: str = "Transferring"):
    """Print two-line progress display with file info and progress"""
    size_str = format_size(file_size)
    
    if not is_first_update:
        # Move cursor up two lines to overwrite previous display
        print("\033[A\033[A", end='')
    
    # Print file information line
    print(f"\r{action}: {filename} ({size_str})\033[K")
    
    # Print progress information line  
    print(f"\rProgress: {progress_percent:.1f}% | Speed: {speed_str} | ETA: {eta_str}\033[K", end='', flush=True)

class TailscaleDetector:
    """Tailscale network detection and peer validation"""
    
    _peer_cache = {}
    _cache_timeout = 30  # seconds
    _last_cache_update = 0
    
    @classmethod
    def get_tailscale_ip(cls) -> Optional[str]:
        """Get the Tailscale IP address for this machine"""
        try:
            result = subprocess.run(['tailscale', 'ip', '--4'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None
    
    @classmethod
    def verify_peer_ip_cached(cls, ip: str) -> Tuple[bool, Optional[str]]:
        """Verify if IP is a Tailscale peer with caching"""
        current_time = time.time()
        
        # Check cache first
        if (current_time - cls._last_cache_update < cls._cache_timeout and
            ip in cls._peer_cache):
            return cls._peer_cache[ip]
        
        # Update cache if expired
        if current_time - cls._last_cache_update >= cls._cache_timeout:
            cls._update_peer_cache()
        
        return cls._peer_cache.get(ip, (False, None))
    
    @classmethod
    def _update_peer_cache(cls):
        """Update the peer cache"""
        try:
            result = subprocess.run(['tailscale', 'status'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                cls._peer_cache.clear()
                for line in result.stdout.split('\n'):
                    if line.strip() and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 2:
                            ip = parts[0]
                            name = parts[1] if len(parts) > 1 else "unknown"
                            cls._peer_cache[ip] = (True, name)
                cls._last_cache_update = time.time()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

class SecureTokenGenerator:
    """Secure token generation with word-based tokens"""
    
    # Word list for generating memorable tokens  
    WORDS = [
        "ocean", "forest", "mountain", "river", "desert", "valley", "island", "canyon",
        "tiger", "eagle", "dolphin", "wolf", "bear", "fox", "owl", "shark",
        "piano", "guitar", "violin", "drums", "flute", "trumpet", "harp", "saxophone",
        "ruby", "emerald", "diamond", "sapphire", "pearl", "crystal", "amber", "jade",
        "storm", "thunder", "lightning", "rainbow", "sunset", "sunrise", "aurora", "comet",
        "castle", "bridge", "tower", "garden", "temple", "palace", "fortress", "lighthouse",
        "voyage", "quest", "journey", "adventure", "discovery", "expedition", "exploration", "mission",
        "wisdom", "courage", "honor", "justice", "freedom", "peace", "harmony", "unity",
        "crimson", "azure", "golden", "silver", "violet", "emerald", "scarlet", "indigo",
        "mystic", "ancient", "eternal", "infinite", "divine", "sacred", "blessed", "noble",
        "warrior", "guardian", "sentinel", "champion", "defender", "protector", "knight", "hero",
        "phoenix", "dragon", "griffin", "unicorn", "pegasus", "sphinx", "chimera", "hydra",
        "whisper", "echo", "melody", "rhythm", "harmony", "symphony", "chorus", "ballad",
        "summit", "peak", "cliff", "ridge", "slope", "plateau", "gorge", "ravine",
        "stream", "brook", "creek", "waterfall", "rapid", "cascade", "spring", "pond",
        "meadow", "prairie", "field", "grove", "thicket", "woodland", "clearing", "glade",
        "dawn", "dusk", "twilight", "midnight", "moonlight", "starlight", "daybreak", "nightfall",
        "breeze", "gale", "hurricane", "tornado", "cyclone", "tempest", "blizzard", "typhoon",
        "ember", "flame", "spark", "blaze", "inferno", "pyre", "beacon", "torch",
        "frost", "ice", "snow", "hail", "glacier", "icicle", "crystal", "winter",
        "bloom", "blossom", "petal", "nectar", "pollen", "fragrance", "bouquet", "garland",
        "orbit", "galaxy", "nebula", "constellation", "planet", "asteroid", "meteor", "cosmos",
        "treasure", "fortune", "riches", "bounty", "prize", "reward", "jewel", "crown",
        "legend", "myth", "tale", "saga", "epic", "chronicle", "story", "fable",
        "magic", "spell", "charm", "enchantment", "sorcery", "wizardry", "alchemy", "potion"
    ]
    
    @classmethod
    def generate_token(cls) -> str:
        """Generate a secure two-word token"""
        # Use cryptographically secure random selection
        word1 = secrets.choice(cls.WORDS)
        word2 = secrets.choice(cls.WORDS)
        return f"{word1}-{word2}"

class FileWriter:
    """Manages incremental file writing with hash tracking for resume capability"""
    
    def __init__(self, filename: str, size: int, offset: int):
        self.filename = filename
        self.size = size
        self.offset = offset
        self.written = 0
        self.handle = None
        self.hasher = hashlib.sha256()
        self.part_file = Path(f"{filename}.part")
        self.is_complete = False
        
    def open_for_writing(self, resume: bool = False):
        """Open file for writing, optionally resuming from existing partial file"""
        # Create parent directories
        self.part_file.parent.mkdir(parents=True, exist_ok=True)
        
        if resume and self.part_file.exists():
            # Resume from existing partial file
            self.written = self.part_file.stat().st_size
            if self.written < self.size:
                # Verify existing data by rehashing
                self.hasher = hashlib.sha256()
                with open(self.part_file, 'rb') as f:
                    while True:
                        chunk = f.read(64 * 1024)
                        if not chunk:
                            break
                        self.hasher.update(chunk)
                
                # Open for append
                self.handle = open(self.part_file, 'ab')
                print(f"Resuming {self.filename}: {self.written}/{self.size} bytes already written")
            else:
                # File already complete
                self.is_complete = True
                return
        else:
            # Start fresh
            self.written = 0
            self.hasher = hashlib.sha256()
            self.handle = open(self.part_file, 'wb')
    
    def write_chunk(self, data: bytes) -> int:
        """Write data chunk and update hash. Returns bytes written."""
        if self.is_complete or not self.handle:
            return 0
            
        bytes_to_write = min(len(data), self.size - self.written)
        if bytes_to_write > 0:
            chunk_to_write = data[:bytes_to_write]
            self.handle.write(chunk_to_write)
            self.handle.flush()  # Ensure data is written
            self.hasher.update(chunk_to_write)
            self.written += bytes_to_write
            
            # Check if file is complete
            if self.written >= self.size:
                self.complete_file()
                
        return bytes_to_write
    
    def complete_file(self):
        """Mark file as complete and move from .part to final name"""
        if self.handle:
            self.handle.close()
            self.handle = None
        
        if self.written == self.size:
            # Move .part file to final location
            final_path = Path(self.filename)
            
            # Handle filename conflicts
            counter = 1
            original_path = final_path
            while final_path.exists():
                parent_dir = original_path.parent
                name_parts = original_path.stem, counter, original_path.suffix
                final_path = parent_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                counter += 1
            
            self.part_file.rename(final_path)
            self.is_complete = True
            print(f"Completed: {final_path}")
        
    def get_hash(self) -> str:
        """Get current hash of written data"""
        return self.hasher.hexdigest()
    
    def needs_data(self, stream_position: int) -> bool:
        """Check if this file needs data at the given stream position"""
        file_start = self.offset
        file_end = self.offset + self.size
        return file_start <= stream_position < file_end and not self.is_complete
    
    def close(self):
        """Close file handle"""
        if self.handle:
            self.handle.close()
            self.handle = None


class SecureCrypto:
    """Cryptographic operations for secure file transfer"""
    
    def __init__(self):
        """Initialize with fresh X25519 key pair"""
        self.private_key = x25519.X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        self.session_key = None
        self.cipher = None
    
    def get_public_key_bytes(self) -> bytes:
        """Get public key as bytes for transmission"""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    
    def derive_session_key(self, peer_public_key_bytes: bytes, shared_token: str):
        """Derive session key from ECDH + shared token"""
        # Reconstruct peer's public key
        peer_public_key = x25519.X25519PublicKey.from_public_bytes(peer_public_key_bytes)
        
        # Perform ECDH
        shared_key = self.private_key.exchange(peer_public_key)
        
        # Derive session key using HKDF with token as salt
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,  # ChaCha20 key size
            salt=shared_token.encode(),
            info=b'file-transfer-session'
        )
        self.session_key = hkdf.derive(shared_key)
        
        # Initialize cipher
        self.cipher = ChaCha20Poly1305(self.session_key)
    
    def encrypt(self, data: bytes, nonce: bytes) -> bytes:
        """Encrypt data with session key"""
        if not self.cipher:
            raise RuntimeError("Session key not established")
        return self.cipher.encrypt(nonce, data, None)
    
    def decrypt(self, ciphertext: bytes, nonce: bytes) -> bytes:
        """Decrypt data with session key"""
        if not self.cipher:
            raise RuntimeError("Session key not established")
        return self.cipher.decrypt(nonce, ciphertext, None)

def send_files(file_paths: List[str], pod: bool = False, novenv: bool = False):
    """Sender mode: listen for connections and send files"""
    
    # Validate files exist
    files = validate_files(file_paths)
    
    # Get Tailscale IP for connection string
    tailscale_ip = TailscaleDetector.get_tailscale_ip()
    if not tailscale_ip:
        print("Error: Could not detect Tailscale IP. Ensure Tailscale is running.")
        sys.exit(1)
    
    # Auto-detect Tailscale userspace mode or use explicit pod flag
    auto_pod_mode = detect_tailscale_userspace_mode()
    effective_pod_mode = pod or auto_pod_mode
    
    # Set bind IP (localhost for pod mode, all interfaces otherwise)
    if effective_pod_mode:
        bind_ip = "127.0.0.1"
        if auto_pod_mode and not pod:
            print("Tailscale userspace mode detected: enabling pod mode")
        else:
            print("Pod mode: Binding to localhost")
    else:
        bind_ip = "0.0.0.0"  # Bind to all interfaces for Tailscale peer connections
    
    # Generate token
    token = SecureTokenGenerator.generate_token()
    
    print(f"type into receiver: transfer.py receive {tailscale_ip}:{token}")
    
    # Prepare files for unified streaming transfer
    if any(f.is_dir() for f in files):
        # Use recursive collection for directories
        collected_files = collect_files_recursive(files, exclude_venv=novenv)
    else:
        # Regular files
        collected_files = [(f, f.name) for f in files]
    
    # Calculate total size and prepare metadata for all files
    total_size = sum(abs_path.stat().st_size for abs_path, _ in collected_files)
    filename = f"{len(collected_files)}_files" if len(collected_files) > 1 else collected_files[0][1]
    
    # Start server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((bind_ip, TRANSFER_PORT))
    server_socket.listen(1)
    server_socket.settimeout(300)  # 5 minute timeout
    
    print("Waiting for receiver to connect...")
    
    try:
        client_socket, client_addr = server_socket.accept()
        
        # Validate client is from Tailscale network (skip for localhost in pod mode)
        if effective_pod_mode and client_addr[0] == "127.0.0.1":
            print("Pod mode: Accepting localhost connection")
        else:
            is_valid, peer_name = TailscaleDetector.verify_peer_ip_cached(client_addr[0])
            if not is_valid:
                print(f"Error: Rejected connection from unauthorized IP: {client_addr[0]}")
                client_socket.close()
                return
        
        # Perform secure handshake
        crypto = SecureCrypto()
        public_key_bytes = crypto.get_public_key_bytes()
        
        # Send public key first
        client_socket.send(len(public_key_bytes).to_bytes(4, 'big'))
        client_socket.send(public_key_bytes)
        
        # Receive peer's public key
        peer_key_len = int.from_bytes(recv_all(client_socket, 4), 'big')
        peer_public_key_bytes = recv_all(client_socket, peer_key_len)
        
        # Derive session key
        crypto.derive_session_key(peer_public_key_bytes, token)
        
        # Send authentication challenge
        challenge = secrets.token_bytes(32)
        expected_response = hashlib.sha256(challenge + token.encode()).digest()
        
        nonce1 = secrets.token_bytes(12)
        encrypted_challenge = crypto.encrypt(challenge, nonce1)
        client_socket.send(len(nonce1).to_bytes(4, 'big'))
        client_socket.send(nonce1)
        client_socket.send(len(encrypted_challenge).to_bytes(4, 'big'))
        client_socket.send(encrypted_challenge)
        
        # Receive response
        response_len = int.from_bytes(recv_all(client_socket, 4), 'big')
        response = recv_all(client_socket, response_len)
        
        if response != expected_response:
            print("Error: Authentication failed")
            client_socket.close()
            return
        
        print("Authentication successful")
        
        # Send batch metadata for all files
        files_metadata = []
        current_offset = 0
        
        # Prepare metadata for all files with offsets
        for file_path, relative_path in collected_files:
            file_size = file_path.stat().st_size
            files_metadata.append({
                'filename': relative_path,
                'size': file_size,
                'offset': current_offset
            })
            current_offset += file_size
        
        batch_metadata = {
            'type': 'stream',
            'file_count': len(collected_files),
            'total_size': total_size,  # Original uncompressed size for progress tracking
            'compressed': True,
            'compressor': BLOSC_COMPRESSOR,
            'files': files_metadata
        }
        metadata_json = json.dumps(batch_metadata).encode()
        
        nonce_meta = secrets.token_bytes(12)
        encrypted_metadata = crypto.encrypt(metadata_json, nonce_meta)
        client_socket.send(len(nonce_meta).to_bytes(4, 'big'))
        client_socket.send(nonce_meta)
        client_socket.send(len(encrypted_metadata).to_bytes(4, 'big'))
        client_socket.send(encrypted_metadata)
        
        # Stream all files using large buffer chunks
        buffer_size = 1024 * 1024  # 1MB buffer for streaming
        start_time = time.time()
        
        # Create streaming buffer and track progress
        buffer = bytearray()
        file_hashes = {}
        original_bytes_processed = 0  # Track original file bytes for progress
        current_file_start = 0  # Track start position of current file
        first_progress_update = True  # Track if this is the first progress update
        
        for file_path, relative_path in collected_files:
            file_size = file_path.stat().st_size
            
            # Read file, compress, and calculate hash of original data
            hasher = hashlib.sha256()
            file_bytes_processed = 0
            
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(64 * 1024)  # Read in 64KB chunks
                    if not chunk:
                        break
                    
                    # Hash original data for integrity verification
                    hasher.update(chunk)
                    original_bytes_processed += len(chunk)
                    file_bytes_processed += len(chunk)
                    
                    # Compress chunk with Blosc+LZ4 for maximum speed
                    compressed_chunk = blosc.compress(chunk, cname=BLOSC_COMPRESSOR, clevel=BLOSC_LEVEL)
                    buffer.extend(compressed_chunk)
                    
                    # Send buffer when it reaches target size
                    while len(buffer) >= buffer_size:
                        send_chunk = bytes(buffer[:buffer_size])
                        buffer = buffer[buffer_size:]
                        
                        # Encrypt and send
                        nonce = secrets.token_bytes(12)
                        encrypted_chunk = crypto.encrypt(send_chunk, nonce)
                        
                        client_socket.send(len(nonce).to_bytes(4, 'big'))
                        client_socket.send(nonce)
                        client_socket.send(len(encrypted_chunk).to_bytes(4, 'big'))
                        client_socket.send(encrypted_chunk)
                        
                        # Update progress with current file info
                        elapsed = time.time() - start_time
                        if elapsed > 0:
                            current_speed = calculate_speed(original_bytes_processed, elapsed)
                            speed_str = format_speed(current_speed)
                            remaining_bytes = total_size - original_bytes_processed
                            eta_seconds = calculate_eta(remaining_bytes, current_speed)
                            eta_str = format_eta(eta_seconds)
                            
                            # Calculate current file progress
                            file_progress = (file_bytes_processed / file_size) * 100 if file_size > 0 else 100
                            
                            # Use two-line progress display
                            print_transfer_progress(relative_path, file_size, file_progress, 
                                                  speed_str, eta_str, first_progress_update, "Transferring")
                            first_progress_update = False
            
            # Store file hash
            file_hashes[relative_path] = hasher.hexdigest()
            current_file_start += file_size
        
        # Send remaining buffer
        if buffer:
            nonce = secrets.token_bytes(12)
            encrypted_chunk = crypto.encrypt(bytes(buffer), nonce)
            
            client_socket.send(len(nonce).to_bytes(4, 'big'))
            client_socket.send(nonce)
            client_socket.send(len(encrypted_chunk).to_bytes(4, 'big'))
            client_socket.send(encrypted_chunk)
            
            total_bytes_sent += len(buffer)
        
        # Send file hashes for verification
        hash_data = json.dumps(file_hashes).encode()
        nonce_hash = secrets.token_bytes(12)
        encrypted_hashes = crypto.encrypt(hash_data, nonce_hash)
        client_socket.send(len(nonce_hash).to_bytes(4, 'big'))
        client_socket.send(nonce_hash)
        client_socket.send(len(encrypted_hashes).to_bytes(4, 'big'))
        client_socket.send(encrypted_hashes)
        
        # Send end marker
        client_socket.send(b'\x00\x00\x00\x00')
        
        # Calculate and show completion
        total_time = time.time() - start_time
        avg_speed = calculate_speed(original_bytes_processed, total_time)
        avg_speed_str = format_speed(avg_speed)
        print(f"\nTransfer complete! (avg: {avg_speed_str})")
        
    except socket.timeout:
        print("Error: Connection timeout - no receiver connected")
    except Exception as e:
        print(f"Error during transfer: {e}")
    finally:
        server_socket.close()


def receive_files(connection_string: str, pod: bool = False, resume: bool = False):
    """Receiver mode: connect to sender and receive files"""
    
    # Parse connection string
    if ':' not in connection_string:
        print("Error: Invalid connection string format. Expected ip:token")
        sys.exit(1)
        
    parts = connection_string.split(':')
    if len(parts) != 2:
        print("Error: Invalid connection string format. Expected ip:token")
        sys.exit(1)
    
    ip, token = parts
    
    # Auto-detect Tailscale userspace mode or use explicit pod flag
    auto_pod_mode = detect_tailscale_userspace_mode()
    effective_pod_mode = pod or auto_pod_mode
    
    # Validate IP is Tailscale peer (skip for localhost in pod mode)
    if effective_pod_mode and ip == "127.0.0.1":
        if auto_pod_mode and not pod:
            print("Tailscale userspace mode detected: enabling pod mode")
        else:
            print("Pod mode: Accepting localhost connection")
    else:
        is_valid, peer_name = TailscaleDetector.verify_peer_ip_cached(ip)
        if not is_valid:
            print(f"Error: IP address {ip} is not an active peer in Tailscale network")
            sys.exit(1)
    
    # Connect to sender
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.settimeout(30)  # 30 second timeout
    
    try:
        print("Connecting to sender...")
        client_socket.connect((ip, TRANSFER_PORT))
        
        # Perform secure handshake
        crypto = SecureCrypto()
        public_key_bytes = crypto.get_public_key_bytes()
        
        # Receive sender's public key
        sender_key_len = int.from_bytes(recv_all(client_socket, 4), 'big')
        sender_public_key = recv_all(client_socket, sender_key_len)
        
        # Send our public key
        client_socket.send(len(public_key_bytes).to_bytes(4, 'big'))
        client_socket.send(public_key_bytes)
        
        # Derive session key
        crypto.derive_session_key(sender_public_key, token)
        
        # Receive and respond to authentication challenge
        nonce_len = int.from_bytes(recv_all(client_socket, 4), 'big')
        nonce = recv_all(client_socket, nonce_len)
        challenge_len = int.from_bytes(recv_all(client_socket, 4), 'big')
        encrypted_challenge = recv_all(client_socket, challenge_len)
        
        # Decrypt challenge
        challenge = crypto.decrypt(encrypted_challenge, nonce)
        
        # Generate and send response
        response = hashlib.sha256(challenge + token.encode()).digest()
        client_socket.send(len(response).to_bytes(4, 'big'))
        client_socket.send(response)
        
        print("Authentication successful")
        
        # Receive file metadata
        meta_nonce_len = int.from_bytes(recv_all(client_socket, 4), 'big')
        meta_nonce = recv_all(client_socket, meta_nonce_len)
        meta_len = int.from_bytes(recv_all(client_socket, 4), 'big')
        encrypted_metadata = recv_all(client_socket, meta_len)
        
        metadata_json = crypto.decrypt(encrypted_metadata, meta_nonce)
        metadata = json.loads(metadata_json.decode())
        
        # Handle new streaming protocol
        if metadata.get('type') != 'stream':
            print("Error: Unsupported transfer protocol")
            sys.exit(1)
            
        file_count = metadata['file_count']
        total_size = metadata['total_size']
        files_info = metadata['files']
        is_compressed = metadata.get('compressed', False)
        compressor = metadata.get('compressor', 'none')
        
        if is_compressed:
            print(f"Receiving {file_count} file(s) ({total_size} bytes total, {compressor} compressed)")
        else:
            print(f"Receiving {file_count} file(s) ({total_size} bytes total)")
        
        # Create FileWriter instances for incremental saving
        file_writers = []
        for file_info in files_info:
            filename = file_info['filename']
            file_size = file_info['size']
            file_offset = file_info['offset']
            
            # Check for unsafe filename
            if os.path.isabs(filename) or ".." in filename:
                print(f"\nError: Unsafe filename: {filename}")
                sys.exit(1)
            
            writer = FileWriter(filename, file_size, file_offset)
            writer.open_for_writing(resume=resume)
            file_writers.append(writer)
        
        # Receive streaming data with incremental saving
        stream_position = 0
        total_bytes_received = 0
        start_time = time.time()
        first_progress_update = True  # Track if this is the first progress update
        
        try:
            # Receive all streaming data chunks
            while True:
                # Check for hashes marker (indicates data stream is complete)
                nonce_len_bytes = recv_all(client_socket, 4)
                if nonce_len_bytes == b'\x00\x00\x00\x00':
                    break
                    
                nonce_len = int.from_bytes(nonce_len_bytes, 'big')
                chunk_nonce = recv_all(client_socket, nonce_len)
                chunk_len = int.from_bytes(recv_all(client_socket, 4), 'big')
                encrypted_chunk = recv_all(client_socket, chunk_len)
                
                # Check if this is the hash data (comes right before end marker)
                decrypted_data = crypto.decrypt(encrypted_chunk, chunk_nonce)
                
                # Try to detect if this is hash data by checking if it's JSON-formatted
                # Hash data is not compressed and contains JSON structure
                try:
                    if not is_compressed:
                        # No compression, use original size check
                        if stream_position + len(decrypted_data) > total_size:
                            hash_data = decrypted_data
                            file_hashes = json.loads(hash_data.decode())
                            break
                    else:
                        # With compression, we need to check if we've received all data
                        # by trying to parse as JSON (hash data is always JSON)
                        potential_hash = json.loads(decrypted_data.decode())
                        if isinstance(potential_hash, dict) and stream_position >= total_size:
                            # This looks like hash data and we've processed enough stream data
                            file_hashes = potential_hash
                            break
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Not hash data, continue processing as file data
                    pass
                
                # Decompress if needed (data already decrypted above)
                if is_compressed:
                    chunk = blosc.decompress(decrypted_data)
                else:
                    chunk = decrypted_data
                
                # Write to appropriate files incrementally
                chunk_offset = 0
                while chunk_offset < len(chunk):
                    remaining_chunk = chunk[chunk_offset:]
                    bytes_written = 0
                    
                    # Find which files need data at this stream position
                    for writer in file_writers:
                        if writer.needs_data(stream_position + chunk_offset):
                            bytes_written = writer.write_chunk(remaining_chunk)
                            break
                    
                    if bytes_written == 0:
                        # No file needed this data, advance position
                        chunk_offset = len(chunk)
                    else:
                        chunk_offset += bytes_written
                
                stream_position += len(chunk)
                total_bytes_received += len(chunk)
                
                # Update progress with current file info
                elapsed = time.time() - start_time
                if elapsed > 0:
                    current_speed = calculate_speed(total_bytes_received, elapsed)
                    speed_str = format_speed(current_speed)
                    remaining_bytes = total_size - total_bytes_received
                    eta_seconds = calculate_eta(remaining_bytes, current_speed)
                    eta_str = format_eta(eta_seconds)
                    
                    # Find current file being received
                    current_file = get_current_file_info(stream_position, files_info)
                    if current_file:
                        file_start = current_file['offset']
                        file_size = current_file['size']
                        file_position = stream_position - file_start
                        file_progress = (file_position / file_size) * 100 if file_size > 0 else 100
                        
                        # Use two-line progress display
                        print_transfer_progress(current_file['filename'], file_size, file_progress, 
                                              speed_str, eta_str, first_progress_update, "Receiving")
                        first_progress_update = False
                    else:
                        # Fallback to overall progress with two-line display
                        progress = (total_bytes_received / total_size) * 100
                        print_transfer_progress("multiple files", total_size, progress, 
                                              speed_str, eta_str, first_progress_update, "Receiving")
                        first_progress_update = False
        
        finally:
            # Always close file handles
            for writer in file_writers:
                writer.close()
        
        # Verify file integrity and collect completed files
        received_files = []
        for writer in file_writers:
            # Ensure all files are completed
            if not writer.is_complete:
                writer.complete_file()
            
            # Verify file integrity
            expected_hash = file_hashes.get(writer.filename)
            if expected_hash:
                received_hash = writer.get_hash()
                if received_hash != expected_hash:
                    print(f"\nError: File integrity check failed for {writer.filename}!")
                    print(f"Expected: {expected_hash}")
                    print(f"Received: {received_hash}")
                    sys.exit(1)
            
            # Add to received files list (FileWriter handles final naming)
            final_path = Path(writer.filename)
            if final_path.exists():
                received_files.append(final_path)
            else:
                # Check for renamed file due to conflicts
                counter = 1
                while True:
                    parent_dir = final_path.parent
                    name_parts = final_path.stem, counter, final_path.suffix
                    renamed_path = parent_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                    if renamed_path.exists():
                        received_files.append(renamed_path)
                        break
                    counter += 1
                    if counter > 100:  # Prevent infinite loop
                        print(f"Warning: Could not locate final file for {writer.filename}")
                        break
        
        # Calculate and show completion
        total_time = time.time() - start_time
        avg_speed = calculate_speed(total_bytes_received, total_time)
        avg_speed_str = format_speed(avg_speed)
        print(f"\nTransfer complete! (avg: {avg_speed_str})")
        
    except socket.timeout:
        print("Error: Connection timeout")
        sys.exit(1)
    except ConnectionRefusedError:
        print("Error: Connection refused - sender not available")
        sys.exit(1)
    except Exception as e:
        print(f"Error during transfer: {e}")
        sys.exit(1)
    finally:
        client_socket.close()


def main():
    parser = argparse.ArgumentParser(
        description="Secure file transfer over Tailscale networks"
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Send command
    send_parser = subparsers.add_parser('send', help='Send files/folders')
    send_parser.add_argument('files', nargs='+', help='Files or folders to send')
    send_parser.add_argument('--pod', action='store_true', help='Bind to localhost (127.0.0.1) for containerized environments')
    send_parser.add_argument('--novenv', action='store_true', help='Exclude virtual environment and cache folders (venv, node_modules, __pycache__, etc.)')
    
    # Receive command  
    receive_parser = subparsers.add_parser('receive', help='Receive files')
    receive_parser.add_argument('connection', help='Connection string: ip:token')
    receive_parser.add_argument('--pod', action='store_true', help='Accept connections from localhost (127.0.0.1) for containerized environments')
    receive_parser.add_argument('--resume', action='store_true', help='Resume interrupted transfer from existing partial files')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'send':
        send_files(args.files, pod=args.pod, novenv=args.novenv)
    elif args.command == 'receive':
        receive_files(args.connection, pod=args.pod, resume=args.resume)


if __name__ == "__main__":
    main()