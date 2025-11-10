# send_files() Function

High-performance file transmission server with streaming protocol and end-to-end encryption.

## Overview

Main server function that handles file transmission using optimized streaming buffers. Sets up TCP server, performs key exchange, and securely transmits files using a unified streaming protocol optimized for maximum throughput, especially for many small files.

## Call Graph

```mermaid
graph LR
    main["main()"]:::red --> send_files["send_files()"]:::highlight
    send_files --> validate_files["validate_files()"]:::green
    send_files --> collect_files_recursive["collect_files_recursive()"]:::green
    send_files --> get_tailscale_ip["TailscaleDetector.get_tailscale_ip()"]:::green
    send_files --> verify_peer_ip_cached["TailscaleDetector.verify_peer_ip_cached()"]:::green
    send_files --> generate_token["SecureTokenGenerator.generate_token()"]:::green
    send_files --> crypto_init["SecureCrypto()"]:::green
    send_files --> recv_all["recv_all()"]:::green
    send_files --> calculate_speed["calculate_speed()"]:::green
    send_files --> format_speed["format_speed()"]:::green

    classDef red fill:#f78166,stroke:#333,color:#fff
    classDef highlight fill:#58a6ff,stroke:#333,color:#fff,stroke-width:3px
    classDef green fill:#56d364,stroke:#333,color:#fff
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_paths` | `List[str]` | List of file/directory paths to send |
| `pod` | `bool` | Bind to localhost for containerized environments (default: False) |

## Return Value

- **Type**: `None`
- **Description**: Function completes file transmission or raises exception on failure

## Requirements

send_files() shall establish TCP server on port 15820 when function is invoked with valid file paths where the server accepts connections from authenticated Tailscale peers.

send_files() shall validate all file paths before transmission when file_paths parameter is provided where validation ensures files exist and are accessible.

send_files() shall perform key exchange with connecting client when client connection is established where the exchange uses X25519 ECDH with shared authentication token.

send_files() shall encrypt all transmitted data using ChaCha20Poly1305 when session key is derived where encryption provides confidentiality and integrity.

send_files() shall prompt user to exclude virtual environment directories when venv patterns are detected where exclusion improves transfer efficiency by skipping cache directories.

send_files() shall prompt user to enable compression when preparing to transfer files where compression defaults to No and uses Blosc+LZ4 when enabled.

send_files() shall stream files using 1MB buffers when transmitting data where streaming optimizes performance for large files and many small files.

send_files() shall bind to localhost when pod parameter is True where localhost binding enables containerized deployment.

send_files() shall verify connecting peer IP using Tailscale peer verification when pod parameter is False where verification prevents unauthorized access.

## Algorithm Flow

```mermaid
graph TD
    start(["Start: send_files(file_paths, pod)"]):::blue

    validate_input["validate_files(file_paths)"]:::green
    collect_files["collect_files_recursive()<br/>Build file manifest"]:::green

    venv_prompt["Prompt: Exclude venv dirs?<br/>[Y/n]"]:::pink
    compression_prompt["Prompt: Use compression?<br/>[y/N]"]:::pink

    get_ip["get_tailscale_ip()<br/>Get local IP"]:::green
    bind_check{"pod == True?"}:::yellow
    bind_localhost["Bind to 127.0.0.1:15820"]:::orange
    bind_tailscale["Bind to tailscale_ip:15820"]:::orange

    generate_auth["generate_token()<br/>Create 2-word token"]:::green
    display_token["Display connection string:<br/>'transfer.py receive ip:token'"]:::pink

    wait_conn["Accept TCP connection<br/>(5 minute timeout)"]:::lightblue
    verify_peer["verify_peer_ip_cached()<br/>Validate client IP"]:::green

    crypto_init["SecureCrypto()<br/>Generate X25519 keypair"]:::green
    exchange_keys["Exchange public keys<br/>(64 bytes total)"]:::lightblue
    derive_key["derive_session_key()<br/>ECDH + HKDF-SHA256"]:::green

    send_metadata["Send batch metadata:<br/>{filename, size, hash}"]:::success
    stream_files["Stream files with 1MB buffers:<br/>read → hash → encrypt → send"]:::success

    calc_speed["calculate_speed()<br/>Compute transfer rate"]:::green
    show_result["Display: 'Transfer complete:<br/>X bytes sent'"]:::pink
    cleanup["Close connections<br/>Cleanup resources"]:::gray
    end_success(["Return (success)"]):::success

    error_validation["Validation Error:<br/>Files not found/accessible"]:::error
    error_network["Network Error:<br/>Cannot bind/connect"]:::error
    error_auth["Authentication Error:<br/>Peer verification failed"]:::error
    error_crypto["Cryptographic Error:<br/>Key exchange failed"]:::error
    end_error(["Raise Exception"]):::error

    start --> validate_input
    validate_input --> collect_files
    collect_files --> venv_prompt
    venv_prompt --> compression_prompt
    compression_prompt --> get_ip
    get_ip --> bind_check
    bind_check -->|Yes| bind_localhost
    bind_check -->|No| bind_tailscale
    bind_localhost --> generate_auth
    bind_tailscale --> generate_auth
    generate_auth --> display_token
    display_token --> wait_conn
    wait_conn --> verify_peer
    verify_peer --> crypto_init
    crypto_init --> exchange_keys
    exchange_keys --> derive_key
    derive_key --> send_metadata
    send_metadata --> stream_files
    stream_files --> calc_speed
    calc_speed --> show_result
    show_result --> cleanup
    cleanup --> end_success

    validate_input -.->|error| error_validation
    get_ip -.->|error| error_network
    bind_localhost -.->|error| error_network
    bind_tailscale -.->|error| error_network
    wait_conn -.->|error| error_network
    verify_peer -.->|error| error_auth
    exchange_keys -.->|error| error_crypto
    derive_key -.->|error| error_crypto

    error_validation --> end_error
    error_network --> end_error
    error_auth --> end_error
    error_crypto --> end_error

    classDef blue fill:#58a6ff,stroke:#333,color:#fff
    classDef green fill:#56d364,stroke:#333,color:#fff
    classDef pink fill:#e91e63,stroke:#333,color:#fff
    classDef yellow fill:#ffeb3b,stroke:#333,color:#000
    classDef orange fill:#ff9800,stroke:#333,color:#fff
    classDef lightblue fill:#2196f3,stroke:#333,color:#fff
    classDef success fill:#4caf50,stroke:#333,color:#fff
    classDef gray fill:#9e9e9e,stroke:#333,color:#fff
    classDef error fill:#f44336,stroke:#333,color:#fff
```

## Security Considerations

### **Network Security**
- **Peer Verification**: Uses `verify_peer_ip_cached()` to ensure only authenticated Tailscale peers can connect
- **Port Binding**: Fixed port 15820 provides consistent endpoint, pod mode allows containerized deployment
- **Connection Timeout**: 5-minute timeout prevents resource exhaustion from stalled connections

### **Cryptographic Security**
- **Perfect Forward Secrecy**: Ephemeral X25519 keys generated per session protect past communications if keys compromised
- **Authenticated Encryption**: ChaCha20Poly1305 AEAD prevents tampering and provides confidentiality
- **Key Exchange Security**: ECDH + HKDF-SHA256 with shared token ensures mutual authentication

### **Authentication Security**
- **Two-Word Tokens**: 34.6 bits entropy (~200² combinations) provides adequate security for short-lived sessions
- **Token Integration**: Shared token mixed into HKDF salt prevents man-in-the-middle attacks
- **Visual Verification**: Human-readable tokens enable out-of-band verification

### **File System Security**
- **Path Validation**: `validate_files()` prevents path traversal attacks and validates file accessibility
- **Integrity Protection**: SHA-256 hashing during streaming enables end-to-end integrity verification
- **Access Control**: File permissions checked before transmission

### **Performance Security**
- **Memory Management**: 1MB streaming buffers prevent excessive memory usage with large files
- **Resource Limits**: Connection timeouts and buffer limits prevent DoS attacks
- **Streaming Protocol**: Single-pass I/O minimizes data exposure time in memory

### **Attack Mitigation**
- **Replay Protection**: Ephemeral keys and nonces prevent replay attacks
- **Timing Attack Resistance**: ChaCha20Poly1305 provides constant-time operations
- **Side-Channel Protection**: Secure key generation and handling procedures
