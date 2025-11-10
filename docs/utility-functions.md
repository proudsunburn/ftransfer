# Utility Functions

Helper functions for file operations, network communication, speed calculation, and data validation.

## Functions

### File & Network Operations
- **[recv_all()](recv_all.md)** - Reliable socket data reception
- **[validate_files()](validate_files.md)** - File path validation and verification
- **[collect_files_recursive()](collect_files_recursive.md)** - Recursive directory traversal
- **[log_warning()](log_warning.md)** - Silent warning logging system

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
