# Transfer Files System Overview

Secure file transfer program over Tailscale networks using end-to-end encryption with automatic key exchange and peer authentication.

## System Architecture

```mermaid
graph TD
    sender["Sender<br/>(send_files)"]:::blue
    tailscale["Tailscale Network<br/>(Encrypted Tunnel)"]:::green
    receiver["Receiver<br/>(receive_files)"]:::blue
    crypto["X25519 + ChaCha20Poly1305<br/>End-to-End Encryption"]:::red

    sender -->|Port 15820| tailscale
    tailscale -->|Encrypted Data| receiver
    sender -.->|uses| crypto
    receiver -.->|uses| crypto

    classDef blue fill:#58a6ff,stroke:#333,color:#fff
    classDef green fill:#56d364,stroke:#333,color:#fff
    classDef red fill:#f78166,stroke:#333,color:#fff
```

## Transfer Protocol Flow

### Sender Workflow

```mermaid
graph LR
    main["main()"]:::red --> send["send_files()"]:::blue
    send --> validate["validate_files()"]:::green
    validate --> getip["get_tailscale_ip()"]:::green
    getip --> token["generate_token()"]:::green
    token --> crypto1["SecureCrypto()"]:::green
    crypto1 --> stream["Stream Files<br/>(1MB buffers)"]:::green

    classDef red fill:#f78166,stroke:#333,color:#fff
    classDef blue fill:#58a6ff,stroke:#333,color:#fff
    classDef green fill:#56d364,stroke:#333,color:#fff
```

### Receiver Workflow

```mermaid
graph LR
    main2["main()"]:::red --> receive["receive_files()"]:::blue
    receive --> verify["verify_peer_ip_cached()"]:::green
    verify --> crypto2["SecureCrypto()"]:::green
    crypto2 --> recvall["recv_all()"]:::green
    recvall --> decrypt["decrypt()"]:::green

    classDef red fill:#f78166,stroke:#333,color:#fff
    classDef blue fill:#58a6ff,stroke:#333,color:#fff
    classDef green fill:#56d364,stroke:#333,color:#fff
```

## Security Architecture

```mermaid
graph TD
    subgraph network[" Network Security "]
        tailscale_net["Tailscale Peer Verification"]:::green
        port["Fixed Port 15820"]:::green
    end

    subgraph cryptography[" Cryptographic Security "]
        x25519["X25519 ECDH<br/>Key Exchange"]:::blue
        chacha20["ChaCha20Poly1305<br/>AEAD Encryption"]:::blue
        hkdf["HKDF-SHA256<br/>Key Derivation"]:::blue
    end

    subgraph auth[" Authentication "]
        tokens["2-Word Tokens<br/>34.6 bits entropy"]:::red
    end

    tailscale_net --> x25519
    x25519 --> hkdf
    hkdf --> chacha20
    tokens --> x25519

    classDef blue fill:#58a6ff,stroke:#333,color:#fff
    classDef green fill:#56d364,stroke:#333,color:#fff
    classDef red fill:#f78166,stroke:#333,color:#fff
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
