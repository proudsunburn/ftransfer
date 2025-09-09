---
layout: default
title: verify_peer_ip_cached()
permalink: /verify_peer_ip_cached/
---

<script>
document.documentElement.style.setProperty('--bg-color', '#0d1117');
document.body.style.backgroundColor = '#0d1117';
document.body.style.color = '#f0f6fc';
</script>


<style>
.butterfly-diagram {
  text-align: center;
  margin: 20px 0;
  padding: 20px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 8px;
}
</style>

# TailscaleDetector.verify_peer_ip_cached()

*Primary security validation for peer connections using cached data*

## Overview

The primary security validation method for incoming file transfer connections. This method verifies that an IP address belongs to an active Tailscale peer using cached peer information to minimize performance overhead. It serves as the first line of defense against unauthorized connections.

## Call Graph

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=LR;
    bgcolor="transparent";
    
    // Nodes
    send_files [label="send_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    receive_files [label="receive_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    verify_peer_ip_cached [label="verify_peer_ip_cached()" shape=box style=filled fillcolor="#58a6ff" fontcolor="white" fontsize=12 penwidth=3];
    subprocess_run [label="subprocess.run()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    
    // Edges
    send_files -> verify_peer_ip_cached [color="#6e7681"];
    receive_files -> verify_peer_ip_cached [color="#6e7681"];
    verify_peer_ip_cached -> subprocess_run [color="#6e7681"];
}
{% endgraphviz %}
</div>

## Parameters

- **`ip`** (str): IP address to validate in dotted decimal notation (e.g., `"100.101.29.44"`)

## Return Value

- **Type**: `Tuple[bool, str]`
- **Success**: `(True, peer_hostname)` - IP is authenticated Tailscale peer with hostname
- **Failure**: `(False, "unknown_tailscale_peer")` - IP validation failed or peer not found

### Return Value Details

- **`is_valid`** (bool): 
  - `True`: IP belongs to an active, authenticated Tailscale peer
  - `False`: IP is not a valid or active Tailscale peer
- **`peer_name`** (str):
  - On success: Hostname of the validated peer (e.g., `"laptop-alice"`)
  - On failure: `"unknown_tailscale_peer"` constant string


## Requirements

verify_peer_ip_cached() shall return (True, peer_hostname) when the provided IP address matches an active Tailscale peer in the cached status output where the peer has valid authentication credentials.

verify_peer_ip_cached() shall return (False, "unknown_tailscale_peer") when the provided IP address is not found in Tailscale peer list or when Tailscale CLI execution fails.

verify_peer_ip_cached() shall refresh peer cache when cache age exceeds 30 seconds where cache age is measured from last successful status retrieval.

verify_peer_ip_cached() shall execute "tailscale status --json" command when cache refresh is required where the command provides current peer information.

verify_peer_ip_cached() shall parse JSON output to extract peer IP addresses and hostnames when Tailscale command succeeds where parsing creates IP-to-hostname mapping.

## Algorithm Flow

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=TB;
    bgcolor="transparent";
    edge [color="#6e7681"];
    
    // Start
    start [label="Start: verify_peer_ip_cached(ip)" shape=ellipse style=filled fillcolor="#58a6ff" fontcolor="white"];
    
    // Input validation
    validate_ip_format [label="Valid IPv4 format?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    check_cache [label="Cache exists and\nage < 30 seconds?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Cache hit path
    search_cache [label="Search cached peer list\nfor matching IP" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    found_in_cache [label="IP found in cache?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    return_cached [label="Return (True, hostname)\nfrom cached data" shape=ellipse style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Cache miss/refresh path
    exec_tailscale [label="Execute subprocess:\n'tailscale status --json'" shape=box style=filled fillcolor="#2196f3" fontcolor="white"];
    cmd_timeout [label="Command timeout\n(5 second limit)" shape=box style=filled fillcolor="#ff9800" fontcolor="white"];
    cmd_success [label="Command successful?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // JSON processing
    parse_json [label="Parse JSON output\nfrom Tailscale CLI" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    json_valid [label="Valid JSON?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    extract_peers [label="Extract 'Peer' section\nfrom status data" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    
    // Peer processing
    build_cache [label="Build IP → hostname map:\n{ip: peer.HostName}" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    update_timestamp [label="Update cache timestamp\ntime.time()" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    search_fresh [label="Search fresh peer list\nfor matching IP" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    found_in_fresh [label="IP found in peers?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Success paths
    return_found [label="Return (True, hostname)\nfrom peer data" shape=ellipse style=filled fillcolor="#4caf50" fontcolor="white"];
    return_not_found [label="Return (False, \n'unknown_tailscale_peer')" shape=ellipse style=filled fillcolor="#ff9800" fontcolor="white"];
    
    // Error paths
    error_invalid_ip [label="ValueError:\nInvalid IP address format" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_cmd_failed [label="SubprocessError:\nTailscale command failed" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_json [label="JSONDecodeError:\nInvalid JSON response" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_timeout [label="TimeoutError:\nCommand exceeded 5 seconds" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    return_error [label="Return (False,\n'unknown_tailscale_peer')" shape=ellipse style=filled fillcolor="#f44336" fontcolor="white"];
    
    // Main flow
    start -> validate_ip_format;
    validate_ip_format -> check_cache [label="Yes" color="green"];
    check_cache -> search_cache [label="Yes" color="green"];
    check_cache -> exec_tailscale [label="No" color="orange"];
    search_cache -> found_in_cache;
    found_in_cache -> return_cached [label="Yes" color="green"];
    found_in_cache -> return_not_found [label="No" color="orange"];
    
    // Fresh lookup flow
    exec_tailscale -> cmd_timeout;
    cmd_timeout -> cmd_success;
    cmd_success -> parse_json [label="Yes" color="green"];
    parse_json -> json_valid;
    json_valid -> extract_peers [label="Yes" color="green"];
    extract_peers -> build_cache;
    build_cache -> update_timestamp;
    update_timestamp -> search_fresh;
    search_fresh -> found_in_fresh;
    found_in_fresh -> return_found [label="Yes" color="green"];
    found_in_fresh -> return_not_found [label="No" color="orange"];
    
    // Error flows
    validate_ip_format -> error_invalid_ip [label="No" color="red" style=dashed];
    cmd_success -> error_cmd_failed [label="No" color="red" style=dashed];
    cmd_timeout -> error_timeout [color="red" style=dashed];
    json_valid -> error_json [label="No" color="red" style=dashed];
    
    error_invalid_ip -> return_error;
    error_cmd_failed -> return_error;
    error_json -> return_error;
    error_timeout -> return_error;
}
{% endgraphviz %}

</div>

## Security Considerations

### **Authentication Bypass Prevention**
- **IP Format Validation**: Strict IPv4 validation prevents malformed input that could bypass authentication
- **Peer List Authority**: Only accepts IP addresses explicitly listed in Tailscale's active peer database  
- **Cache Invalidation**: 30-second cache TTL ensures recently disconnected peers cannot maintain access
- **Fail-Secure Design**: Any error condition returns authentication failure rather than allowing access

### **Command Injection Protection**
- **Subprocess Security**: Uses `subprocess.run()` with explicit argument array to prevent command injection
- **Fixed Command Path**: Only executes `tailscale status --json` with no user-controlled parameters
- **Timeout Protection**: 5-second hard timeout prevents hanging on malicious input or system issues
- **Output Sanitization**: JSON parsing provides structured data access without shell interpretation

### **Cache Security**
- **Time-Based Invalidation**: Cache automatically expires after 30 seconds to limit stale data exposure
- **Memory Isolation**: Peer cache stored in process memory, not persistent storage
- **Atomic Updates**: Cache updates are atomic to prevent race conditions during refresh
- **Cache Poisoning Resistance**: Cache populated only from authenticated Tailscale CLI output

### **Network Discovery Protection**
- **Authorized Peers Only**: Only returns hostnames for IPs explicitly in Tailscale network
- **Information Disclosure Limits**: Returns only hostname, not full peer details or network topology
- **Enumeration Prevention**: No bulk peer listing exposed, only individual IP lookups
- **Unknown Peer Handling**: Consistent response for unknown peers prevents information leakage

### **Error Handling Security**
- **Consistent Failure Response**: All error conditions return same `(False, "unknown_tailscale_peer")` format
- **No Information Leakage**: Error responses don't reveal system state, command failures, or network details
- **Graceful Degradation**: Function fails securely rather than allowing unauthorized access
- **Exception Safety**: All exceptions caught and converted to authentication failure

### **Tailscale Integration Security**
- **CLI Authority**: Relies on Tailscale CLI as trusted source of peer authentication data
- **JSON Structure Validation**: Validates expected JSON structure from Tailscale output
- **Version Compatibility**: Designed to work across Tailscale CLI versions with graceful failure
- **Authentication Inheritance**: Inherits Tailscale's device authentication and key management

### **Performance Security**
- **DoS Prevention**: Command timeout and cache limit prevent resource exhaustion attacks
- **Rate Limiting**: Cache mechanism naturally rate-limits expensive CLI operations
- **Memory Management**: Fixed-size cache prevents memory exhaustion from malicious peers
- **CPU Protection**: JSON parsing and string operations bounded by reasonable peer list sizes

### **System Security**
- **Privilege Isolation**: Runs with same privileges as calling process, no privilege escalation
- **File System Access**: No direct file system access, only subprocess execution
- **Network Isolation**: No direct network operations, relies on Tailscale CLI for network access
- **Logging Security**: No sensitive data logged, only functional operation details

<script src="{{ "/assets/js/dark-mode.js" | relative_url }}"></script>