---
layout: default
title: receive_files()
parent: Main Functions
nav_order: 2
---

# receive_files() Function

High-performance file reception client with streaming protocol and end-to-end decryption.

## Overview

Main client function that connects to sender, performs key exchange, and securely receives files using the optimized streaming protocol. Handles connection parsing, peer verification, and file reconstruction from streamed data with batch metadata processing.

## Call Graph

```mermaid
graph LR
    main["main()"]:::red
    receive_files["receive_files()"]:::highlight
    verify_peer_ip_cached["TailscaleDetector.verify_peer_ip_cached()"]:::green
    crypto_init["SecureCrypto()"]:::green
    recv_all["recv_all()"]:::green
    calculate_speed["calculate_speed()"]:::green
    format_speed["format_speed()"]:::green

    main --> receive_files
    receive_files --> verify_peer_ip_cached
    receive_files --> crypto_init
    receive_files --> recv_all
    receive_files --> calculate_speed
    receive_files --> format_speed

    classDef red fill:#f78166,stroke:#333,color:#fff
    classDef highlight fill:#58a6ff,stroke:#333,color:#fff,stroke-width:3px
    classDef green fill:#56d364,stroke:#333,color:#000
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `connection_string` | `str` | Connection string in format "ip:token" |
| `pod` | `bool` | Accept connections from localhost for containerized environments (default: False) |

## Return Value

- **Type**: `None`
- **Description**: Function completes file reception or raises exception on failure

## Requirements

receive_files() shall parse connection string to extract IP address and authentication token when connection_string parameter is provided where the format is "ip:token".

receive_files() shall establish TCP connection to sender on port 15820 when IP address is parsed where connection timeout is 30 seconds.

receive_files() shall verify sender IP using Tailscale peer verification when pod parameter is False where verification ensures sender is authenticated peer.

receive_files() shall perform key exchange with sender when TCP connection is established where the exchange uses X25519 ECDH with shared authentication token.

receive_files() shall decrypt all received data using ChaCha20Poly1305 when session key is derived where decryption ensures data confidentiality and integrity.

receive_files() shall automatically detect compression from metadata when batch metadata is received where decompression is applied only if sender enabled compression.

receive_files() shall receive files using streaming protocol with incremental saving when encrypted data is received where FileWriter instances handle direct stream-to-disk writing without memory accumulation.

receive_files() shall accept connections from localhost when pod parameter is True where localhost acceptance enables containerized deployment.

receive_files() shall automatically detect and resume from existing lock files and .part files where TransferLockManager instances verify existing data integrity before continuing transfers.

## Algorithm Flow

```mermaid
graph TD
    start(["Start: receive_files(connection_string, pod)"]):::highlight

    parse_conn["Parse connection string<br/>'ip:token' format"]:::green
    validate_format{"Valid format?"}:::yellow
    extract_ip["Extract IP address<br/>and authentication token"]:::green
    validate_ip{"Valid IPv4?"}:::yellow

    pod_check{"pod == True?"}:::yellow
    verify_peer["verify_peer_ip_cached(ip)<br/>Validate Tailscale peer"]:::green
    skip_verification["Skip peer verification<br/>(pod mode)"]:::orange
    peer_valid{"Peer authenticated?"}:::yellow

    connect_tcp["TCP connect to ip:15820<br/>(30 second timeout)"]:::lightblue
    connection_ok{"Connection successful?"}:::yellow

    crypto_init["SecureCrypto()<br/>Generate X25519 keypair"]:::green
    exchange_keys["Exchange public keys<br/>with sender"]:::lightblue
    derive_key["derive_session_key()<br/>ECDH + HKDF-SHA256 + token"]:::green
    key_success{"Key derivation successful?"}:::yellow

    receive_metadata["Receive batch metadata:<br/>{filename, size, hash, offset}"]:::success
    create_filewriters["Create FileWriter instances<br/>for incremental saving"]:::success
    open_part_files["Initialize TransferLockManager<br/>(automatic resume detection)"]:::success
    stream_loop["Stream chunks:<br/>recv() → decrypt() → write_chunk()"]:::success
    complete_files["Complete files:<br/>move .part to final names"]:::success
    verify_integrity["Verify SHA-256 hashes<br/>for all received files"]:::success
    integrity_ok{"All hashes valid?"}:::yellow

    calc_speed["calculate_speed()<br/>Compute transfer rate"]:::green
    show_result["Display: 'Transfer complete!<br/>Saved: files'"]:::pink
    cleanup["Close connections<br/>Cleanup resources"]:::gray
    end_success(["Return (success)"]):::success

    error_parse["ParseError:<br/>Invalid connection string"]:::error
    error_ip["ValueError:<br/>Invalid IP address"]:::error
    error_peer["AuthenticationError:<br/>Peer not verified"]:::error
    error_network["NetworkError:<br/>Connection failed"]:::error
    error_crypto["CryptographicError:<br/>Key exchange failed"]:::error
    error_integrity["IntegrityError:<br/>File hash mismatch"]:::error
    end_error(["Raise Exception"]):::error

    start --> parse_conn
    parse_conn --> validate_format
    validate_format -->|Yes| extract_ip
    extract_ip --> validate_ip
    validate_ip -->|Yes| pod_check
    pod_check -->|Yes| skip_verification
    pod_check -->|No| verify_peer
    verify_peer --> peer_valid
    peer_valid -->|Yes| connect_tcp
    skip_verification --> connect_tcp
    connect_tcp --> connection_ok
    connection_ok -->|Yes| crypto_init
    crypto_init --> exchange_keys
    exchange_keys --> derive_key
    derive_key --> key_success
    key_success -->|Yes| receive_metadata
    receive_metadata --> create_filewriters
    create_filewriters --> open_part_files
    open_part_files --> stream_loop
    stream_loop --> complete_files
    complete_files --> verify_integrity
    verify_integrity --> integrity_ok
    integrity_ok -->|Yes| calc_speed
    calc_speed --> show_result
    show_result --> cleanup
    cleanup --> end_success

    validate_format -.->|No| error_parse
    validate_ip -.->|No| error_ip
    peer_valid -.->|No| error_peer
    connection_ok -.->|No| error_network
    key_success -.->|No| error_crypto
    integrity_ok -.->|No| error_integrity

    error_parse --> end_error
    error_ip --> end_error
    error_peer --> end_error
    error_network --> end_error
    error_crypto --> end_error
    error_integrity --> end_error

    classDef highlight fill:#58a6ff,stroke:#333,color:#fff
    classDef green fill:#56d364,stroke:#333,color:#fff
    classDef yellow fill:#ffeb3b,stroke:#333,color:#000
    classDef orange fill:#ff9800,stroke:#333,color:#fff
    classDef lightblue fill:#2196f3,stroke:#333,color:#fff
    classDef success fill:#4caf50,stroke:#333,color:#fff
    classDef pink fill:#e91e63,stroke:#333,color:#fff
    classDef gray fill:#9e9e9e,stroke:#333,color:#fff
    classDef error fill:#f44336,stroke:#333,color:#fff
```

## Automatic Resume Workflow

The receiver implements intelligent automatic resume detection without requiring manual flags or user intervention.

```mermaid
graph TD
    start(["receive_files() starts"]):::pink

    check_lock["Initialize TransferLockManager<br/>Check for .transfer_lock.json"]:::success
    lock_exists{"Valid lock file<br/>found?"}:::yellow

    load_lock["Load existing lock data:<br/>session, file states, hashes"]:::lightblue
    analyze_files["Analyze incoming files vs<br/>lock state: completed/partial/fresh"]:::lightblue
    create_plan["Generate resume plan:<br/>X completed, Y partial, Z fresh"]:::lightblue
    show_resume["Display: 'Resuming transfer:<br/>X completed, Y partial, Z fresh files'"]:::pink

    create_lock["Create new lock file<br/>with session metadata"]:::success
    show_fresh["Display: 'Starting fresh transfer'"]:::pink

    setup_writers["Setup FileWriter instances:<br/>- Resume from lock offsets<br/>- Fresh files from zero"]:::success

    transfer_loop["Transfer files with<br/>integrity verification"]:::success
    check_integrity["Verify SHA-256 hashes<br/>for all files"]:::success
    integrity_ok{"All files<br/>pass integrity?"}:::yellow

    retry_count{"Retry attempts<br/>< 3?"}:::yellow
    request_retry["Send retry request<br/>to sender for failed files"]:::orange
    receive_retry["Receive retry data<br/>for failed files only"]:::orange

    cleanup_lock["Remove lock file<br/>(successful completion)"]:::success
    complete(["Transfer complete!"]):::success

    final_error["Report integrity failure<br/>after 3 attempts"]:::error

    start --> check_lock
    check_lock --> lock_exists
    lock_exists -->|yes| load_lock
    lock_exists -->|no| create_lock
    load_lock --> analyze_files
    analyze_files --> create_plan
    create_plan --> show_resume
    create_lock --> show_fresh
    show_resume --> setup_writers
    show_fresh --> setup_writers
    setup_writers --> transfer_loop
    transfer_loop --> check_integrity
    check_integrity --> integrity_ok
    integrity_ok -->|pass| cleanup_lock
    integrity_ok -->|fail| retry_count
    retry_count -->|yes| request_retry
    retry_count -->|no| final_error
    request_retry --> receive_retry
    receive_retry --> check_integrity
    cleanup_lock --> complete

    classDef pink fill:#e91e63,stroke:#333,color:#fff
    classDef success fill:#4caf50,stroke:#333,color:#fff
    classDef yellow fill:#ffeb3b,stroke:#333,color:#000
    classDef lightblue fill:#2196f3,stroke:#333,color:#fff
    classDef orange fill:#ff9800,stroke:#333,color:#fff
    classDef error fill:#f44336,stroke:#333,color:#fff
```

### **Lock File State Management**

The automatic resume system uses `.transfer_lock.json` files to track transfer state:

```json
{
  "version": "1.0",
  "session_id": "uuid-12345",
  "timestamp": "2024-01-01T12:00:00Z",
  "sender_ip": "100.101.29.44",
  "total_files": 1000,
  "total_size": 1048576000,
  "files": {
    "document.pdf": {
      "status": "completed",
      "size": 524288,
      "transferred_bytes": 524288,
      "original_hash": "sha256-hash",
      "partial_hash": "sha256-hash"
    },
    "archive.zip": {
      "status": "in_progress",
      "size": 1048576,
      "transferred_bytes": 262144,
      "partial_hash": "sha256-partial"
    }
  }
}
```

### **File Integrity Retry System**

When integrity check failures occur, the receiver automatically retries up to 3 times:

1. **Detection**: SHA-256 hash mismatch detected for received files
2. **Request**: Send retry request to sender with failed file list
3. **Resend**: Sender locates and resends only failed files
4. **Verification**: Re-verify integrity of retried files
5. **Loop**: Repeat up to 3 total attempts
6. **Completion**: Success after retry or final error report

### **Resume Decision Logic**

```python
def get_resume_plan(incoming_files):
    completed_files = []    # Skip entirely
    resume_files = []       # Resume from partial offset
    fresh_files = []        # Transfer from beginning

    for file in incoming_files:
        lock_status = lock_data.files[file.name].status
        if lock_status == "completed":
            completed_files.append(file.name)
        elif lock_status == "in_progress":
            resume_files.append((file.name, transferred_bytes))
        else:
            fresh_files.append(file)
```

## Security Considerations

### **Connection Security**
- **Connection String Validation**: Strict parsing of "ip:token" format prevents injection attacks
- **IP Address Validation**: IPv4 format validation prevents malformed address exploitation
- **Connection Timeout**: 30-second timeout prevents hanging connections and resource exhaustion

### **Peer Authentication**
- **Tailscale Peer Verification**: Uses `verify_peer_ip_cached()` to ensure sender is authenticated Tailscale peer
- **Cached Verification**: 30-second cache prevents repeated CLI calls while maintaining security
- **Pod Mode Override**: Localhost-only mode for containerized deployments bypasses peer verification

### **Cryptographic Security**
- **Perfect Forward Secrecy**: Ephemeral X25519 keys generated per session protect past communications
- **Mutual Authentication**: ECDH key exchange with shared token prevents man-in-the-middle attacks
- **Session Key Derivation**: HKDF-SHA256 with token salt ensures both parties know the shared secret

### **File Reception Security**
- **Directory Traversal Prevention**: File paths validated before FileWriter creation to prevent escape attacks
- **Incremental File Writing**: FileWriter class manages .part files with atomic completion operations
- **Lock File Validation**: TransferLockManager verifies existing transfer state and file integrity before resuming
- **Integrity Verification**: SHA-256 hash verification ensures files haven't been tampered with
- **Atomic File Operations**: Files written to .part locations then atomically renamed on completion

### **Data Protection**
- **Authenticated Decryption**: ChaCha20Poly1305 AEAD prevents accepting tampered data
- **Streaming Decryption**: Data decrypted in chunks and written directly to disk without memory accumulation
- **Memory Efficiency**: FileWriter approach eliminates large memory buffers, reducing attack surface
- **Secure Cleanup**: Connection resources and .part files properly cleaned up on failure

### **Error Handling Security**
- **Fail-Safe Design**: Any error condition results in complete operation failure
- **Information Disclosure Prevention**: Error messages don't reveal sensitive network or cryptographic details
- **Resource Cleanup**: Ensures connections and partial files cleaned up on failure

### **Network Security**
- **Port Consistency**: Fixed port 15820 provides predictable endpoint for firewall configuration
- **Connection Limits**: Single connection per session prevents resource exhaustion
- **Timeout Protection**: Network timeouts prevent indefinite blocking

### **FileWriter Security**
- **Incremental Hash Verification**: Continuous SHA-256 hashing during writing ensures data integrity
- **Resume Integrity**: Existing .part files re-hashed completely before resuming to detect tampering
- **Atomic Completion**: Files moved from .part to final names only after complete verification
- **Partial File Isolation**: Incomplete transfers isolated with .part extension to prevent confusion
- **Memory Attack Prevention**: Direct stream-to-disk writing eliminates large memory allocations

### **Attack Mitigation**
- **Replay Protection**: Ephemeral keys and session binding prevent replay attacks
- **DoS Protection**: Connection timeouts and resource limits prevent denial of service
- **Data Validation**: All received data validated before processing or storage
- **Resume Attack Prevention**: .part files validated with hash verification before continuation
- **Side-Channel Resistance**: Cryptographic operations designed to resist timing attacks
