---
layout: default
title: Utility Functions
nav_order: 4
has_children: true
---

# Utility Functions

Helper functions for file operations, network communication, speed calculation, and data validation.

## Functions

### File & Network Operations
- **[recv_all()]({% link recv_all.md %})** - Reliable socket data reception
- **[validate_files()]({% link validate_files.md %})** - File path validation and verification
- **[collect_files_recursive()]({% link collect_files_recursive.md %})** - Recursive directory traversal
- **[log_warning()]({% link log_warning.md %})** - Silent warning logging system

### Crypto & Security
- **[crypto_init()]({% link crypto_init.md %})** - SecureCrypto initialization
- **[derive_session_key()]({% link derive_session_key.md %})** - ECDH key derivation
- **[encrypt()]({% link encrypt.md %})** - ChaCha20Poly1305 encryption
- **[decrypt()]({% link decrypt.md %})** - ChaCha20Poly1305 decryption
- **[get_public_key_bytes()]({% link get_public_key_bytes.md %})** - Public key serialization
- **[generate_token()]({% link generate_token.md %})** - Secure token generation
- **[get_tailscale_ip()]({% link get_tailscale_ip.md %})** - Local Tailscale IP detection
- **[verify_peer_ip_cached()]({% link verify_peer_ip_cached.md %})** - Peer verification with caching

### Performance & Progress
- **[calculate_speed()]({% link calculate_speed.md %})** - Transfer speed calculation
- **[format_speed()]({% link format_speed.md %})** - Human-readable speed formatting
