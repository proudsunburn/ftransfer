# Utility Functions

Helper functions for file operations, network communication, speed calculation, and data validation.

## Functions

### Console & Output Handling
- **[safe_print()](#safe_print)** - Print with protection against stdout failures (BrokenPipeError, IOError)
- **[safe_flush()](#safe_flush)** - Safely flush stdout, catching any errors
- **[handle_sigpipe()](#handle_sigpipe)** - Handle SIGPIPE (broken pipe) gracefully
- **[handle_sighup()](#handle_sighup)** - Handle SIGHUP (hangup) gracefully

### File & Network Operations
- **[recv_all()](recv_all.md)** - Reliable socket data reception
- **[validate_files()](validate_files.md)** - File path validation and verification
- **[collect_files_recursive()](collect_files_recursive.md)** - Recursive directory traversal
- **[log_warning()](log_warning.md)** - Silent warning logging system
- **[detect_existing_conflicts()](#detect_existing_conflicts)** - Detect file/folder conflicts before transfer

### Crypto & Security
- **[crypto_init()](crypto_init.md)** - SecureCrypto initialization
- **[derive_session_key()](derive_session_key.md)** - ECDH key derivation
- **[encrypt()](encrypt.md)** - ChaCha20Poly1305 encryption
- **[decrypt()](decrypt.md)** - ChaCha20Poly1305 decryption
- **[get_public_key_bytes()](get_public_key_bytes.md)** - Public key serialization
- **[generate_token()](generate_token.md)** - Secure token generation
- **[get_tailscale_ip()](get_tailscale_ip.md)** - Local Tailscale IP detection
- **[verify_peer_ip_cached()](verify_peer_ip_cached.md)** - Peer verification with caching

### Performance & Progress
- **[calculate_speed()](calculate_speed.md)** - Transfer speed calculation
- **[format_speed()](format_speed.md)** - Human-readable speed formatting
- **[calculate_eta()](#calculate_eta)** - Estimated time to completion
- **[calculate_smoothed_speed()](#calculate_smoothed_speed)** - Smoothed speed using moving average
- **[calculate_smoothed_eta()](#calculate_smoothed_eta)** - ETA with smoothing to prevent dramatic increases
- **[format_eta()](#format_eta)** - Format ETA for display as MM:SS or HH:MM:SS
- **[format_size()](#format_size)** - Format file size for human-readable display
- **[get_current_file_info()](#get_current_file_info)** - Get information about file at stream position
- **[print_transfer_progress()](#print_transfer_progress)** - Three-line progress display with file info and warnings

---

## Console & Output Handling

### safe_print()

**Recent Addition:** Commit 091a75d (Nov 12, 2025) - Critical bugfix for background/daemon operation

Print with protection against stdout failures (BrokenPipeError, IOError).

**Signature:**
```python
def safe_print(*args, **kwargs)
```

**Purpose:**
Handles terminal disconnect scenarios gracefully. When stdout is broken (remote terminal disconnect, pipe closure), falls back to stderr and file logging instead of crashing.

**Parameters:**
- `*args` - Arguments to print (same as built-in `print()`)
- `**kwargs` - Keyword arguments (same as built-in `print()`)

**Behavior:**
1. Attempts normal `print()` to stdout
2. If `flush=True` or custom `end`, explicitly flushes to detect broken pipes early
3. On BrokenPipeError/IOError/OSError:
   - Falls back to stderr
   - Logs to `transfer_warnings.log`
   - If message contains "complete", exits gracefully (transfer done)

**Use Cases:**
- Background transfers where terminal may disconnect
- Daemon-like operations
- Remote SSH sessions that may drop
- Piped output that may close

**Example:**
```python
# Instead of:
print("Transfer complete!")  # May crash on broken pipe

# Use:
safe_print("Transfer complete!")  # Gracefully handles broken pipe
```

---

### safe_flush()

Safely flush stdout, catching any errors.

**Signature:**
```python
def safe_flush()
```

**Purpose:**
Flushes stdout without raising exceptions on broken pipes or closed terminals.

**Behavior:**
- Attempts `sys.stdout.flush()`
- Catches and suppresses BrokenPipeError, IOError, OSError
- Silent failure (no-op if stdout broken)

**Use Cases:**
- Forcing output before long operations
- Ensuring progress updates are visible
- Pre-disconnect cleanup

---

### handle_sigpipe()

Handle SIGPIPE (broken pipe) signal gracefully.

**Signature:**
```python
def handle_sigpipe(signum, frame)
```

**Purpose:**
Signal handler for SIGPIPE (sent when writing to broken pipe). Ensures graceful exit instead of crash.

**Parameters:**
- `signum` (int) - Signal number (13 for SIGPIPE)
- `frame` - Current stack frame

**Behavior:**
1. Logs "SIGPIPE received - terminal disconnected" to warnings
2. Exits cleanly with code 0

**Installation:**
```python
signal.signal(signal.SIGPIPE, handle_sigpipe)  # Unix/Linux/macOS only
```

**Platform Notes:**
- Not available on Windows (SIGPIPE doesn't exist)
- Automatically skipped on Windows via `try/except AttributeError`

---

### handle_sighup()

Handle SIGHUP (hangup) signal gracefully.

**Signature:**
```python
def handle_sighup(signum, frame)
```

**Purpose:**
Signal handler for SIGHUP (sent when controlling terminal closes). Ensures graceful exit.

**Parameters:**
- `signum` (int) - Signal number (1 for SIGHUP)
- `frame` - Current stack frame

**Behavior:**
1. Logs "SIGHUP received - terminal hung up" to warnings
2. Exits cleanly with code 0

**Installation:**
```python
signal.signal(signal.SIGHUP, handle_sighup)  # Unix/Linux/macOS
```

**Common Triggers:**
- SSH connection drops
- Terminal window closed
- Parent shell exits
- `nohup` scenarios

---

## File & Network Operations (New)

### detect_existing_conflicts()

Detect existing files/folders that would conflict with incoming transfer.

**Signature:**
```python
def detect_existing_conflicts(files_info: List[Dict]) -> List[str]
```

**Purpose:**
Prevents accidental overwrites by detecting conflicts before transfer starts. Prompts user for confirmation if conflicts found.

**Parameters:**
- `files_info` (List[Dict]) - List of file metadata dictionaries from sender

**Returns:**
- `List[str]` - List of conflicting file/folder paths

**Detection Logic:**
1. **Direct File Conflicts**: File with same name exists
2. **Directory Conflicts**: Directory with same name exists (shown with `/` suffix)
3. **Parent Directory Conflicts**: File exists where directory needs to be created

**Example:**
```python
files_info = [
    {'filename': 'document.pdf', 'size': 1234},
    {'filename': 'folder/file.txt', 'size': 567}
]

conflicts = detect_existing_conflicts(files_info)
# Returns: ['document.pdf', 'folder/'] if they exist
```

**Security:**
- Validates filename safety (no absolute paths, no `..`)
- Uses Path normalization for security

**User Interaction:**
If conflicts detected, prompts:
```
Warning: The following files/folders will be overwritten:
  - document.pdf
  - folder/
Continue? [Y/n]:
```

---

## Performance & Progress (New)

### calculate_eta()

Calculate estimated time to completion in seconds.

**Signature:**
```python
def calculate_eta(remaining_bytes: int, current_speed: float) -> int
```

**Parameters:**
- `remaining_bytes` (int) - Bytes remaining to transfer
- `current_speed` (float) - Current transfer speed in bytes/second

**Returns:**
- `int` - Estimated seconds to completion (0 if speed ≤ 0 or remaining ≤ 0)

**Example:**
```python
eta = calculate_eta(1048576, 131072)  # 1 MB remaining at 128 KB/s
# Returns: 8 (seconds)
```

---

### calculate_smoothed_speed()

Calculate smoothed speed using weighted moving average of recent measurements.

**Signature:**
```python
def calculate_smoothed_speed(recent_speeds: list, current_bytes: int,
                            elapsed_time: float) -> float
```

**Purpose:**
Prevents speed display from jumping erratically by smoothing recent measurements.

**Parameters:**
- `recent_speeds` (list) - List of recent speed measurements (modified in-place)
- `current_bytes` (int) - Total bytes transferred so far
- `elapsed_time` (float) - Total elapsed time in seconds

**Returns:**
- `float` - Smoothed speed in bytes/second

**Algorithm:**
1. Calculate current speed: `current_bytes / elapsed_time`
2. Add to recent_speeds list (keeps last 15 measurements)
3. Apply exponential weighting favoring recent values: `weight = (i + 1) ** 1.5`
4. Return weighted average

**Benefits:**
- Reduces speed fluctuations
- More stable progress display
- Recent measurements weighted higher (responsive to changes)

**Example:**
```python
recent_speeds = []
speed = calculate_smoothed_speed(recent_speeds, 1048576, 8.0)
# Returns smoothed speed, adds to recent_speeds for next call
```

---

### calculate_smoothed_eta()

Calculate ETA with smoothing to prevent dramatic increases.

**Signature:**
```python
def calculate_smoothed_eta(remaining_bytes: int, smoothed_speed: float,
                          previous_eta: int, progress_percent: float) -> int
```

**Purpose:**
Prevents ETA from jumping dramatically (especially increases) for better UX.

**Parameters:**
- `remaining_bytes` (int) - Bytes remaining
- `smoothed_speed` (float) - Already-smoothed speed
- `previous_eta` (int) - Previous ETA value
- `progress_percent` (float) - Current progress percentage (0-100)

**Returns:**
- `int` - Smoothed ETA in seconds

**Adaptive Smoothing:**
- **Early in transfer (< 10%)**: `smoothing_factor = 0.3` (allow more variation)
- **Mid transfer (10-90%)**: `smoothing_factor = 0.5` (moderate smoothing)
- **Late in transfer (> 90%)**: `smoothing_factor = 0.7` (heavy smoothing)

**ETA Increase Caps:**
- Maximum increase: 20% of previous ETA or 10 seconds (whichever is larger)
- Prevents dramatic ETA jumps that frustrate users

**Example:**
```python
eta = calculate_smoothed_eta(524288, 65536, 10, 75.0)
# Returns smoothed ETA, capping dramatic increases
```

---

### format_eta()

Format ETA for display as MM:SS or HH:MM:SS.

**Signature:**
```python
def format_eta(seconds: int) -> str
```

**Parameters:**
- `seconds` (int) - ETA in seconds

**Returns:**
- `str` - Formatted ETA string

**Format Logic:**
- **< 1 hour**: `MM:SS` (e.g., "05:42")
- **≥ 1 hour**: `HH:MM:SS` (e.g., "01:23:45")
- **≤ 0**: `"00:00"`

**Examples:**
```python
format_eta(342)   # Returns: "05:42"
format_eta(5025)  # Returns: "01:23:45"
format_eta(0)     # Returns: "00:00"
```

---

### format_size()

Format file size for human-readable display.

**Signature:**
```python
def format_size(size: int) -> str
```

**Parameters:**
- `size` (int) - File size in bytes

**Returns:**
- `str` - Human-readable size string

**Format Logic:**
- **< 1024**: `X B`
- **< 1 MB**: `X.X KB`
- **< 1 GB**: `X.X MB`
- **≥ 1 GB**: `X.X GB`

**Examples:**
```python
format_size(512)        # Returns: "512 B"
format_size(1536)       # Returns: "1.5 KB"
format_size(2097152)    # Returns: "2.0 MB"
format_size(3221225472) # Returns: "3.0 GB"
```

---

### get_current_file_info()

Get information about the file currently being processed at stream position.

**Signature:**
```python
def get_current_file_info(stream_position: int,
                         files_metadata: List[Dict]) -> Optional[Dict]
```

**Purpose:**
Determines which file is being transferred at a specific position in the unified stream.

**Parameters:**
- `stream_position` (int) - Current position in transfer stream
- `files_metadata` (List[Dict]) - List of file metadata with 'offset' and 'size'

**Returns:**
- `Dict` - File metadata dictionary if found
- `None` - If no file matches the position

**Example:**
```python
files_metadata = [
    {'filename': 'file1.txt', 'offset': 0, 'size': 1000},
    {'filename': 'file2.txt', 'offset': 1000, 'size': 2000}
]

file_info = get_current_file_info(1500, files_metadata)
# Returns: {'filename': 'file2.txt', 'offset': 1000, 'size': 2000}
```

---

### print_transfer_progress()

Print three-line progress display with file info, progress, and warnings.

**Signature:**
```python
def print_transfer_progress(filename: str, file_size: int,
                           progress_percent: float, speed_str: str,
                           eta_str: str, is_first_update: bool,
                           action: str = "Transferring",
                           warning_msg: str = "")
```

**Purpose:**
Clean, minimal three-line progress display with in-place updating.

**Parameters:**
- `filename` (str) - Current file being processed
- `file_size` (int) - Size of current file
- `progress_percent` (float) - Overall progress percentage
- `speed_str` (str) - Formatted speed string
- `eta_str` (str) - Formatted ETA string
- `is_first_update` (bool) - Whether this is first update (don't move cursor)
- `action` (str) - Action verb (default: "Transferring")
- `warning_msg` (str) - Optional warning to display on line 3

**Display Format:**
```
Transferring: document.pdf (15.8 MB)
Progress: 45.2% | Speed: 2.1 MB/s | ETA: 00:03
[Warning messages or blank line]
```

**Features:**
- **In-Place Updates**: Uses ANSI escape codes to overwrite previous output
- **Line Clearing**: `\033[K` clears to end of line (prevents artifacts)
- **Cursor Movement**: `\033[2A` moves cursor up 2 lines for updates
- **Safe Output**: Uses `safe_print()` for broken pipe protection

**Example:**
```python
print_transfer_progress(
    filename="document.pdf",
    file_size=16588800,
    progress_percent=45.2,
    speed_str="2.1 MB/s",
    eta_str="00:03",
    is_first_update=False,
    action="Receiving",
    warning_msg="Warning: Low disk space"
)
```