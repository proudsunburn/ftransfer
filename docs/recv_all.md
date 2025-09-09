---
layout: default
title: recv_all()
permalink: /recv_all/
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

# recv_all() Function

Reliable socket data reception with guaranteed completeness.

## Overview

Utility function that ensures complete reception of a specified amount of data from a socket connection. Handles partial receives and network interruptions to guarantee data integrity.

## Call Graph

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=LR;
    bgcolor="transparent";
    
    // Nodes
    send_files [label="send_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    receive_files [label="receive_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    recv_all [label="recv_all()" shape=box style=filled fillcolor="#58a6ff" fontcolor="white" fontsize=12 penwidth=3];
    socket_recv [label="socket.recv()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    
    // Edges
    send_files -> recv_all [color="#6e7681"];
    receive_files -> recv_all [color="#6e7681"];
    recv_all -> socket_recv [color="#6e7681"];
}
{% endgraphviz %}
</div>

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `sock` | `socket.socket` | TCP socket connection to read from |
| `size` | `int` | Exact number of bytes to receive |

## Return Value

- **Type**: `bytes`
- **Description**: Exactly `size` bytes of data from the socket

## Requirements

recv_all() shall receive exactly the requested number of bytes when size parameter is provided where the function handles partial receives.

recv_all() shall loop until all bytes are received when socket provides partial data where looping ensures complete data reception.

recv_all() shall handle connection interruptions when network issues occur where the function attempts to continue receiving.

recv_all() shall raise exception when connection is closed prematurely where closure prevents complete data reception.

recv_all() shall return bytes object of exact size when all data is received where the size matches the requested size parameter.

## Algorithm Flow

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=TB;
    bgcolor="transparent";
    edge [color="#6e7681"];
    
    // Start
    start [label="Start: recv_all(sock, size)" shape=ellipse style=filled fillcolor="#58a6ff" fontcolor="white"];
    
    // Input validation
    check_socket [label="sock provided and valid?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    check_size [label="size > 0?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    validate_socket_state [label="Socket connected?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Initialize reception
    init_buffer [label="data = b''\nremaining = size\nInitialize reception state" shape=box style=filled fillcolor="#2196f3" fontcolor="white"];
    
    // Reception loop
    start_loop [label="while remaining > 0:" shape=box style=filled fillcolor="#ff9800" fontcolor="white"];
    calculate_chunk [label="chunk_size = min(remaining, 65536)\nLimit recv size for efficiency" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    
    // Socket receive
    socket_recv [label="chunk = sock.recv(chunk_size)\nReceive data from socket" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    check_chunk [label="len(chunk) > 0?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Data processing
    append_data [label="data += chunk\nremaining -= len(chunk)\nAdd received data" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    check_complete [label="remaining == 0?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Progress tracking
    update_progress [label="Update reception progress\n(optional progress callback)" shape=box style=filled fillcolor="#9e9e9e" fontcolor="white"];
    
    // Success path
    validate_result [label="len(data) == size?\nVerify complete reception" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    return_data [label="return data\n(exactly size bytes)" shape=ellipse style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Error paths
    error_no_socket [label="ValueError:\nNo socket provided" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_invalid_size [label="ValueError:\nInvalid size parameter" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_socket_closed [label="ConnectionError:\nSocket not connected" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_connection_lost [label="ConnectionError:\nConnection closed by peer\n(recv returned 0 bytes)" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_socket_error [label="OSError:\nSocket receive error" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_timeout [label="TimeoutError:\nSocket receive timeout" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_incomplete [label="IncompleteReceiveError:\nReceived data size mismatch" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    raise_error [label="Raise Exception" shape=ellipse style=filled fillcolor="#f44336" fontcolor="white"];
    
    // Main flow
    start -> check_socket;
    check_socket -> check_size [label="Yes" color="green"];
    check_size -> validate_socket_state [label="Yes" color="green"];
    validate_socket_state -> init_buffer [label="Yes" color="green"];
    init_buffer -> start_loop;
    start_loop -> calculate_chunk;
    calculate_chunk -> socket_recv;
    socket_recv -> check_chunk;
    check_chunk -> append_data [label="Yes" color="green"];
    append_data -> check_complete;
    check_complete -> update_progress [label="No" color="orange"];
    check_complete -> validate_result [label="Yes" color="green"];
    update_progress -> start_loop [color="orange"];
    validate_result -> return_data [label="Yes" color="green"];
    
    // Error flows
    check_socket -> error_no_socket [label="No" color="red" style=dashed];
    check_size -> error_invalid_size [label="No" color="red" style=dashed];
    validate_socket_state -> error_socket_closed [label="No" color="red" style=dashed];
    check_chunk -> error_connection_lost [label="No" color="red" style=dashed];
    socket_recv -> error_socket_error [color="red" style=dashed];
    socket_recv -> error_timeout [color="red" style=dashed];
    validate_result -> error_incomplete [label="No" color="red" style=dashed];
    
    error_no_socket -> raise_error;
    error_invalid_size -> raise_error;
    error_socket_closed -> raise_error;
    error_connection_lost -> raise_error;
    error_socket_error -> raise_error;
    error_timeout -> raise_error;
    error_incomplete -> raise_error;
}
{% endgraphviz %}

</div>

## Security Considerations

### **Network Security**
- **Connection Validation**: Verifies socket is properly connected before attempting data reception
- **Timeout Protection**: Relies on socket timeout settings to prevent indefinite blocking
- **Resource Management**: Limits individual recv() calls to prevent memory exhaustion
- **Connection State Monitoring**: Detects connection closure to fail fast on network issues

### **Data Integrity**
- **Complete Reception Guarantee**: Ensures exactly the requested number of bytes are received
- **Partial Receive Handling**: Properly handles TCP's stream nature where data may arrive in chunks
- **Size Validation**: Validates received data matches expected size before returning
- **Buffer Management**: Safely accumulates received data without corruption

### **DoS Attack Mitigation**
- **Memory Limits**: Chunks reception into reasonable sizes (64KB) to prevent memory exhaustion
- **Progress Tracking**: Enables monitoring of reception progress for detecting stalls
- **Fail-Fast Design**: Immediately fails on connection errors rather than hanging indefinitely
- **Resource Bounds**: Natural bounds on memory usage based on expected data size

### **Error Handling Security**
- **Connection Failure Detection**: Properly detects when peer closes connection unexpectedly
- **Exception Safety**: Ensures no partial data returned on errors
- **Information Leakage Prevention**: Error messages don't reveal sensitive network details
- **Graceful Degradation**: Fails cleanly without corrupting application state

### **Socket Security**
- **Socket State Validation**: Verifies socket is in proper state for receiving data
- **Error Propagation**: Properly propagates socket errors without masking security issues
- **Resource Cleanup**: Doesn't manage socket lifecycle, leaves that to caller
- **Protocol Compliance**: Works within TCP/IP protocol constraints

### **Attack Surface Minimization**
- **Simple Operation**: Performs only data reception, no protocol interpretation
- **No Network Logic**: Doesn't make networking decisions, just receives requested data
- **Caller Responsibility**: Pushes security decisions to calling functions
- **Minimal Dependencies**: Uses only standard socket operations

<script src="{{ "/assets/js/dark-mode.js" | relative_url }}"></script>