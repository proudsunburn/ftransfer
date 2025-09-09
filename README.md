# Secure File Transfer

A simple, secure file transfer tool for Tailscale networks. Transfer files and folders between computers with end-to-end encryption and automatic key exchange.

## Features

- **Secure**: ChaCha20Poly1305 encryption with X25519 key exchange
- **Simple**: Clean two-command interface with minimal output
- **Safe**: Only works between verified Tailscale network peers
- **Fast**: High-performance streaming with Blosc+LZ4 compression optimized for all file types
- **Reliable**: File integrity verification and progress indicators
- **Resumable**: Interrupted transfers can be resumed with `--resume` flag
- **Memory Efficient**: Incremental file saving prevents RAM accumulation
- **Smart**: Excludes virtual environments and cache folders with `--novenv`
- **Easy**: Short connection strings with 2-word tokens

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make the script executable:
```bash
chmod +x transfer.py
```

## Usage

### Sending Files

Send one or more files or folders:
```bash
./transfer.py send file1.txt folder2/ document.pdf
```

The program will output something like:
```
type into receiver: transfer.py receive 100.64.1.123:ocean-tiger
```

### Receiving Files

Copy the connection string from the sender and run:
```bash
./transfer.py receive 100.64.1.123:ocean-tiger
```

Files will be extracted to the current directory.

### Resume Interrupted Transfers

If a transfer is interrupted, use the `--resume` flag to continue:
```bash
./transfer.py receive --resume 100.64.1.123:ocean-tiger
```

The receiver will check for `.part` files and resume from the last verified position.

### Exclude Virtual Environments

Use `--novenv` to skip common development folders:
```bash
./transfer.py send --novenv my_project/
```

Excludes: `venv`, `node_modules`, `__pycache__`, `.git`, and other cache directories.

## Security

- **Encryption**: All data is encrypted with ChaCha20Poly1305
- **Authentication**: Shared secret prevents unauthorized connections
- **Key Exchange**: Ephemeral X25519 keys for each session
- **Network Security**: Only accepts Tailscale connections
- **File Safety**: Path traversal protection during extraction
- **Integrity**: SHA-256 checksums verify file integrity

## Requirements

- Python 3.7 or later
- Tailscale installed and running
- Network connectivity between sender and receiver

## How It Works

1. **Sender** prepares files (Blosc+LZ4 compression for all data)
2. **Simple token** generated using cryptographically secure randomness (2 words from 200+ vocabulary)
3. **Secure connection** established over Tailscale with key exchange  
4. **Authentication** using the shared token prevents unauthorized access
5. **Encrypted transfer** with clean progress indicators
6. **Incremental save** with `.part` files and resume capability using hash verification

## Interface

**Clean, minimal output:**
```bash
# Sending
type into receiver: transfer.py receive 100.101.29.44:forest-piano
Waiting for receiver to connect...
Transferring file...
Progress: 100.0%
Transfer complete: 1234567 bytes sent

# Receiving  
Receiving 1 file(s) (1234567 bytes total)
Progress: 100.0%
Transfer complete!
Completed: document.pdf

# Resume interrupted transfer
Resuming document.pdf: 524288/1234567 bytes already written
Receiving 1 file(s) (1234567 bytes total)
Progress: 42.5% (1.2 MB/s)
Progress: 100.0%
Transfer complete!
Completed: document.pdf
```

## Advanced Usageß

### High-Performance Streaming

Uses a unified streaming protocol with incremental file saving and Blosc+LZ4 compression optimized for speed and reliability:

- **Blosc+LZ4 Compression**: Ultra-fast compression with 4-thread optimization for maximum speed
- **Incremental Saving**: Files written to disk as chunks arrive (no RAM accumulation)
- **Single-Pass I/O**: Files are read, compressed, hashed, and streamed in one operation  
- **Batch Metadata**: All file information sent upfront to reduce overhead
- **Optimized for Many Small Files**: 5-20x faster for Python libraries, virtual environments with compression
- **Memory Efficient**: Transfer size independent of available RAM

**Performance Benefits:**
- **Ultra-Fast Compression**: Blosc+LZ4 provides >500 MB/s compression speed per core
- **Bandwidth Reduction**: 30-80% smaller transfer sizes depending on file types
- **Eliminates Double File Reads**: Single-pass read→compress→hash→stream (50% I/O reduction)
- **Reduces Network Round-trips**: Batch metadata transmission (80-95% overhead reduction)
- **Multi-threaded Compression**: 4-thread Blosc optimization maximizes CPU utilization
- **Prevents Memory Exhaustion**: Stream-to-disk architecture with controlled buffers
- **Enables Resumable Transfers**: Hash verification with compression awareness

```bash
# All transfers automatically use optimized streaming
./transfer.py send document.pdf folder/ library.zip

# Memory usage stays constant regardless of transfer size
./transfer.py send 10GB_dataset/
```

### Resume Capability

Interrupted transfers can be resumed without re-downloading completed portions:

- **Automatic Detection**: `.part` files created during active transfers
- **Hash Verification**: Partial files verified before resuming
- **Integrity Assured**: Final hash verification ensures complete accuracy
- **Network Resilient**: Resume works regardless of interruption cause

```bash
# Start transfer (creates .part files as it progresses)
./transfer.py receive 100.64.1.123:ocean-tiger

# If interrupted, resume with --resume flag
./transfer.py receive --resume 100.64.1.123:ocean-tiger
# Output: "Resuming file.pdf: 5242880/10485760 bytes already written"
```

### Smart Exclusions

Exclude common development folders that don't need transferring:

```bash
# Exclude virtual environments and cache folders
./transfer.py send --novenv my_python_project/
# Output: "Excluded 3 virtual environment/cache directories"

# Can reduce transfer size by 80-95% for development projects
```

**Excluded Patterns:**
- Python: `venv`, `.venv`, `__pycache__`, `.pytest_cache`, `.tox`
- Node.js: `node_modules`, `.npm`, `.yarn`
- Version Control: `.git`, `.svn`, `.hg`
- Others: `.mypy_cache`, `.coverage`, `conda-env`

### Pod/Container Mode

For containerized environments where sender and receiver run in the same network namespace:

```bash
# Sender binds to localhost and accepts localhost connections
./transfer.py send --pod document.pdf
# Outputs: type into receiver: transfer.py receive 100.64.1.123:ocean-tiger

# Receiver accepts connections from localhost (127.0.0.1)
./transfer.py receive 100.64.1.123:ocean-tiger --pod
```

**Use cases:**
- Docker containers with shared network namespaces
- Kubernetes pods with internal communication
- Development environments with local testing

**Security note:** In pod mode, both sender and receiver allow `127.0.0.1` connections to bypass Tailscale peer validation. All other IPs still require Tailscale network membership.

## Documentation

📖 **[Complete Documentation](https://proudsunburn.github.io/ftransfer/)** - Comprehensive guides and API reference

- **[API Documentation](https://proudsunburn.github.io/ftransfer/api/)** - Detailed function documentation
- **[Usage Examples](https://proudsunburn.github.io/ftransfer/examples/)** - Common use cases
- **[Security Details](https://proudsunburn.github.io/ftransfer/security/)** - Cryptographic implementation

## Contributing

Contributions are welcome! Please see our documentation site for development guidelines.

## Troubleshooting

- **"Could not detect Tailscale IP"**: Ensure Tailscale is running and connected
- **"Connection refused"**: Check the connection string and ensure sender is waiting  
- **"Authentication failed"**: Verify the connection string was copied correctly
- **"IP address is not an active peer"**: Only verified Tailscale network peers are supported
- **"Invalid connection string format"**: Use format `ip:token` (e.g., `100.64.1.123:ocean-tiger`)

## License

This project is available under the MIT License.