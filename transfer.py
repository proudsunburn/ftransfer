#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import secrets
import select
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import tempfile
import blosc
# Import resource module (Unix-only) with fallback for Windows
try:
    import resource
except ImportError:
    resource = None  # Not available on Windows
# blosc_extension is not directly importable, but blosc uses it internally
# We'll catch the specific error type using a different approach

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
import datetime
import uuid

# Constants
TRANSFER_PORT = 15820
MAX_RETRY_ATTEMPTS = 3

def log_warning(message: str):
    """Log warning message to transfer_warnings.log file"""
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("transfer_warnings.log", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        # Silently ignore logging failures to avoid disrupting transfer
        pass

def safe_print(*args, **kwargs):
    """Print with protection against stdout failures (BrokenPipeError, IOError)"""
    try:
        print(*args, **kwargs)
        # Explicit flush to detect broken pipes early
        if kwargs.get('flush', False) or (not kwargs.get('end', '\n') == '\n'):
            sys.stdout.flush()
    except (BrokenPipeError, IOError, OSError) as e:
        # stdout is broken - try stderr as fallback
        try:
            message = ' '.join(str(arg) for arg in args)
            sys.stderr.write(f"{message}\n")
            sys.stderr.flush()
        except:
            pass  # Both stdout and stderr broken

        # Log the critical message to file
        try:
            message = ' '.join(str(arg) for arg in args)
            log_warning(f"Console output failed: {message}")
        except:
            pass  # Last resort logging also failed

        # For certain critical errors, we should exit
        if 'complete' in ' '.join(str(arg) for arg in args).lower():
            # This is a completion message - exit after logging
            sys.exit(0)

def safe_flush():
    """Safely flush stdout, catching any errors"""
    try:
        sys.stdout.flush()
    except (BrokenPipeError, IOError, OSError):
        # stdout is broken, don't raise
        pass

# Signal handlers for graceful handling of terminal disconnection
def handle_sigpipe(signum, frame):
    """Handle SIGPIPE (broken pipe) gracefully"""
    log_warning("SIGPIPE received - terminal disconnected")
    sys.exit(0)

def handle_sighup(signum, frame):
    """Handle SIGHUP (hangup) gracefully"""
    log_warning("SIGHUP received - terminal hung up")
    sys.exit(0)

# Install signal handlers (skip on Windows where SIGPIPE doesn't exist)
try:
    signal.signal(signal.SIGPIPE, handle_sigpipe)
except AttributeError:
    pass  # SIGPIPE doesn't exist on Windows

try:
    signal.signal(signal.SIGHUP, handle_sighup)
except AttributeError:
    pass  # SIGHUP might not exist on Windows

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
    '.mypy_cache', '.coverage', '.cache'
]

def detect_tailscale_userspace_mode():
    """Detect if Tailscale is running in userspace proxy mode (containers)
    
    Returns:
        bool: True if Tailscale is running in userspace mode (no TUN interface),
              False if running in kernel TUN mode (normal)
    """
    try:
        # Try using netifaces-plus if available
        import netifaces_plus as netifaces
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

def collect_files_recursive(file_paths: List[Path]) -> Tuple[List[Tuple[Path, str]], List[str]]:
    """Collect all files recursively from directories and detect virtual environment directories
    
    Args:
        file_paths: List of file/directory paths to process
    
    Returns:
        Tuple of (files_list, detected_venv_dirs_list)
        - files_list: List of (absolute_path, relative_path) tuples  
        - detected_venv_dirs_list: List of virtual env/cache directories found
    """
    collected_files = []
    detected_venv_dirs = []
    
    def is_venv_dir(dir_name: str) -> bool:
        """Check if directory matches virtual environment patterns"""
        return dir_name.lower() in [pattern.lower() for pattern in VENV_PATTERNS]
    
    def collect_from_directory(base_path: Path, current_path: Path, exclude_venv: bool = False):
        """Recursively collect files from directory"""
        try:
            for item in current_path.iterdir():
                if item.is_file():
                    # Calculate relative path from the base directory being sent
                    relative_path = item.relative_to(base_path.parent)
                    collected_files.append((item, str(relative_path)))
                elif item.is_dir():
                    # Check if this directory matches venv patterns
                    if is_venv_dir(item.name):
                        detected_venv_dirs.append(item.name)
                        # Only skip recursion if we're excluding venv dirs
                        if not exclude_venv:
                            collect_from_directory(base_path, item, exclude_venv)
                    else:
                        # Recursively process subdirectory
                        collect_from_directory(base_path, item, exclude_venv)
        except PermissionError:
            log_warning(f"Permission denied accessing {current_path}")
    
    for path in file_paths:
        if path.is_file():
            collected_files.append((path, path.name))
        elif path.is_dir():
            collect_from_directory(path, path)
        else:
            log_warning(f"Skipping {path} (not a regular file or directory)")
    
    return collected_files, list(set(detected_venv_dirs))  # Remove duplicates

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

def should_skip_conflict_detection(has_existing_lock: bool, resume_dict: Dict, output_dir: str, num_files: int) -> bool:
    """Determine if we can safely skip upfront conflict checking

    Args:
        has_existing_lock: Whether resuming an existing transfer
        resume_dict: Resume plan from lock manager
        output_dir: Directory where files will be written
        num_files: Number of files in the transfer

    Returns:
        True if conflict detection can be skipped safely
    """
    # Case 1: Resuming a transfer - conflicts already handled previously
    if has_existing_lock and resume_dict and resume_dict.get("action") == "resume":
        return True

    # Case 2: Output directory doesn't exist or is empty
    output_path = Path(output_dir)
    if not output_path.exists():
        return True

    try:
        if not any(output_path.iterdir()):  # Empty directory
            return True
    except (PermissionError, OSError):
        pass  # Fall through to normal checking

    # Case 3: Very large transfer - defer to on-demand checking
    # FileWriter.open_for_writing() handles overwrites naturally
    if num_files > 5000:
        return True

    return False


def detect_existing_conflicts(files_info: List[Dict], output_dir: str = '.') -> List[str]:
    """Detect existing files/folders that would conflict with incoming transfer

    Args:
        files_info: List of file metadata dictionaries from sender
        output_dir: Directory where files will be written

    Returns:
        List of conflicting file/folder paths
    """
    conflicts = []
    output_path = Path(output_dir)

    for file_info in files_info:
        filename = file_info['filename']

        # Check for unsafe filename (should already be caught earlier, but double-check)
        if os.path.isabs(filename) or ".." in filename:
            continue

        final_path = output_path / filename
        
        # Check for direct file conflict
        if final_path.exists():
            # Add appropriate suffix for display
            if final_path.is_dir():
                conflicts.append(f"{filename}/")
            else:
                conflicts.append(filename)
        
        # Check for directory conflicts (if incoming file would create directories)
        # that conflict with existing files
        parent = final_path.parent
        while parent != Path('.') and str(parent) != '.':
            if parent.exists() and parent.is_file():
                # A file exists where we need to create a directory
                conflicts.append(str(parent))
                break
            parent = parent.parent
    
    # Remove duplicates while preserving order
    seen = set()
    unique_conflicts = []
    for conflict in conflicts:
        if conflict not in seen:
            seen.add(conflict)
            unique_conflicts.append(conflict)
    
    return unique_conflicts

class ResourceMonitor:
    """Monitor system resource usage to prevent file descriptor exhaustion"""
    
    @staticmethod
    def get_open_fd_count() -> Optional[int]:
        """Get the current number of open file descriptors for this process"""
        try:
            # Try to count open file descriptors in /proc/self/fd (Linux)
            if os.path.exists('/proc/self/fd'):
                return len([f for f in os.listdir('/proc/self/fd') if f.isdigit()])

            # Fallback: use resource module (works on most Unix systems, not Windows)
            if resource is not None:
                return resource.getrlimit(resource.RLIMIT_NOFILE)[0] - 100  # Conservative estimate

            return None  # Not available on Windows
        except (OSError, AttributeError):
            return None
    
    @staticmethod
    def get_fd_limit() -> Optional[int]:
        """Get the soft limit for file descriptors"""
        try:
            # resource module not available on Windows
            if resource is None:
                return None

            soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
            return soft_limit
        except (OSError, AttributeError):
            return None
    
    @staticmethod
    def check_fd_usage(file_count: int) -> bool:
        """Check if processing this many files might exceed FD limits"""
        fd_limit = ResourceMonitor.get_fd_limit()
        if fd_limit is None:
            return True  # Can't check, assume it's okay
        
        # Reserve some FDs for system use (stdin, stdout, stderr, sockets, etc.)
        available_fds = fd_limit - 50
        
        return file_count < available_fds

def calculate_eta(remaining_bytes: int, current_speed: float) -> int:
    """Calculate estimated time to completion in seconds"""
    if current_speed <= 0 or remaining_bytes <= 0:
        return 0
    return int(remaining_bytes / current_speed)

def calculate_smoothed_speed(recent_speeds: list, delta_bytes: int, delta_time: float) -> float:
    """Calculate smoothed speed using moving average of recent measurements

    Args:
        recent_speeds: List of recent speed measurements
        delta_bytes: Bytes transferred since last measurement
        delta_time: Time elapsed since last measurement

    Returns:
        Smoothed speed in bytes/second
    """
    # Calculate instantaneous speed from delta values
    if delta_time <= 0 or delta_bytes <= 0:
        current_speed = 0.0
    else:
        current_speed = delta_bytes / delta_time

    # Add to recent speeds list (keep last 15 measurements)
    recent_speeds.append(current_speed)
    if len(recent_speeds) > 15:
        recent_speeds.pop(0)

    # Use weighted average favoring recent measurements
    if len(recent_speeds) == 1:
        return current_speed

    # Weight recent speeds more heavily (exponential weighting)
    total_weight = 0
    weighted_sum = 0
    for i, speed in enumerate(recent_speeds):
        weight = (i + 1) ** 1.5  # Exponential weighting favoring recent values
        weighted_sum += speed * weight
        total_weight += weight

    return weighted_sum / total_weight if total_weight > 0 else current_speed

def calculate_smoothed_eta(remaining_bytes: int, smoothed_speed: float, previous_eta: int, progress_percent: float) -> int:
    """Calculate ETA with smoothing to prevent dramatic increases"""
    if smoothed_speed <= 0 or remaining_bytes <= 0:
        return 0
    
    # Basic ETA calculation
    raw_eta = int(remaining_bytes / smoothed_speed)
    
    # Early in transfer (< 10%), allow more ETA variation
    # Late in transfer (> 90%), be more conservative
    if progress_percent < 10:
        smoothing_factor = 0.3  # Allow more variation
    elif progress_percent > 90:
        smoothing_factor = 0.7  # Heavy smoothing near end
    else:
        smoothing_factor = 0.5  # Moderate smoothing
    
    # Don't let ETA increase dramatically (cap increases)
    if previous_eta > 0:
        # If new ETA is much higher than previous, smooth the transition
        max_increase = max(10, previous_eta * 0.2)  # Max 20% increase or 10 seconds
        if raw_eta > previous_eta + max_increase:
            raw_eta = previous_eta + max_increase
        
        # Apply exponential smoothing
        smoothed_eta = int(previous_eta * smoothing_factor + raw_eta * (1 - smoothing_factor))
        return max(0, smoothed_eta)
    
    return raw_eta

def progress_update_thread(state: dict, stop_event: threading.Event, stall_callback=None):
    """Background thread to continuously update progress display every 200ms

    Args:
        state: Shared state dictionary with keys:
            - 'filename': Current file being transferred
            - 'file_size': Size of current file
            - 'bytes_transferred': Total bytes transferred so far
            - 'total_size': Total transfer size
            - 'action': "Sending" or "Receiving"
            - 'start_time': Transfer start timestamp
            - 'stream_position': Current stream position (for stall recovery)
        stop_event: Event to signal thread to stop
        stall_callback: Optional callback function(stream_position) called when stall detected
    """
    PROGRESS_UPDATE_INTERVAL = 0.2  # Update every 200ms
    STALL_TIMEOUT = 10.0  # 10 seconds of zero progress = stall
    recent_speeds = []
    previous_eta = 0
    last_bytes = 0
    last_time = time.time()
    first_update = True

    # Stall detection tracking
    last_stall_check_time = time.time()
    last_stall_check_bytes = 0

    while not stop_event.is_set():
        try:
            # Wait for the update interval
            stop_event.wait(PROGRESS_UPDATE_INTERVAL)
            if stop_event.is_set():
                break

            current_time = time.time()
            current_bytes = state.get('bytes_transferred', 0)
            total_size = state.get('total_size', 0)
            start_time = state.get('start_time', current_time)

            # OPTIMIZATION: Warmup mode for smooth initial speed calculation
            # Use cumulative speed for first 5 seconds, then switch to delta speed
            elapsed_total = current_time - start_time
            warmup_period = state.get('warmup_period', False)

            if warmup_period and elapsed_total < 5.0:
                # Cumulative average - more stable during warmup
                if elapsed_total > 0:
                    smoothed_speed = current_bytes / elapsed_total
                else:
                    smoothed_speed = 0.0
            else:
                # Graduated to delta speed - more responsive
                if warmup_period:
                    state['warmup_period'] = False  # Switch off warmup mode

                # Calculate delta values for instantaneous speed
                delta_bytes = current_bytes - last_bytes
                delta_time = current_time - last_time

                # Calculate smoothed speed using delta values
                smoothed_speed = calculate_smoothed_speed(recent_speeds, delta_bytes, delta_time)

            speed_str = format_speed(smoothed_speed)

            # Calculate progress and ETA
            if total_size > 0:
                progress_percent = (current_bytes / total_size) * 100
            else:
                progress_percent = 100

            remaining_bytes = total_size - current_bytes
            eta_seconds = calculate_smoothed_eta(remaining_bytes, smoothed_speed, previous_eta, progress_percent)
            eta_str = format_eta(eta_seconds)
            previous_eta = eta_seconds

            # Stall detection logic
            if stall_callback and not warmup_period:
                time_since_last_progress = current_time - last_stall_check_time
                bytes_since_last_check = current_bytes - last_stall_check_bytes

                if time_since_last_progress >= STALL_TIMEOUT and bytes_since_last_check == 0:
                    # STALL DETECTED - trigger callback if not already recovering
                    if not state.get('stall_recovery_in_progress', False):
                        state['stall_recovery_in_progress'] = True
                        stream_position = state.get('stream_position', current_bytes)
                        log_warning(f"Stall detected: no progress for {STALL_TIMEOUT}s at position {stream_position}")
                        stall_callback(stream_position)
                        last_stall_check_time = current_time  # Reset timer after triggering

                # Update stall check tracking if progress made
                if bytes_since_last_check > 0:
                    # Progress made, reset stall timer
                    last_stall_check_time = current_time
                    last_stall_check_bytes = current_bytes
                    state['stall_recovery_in_progress'] = False

            # Display progress
            filename = state.get('filename', 'transfer')
            file_size = state.get('file_size', total_size)
            action = state.get('action', 'Transferring')

            print_transfer_progress(filename, file_size, progress_percent,
                                  speed_str, eta_str, first_update, action)
            first_update = False

            # Update tracking variables
            last_bytes = current_bytes
            last_time = current_time

        except Exception as e:
            # Log errors but don't crash the thread
            log_warning(f"Progress thread error: {e}")
            continue

def send_resend_request(client_socket, crypto, stream_position, retry_count=0):
    """Send RESEND request to sender when transfer stalls

    Args:
        client_socket: Socket connection to sender
        crypto: SecureCrypto instance for encryption
        stream_position: Current byte offset in stream where stall occurred
        retry_count: Number of RESEND attempts so far
    """
    try:
        resend_message = {
            'type': 'resend_request',
            'stream_position': stream_position,
            'timestamp': time.time(),
            'retry_count': retry_count
        }

        # Encrypt and send using existing protocol pattern
        message_json = json.dumps(resend_message).encode()
        nonce = secrets.token_bytes(12)
        encrypted_message = crypto.encrypt(message_json, nonce)

        # Send using standard 4-byte length prefix pattern
        client_socket.send(len(nonce).to_bytes(4, 'big'))
        client_socket.send(nonce)
        client_socket.send(len(encrypted_message).to_bytes(4, 'big'))
        client_socket.send(encrypted_message)

        log_warning(f"Receiver: Sent RESEND request for position {stream_position} (attempt {retry_count + 1})")

    except Exception as e:
        log_warning(f"Receiver: Failed to send RESEND request: {e}")

def find_file_at_stream_position(collected_files, stream_position):
    """Find which file and offset corresponds to stream position

    Args:
        collected_files: List of (file_path, relative_path) tuples
        stream_position: Byte offset in the stream

    Returns:
        Tuple of ((file_path, relative_path), offset_in_file) or (None, 0)
    """
    current_position = 0
    for file_path, relative_path in collected_files:
        try:
            file_size = file_path.stat().st_size
            if current_position <= stream_position < current_position + file_size:
                offset = stream_position - current_position
                return (file_path, relative_path), offset
            current_position += file_size
        except Exception as e:
            log_warning(f"Sender: Error checking file {relative_path}: {e}")
            continue
    return None, 0

def send_chunk_from_position(client_socket, crypto, file_path, offset, chunk_size, use_compression):
    """Send a specific chunk from file at offset

    Args:
        client_socket: Socket to send through
        crypto: SecureCrypto instance
        file_path: Path to file
        offset: Byte offset to start reading from
        chunk_size: Number of bytes to read
        use_compression: Whether to compress the chunk
    """
    try:
        with open(file_path, 'rb') as f:
            f.seek(offset)
            chunk = f.read(chunk_size)

        if not chunk:
            log_warning(f"Sender: No data at offset {offset} in {file_path}")
            return

        # Compress if needed
        if use_compression:
            chunk_to_send = blosc.compress(chunk, cname='lz4', clevel=3, shuffle=blosc.BITSHUFFLE, nthreads=4)
        else:
            chunk_to_send = chunk

        # Encrypt and send (same pattern as normal chunk sending)
        nonce = secrets.token_bytes(12)
        encrypted_chunk = crypto.encrypt(chunk_to_send, nonce)

        client_socket.send(len(nonce).to_bytes(4, 'big'))
        client_socket.send(nonce)
        client_socket.send(len(encrypted_chunk).to_bytes(4, 'big'))
        client_socket.send(encrypted_chunk)

        log_warning(f"Sender: Resent {len(chunk)} bytes from offset {offset}")

    except Exception as e:
        log_warning(f"Sender: Error resending chunk: {e}")

def handle_resend_request(client_socket, crypto, collected_files, use_compression):
    """Handle RESEND request from receiver during active transfer

    Args:
        client_socket: Socket connection
        crypto: SecureCrypto instance
        collected_files: List of (file_path, relative_path) tuples
        use_compression: Whether compression is enabled

    Returns:
        True if RESEND was handled, False if no RESEND or error
    """
    try:
        # Read RESEND message (non-blocking, we know data is available)
        nonce_len_bytes = client_socket.recv(4)
        if not nonce_len_bytes or len(nonce_len_bytes) < 4:
            return False

        nonce_len = int.from_bytes(nonce_len_bytes, 'big')
        nonce = recv_all(client_socket, nonce_len)
        msg_len_bytes = recv_all(client_socket, 4)
        msg_len = int.from_bytes(msg_len_bytes, 'big')
        encrypted_msg = recv_all(client_socket, msg_len)

        # Decrypt and parse
        decrypted = crypto.decrypt(encrypted_msg, nonce)
        resend_req = json.loads(decrypted.decode())

        if resend_req.get('type') != 'resend_request':
            log_warning(f"Sender: Received unexpected message type: {resend_req.get('type')}")
            return False

        stream_position = resend_req.get('stream_position', 0)
        retry_count = resend_req.get('retry_count', 0)

        # Find which file corresponds to stream position
        target_file, file_offset = find_file_at_stream_position(collected_files, stream_position)

        if not target_file:
            log_warning(f"Sender: RESEND request for invalid position {stream_position}")
            return False

        log_warning(f"Sender: RESEND request for position {stream_position} "
                   f"(file: {target_file[1]}, offset: {file_offset}, attempt: {retry_count + 1})")

        # Send a chunk from the requested position (1MB)
        resend_chunk_size = 1024 * 1024  # 1MB
        send_chunk_from_position(client_socket, crypto, target_file[0],
                                file_offset, resend_chunk_size, use_compression)

        return True

    except Exception as e:
        log_warning(f"Sender: Error handling RESEND request: {e}")
        return False

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
                           action: str = "Transferring", warning_msg: str = ""):
    """Print three-line progress display with file info, progress, and warnings"""
    size_str = format_size(file_size)

    if not is_first_update:
        # Move cursor up 2 lines to overwrite all three lines
        safe_print("\033[2A\r", end='')

    # Line 1: Current filename being processed (clear line and print)
    safe_print(f"\r{action}: {filename} ({size_str})\033[K")

    # Line 2: Overall progress, speed, and ETA (clear line and print)
    safe_print(f"\rProgress: {progress_percent:.1f}% | Speed: {speed_str} | ETA: {eta_str}\033[K")

    # Line 3: Warning messages (clear line and print, no newline at end)
    if warning_msg:
        safe_print(f"\r{warning_msg}\033[K", end='', flush=True)
    else:
        safe_print(f"\r\033[K", end='', flush=True)  # Clear warning line

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
    
    def __init__(self, filename: str, size: int, offset: int, lock_manager: 'TransferLockManager' = None, overwrite_mode: bool = False, output_dir: str = '.'):
        self.filename = filename
        self.size = size
        self.offset = offset
        self.written = 0
        self.hasher = hashlib.sha256()
        self.output_dir = Path(output_dir)
        self.part_file = self.output_dir / f"{filename}.part"
        self.is_complete = False
        self.lock_manager = lock_manager
        self.needs_rehash = False
        self.overwrite_mode = overwrite_mode
        
    def open_for_writing(self, resume_bytes: int = 0):
        """Prepare file for writing, optionally resuming from specific byte offset"""
        # Create parent directories
        self.part_file.parent.mkdir(parents=True, exist_ok=True)
        
        if resume_bytes > 0 and self.part_file.exists():
            # Resume from specific byte offset based on lock file
            actual_size = self.part_file.stat().st_size
            if actual_size == resume_bytes and resume_bytes < self.size:
                self.written = resume_bytes
                self.needs_rehash = True  # Need to rehash existing data
                if self.lock_manager:
                    self.lock_manager.update_file_status(self.filename, "in_progress", self.written)
            else:
                # Size mismatch, start fresh
                self.written = 0
                self.hasher = hashlib.sha256()
                if self.lock_manager:
                    self.lock_manager.update_file_status(self.filename, "pending", 0)
        elif resume_bytes >= self.size:
            # File already complete according to lock
            self.is_complete = True
            if self.lock_manager:
                self.lock_manager.update_file_status(self.filename, "completed", self.size)
            return
        else:
            # Start fresh
            self.written = 0
            self.hasher = hashlib.sha256()
            if self.lock_manager:
                self.lock_manager.update_file_status(self.filename, "pending", 0)
    
    def _ensure_resume_hash(self):
        """Verify existing data by rehashing if needed (only done once)"""
        if self.needs_rehash:
            self.hasher = hashlib.sha256()
            try:
                with open(self.part_file, 'rb') as f:
                    while True:
                        chunk = f.read(64 * 1024)
                        if not chunk:
                            break
                        self.hasher.update(chunk)
                
                # Update lock file with partial hash
                if self.lock_manager:
                    partial_hash = self.hasher.hexdigest()
                    self.lock_manager.update_file_status(self.filename, "in_progress", self.written, partial_hash)
                    
            except OSError:
                # If we can't read the file, start fresh
                self.written = 0
                self.hasher = hashlib.sha256()
                if self.lock_manager:
                    self.lock_manager.update_file_status(self.filename, "pending", 0)
            
            self.needs_rehash = False
    
    def write_chunk(self, data: bytes) -> int:
        """Write data chunk and update hash. Returns bytes written."""
        if self.is_complete:
            return 0
        
        # Ensure we've rehashed existing data if resuming
        self._ensure_resume_hash()
            
        bytes_to_write = min(len(data), self.size - self.written)
        if bytes_to_write > 0:
            chunk_to_write = data[:bytes_to_write]

            # Open file, write data, and immediately close
            try:
                with open(self.part_file, 'ab' if self.written > 0 else 'wb') as f:
                    f.write(chunk_to_write)
                    # Flush every 10MB or when file is complete (reduces I/O blocking by ~10x)
                    if self.written % (10 * 1024 * 1024) < len(chunk_to_write) or self.written + bytes_to_write >= self.size:
                        f.flush()

                self.hasher.update(chunk_to_write)
                self.written += bytes_to_write

                # Update lock file every 10MB or when complete (reduces lock file I/O)
                if self.lock_manager:
                    if self.written % (10 * 1024 * 1024) < len(chunk_to_write) or self.written >= self.size:
                        self.lock_manager.update_file_status(self.filename, "in_progress", self.written)

                # Check if file is complete
                if self.written >= self.size:
                    self.complete_file()
                    
            except OSError as e:
                # Handle file operation errors gracefully
                log_warning(f"Failed to write to {self.part_file}: {e}")
                return 0
                
        return bytes_to_write
    
    def complete_file(self):
        """Mark file as complete and move from .part to final name"""
        if self.written == self.size and not self.is_complete:
            try:
                # Move .part file to final location
                final_path = self.output_dir / self.filename
                
                # Handle filename conflicts based on overwrite mode
                if self.overwrite_mode and final_path.exists():
                    # Overwrite mode: remove existing file/directory
                    try:
                        if final_path.is_dir():
                            shutil.rmtree(final_path)
                        else:
                            final_path.unlink()
                    except OSError as e:
                        log_warning(f"Failed to remove existing file {final_path}: {e}")
                        # Fall back to renaming if overwrite fails
                        counter = 1
                        original_path = final_path
                        while final_path.exists():
                            parent_dir = original_path.parent
                            name_parts = original_path.stem, counter, original_path.suffix
                            final_path = parent_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                            counter += 1
                elif not self.overwrite_mode:
                    # Non-overwrite mode: rename if conflict exists (preserve current behavior)
                    counter = 1
                    original_path = final_path
                    while final_path.exists():
                        parent_dir = original_path.parent
                        name_parts = original_path.stem, counter, original_path.suffix
                        final_path = parent_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                        counter += 1
                
                self.part_file.rename(final_path)
                self.is_complete = True
                
                # Update lock file with completion
                if self.lock_manager:
                    final_hash = self.hasher.hexdigest()
                    self.lock_manager.update_file_status(self.filename, "completed", self.size, final_hash)
                
                # print(f"Completed: {final_path}")  # Removed to keep clean progress display
            except OSError as e:
                log_warning(f"Failed to complete file {self.filename}: {e}")
                pass
        
    def get_hash(self) -> str:
        """Get current hash of written data"""
        return self.hasher.hexdigest()
    
    def reset_for_retry(self):
        """Reset file writer for retry attempt"""
        self.hasher = hashlib.sha256()
        self.written = 0
        self.is_complete = False
        self.needs_rehash = False
        
        # Update lock file to pending status
        if self.lock_manager:
            self.lock_manager.update_file_status(self.filename, "pending", 0)
        
        # Remove the corrupted part file
        if self.part_file.exists():
            try:
                self.part_file.unlink()
            except:
                pass  # Ignore errors during cleanup
    
    def needs_data(self, stream_position: int) -> bool:
        """Check if this file needs data at the given stream position"""
        file_start = self.offset
        file_end = self.offset + self.size
        return file_start <= stream_position < file_end and not self.is_complete
    
    def close(self):
        """Close file handle - no-op since we don't keep handles open"""
        pass  # Files are opened and closed immediately in write_chunk


class LazyFileWriterDict:
    """Creates FileWriters on-demand as data arrives, eliminating upfront delay

    OPTIMIZATION: Instead of creating all FileWriters upfront (which triggers O(N)
    lock updates and disk I/O), this class creates them lazily as chunks arrive.
    This eliminates setup delay and allows READY signal to be sent immediately.
    """

    def __init__(self, files_info: List[Dict], resume_dict: Dict[str, int],
                 output_dir: str, lock_manager: 'TransferLockManager',
                 overwrite_mode: bool = False):
        """Initialize with file metadata but don't create FileWriters yet

        Args:
            files_info: List of file metadata dicts with filename, size, offset
            resume_dict: Dict mapping filename to resume byte count
            output_dir: Directory where files will be written
            lock_manager: TransferLockManager instance for state tracking
            overwrite_mode: Whether to overwrite existing files
        """
        # Build lookup dict but don't create FileWriters yet
        self._files_info = {f['filename']: f for f in files_info}
        self._resume_dict = resume_dict
        self._output_dir = output_dir
        self._lock_manager = lock_manager
        self._overwrite_mode = overwrite_mode
        self._writers = {}  # Created on-demand

        # OPTIMIZATION: Build offset index for O(1) lookups (sorted by start offset)
        self._offset_index = []
        for file_info in files_info:
            start = file_info['offset']
            end = start + file_info['size']
            self._offset_index.append((start, end, file_info['filename']))
        self._offset_index.sort(key=lambda x: x[0])  # Sort by start offset

    def __getitem__(self, filename: str) -> FileWriter:
        """Get existing writer or create new one on first access"""
        if filename not in self._writers:
            if filename not in self._files_info:
                raise KeyError(f"File {filename} not in transfer")

            file_info = self._files_info[filename]
            resume_bytes = self._resume_dict.get(filename, 0)

            # Create FileWriter only when needed
            writer = FileWriter(
                filename,
                file_info['size'],
                file_info['offset'],
                self._lock_manager,
                self._overwrite_mode,
                self._output_dir
            )
            writer.open_for_writing(resume_bytes)
            self._writers[filename] = writer

        return self._writers[filename]

    def __contains__(self, filename: str) -> bool:
        """Check if filename is in transfer (not whether writer was created)"""
        return filename in self._files_info

    def values(self):
        """Return all created writers (for cleanup)"""
        return self._writers.values()

    def items(self):
        """Return all created (filename, writer) pairs"""
        return self._writers.items()

    def keys(self):
        """Return all filenames that have had writers created"""
        return self._writers.keys()

    def __iter__(self):
        """Iterate over all writers in stream order (by offset), creating them lazily

        This enables iteration with 'for writer in file_writers:' without triggering
        Python's numeric indexing fallback that would cause KeyError.
        """
        # Sort files by offset to iterate in stream order
        sorted_infos = sorted(self._files_info.values(), key=lambda f: f['offset'])
        for file_info in sorted_infos:
            yield self[file_info['filename']]  # Creates writer on-demand via __getitem__

    def __len__(self):
        """Return total number of files in transfer (not just created writers)"""
        return len(self._files_info)

    def get_writer_at_offset(self, stream_position: int):
        """Get the writer for the file at the given stream position (O(log N) lookup)

        Args:
            stream_position: Position in the stream (after decompression)

        Returns:
            FileWriter for the file at this position, or None if position is beyond all files
        """
        # OPTIMIZATION: Use binary search on sorted offset index for O(log N) lookup
        # Since files are transferred sequentially, we could also optimize for sequential access
        # but binary search is fast enough and handles any access pattern
        import bisect

        # Binary search to find the file containing this position
        # We search for the rightmost file start <= stream_position
        idx = bisect.bisect_right(self._offset_index, (stream_position, float('inf'), ''))

        if idx > 0:
            start, end, filename = self._offset_index[idx - 1]
            if start <= stream_position < end:
                return self[filename]  # Creates writer on-demand via __getitem__

        # Position is beyond all files
        return None


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


class TransferLockManager:
    """Manages transfer state and automatic resume functionality"""
    
    LOCK_FILE_NAME = ".transfer_lock.json"
    LOCK_VERSION = "1.0"
    
    def __init__(self, working_dir: str = "."):
        self.working_dir = Path(working_dir)
        self.lock_file_path = self.working_dir / self.LOCK_FILE_NAME
        self.lock_data = None
        self._pending_updates = {}  # Buffer for batched updates
        self._last_save_time = 0
        self._save_interval = 2.0  # Save every 2 seconds max
        self._max_pending = 150   # Max pending updates before forced save
        # OPTIMIZATION: Defer mode for bulk FileWriter creation
        self._defer_mode = False
        self._deferred_updates = []
    
    def create_lock_file(self, sender_ip: str, file_list: List[Dict], total_size: int):
        """Create a new transfer lock file"""
        session_id = str(uuid.uuid4())
        timestamp = datetime.datetime.now().isoformat()
        
        lock_data = {
            "version": self.LOCK_VERSION,
            "session_id": session_id,
            "timestamp": timestamp,
            "sender_ip": sender_ip,
            "total_files": len(file_list),
            "total_size": total_size,
            "files": {}
        }
        
        # Add each file to the lock
        for file_info in file_list:
            filename = file_info.get('path') or file_info.get('filename')
            lock_data["files"][filename] = {
                "status": "pending",
                "size": file_info["size"],
                "original_hash": None,  # Will be set by sender
                "transferred_bytes": 0,
                "partial_hash": None,
                "last_modified": None
            }
        
        self.lock_data = lock_data
        self._save_lock_file()
        return session_id
    
    def load_existing_lock(self) -> bool:
        """Load existing lock file if present. Returns True if lock was loaded."""
        if not self.lock_file_path.exists():
            return False
        
        try:
            with open(self.lock_file_path, 'r', encoding='utf-8') as f:
                self.lock_data = json.load(f)
            
            # Validate lock file structure
            if not self._validate_lock_file():
                log_warning(f"Invalid lock file structure, ignoring: {self.lock_file_path}")
                return False
            
            # Check if lock file is stale (older than 24 hours)
            lock_time = datetime.datetime.fromisoformat(self.lock_data["timestamp"])
            age = datetime.datetime.now() - lock_time
            if age.total_seconds() > 24 * 3600:  # 24 hours
                log_warning(f"Stale lock file found (age: {age}), ignoring")
                return False
            
            return True
            
        except (json.JSONDecodeError, OSError, KeyError) as e:
            log_warning(f"Failed to load lock file: {e}")
            return False
    
    def _validate_lock_file(self) -> bool:
        """Validate lock file has required structure"""
        if not self.lock_data:
            return False
        
        required_fields = ["version", "session_id", "timestamp", "files"]
        return all(field in self.lock_data for field in required_fields)
    
    def update_file_status(self, filename: str, status: str, transferred_bytes: int = 0, partial_hash: str = None, force_save: bool = False):
        """Update status of a specific file with batching optimization"""
        if not self.lock_data or filename not in self.lock_data["files"]:
            return

        # OPTIMIZATION: If in defer mode, just buffer the update without any disk I/O
        if self._defer_mode:
            self._deferred_updates.append((filename, status, transferred_bytes, partial_hash))
            return

        # Update the actual lock data
        file_entry = self.lock_data["files"][filename]
        file_entry["status"] = status
        file_entry["transferred_bytes"] = transferred_bytes
        if partial_hash:
            file_entry["partial_hash"] = partial_hash

        # Buffer this update for batched saving
        self._pending_updates[filename] = {
            "status": status,
            "transferred_bytes": transferred_bytes,
            "partial_hash": partial_hash
        }

        # Save immediately for critical operations or when batch limits reached
        current_time = time.time()
        if (force_save or
            status == "completed" or
            status == "failed" or
            len(self._pending_updates) >= self._max_pending or
            current_time - self._last_save_time >= self._save_interval):
            self._flush_pending_updates()
    
    def _flush_pending_updates(self):
        """Save pending updates to lock file and clear buffer"""
        if self._pending_updates:
            self._save_lock_file()
            self._pending_updates.clear()
            self._last_save_time = time.time()
    
    def flush_pending_updates(self):
        """Public method to force flush pending updates"""
        self._flush_pending_updates()

    def enable_defer_mode(self):
        """Enable defer mode to buffer updates without writing to disk"""
        self._defer_mode = True
        self._deferred_updates = []

    def flush_deferred_updates(self):
        """Apply all buffered updates in one operation and save once"""
        if not self._deferred_updates:
            self._defer_mode = False
            return

        # Apply all deferred updates to lock_data
        for filename, status, transferred_bytes, partial_hash in self._deferred_updates:
            if filename in self.lock_data["files"]:
                file_entry = self.lock_data["files"][filename]
                file_entry["status"] = status
                file_entry["transferred_bytes"] = transferred_bytes
                if partial_hash:
                    file_entry["partial_hash"] = partial_hash

        # Single disk write for all updates
        self._save_lock_file()
        self._deferred_updates = []
        self._defer_mode = False
        self._last_save_time = time.time()
    
    def get_resume_plan(self, incoming_files: List[Dict]) -> Dict:
        """Analyze what needs to be transferred based on existing lock"""
        if not self.lock_data:
            return {"action": "fresh_transfer", "files_to_transfer": incoming_files}
        
        resume_files = []
        fresh_files = []
        completed_files = []
        
        # Create lookup dict for incoming files
        incoming_lookup = {f.get('path', f.get('filename')): f for f in incoming_files}
        
        for filename, lock_info in self.lock_data["files"].items():
            if filename not in incoming_lookup:
                # File no longer in transfer list
                continue
            
            incoming_info = incoming_lookup[filename]
            
            # Check if file size changed
            if lock_info["size"] != incoming_info["size"]:
                fresh_files.append(incoming_info)
                continue
            
            status = lock_info["status"]
            if status == "completed":
                completed_files.append(filename)
            elif status == "in_progress" and lock_info["transferred_bytes"] > 0:
                resume_files.append((filename, lock_info["transferred_bytes"]))
            else:
                fresh_files.append(incoming_info)
        
        # Add any new files not in the lock
        for filename, file_info in incoming_lookup.items():
            if filename not in self.lock_data["files"]:
                fresh_files.append(file_info)
        
        return {
            "action": "resume",
            "completed_files": completed_files,
            "resume_files": resume_files,
            "fresh_files": fresh_files
        }
    
    def _save_lock_file(self):
        """Save lock data to file"""
        if not self.lock_data:
            return

        try:
            # Create parent directory if needed
            self.lock_file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write to temporary file first, then rename for atomicity
            temp_path = self.lock_file_path.with_suffix('.tmp')
            num_files = len(self.lock_data.get("files", {}))

            # OPTIMIZATION: Use compact JSON for large transfers to reduce write time
            with open(temp_path, 'w', encoding='utf-8') as f:
                if num_files > 1000:
                    # Compact JSON - no indentation for large transfers
                    json.dump(self.lock_data, f, separators=(',', ':'))
                else:
                    # Pretty JSON for small transfers (debugging friendly)
                    json.dump(self.lock_data, f, indent=2)

            temp_path.rename(self.lock_file_path)

        except OSError as e:
            log_warning(f"Failed to save lock file: {e}")
    
    def cleanup_on_completion(self):
        """Remove lock file after successful transfer"""
        try:
            if self.lock_file_path.exists():
                self.lock_file_path.unlink()
        except OSError as e:
            log_warning(f"Failed to remove lock file: {e}")
    
    def handle_stale_locks(self):
        """Clean up old lock files"""
        try:
            lock_files = [self.lock_file_path] if self.lock_file_path.exists() else []
            current_time = datetime.datetime.now()

            for lock_file in lock_files:
                try:
                    # Check file age
                    stat = lock_file.stat()
                    age = current_time - datetime.datetime.fromtimestamp(stat.st_mtime)
                    
                    if age.total_seconds() > 24 * 3600:  # 24 hours
                        lock_file.unlink()
                        log_warning(f"Removed stale lock file: {lock_file}")
                
                except OSError:
                    continue
        
        except OSError:
            pass  # Ignore errors during cleanup
    
    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """Calculate SHA-256 hash of a file"""
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(64 * 1024), b""):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except OSError as e:
            log_warning(f"Failed to hash file {file_path}: {e}")
            return None
    
    def verify_source_files_unchanged(self, source_file_paths: Dict[str, str]) -> List[str]:
        """
        Verify that source files haven't changed since lock creation.
        Returns list of changed file names.
        """
        if not self.lock_data:
            return []
        
        changed_files = []
        
        for filename, file_path in source_file_paths.items():
            if filename not in self.lock_data["files"]:
                continue
            
            lock_info = self.lock_data["files"][filename]
            original_hash = lock_info.get("original_hash")
            
            if not original_hash:
                # No original hash stored, skip verification
                continue
            
            current_hash = self._calculate_file_hash(file_path)
            if current_hash and current_hash != original_hash:
                changed_files.append(filename)
                # Update lock file to mark for fresh transfer
                lock_info["status"] = "pending"
                lock_info["transferred_bytes"] = 0
                lock_info["original_hash"] = current_hash
                log_warning(f"Source file changed: {filename} (will be retransferred)")
        
        if changed_files:
            self._save_lock_file()
        
        return changed_files
    
    def update_source_file_hashes(self, source_file_paths: Dict[str, str]):
        """Update the lock file with current source file hashes"""
        if not self.lock_data:
            return
        
        for filename, file_path in source_file_paths.items():
            if filename in self.lock_data["files"]:
                current_hash = self._calculate_file_hash(file_path)
                if current_hash:
                    self.lock_data["files"][filename]["original_hash"] = current_hash
                    # Also update last_modified time
                    try:
                        stat = os.stat(file_path)
                        self.lock_data["files"][filename]["last_modified"] = datetime.datetime.fromtimestamp(stat.st_mtime).isoformat()
                    except OSError:
                        pass
        
        self._save_lock_file()


def send_single_file(client_socket, crypto, file_path: str, relative_path: str, use_compression: bool = True) -> str:
    """Send a single file and return its hash"""
    hasher = hashlib.sha256()
    file_size = os.path.getsize(file_path)

    with open(file_path, 'rb') as f:
        bytes_sent = 0
        while bytes_sent < file_size:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break

            # Update hash
            hasher.update(chunk)

            # Conditionally compress chunk
            if use_compression:
                chunk_to_send = blosc.compress(chunk, cname=BLOSC_COMPRESSOR, clevel=BLOSC_LEVEL)
            else:
                chunk_to_send = chunk

            # Encrypt chunk
            nonce = secrets.token_bytes(12)
            encrypted_chunk = crypto.encrypt(chunk_to_send, nonce)
            
            # Send encrypted chunk
            client_socket.send(len(nonce).to_bytes(4, 'big'))
            client_socket.send(nonce)
            client_socket.send(len(encrypted_chunk).to_bytes(4, 'big'))
            client_socket.send(encrypted_chunk)
            
            bytes_sent += len(chunk)
    
    return hasher.hexdigest()


def send_files(file_paths: List[str], pod: bool = False):
    """Sender mode: listen for connections and send files"""
    
    # Validate files exist
    files = validate_files(file_paths)
    
    # Get Tailscale IP for connection string
    tailscale_ip = TailscaleDetector.get_tailscale_ip()
    if not tailscale_ip:
        safe_print("Error: Could not detect Tailscale IP. Ensure Tailscale is running.")
        sys.exit(1)
    
    # Auto-detect Tailscale userspace mode or use explicit pod flag
    auto_pod_mode = detect_tailscale_userspace_mode()
    effective_pod_mode = pod or auto_pod_mode
    
    # Set bind IP (localhost for pod mode, all interfaces otherwise)
    if effective_pod_mode:
        bind_ip = "127.0.0.1"
        if auto_pod_mode and not pod:
            safe_print("Tailscale userspace mode detected: enabling pod mode")
        else:
            safe_print("Pod mode: Binding to localhost")
    else:
        bind_ip = "0.0.0.0"  # Bind to all interfaces for Tailscale peer connections
    
    # Generate token
    token = SecureTokenGenerator.generate_token()
    
    # Prepare files for unified streaming transfer
    if any(f.is_dir() for f in files):
        # Use recursive collection for directories
        collected_files, detected_venv_dirs = collect_files_recursive(files)
        
        # Ask user about excluding virtual environment directories
        exclude_venv = False
        if detected_venv_dirs:
            dir_list = ", ".join(detected_venv_dirs)
            response = input(f"Found virtual environment/cache directories: {dir_list}. Skip? [Y/n]: ").strip().lower()
            exclude_venv = response != 'n'
            
            if exclude_venv:
                # Re-collect files excluding virtual environment directories
                def collect_from_directory_filtered(base_path: Path, current_path: Path):
                    filtered_files = []
                    try:
                        for item in current_path.iterdir():
                            if item.is_file():
                                relative_path = item.relative_to(base_path.parent)
                                filtered_files.append((item, str(relative_path)))
                            elif item.is_dir():
                                # Check if this directory matches venv patterns
                                if not (item.name.lower() in [pattern.lower() for pattern in VENV_PATTERNS]):
                                    # Recursively process subdirectory
                                    filtered_files.extend(collect_from_directory_filtered(base_path, item))
                    except PermissionError:
                        log_warning(f"Permission denied accessing {current_path}")
                    return filtered_files
                
                # Rebuild collected_files excluding venv directories
                collected_files = []
                for path in files:
                    if path.is_file():
                        collected_files.append((path, path.name))
                    elif path.is_dir():
                        collected_files.extend(collect_from_directory_filtered(path, path))
    else:
        # Regular files
        collected_files = [(f, f.name) for f in files]

    # Ask user about compression
    response = input(f"Use compression? [y/N]: ").strip().lower()
    use_compression = response == 'y'

    # Calculate total size and prepare metadata for all files
    total_size = sum(abs_path.stat().st_size for abs_path, _ in collected_files)
    filename = f"{len(collected_files)}_files" if len(collected_files) > 1 else collected_files[0][1]
    
    # Check for potential resource issues
    ResourceMonitor.check_fd_usage(len(collected_files))

    safe_print(f"type into receiver: transfer receive {tailscale_ip}:{token}")

    # Start server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((bind_ip, TRANSFER_PORT))
    server_socket.listen(1)
    server_socket.settimeout(300)  # 5 minute timeout

    safe_print("Waiting for receiver to connect... ", end="")
    
    try:
        client_socket, client_addr = server_socket.accept()

        # Enable TCP_NODELAY for lower latency (disable Nagle's algorithm)
        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        # Validate client is from Tailscale network (skip for localhost in pod mode)
        if effective_pod_mode and client_addr[0] == "127.0.0.1":
            safe_print("Pod mode: Accepting localhost connection")
        else:
            is_valid, peer_name = TailscaleDetector.verify_peer_ip_cached(client_addr[0])
            if not is_valid:
                safe_print(f"Error: Rejected connection from unauthorized IP: {client_addr[0]}")
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
            safe_print("Error: Authentication failed")
            client_socket.close()
            return

        safe_print("Authentication successful")
        
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
            'compressed': use_compression,
            'compressor': BLOSC_COMPRESSOR if use_compression else 'none',
            'files': files_metadata
        }
        metadata_json = json.dumps(batch_metadata).encode()
        
        nonce_meta = secrets.token_bytes(12)
        encrypted_metadata = crypto.encrypt(metadata_json, nonce_meta)
        client_socket.send(len(nonce_meta).to_bytes(4, 'big'))
        client_socket.send(nonce_meta)
        client_socket.send(len(encrypted_metadata).to_bytes(4, 'big'))
        client_socket.send(encrypted_metadata)

        # Wait for RECEIVER_READY signal before streaming files
        # OPTIMIZATION: Adaptive timeout based on file count for large transfers
        num_files = len(files_metadata)
        if num_files > 10000:
            timeout = 180  # 3 minutes for very large transfers
            safe_print(f"Waiting for receiver to be ready (processing {num_files:,} files may take 1-2 minutes)...")
        elif num_files > 1000:
            timeout = 120  # 2 minutes for large transfers
            safe_print(f"Waiting for receiver to be ready (processing {num_files:,} files may take 30-60 seconds)...")
        else:
            timeout = 60   # 1 minute for normal transfers
            safe_print("Waiting for receiver to be ready...")

        client_socket.settimeout(timeout)
        try:
            ready_len = int.from_bytes(recv_all(client_socket, 4), 'big')
            ready_signal = recv_all(client_socket, ready_len)
            if ready_signal != b'READY':
                safe_print("Error: Invalid receiver ready signal")
                client_socket.close()
                return
        except socket.timeout:
            safe_print(f"Error: Timeout waiting for receiver to be ready ({timeout}s)")
            client_socket.close()
            return

        # Use 5 minute timeout to detect true stalls (instead of infinite blocking)
        client_socket.settimeout(300)

        # Stream all files using large buffer chunks
        buffer_size = 1024 * 1024  # 1MB buffer for streaming
        start_time = time.time()

        # RESEND detection tracking
        last_resend_check_time = time.time()
        RESEND_CHECK_INTERVAL = 0.5  # Check every 500ms
        chunks_sent = 0

        # Create streaming buffer and track progress
        buffer = bytearray()
        file_hashes = {}
        original_bytes_processed = 0  # Track original file bytes for progress
        total_bytes_sent = 0  # Track total compressed bytes sent over network
        current_file_start = 0  # Track start position of current file
        buffer_stream_position = 0  # Track stream position of data being sent (for display sync)

        # Setup background progress thread
        progress_state = {
            'filename': '',
            'file_size': 0,
            'bytes_transferred': 0,
            'total_size': total_size,
            'action': 'Sending',
            'start_time': start_time
        }
        stop_progress = threading.Event()
        progress_thread = threading.Thread(
            target=progress_update_thread,
            args=(progress_state, stop_progress),
            daemon=True
        )
        progress_thread.start()

        for file_path, relative_path in collected_files:
            file_size = file_path.stat().st_size

            # Update progress state for this file
            progress_state['filename'] = relative_path
            progress_state['file_size'] = file_size

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

                    # Accumulate uncompressed chunks in buffer
                    buffer.extend(chunk)

                    # When buffer reaches target size, compress entire buffer and send
                    while len(buffer) >= buffer_size:
                        # Extract 1MB of data
                        chunk_data = bytes(buffer[:buffer_size])
                        buffer = buffer[buffer_size:]

                        # Update progress display to show file being SENT (not read)
                        # This syncs sender display with receiver display
                        current_file_sending = get_current_file_info(buffer_stream_position, files_metadata)
                        if current_file_sending:
                            progress_state['filename'] = current_file_sending['filename']
                            progress_state['file_size'] = current_file_sending['size']

                        # Conditionally compress based on user choice
                        if use_compression:
                            chunk_to_send = blosc.compress(chunk_data, cname=BLOSC_COMPRESSOR, clevel=BLOSC_LEVEL)
                        else:
                            chunk_to_send = chunk_data

                        # Encrypt and send
                        nonce = secrets.token_bytes(12)
                        encrypted_chunk = crypto.encrypt(chunk_to_send, nonce)

                        client_socket.send(len(nonce).to_bytes(4, 'big'))
                        client_socket.send(nonce)
                        client_socket.send(len(encrypted_chunk).to_bytes(4, 'big'))
                        client_socket.send(encrypted_chunk)

                        # Track total bytes sent over network
                        total_bytes_sent += len(encrypted_chunk)
                        chunks_sent += 1

                        # Increment buffer stream position (tracks where we are in sending)
                        buffer_stream_position += len(chunk_data)

                        # Periodically check for RESEND requests from receiver
                        current_time = time.time()
                        if current_time - last_resend_check_time >= RESEND_CHECK_INTERVAL:
                            last_resend_check_time = current_time

                            # Use select with 0 timeout to check if data available (non-blocking)
                            readable, _, _ = select.select([client_socket], [], [], 0)
                            if readable:
                                # RESEND request available - handle it
                                handle_resend_request(client_socket, crypto, collected_files, use_compression)

                    # Update progress state (background thread will display it)
                    progress_state['bytes_transferred'] = original_bytes_processed

            # Store file hash
            file_hashes[relative_path] = hasher.hexdigest()
            current_file_start += file_size
        
        # Send remaining buffer if non-empty
        if buffer:
            # Update progress display for remaining data
            current_file_sending = get_current_file_info(buffer_stream_position, files_metadata)
            if current_file_sending:
                progress_state['filename'] = current_file_sending['filename']
                progress_state['file_size'] = current_file_sending['size']

            # Conditionally compress remaining data
            remaining_data = bytes(buffer)
            if use_compression:
                data_to_send = blosc.compress(remaining_data, cname=BLOSC_COMPRESSOR, clevel=BLOSC_LEVEL)
            else:
                data_to_send = remaining_data

            nonce = secrets.token_bytes(12)
            encrypted_chunk = crypto.encrypt(data_to_send, nonce)

            client_socket.send(len(nonce).to_bytes(4, 'big'))
            client_socket.send(nonce)
            client_socket.send(len(encrypted_chunk).to_bytes(4, 'big'))
            client_socket.send(encrypted_chunk)

            total_bytes_sent += len(encrypted_chunk)
        
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

        # Log timing: sender finished sending all data
        data_send_time = time.time() - start_time
        log_warning(f"Sender: All data sent (time: {data_send_time:.1f}s, bytes: {total_bytes_sent})")
        
        # Wait for potential retry requests or completion signal
        # IMPORTANT: Increased timeout from 10s to 120s to allow receiver to complete
        # hash verification and post-processing before sender exits
        client_socket.settimeout(120)  # 120 second timeout for retry requests and completion
        completion_received = False
        completion_start_time = time.time()

        while True:
            try:
                # Check for retry request or completion signal
                nonce_len_bytes = client_socket.recv(4)
                if not nonce_len_bytes or nonce_len_bytes == b'\x00\x00\x00\x00':
                    break

                nonce_len = int.from_bytes(nonce_len_bytes, 'big')
                nonce = recv_all(client_socket, nonce_len)
                encrypted_len_bytes = recv_all(client_socket, 4)
                encrypted_len = int.from_bytes(encrypted_len_bytes, 'big')
                encrypted_data = recv_all(client_socket, encrypted_len)

                # Decrypt the message
                try:
                    decrypted_data = crypto.decrypt(encrypted_data, nonce)
                    message = json.loads(decrypted_data.decode())

                    # Check if it's a completion signal
                    if message.get("status") == "completed":
                        # Receiver confirmed successful completion
                        completion_received = True
                        log_warning(f"Sender: Completion signal received after {time.time() - completion_start_time:.1f}s")
                        break

                    # Otherwise, treat as retry request
                    retry_request = message
                except:
                    # If decryption fails, skip this message
                    continue
                
                failed_files = retry_request.get('failed_files', [])
                attempt = retry_request.get('attempt', 1)

                safe_print(f"\nRetry attempt {attempt}: Resending {len(failed_files)} failed files...")

                # Resend failed files
                retry_file_hashes = {}
                for failed_filename in failed_files:
                    if failed_filename in file_hashes:
                        safe_print(f"Resending: {failed_filename}")
                        
                        # Find and resend the file from files list
                        for file_info in files:
                            if file_info['path'] == failed_filename:
                                # Find the actual file path based on the original source
                                actual_file_path = None
                                for file_path in file_paths:
                                    if os.path.isfile(file_path):
                                        if os.path.basename(file_path) == failed_filename:
                                            actual_file_path = file_path
                                            break
                                    else:
                                        # Search in directory
                                        for root, dirs, dir_files in os.walk(file_path):
                                            for dir_file in dir_files:
                                                full_path = os.path.join(root, dir_file)
                                                relative_path = os.path.relpath(full_path, file_path)
                                                if relative_path == failed_filename:
                                                    actual_file_path = full_path
                                                    break
                                            if actual_file_path:
                                                break
                                
                                if actual_file_path:
                                    retry_file_hashes[failed_filename] = send_single_file(client_socket, crypto, actual_file_path, failed_filename, use_compression)
                                break
                
                # Send retry file hashes
                retry_hash_data = json.dumps(retry_file_hashes).encode()
                retry_nonce_hash = secrets.token_bytes(12)
                retry_encrypted_hashes = crypto.encrypt(retry_hash_data, retry_nonce_hash)
                client_socket.send(len(retry_nonce_hash).to_bytes(4, 'big'))
                client_socket.send(retry_nonce_hash)
                client_socket.send(len(retry_encrypted_hashes).to_bytes(4, 'big'))
                client_socket.send(retry_encrypted_hashes)
                
                # Send retry end marker
                client_socket.send(b'\x00\x00\x00\x00')

                safe_print(f"Retry attempt {attempt} completed")
            except socket.timeout:
                # Timeout waiting for completion signal
                # Log this but don't treat as error - receiver may have finished successfully
                log_warning(f"Sender: Timeout waiting for completion signal after {time.time() - completion_start_time:.1f}s")
                # Close socket immediately so receiver gets clear error if trying to send
                try:
                    client_socket.shutdown(socket.SHUT_RDWR)
                except (OSError, AttributeError):
                    pass  # Socket may already be closed
                break
            except (ConnectionError, ConnectionResetError, OSError) as e:
                # Connection closed by receiver
                # ConnectionError (including "Socket connection broken") is normal
                # errno 54 is ECONNRESET on macOS/BSD
                if isinstance(e, OSError) and hasattr(e, 'errno') and e.errno not in (None, 54):
                    # Re-raise only if it's an unexpected OSError
                    raise
                log_warning(f"Sender: Connection closed by receiver (completion_received={completion_received})")
                break

        # Stop progress thread
        stop_progress.set()
        progress_thread.join(timeout=1.0)

        # Calculate and show completion
        total_time = time.time() - start_time
        avg_speed = calculate_speed(original_bytes_processed, total_time)
        avg_speed_str = format_speed(avg_speed)

        # Health check stdout before final message
        try:
            sys.stdout.write('')
            sys.stdout.flush()
        except (BrokenPipeError, IOError, OSError):
            # stdout is broken - log and exit gracefully
            log_warning(f"Transfer complete but stdout unavailable (avg: {avg_speed_str})")
            sys.exit(0)

        # Display completion message based on whether we received confirmation
        if completion_received:
            log_warning(f"Sender: Transfer confirmed complete by receiver (total time: {total_time:.1f}s)")
            safe_print(f"\nTransfer complete! (avg: {avg_speed_str})")
        else:
            # No completion signal received - warn user
            log_warning(f"Sender: No completion signal received (total time: {total_time:.1f}s)")
            safe_print(f"\nData sent (avg: {avg_speed_str})")
            safe_print("Note: Receiver may still be processing. Check receiver status.")
        
    except socket.timeout:
        safe_print("Error: Connection timeout - no receiver connected")
    except OSError as e:
        if e.errno == 24:  # "Too many open files"
            safe_print("Error: Too many open files - system file descriptor limit exceeded")
            safe_print("This typically happens when reading very large numbers of files.")
            safe_print("Try transferring fewer files at once or increase system limits.")
        elif e.errno == 28:  # "No space left on device"
            safe_print("Error: No space left on device")
            safe_print("The system has run out of disk space for temporary operations.")
        else:
            safe_print(f"Error: System error during transfer: {e}")
    except Exception as e:
        # Handle blosc compression errors specifically
        if 'blosc_extension.error' in str(type(e)):
            safe_print(f"Error: Data compression failed: {e}")
            safe_print("This may indicate system resource issues or corrupted source files.")
        elif isinstance(e, json.JSONDecodeError):
            safe_print(f"Error: Data encoding failed: {e}")
            safe_print("This may indicate corrupted metadata or system issues.")
        else:
            safe_print(f"Error during transfer: {e}")
            safe_print(f"Error type: {type(e).__name__}")
            if hasattr(e, 'errno'):
                safe_print(f"Error code: {e.errno}")
    except KeyboardInterrupt:
        safe_print("\nTransfer interrupted by user")
    finally:
        # Stop progress thread if it exists
        if 'stop_progress' in locals():
            stop_progress.set()
        if 'progress_thread' in locals():
            progress_thread.join(timeout=1.0)

        # Gracefully shutdown sockets before closing
        try:
            if 'client_socket' in locals():
                client_socket.shutdown(socket.SHUT_RDWR)
        except (OSError, AttributeError):
            pass  # Socket may already be closed
        server_socket.close()


def receive_files(connection_string: str, output_dir: str = '.', pod: bool = False):
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
        print("Connecting to sender... ", end="")
        client_socket.connect((ip, TRANSFER_PORT))

        # Enable TCP_NODELAY for lower latency (disable Nagle's algorithm)
        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

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
        
        # Calculate uncompressed total for debugging large transfers
        uncompressed_total = sum(file_info['size'] for file_info in files_info)
        if is_compressed and file_count > 10000:
            compression_ratio = uncompressed_total / total_size if total_size > 0 else 1
        
        # Check for potential resource issues
        ResourceMonitor.check_fd_usage(file_count)
        
        # Initialize transfer lock manager for automatic resume detection
        lock_manager = TransferLockManager(working_dir=output_dir)
        lock_manager.handle_stale_locks()  # Clean up old locks first
        
        # Check for existing lock file and get resume plan
        has_existing_lock = lock_manager.load_existing_lock()
        overwrite_mode = False
        
        if has_existing_lock:
            resume_plan = lock_manager.get_resume_plan(files_info)
            if resume_plan["action"] == "resume":
                completed_count = len(resume_plan["completed_files"])
                resume_count = len(resume_plan["resume_files"])
                fresh_count = len(resume_plan["fresh_files"])
                
                # Ask user if they want to resume (default: yes)
                response = input(f"Resume transfer? ({completed_count} completed, {resume_count} partial, {fresh_count} fresh files) [Y/n]: ").strip().lower()
                if response == 'n' or response == 'no':
                    # User declined resume - clear lock and fall through to fresh transfer logic
                    has_existing_lock = False
                    lock_manager.cleanup_on_completion()
        
        if not has_existing_lock:
            # Create new lock file
            sender_ip = ip
            lock_manager.create_lock_file(sender_ip, files_info, total_size)
            resume_plan = {"action": "fresh_transfer", "completed_files": [], "resume_files": [], "fresh_files": files_info}

            # OPTIMIZATION: Smart conflict detection - skip when safe
            if should_skip_conflict_detection(has_existing_lock, resume_plan, output_dir, len(files_info)):
                conflicts = []
                # For very large transfers (>5K files), show warning about overwrites
                if len(files_info) > 5000:
                    safe_print(f"Large transfer detected ({len(files_info):,} files). Existing files will be overwritten.")
                    overwrite_mode = True
            else:
                # For fresh transfers with potential conflicts, check and ask user
                conflicts = detect_existing_conflicts(files_info, output_dir)
                if conflicts:
                    response = input("Existing files/folders will be overwritten. Continue? [Y/n]: ").strip().lower()
                    if response == 'n' or response == 'no':
                        print("Transfer cancelled to avoid overwriting existing files")
                        sys.exit(0)
                    else:
                        overwrite_mode = True
        
        # OPTIMIZATION Phase 3: Lazy FileWriter creation
        # Build resume bytes dict for lazy initialization (O(1) lookups)
        resume_bytes_dict = {}
        completed_set = set()
        if has_existing_lock:
            resume_bytes_dict = {f: b for f, b in resume_plan.get("resume_files", [])}
            completed_set = set(resume_plan.get("completed_files", []))

        # Filter out unsafe filenames upfront
        safe_files_info = []
        for file_info in files_info:
            filename = file_info['filename']
            if os.path.isabs(filename) or ".." in filename:
                log_warning(f"Skipping unsafe filename: {filename}")
                print(f"\nWarning: Skipping unsafe filename: {filename}")
                continue

            # Mark completed files in resume dict
            if filename in completed_set:
                resume_bytes_dict[filename] = file_info['size']

            safe_files_info.append(file_info)

        # Create LazyFileWriterDict - FileWriters created on-demand as chunks arrive
        file_writers = LazyFileWriterDict(
            safe_files_info,
            resume_bytes_dict,
            output_dir,
            lock_manager,
            overwrite_mode
        )

        # Send RECEIVER_READY signal to sender after setup is complete
        ready_signal = b'READY'
        client_socket.send(len(ready_signal).to_bytes(4, 'big'))
        client_socket.send(ready_signal)

        # Use 5 minute timeout to detect true stalls (instead of infinite blocking)
        client_socket.settimeout(300)

        # Receive streaming data with incremental saving
        stream_position = 0  # Tracks uncompressed data position in the stream
        total_bytes_received = 0  # Tracks compressed bytes received from network
        total_compressed_bytes_received = 0  # Tracks actual compressed data received
        start_time = time.time()

        # OPTIMIZATION: Setup background progress thread with real initial data
        # Initialize with first file data to avoid empty state display
        first_file = safe_files_info[0] if safe_files_info else None
        progress_state = {
            'filename': first_file['filename'] if first_file else '',
            'file_size': first_file['size'] if first_file else 0,
            'bytes_transferred': 0,
            'total_size': uncompressed_total,
            'action': 'Receiving',
            'start_time': start_time,
            'last_update_time': start_time,
            'last_update_bytes': 0,
            'warmup_period': True,  # Use cumulative speed for first 5 seconds
            'stream_position': 0  # Track position for stall recovery
        }

        # Setup stall detection and recovery
        stall_event = threading.Event()
        resend_count = {'value': 0}  # Track RESEND attempts
        MAX_RESEND_ATTEMPTS = 3

        def handle_stall(stream_position):
            """Called by progress thread when stall detected"""
            if resend_count['value'] < MAX_RESEND_ATTEMPTS:
                log_warning(f"Receiver: Triggering stall recovery at position {stream_position}")
                stall_event.set()
            else:
                log_warning(f"Receiver: Maximum RESEND attempts ({MAX_RESEND_ATTEMPTS}) reached, giving up")
                stop_progress.set()

        stop_progress = threading.Event()
        progress_thread = threading.Thread(
            target=progress_update_thread,
            args=(progress_state, stop_progress, None),  # Disable RESEND mechanism to prevent deadlock
            daemon=True
        )
        progress_thread.start()

        try:
            # Receive all streaming data chunks
            while True:
                # Check if stall event is set (triggered by progress thread)
                if stall_event.is_set():
                    stall_event.clear()
                    current_position = progress_state.get('stream_position', stream_position)
                    send_resend_request(client_socket, crypto, current_position, resend_count['value'])
                    resend_count['value'] += 1
                    progress_state['stall_recovery_in_progress'] = False
                    log_warning(f"Receiver: Sent RESEND request #{resend_count['value']} for position {current_position}")

                # Check for hashes marker (indicates data stream is complete)
                nonce_len_bytes = recv_all(client_socket, 4)
                if nonce_len_bytes == b'\x00\x00\x00\x00':
                    break
                    
                nonce_len = int.from_bytes(nonce_len_bytes, 'big')
                chunk_nonce = recv_all(client_socket, nonce_len)
                chunk_len = int.from_bytes(recv_all(client_socket, 4), 'big')
                encrypted_chunk = recv_all(client_socket, chunk_len)
                
                # Decrypt the chunk
                decrypted_data = crypto.decrypt(encrypted_chunk, chunk_nonce)
                
                # Track compressed data received (for determining when we're done with file data)
                total_compressed_bytes_received += len(encrypted_chunk)
                
                # More robust hash data detection
                is_hash_data = False
                
                # Try to detect if this chunk is hash data (always uncompressed JSON)
                try:
                    potential_hash = json.loads(decrypted_data.decode('utf-8'))
                    if isinstance(potential_hash, dict) and all(isinstance(k, str) for k in potential_hash.keys()):
                        # This looks like hash data (dictionary with string keys)
                        file_hashes = potential_hash
                        is_hash_data = True
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Not JSON, must be compressed file data
                    pass
                
                # If not hash data, process as file data
                if not is_hash_data:
                    # Decompress if needed
                    if is_compressed:
                        try:
                            chunk = blosc.decompress(decrypted_data)
                        except Exception as e:
                            # If decompression fails, this might be hash data incorrectly detected as file data
                            if 'blosc_extension.error' in str(type(e)):
                                try:
                                    # Try to parse as hash data
                                    potential_hash = json.loads(decrypted_data.decode('utf-8'))
                                    if isinstance(potential_hash, dict) and all(isinstance(k, str) for k in potential_hash.keys()):
                                        # This looks like file hash data (string keys)
                                        file_hashes = potential_hash
                                        is_hash_data = True
                                        print(f"\nDetected hash data after decompression failure (compressed data tracking: {total_compressed_bytes_received}/{total_size} bytes)")
                                    else:
                                        raise e  # Re-raise if not valid hash data
                                except (json.JSONDecodeError, UnicodeDecodeError):
                                    print(f"\nDecompression failed and data is not valid JSON. Compressed bytes received: {total_compressed_bytes_received}/{total_size}")
                                    raise e  # Re-raise original decompression error
                            else:
                                raise e
                    else:
                        chunk = decrypted_data
                
                # If this was hash data, we're done with file data
                if is_hash_data:
                    break
                
                # Write to appropriate files incrementally
                chunk_offset = 0
                while chunk_offset < len(chunk):
                    remaining_chunk = chunk[chunk_offset:]
                    bytes_written = 0

                    # Find which file needs data at this stream position (O(N) but no writer creation)
                    writer = file_writers.get_writer_at_offset(stream_position + chunk_offset)
                    if writer and writer.needs_data(stream_position + chunk_offset):
                        bytes_written = writer.write_chunk(remaining_chunk)

                    if bytes_written == 0:
                        # No file needed this data, advance position
                        chunk_offset = len(chunk)
                    else:
                        chunk_offset += bytes_written
                
                stream_position += len(chunk)
                total_bytes_received += len(chunk)

                # Update progress state (background thread will display it)
                progress_state['bytes_transferred'] = total_bytes_received
                progress_state['stream_position'] = stream_position  # For stall recovery

                # Update current filename for display
                current_file = get_current_file_info(stream_position, files_info)
                if current_file:
                    progress_state['filename'] = current_file['filename']
                    progress_state['file_size'] = current_file['size']
                else:
                    progress_state['filename'] = 'multiple files'
                    progress_state['file_size'] = total_size
        
        finally:
            # Always close file handles (only created writers)
            for writer in file_writers.values():
                writer.close()

        # Log timing: receiver finished receiving all data
        data_receive_time = time.time() - start_time
        log_warning(f"Receiver: All data received (time: {data_receive_time:.1f}s, bytes: {total_bytes_received})")

        # Verify file integrity and collect any failures
        # Display progress during verification since this can take time for many files
        print("\n\nVerifying file integrity...")
        verification_start_time = time.time()

        # Only verify created writers (files that were actually transferred)
        created_writers = list(file_writers.values())
        log_warning(f"Receiver: Starting hash verification for {len(created_writers)} files")
        received_files = []
        failed_files = []
        total_files = len(created_writers)

        for idx, writer in enumerate(created_writers, 1):
            # Display verification progress every 10 files or on first/last file
            if idx == 1 or idx == total_files or idx % 10 == 0:
                progress_pct = (idx / total_files) * 100
                print(f"\rVerifying: {idx}/{total_files} ({progress_pct:.1f}%) - {writer.filename[:50]}...", end='', flush=True)

            # Ensure all files are completed
            if not writer.is_complete:
                writer.complete_file()

            # Verify file integrity
            expected_hash = file_hashes.get(writer.filename)
            if expected_hash:
                received_hash = writer.get_hash()
                if received_hash != expected_hash:
                    failed_files.append({
                        'filename': writer.filename,
                        'expected_hash': expected_hash,
                        'received_hash': received_hash,
                        'writer': writer
                    })
                    continue  # Skip adding to received_files
            
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
                        log_warning(f"Could not locate final file for {writer.filename}")
                        break

        # Clear verification progress line
        print("\r" + " " * 100 + "\r", end='', flush=True)

        # Log timing: hash verification complete
        verification_time = time.time() - verification_start_time
        log_warning(f"Receiver: Hash verification complete (time: {verification_time:.1f}s, failed: {len(failed_files)})")

        if failed_files:
            print(f"Verification complete: {len(failed_files)} file(s) failed integrity check")
        else:
            print(f"Verification complete: All {total_files} file(s) passed integrity check")

        # Handle integrity check failures with retry mechanism
        retry_attempt = 0
        
        while retry_attempt < MAX_RETRY_ATTEMPTS and failed_files:
            if retry_attempt == 0:
                print(f"\nIntegrity check failed for {len(failed_files)} file(s):")
                for failure in failed_files:
                    print(f"  {failure['filename']}")
                    print(f"    Expected: {failure['expected_hash']}")
                    print(f"    Received: {failure['received_hash']}")
            
            # If this is the last retry attempt, report final failure
            if retry_attempt >= MAX_RETRY_ATTEMPTS - 1:
                print(f"\nFile integrity check failed after {MAX_RETRY_ATTEMPTS} attempts:")
                for failed_file in failed_files:
                    print(f"  - {failed_file['filename']}")
                sys.exit(1)
            
            # Send retry request to sender
            retry_attempt += 1
            failed_filenames = [f['filename'] for f in failed_files]
            
            print(f"\nRetry attempt {retry_attempt}: Requesting resend of {len(failed_files)} failed files...")
            
            retry_request = json.dumps({
                'type': 'retry_request',
                'failed_files': failed_filenames,
                'attempt': retry_attempt
            }).encode()
            
            # Send retry request
            client_socket.send(len(retry_request).to_bytes(4, 'big'))
            client_socket.send(retry_request)
            
            # Reset failed file writers for retry
            for failed_file in failed_files:
                writer = failed_file['writer']
                # Reset the writer for the retry
                writer.reset_for_retry()
                writer.open_for_writing()
            
            # Receive retry data using existing streaming protocol
            print("Receiving retry files...")
            
            # Process retry stream similar to main transfer
            compressed_bytes_received = 0
            
            while True:
                try:
                    # Receive chunk
                    nonce_len_bytes = recv_all(client_socket, 4)
                    if nonce_len_bytes == b'\x00\x00\x00\x00':
                        break
                    
                    nonce_len = int.from_bytes(nonce_len_bytes, 'big')
                    nonce = recv_all(client_socket, nonce_len)
                    chunk_len = int.from_bytes(recv_all(client_socket, 4), 'big')
                    encrypted_chunk = recv_all(client_socket, chunk_len)
                    
                    # Decrypt chunk
                    compressed_chunk = crypto.decrypt(encrypted_chunk, nonce)
                    compressed_bytes_received += len(compressed_chunk)
                    
                    # Check if this might be hash data instead of file data
                    if compressed_bytes_received > total_size:
                        # This is likely hash data - decrypt and parse
                        try:
                            hash_data = crypto.decrypt(encrypted_chunk, nonce)
                            retry_file_hashes = json.loads(hash_data.decode())
                            # Update file_hashes with retry hashes
                            file_hashes.update(retry_file_hashes)
                            break
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            # Not hash data, continue as file data
                            pass
                    
                    # Decompress chunk
                    chunk = blosc.decompress(compressed_chunk)
                    
                    # Write chunk to appropriate failed file writers only
                    current_position = 0
                    for failed_file in failed_files:
                        writer = failed_file['writer']
                        if not writer.is_complete:
                            file_info = next(f for f in files_info if f['path'] == writer.filename)
                            file_size = file_info['size']
                            
                            bytes_needed = file_size - writer.written
                            bytes_to_write = min(bytes_needed, len(chunk) - current_position)
                            
                            if bytes_to_write > 0:
                                writer.write(chunk[current_position:current_position + bytes_to_write])
                                current_position += bytes_to_write
                                
                                if writer.written >= file_size:
                                    writer.complete_file()
                                    
                except Exception as e:
                    if 'blosc_extension.error' in str(type(e)):
                        # This might be hash data
                        try:
                            hash_data = crypto.decrypt(encrypted_chunk, nonce)
                            retry_file_hashes = json.loads(hash_data.decode())
                            file_hashes.update(retry_file_hashes)
                            break
                        except:
                            pass
                    else:
                        break
            
            print(f"Retry attempt {retry_attempt} completed. Verifying integrity...")
            
            # Re-verify integrity for failed files
            new_failed_files = []
            for failed_file in failed_files:
                writer = failed_file['writer']
                expected_hash = failed_file['expected_hash']
                received_hash = writer.get_hash()
                
                if received_hash != expected_hash:
                    new_failed_files.append(failed_file)
                else:
                    print(f"  ✓ {writer.filename} integrity check passed")
            
            failed_files = new_failed_files
            
            if not failed_files:
                print(f"All files passed integrity check on retry attempt {retry_attempt}")
                break
        
        # Calculate and show completion
        total_time = time.time() - start_time
        avg_speed = calculate_speed(total_bytes_received, total_time)
        avg_speed_str = format_speed(avg_speed)
        
        # Clean up lock file on successful completion
        if lock_manager:
            lock_manager.cleanup_on_completion()

        # Flush any pending lock file updates before completion
        if lock_manager:
            lock_manager.flush_pending_updates()

        # Send completion signal to sender before closing connection
        # This is CRITICAL to prevent sender from exiting before receiver is done
        completion_sent = False
        for attempt in range(3):  # Try up to 3 times
            try:
                completion_signal = json.dumps({
                    "status": "completed",
                    "message": "Transfer successful",
                    "completion_time": time.time()
                }).encode()
                completion_nonce = secrets.token_bytes(12)
                encrypted_completion = crypto.encrypt(completion_signal, completion_nonce)

                client_socket.send(len(completion_nonce).to_bytes(4, 'big'))
                client_socket.send(completion_nonce)
                client_socket.send(len(encrypted_completion).to_bytes(4, 'big'))
                client_socket.send(encrypted_completion)

                # Use shutdown to ensure data is flushed before close
                try:
                    client_socket.shutdown(socket.SHUT_WR)  # Signal we're done sending
                except OSError:
                    # Socket may already be closed by sender
                    pass

                completion_sent = True
                log_warning(f"Receiver: Completion signal sent successfully (attempt {attempt + 1})")
                break

            except (ConnectionError, BrokenPipeError, OSError) as e:
                # Connection may have been closed by sender
                log_warning(f"Receiver: Failed to send completion signal (attempt {attempt + 1}): {e}")
                if attempt < 2:  # Don't sleep on last attempt
                    time.sleep(0.1)  # Brief delay before retry
                continue

        if not completion_sent:
            log_warning("Receiver: Failed to send completion signal after 3 attempts")

        # Stop progress thread
        stop_progress.set()
        progress_thread.join(timeout=1.0)

        log_warning(f"Receiver: Transfer complete (total time: {total_time:.1f}s)")
        print(f"\nTransfer complete! (avg: {avg_speed_str})")
        
    except socket.timeout:
        print("Error: Connection timeout")
        sys.exit(1)
    except ConnectionRefusedError:
        print("Error: Connection refused - sender not available")
        sys.exit(1)
    except OSError as e:
        if e.errno == 24:  # "Too many open files"
            print("Error: Too many open files - system file descriptor limit exceeded")
            print("This typically happens with very large numbers of files.")
            print("The transfer uses lazy file opening, but system limits were still exceeded.")
            print("Try transferring fewer files at once or increase system limits.")
        elif e.errno == 28:  # "No space left on device"
            print("Error: No space left on device")
            print("The receiving device has run out of disk space.")
        else:
            print(f"Error: System error during transfer: {e}")
        
        # Cleanup partial files on error
        try:
            cleanup_count = 0
            for writer in file_writers:
                if writer.part_file.exists() and not writer.is_complete:
                    writer.part_file.unlink()
                    cleanup_count += 1
            if cleanup_count > 0:
                print(f"Cleaned up {cleanup_count} partial files")
        except:
            pass  # Don't let cleanup errors mask the original error
        
        sys.exit(1)
    except Exception as e:
        # Handle blosc decompression errors specifically
        if 'blosc_extension.error' in str(type(e)):
            print(f"Error: Data decompression failed: {e}")
            print("This indicates corrupted compressed data or protocol mismatch.")
            print("The sender may have sent hash data that was incorrectly processed as file data.")
        elif isinstance(e, json.JSONDecodeError):
            print(f"Error: JSON decoding failed: {e}")
            print("This may indicate network corruption or protocol issues.")
        elif 'InvalidTag' in str(type(e)) or type(e).__name__ == 'InvalidTag':
            print("Error: Authentication failed, check key")
            sys.exit(1)
        else:
            print(f"Error during transfer: {e}")
            print(f"Error type: {type(e).__name__}")
            if hasattr(e, 'errno'):
                print(f"Error code: {e.errno}")
        
        # Provide recovery suggestions
        print("\nRecovery suggestions:")
        print("1. Retry the transfer if partial files exist (automatic resume will be attempted)")
        print("2. Try transferring fewer files at once")
        print("3. Check network connectivity and stability")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nTransfer interrupted by user")
        # Partial files will remain for potential resume
        print("Partial files have been preserved for automatic resume on next transfer")
        sys.exit(1)
    except Exception as e:
        print(f"Error during transfer: {e}")
        # Provide more context for debugging
        print(f"Error type: {type(e).__name__}")
        if hasattr(e, 'errno'):
            print(f"Error code: {e.errno}")
        sys.exit(1)
    finally:
        # Stop progress thread if it exists
        if 'stop_progress' in locals():
            stop_progress.set()
        if 'progress_thread' in locals():
            progress_thread.join(timeout=1.0)

        # Gracefully shutdown socket before closing
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
        except (OSError, AttributeError):
            pass  # Socket may already be closed or shutdown
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
    
    # Receive command
    receive_parser = subparsers.add_parser('receive', help='Receive files')
    receive_parser.add_argument('connection', help='Connection string: ip:token')
    receive_parser.add_argument('-o', '--output-dir', default='.', help='Output directory for received files (default: current directory)')
    receive_parser.add_argument('--pod', action='store_true', help='Accept connections from localhost (127.0.0.1) for containerized environments')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'send':
        send_files(args.files, pod=args.pod)
    elif args.command == 'receive':
        receive_files(args.connection, output_dir=args.output_dir, pod=args.pod)


if __name__ == "__main__":
    main()