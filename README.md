# Secure File Transfer

A simple, secure file transfer tool for Tailscale networks. Transfer files and folders between computers with end-to-end encryption and automatic key exchange.

## Features

- **Secure**: ChaCha20Poly1305 encryption with X25519 key exchange
- **Simple**: Clean two-command interface with minimal output
- **Safe**: Only works between verified Tailscale network peers
- **Fast**: High-performance streaming with optional Blosc+LZ4 compression
- **Reliable**: File integrity verification and progress indicators
- **Resumable**: Interrupted transfers automatically resume from last verified position
- **Memory Efficient**: Incremental file saving prevents RAM accumulation
- **Smart**: Automatically detects and offers to exclude virtual environments and cache folders
- **Easy**: Short connection strings with 2-word tokens

## Installation

### Recommended: Global Installation

Install using `uv tool` to make the `transfer` command available globally from any directory:

```bash
# Install globally (works anywhere, no venv needed)
cd /path/to/ftransfer
uv tool install .
```

After installation, the `transfer` command will be available from any directory without activating a virtual environment.

To update after changes:
```bash
uv tool install --reinstall .
```

To uninstall:
```bash
uv tool uninstall ftransfer
```

### Alternative Methods

**Using pipx** (if you prefer pipx over uv):
```bash
pipx install .
```

**Development installation** (in a virtual environment):
```bash
pip install -e .  # Requires venv activation
```

**Manual installation** (no package installation):

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make the script executable:
```bash
chmod +x transfer.py
```

Then use `./transfer.py` instead of `transfer` in the examples below.

## Usage

### Sending Files

Send one or more files or folders:
```bash
transfer send file1.txt folder2/ document.pdf
```

The program will output something like:
```
type into receiver: transfer receive 100.64.1.123:ocean-tiger
```

### Receiving Files

Copy the connection string from the sender and run:
```bash
transfer receive 100.64.1.123:ocean-tiger
```

Files will be saved to the current directory.

### Automatic Resume

Transfers automatically resume if interrupted. Simply run the same receive command again:
```bash
transfer receive 100.64.1.123:ocean-tiger
```

The receiver will automatically detect `.part` files and lock files, then resume from the last verified position.

### Virtual Environment Detection

The program automatically detects virtual environment and cache directories and asks if you want to exclude them:
```bash
transfer send my_project/
# Output: Found virtual environment/cache directories: venv, __pycache__, node_modules. Skip? [Y/n]:
```

Detects: `venv`, `node_modules`, `__pycache__`, `.cache`, `.git`, and other common development cache directories.

## Security

- **Encryption**: All data is encrypted with ChaCha20Poly1305
- **Authentication**: Shared secret prevents unauthorized connections
- **Key Exchange**: Ephemeral X25519 keys for each session
- **Network Security**: Only accepts Tailscale connections
- **File Safety**: Path traversal protection during file saving
- **Integrity**: SHA-256 checksums verify file integrity

## Requirements

- Python 3.7 or later
- Tailscale installed and running
- Network connectivity between sender and receiver

## How It Works

1. **Sender** prepares files with optional Blosc+LZ4 compression (user prompted)
2. **Simple token** generated using cryptographically secure randomness (2 words from 200+ vocabulary)
3. **Secure connection** established over Tailscale with key exchange
4. **Authentication** using the shared token prevents unauthorized access
5. **Encrypted transfer** with clean progress indicators
6. **Incremental save** with `.part` files and automatic resume using hash verification

## Interface

**Clean, minimal output with real-time progress:**
```bash
# Sending
type into receiver: transfer.py receive 100.101.29.44:forest-piano
Waiting for receiver to connect...
Transferring: document.pdf (15.8 MB)
Progress: 45.2% | Speed: 2.1 MB/s | ETA: 00:03
Transfer complete! (avg: 2.3 MB/s)

# Receiving
Receiving 1 file(s) (1234567 bytes total)
Receiving: document.pdf (15.8 MB)
Progress: 78.4% | Speed: 1.8 MB/s | ETA: 00:01
Transfer complete! (avg: 2.0 MB/s)

# Automatic Resume
Resuming document.pdf: 524288/1234567 bytes already written
Receiving 1 file(s) (1234567 bytes total)
Receiving: document.pdf (15.8 MB)
Progress: 42.5% | Speed: 1.2 MB/s | ETA: 00:07
Transfer complete! (avg: 1.5 MB/s)
```

## Advanced Usage

### High-Performance Streaming

Uses a unified streaming protocol with incremental file saving and optional Blosc+LZ4 compression:

- **Optional Blosc+LZ4 Compression**: Ultra-fast compression with 4-thread optimization (user prompted, default: No)
- **Incremental Saving**: Files written to disk as chunks arrive (no RAM accumulation)
- **Single-Pass I/O**: Files are read, optionally compressed, hashed, and streamed in one operation
- **Batch Metadata**: All file information sent upfront to reduce overhead
- **Optimized for Many Small Files**: 5-20x faster for Python libraries, virtual environments with compression
- **Memory Efficient**: Transfer size independent of available RAM

**Performance Benefits:**
- **Ultra-Fast Compression** (when enabled): Blosc+LZ4 provides >500 MB/s compression speed per core
- **Bandwidth Reduction** (when enabled): 30-80% smaller transfer sizes depending on file types
- **Single-Pass I/O**: Files read→hash→stream in one operation (50% I/O reduction)
- **Reduces Network Round-trips**: Batch metadata transmission (80-95% overhead reduction)
- **Multi-threaded Compression** (when enabled): 4-thread Blosc optimization maximizes CPU utilization
- **Prevents Memory Exhaustion**: Stream-to-disk architecture with controlled buffers
- **Automatic Resume**: Hash verification enables intelligent continuation from last verified position

```bash
# All transfers automatically use optimized streaming
transfer send document.pdf folder/ library.zip

# Memory usage stays constant regardless of transfer size
transfer send 10GB_dataset/
```

### Resume Capability

Interrupted transfers can be resumed without re-downloading completed portions:

- **Automatic Detection**: `.part` files created during active transfers
- **Hash Verification**: Partial files verified before resuming
- **Integrity Assured**: Final hash verification ensures complete accuracy
- **Network Resilient**: Resume works regardless of interruption cause

```bash
# Start transfer (creates .part files as it progresses)
transfer receive 100.64.1.123:ocean-tiger

# If interrupted, simply run the same command again - resume is automatic
transfer receive 100.64.1.123:ocean-tiger
# Output: "Resuming transfer: 1 completed, 0 partial, 0 fresh files"
```

### Smart Exclusions

Exclude common development folders that don't need transferring:

```bash
# Automatically detects and offers to exclude virtual environments and cache folders
transfer send my_python_project/
# Output: "Found virtual environment/cache directories: venv, __pycache__, node_modules. Skip? [Y/n]:"

# Can reduce transfer size by 80-95% for development projects
```

**Excluded Patterns:**
- Python: `venv`, `.venv`, `env`, `virtualenv`, `__pycache__`, `.pytest_cache`, `.tox`, `.coverage`
- Node.js: `node_modules`, `.npm`, `.yarn`
- Version Control: `.git`, `.svn`, `.hg`
- Build/Cache: `.cache`, `.mypy_cache`, `conda-env`, `.conda`
- Environment: `.env` (environment variable files)

### Pod/Container Mode

**Automatic Detection**: The application automatically detects containerized Tailscale environments and enables pod mode when no TUN interface is present (userspace proxy mode).

For containerized environments or manual pod mode where sender and receiver run in the same network namespace:

```bash
# Sender binds to localhost and accepts localhost connections
transfer send --pod document.pdf
# Outputs: type into receiver: transfer receive 100.64.1.123:ocean-tiger

# Receiver accepts connections from localhost (127.0.0.1)
transfer receive 100.64.1.123:ocean-tiger --pod
```

**Use cases:**
- Docker containers with shared network namespaces
- Kubernetes pods with internal communication
- Development environments with local testing

**Security note:** In pod mode, both sender and receiver allow `127.0.0.1` connections to bypass Tailscale peer validation. All other IPs still require Tailscale network membership.

## Technical Details

### User Interaction Prompts

The program prompts users for decisions during transfers:

**Compression Prompt** (Sender):
```
Use compression? [y/N]:
```
- Default: **No** (press Enter)
- Enables Blosc+LZ4 compression when 'y' selected
- Recommended for: Python libraries, text files, many small files
- Not recommended for: Already compressed files (images, videos, archives)

**Virtual Environment Exclusion** (Sender):
```
Found virtual environment/cache directories: venv, __pycache__, node_modules. Skip? [Y/n]:
```
- Default: **Yes** (press Enter)
- Skips detected development cache directories
- Can reduce transfer size by 80-95% for dev projects

**Resume Existing Transfer** (Receiver):
```
Resume transfer? [Y/n]:
```
- Default: **Yes** (press Enter)
- Automatically detects existing `.transfer_lock.json` and `.part` files
- Resumes from last verified position

**File Conflict Warning** (Receiver):
```
Warning: The following files/folders will be overwritten:
  - document.pdf
  - folder/
Continue? [Y/n]:
```
- Default: **Yes** (press Enter)
- Shows all files that will be overwritten
- Allows cancellation before transfer starts

### Compression Configuration

**Blosc+LZ4 Settings:**
- **Threads**: 4 (parallel compression)
- **Compressor**: LZ4 (ultra-fast, ~500 MB/s per core)
- **Level**: 1 (speed-optimized, minimal CPU overhead)
- **GIL Release**: Enabled (true multi-threading in Python)

**Performance Characteristics:**
- Compression speed: >500 MB/s per core on modern CPUs
- Typical compression ratio: 30-80% reduction for text/code
- Best for: Python libraries (5-20x faster), source code, logs
- Overhead: Minimal (~2-5% CPU increase)

### Network Timeouts

**Connection Timeouts:**
- **Sender**: 300 seconds (5 minutes) - Long timeout for slow connections
- **Receiver**: 30 seconds - Quick detection of sender unavailability
- **Retry/Completion**: 120 seconds (2 minutes) - For integrity verification retry requests

**Recent Changes:**
- Retry timeout increased from 10s to 120s (commit 65683e7, Nov 15, 2025)
- Allows time for sender to prepare retried files
- Prevents premature timeout on slow/large retries

### TCP Optimization

**TCP_NODELAY Enabled:**
- Disables Nagle's algorithm for lower latency
- Applied to both sender (line 1211) and receiver (line 1619)
- Reduces delay for small packet transfers
- Critical for interactive progress updates and metadata exchange

**Benefits:**
- ~20-50ms latency reduction for small messages
- Faster authentication and handshake
- More responsive progress updates

### Automatic Resume System

**Lock File System:**
- **File**: `.transfer_lock.json` created in receiver directory
- **Format**: JSON with session metadata and per-file state
- **Timeout**: 24 hours (stale locks automatically ignored)
- **Batched Updates**: Lock file updated every 150 file operations or 2 seconds (whichever comes first)

**Lock File Structure:**
```json
{
  "version": "1.0",
  "session_id": "uuid-v4-string",
  "timestamp": "2025-11-15T12:34:56Z",
  "sender_ip": "100.101.29.44",
  "total_files": 1234,
  "total_size": 567890123,
  "files": {
    "path/to/file.txt": {
      "status": "completed|in_progress|pending|failed",
      "size": 12345,
      "original_hash": "sha256-hash-of-source-file",
      "transferred_bytes": 12345,
      "partial_hash": "sha256-hash-of-partial-data",
      "last_modified": "2025-11-15T11:59:00Z"
    }
  }
}
```

**File Change Detection:**
- SHA-256 hash comparison detects source file modifications
- Changed files automatically marked for retransfer
- Prevents incomplete/corrupted transfers from mismatched sources

**Resume Workflow:**
1. Receiver detects `.transfer_lock.json` on startup
2. Validates lock file (structure, age, integrity)
3. Compares incoming files with lock state
4. Categorizes files: completed (skip), partial (resume), fresh (start)
5. Displays: "Resuming transfer: X completed, Y partial, Z fresh files"

### Integrity Verification & Retry

**Automatic Retry System:**
- **Max Attempts**: 3 retries per file on hash verification failure
- **Selective Retry**: Only failed files retransmitted, not entire transfer
- **Hash Algorithm**: SHA-256 for all file integrity verification
- **Sender Cooperation**: Sender listens for retry requests and resends specific files

**Retry Workflow:**
1. Receiver completes file transfer
2. Compares SHA-256 hash with sender's hash
3. On mismatch: Requests file retry from sender
4. Sender retransmits failed file
5. Up to 3 attempts per file
6. After 3 failures: File marked as failed in lock file

**Benefits:**
- Handles transient network errors automatically
- No manual intervention required
- Clean console output (failures logged to file)

### Warning Logging System

**Log File:** `transfer_warnings.log` in current directory

**Logged Events:**
- File permission errors during directory traversal
- Resource monitoring warnings (file descriptor limits)
- Console disconnect events (SIGPIPE, SIGHUP)
- Lock file errors and stale lock cleanup
- Source file change detection
- Retry failures and integrity check issues

**Format:**
```
[2025-11-15 12:34:56] Warning: File descriptor usage at 85% of limit
[2025-11-15 12:35:01] SIGPIPE received - terminal disconnected
[2025-11-15 12:35:10] Failed to write to document.pdf.part: Permission denied
```

**Why Silent Warnings?**
- Maintains clean, minimal console interface
- Prevents warning spam from disrupting progress display
- All warnings preserved for debugging
- Critical errors still shown to user

### Resource Monitoring

**File Descriptor Monitoring** (Unix/Linux/macOS only):
- **Detection Methods**:
  - Linux: `/proc/self/fd` directory counting
  - Unix/macOS: `resource.getrlimit(RLIMIT_NOFILE)`
  - Windows: Gracefully disabled (not available)
- **Warning Threshold**: 85% of soft limit
- **Logged To**: `transfer_warnings.log`

**Large Transfer Optimization:**
- Prevents "Too many open files" (errno 24) errors
- FileWriter class never holds file handles open (open → write → close immediately)
- Can handle thousands of files without FD exhaustion
- Warnings logged when approaching system limits

## Documentation

**[Complete Documentation](https://proudsunburn.github.io/ftransfer/)** - Comprehensive guides and API reference

## Troubleshooting

### Common Errors

- **"Could not detect Tailscale IP"**: Ensure Tailscale is running and connected (`tailscale status`)
- **"Connection refused"**: Check the connection string and ensure sender is waiting
- **"Authentication failed"**: Verify the connection string was copied correctly
- **"IP address is not an active peer"**: Only verified Tailscale network peers are supported
- **"Invalid connection string format"**: Use format `ip:token` (e.g., `100.64.1.123:ocean-tiger`)

### File & Permission Errors

- **"Permission denied" during transfer**:
  - Check write permissions in receiver directory
  - Try running from a directory you own
  - Warnings logged to `transfer_warnings.log`

- **"Too many open files" (errno 24)**:
  - Rare with current implementation (files closed immediately)
  - Check FD warnings in `transfer_warnings.log`
  - Increase system limits: `ulimit -n 4096` (Unix/Linux/macOS)

- **Lock file corruption**:
  - Automatic graceful fallback to fresh transfer
  - Old `.transfer_lock.json` ignored, new one created
  - Manual fix: Delete `.transfer_lock.json` and restart

### Hash Verification Failures

- **"Hash verification failed, retrying..."**:
  - Automatic retry up to 3 attempts
  - Usually caused by transient network errors
  - File retransmitted automatically
  - After 3 failures: Logged to `transfer_warnings.log`, transfer continues with other files

### Console & Terminal Issues

- **Terminal disconnected during transfer**:
  - Transfer continues in background (handled gracefully)
  - Progress logged to `transfer_warnings.log`
  - Check log file for completion status

- **Progress display garbled**:
  - Terminal doesn't support ANSI escape codes
  - Transfer still works, only display affected
  - Use `transfer ... > output.log 2>&1` to capture to file

### Network Issues

- **Timeout during large file transfer**:
  - Sender timeout: 300 seconds (5 minutes)
  - Retry timeout: 120 seconds (2 minutes)
  - Check network stability with `ping` or `tailscale ping <ip>`

- **Transfer slower than expected**:
  - Check if compression is enabled (may slow CPU-bound transfers)
  - Verify network speed: `iperf3` between Tailscale peers
  - Check CPU usage during compression

### Debugging

**Check Warning Logs:**
```bash
cat transfer_warnings.log
```

**Check Lock File State:**
```bash
cat .transfer_lock.json | python3 -m json.tool
```

**Verify Tailscale Connectivity:**
```bash
tailscale status
tailscale ping <receiver-ip>
```

**Test File Integrity:**
```bash
sha256sum filename.ext  # Unix/Linux
shasum -a 256 filename.ext  # macOS
```

## License

This project is available under the AGPL-3.0 License.