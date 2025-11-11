# Transfer Files System Overview

Secure file transfer program over Tailscale networks using end-to-end encryption with automatic key exchange and peer authentication.

## System Architecture

```mermaid
graph TD
    sender["Sender<br/>(send_files)"]
    tailscale["Tailscale Network<br/>(Encrypted Tunnel)"]
    receiver["Receiver<br/>(receive_files)"]
    crypto["X25519 + ChaCha20Poly1305<br/>End-to-End Encryption"]

    sender -->|Port 15820| tailscale
    tailscale -->|Encrypted Data| receiver
    sender -.->|uses| crypto
    receiver -.->|uses| crypto
```

## Transfer Protocol Flow

### Sender Workflow

```mermaid
graph LR
    main["main()"] --> send["send_files()"]
    send --> validate["validate_files()"]
    validate --> getip["get_tailscale_ip()"]
    getip --> token["generate_token()"]
    token --> crypto1["SecureCrypto()"]
    crypto1 --> stream["Stream Files<br/>(1MB buffers)"]
```

### Receiver Workflow

```mermaid
graph LR
    main2["main()"] --> receive["receive_files()"]
    receive --> verify["verify_peer_ip_cached()"]
    verify --> crypto2["SecureCrypto()"]
    crypto2 --> recvall["recv_all()"]
    recvall --> decrypt["decrypt()"]
```

## Security Architecture

```mermaid
graph TD
    subgraph network[" Network Security "]
        tailscale_net["Tailscale Peer Verification"]
        port["Fixed Port 15820"]
    end

    subgraph cryptography[" Cryptographic Security "]
        x25519["X25519 ECDH<br/>Key Exchange"]
        chacha20["ChaCha20Poly1305<br/>AEAD Encryption"]
        hkdf["HKDF-SHA256<br/>Key Derivation"]
    end

    subgraph auth[" Authentication "]
        tokens["2-Word Tokens<br/>34.6 bits entropy"]
    end

    tailscale_net --> x25519
    x25519 --> hkdf
    hkdf --> chacha20
    tokens --> x25519
```

## Performance Features

- **Optional Blosc+LZ4 Compression**: User-selectable compression for bandwidth reduction (default: No)
- **Unified Streaming Protocol**: Single-pass I/O (read → optionally compress → hash → stream)
- **1MB Buffer Strategy**: Memory-efficient for large files, 3-10x faster for many small files
- **Batch Metadata Transmission**: Reduces network overhead for libraries/venvs
- **Connection Caching**: 30-second TTL for peer verification
- **Perfect Forward Secrecy**: Ephemeral X25519 keys protect past communications

## Key Components

| Component | Purpose | Security Level |
|-----------|---------|----------------|
| **TailscaleDetector** | Network peer validation and IP discovery | Safety-Critical |
| **SecureCrypto** | End-to-end encryption and key management | Safety-Critical |
| **SecureTokenGenerator** | Human-readable authentication tokens | Security-Critical |
| **send_files() / receive_files()** | Main transfer coordination | Security-Critical |
| **Utility Functions** | File validation, speed calculation, etc. | Reliability-Critical |

---

*Use the navigation panel to explore detailed documentation for each component. All documentation includes formal specifications, call graphs, and security analysis.*
