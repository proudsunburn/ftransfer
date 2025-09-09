---
layout: default
title: calculate_speed()
permalink: /calculate_speed/
---

<script>
document.documentElement.style.setProperty('--bg-color', '#0d1117');
document.body.style.backgroundColor = '#0d1117';
document.body.style.color = '#f0f6fc';
</script>

# calculate_speed()

*Transfer speed calculation utility for real-time performance monitoring*

## Overview

Calculates transfer speed in bytes per second based on the number of bytes transferred and elapsed time. This utility function provides accurate speed measurements for file transfers, network operations, and performance monitoring, with built-in protection against division-by-zero errors.

## Parameters

- **`bytes_transferred`** (int): Total number of bytes transferred
  - **Range**: 0 to very large values (limited by system memory)
  - **Units**: Bytes
- **`elapsed_time`** (float): Time elapsed during transfer in seconds
  - **Range**: > 0.0 for meaningful calculations
  - **Precision**: Supports microsecond precision

## Return Value

- **Type**: `float`
- **Units**: Bytes per second
- **Range**: 0.0 to theoretical maximum based on input values
- **Special Cases**: Returns 0.0 for zero elapsed time or negative values

## Call Graph

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=LR;
    bgcolor="transparent";
    
    // Nodes
    send_files [label="send_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    receive_files [label="receive_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    format_speed [label="format_speed()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    calculate_speed [label="calculate_speed()" shape=box style=filled fillcolor="#58a6ff" fontcolor="white" fontsize=12 penwidth=3];
    
    // Edges
    send_files -> calculate_speed [color="#6e7681"];
    receive_files -> calculate_speed [color="#6e7681"];
    format_speed -> calculate_speed [color="#6e7681"];
}
{% endgraphviz %}

</div>

## Requirements

calculate_speed() shall compute bytes per second when bytes_transferred and elapsed_time parameters are provided where computation uses simple division.

calculate_speed() shall return zero when elapsed_time is zero or negative where zero prevents division-by-zero errors.

calculate_speed() shall return zero when bytes_transferred is zero or negative where zero indicates no transfer occurred.

calculate_speed() shall return float value when computation succeeds where the value represents transfer rate in bytes per second.

calculate_speed() shall handle very large byte counts when high-volume transfers are measured where computation maintains numeric precision.

## Algorithm Flow

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=TB;
    bgcolor="transparent";
    edge [color="#6e7681"];
    
    // Start
    start [label="Start: calculate_speed(bytes_transferred, elapsed_time)" shape=ellipse style=filled fillcolor="#58a6ff" fontcolor="white"];
    
    // Input validation
    check_bytes [label="bytes_transferred provided?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    check_time [label="elapsed_time provided?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    validate_bytes [label="bytes_transferred >= 0?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    validate_time [label="elapsed_time > 0?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Type validation
    check_bytes_type [label="isinstance(bytes_transferred, int)?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    check_time_type [label="isinstance(elapsed_time, (int, float))?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Special case handling
    check_zero_bytes [label="bytes_transferred == 0?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    check_very_small_time [label="elapsed_time < 0.000001?\n(1 microsecond)" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Speed calculation
    perform_division [label="speed = bytes_transferred / elapsed_time\nCompute transfer rate" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Result validation
    check_overflow [label="speed finite and not NaN?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    check_reasonable [label="speed <= MAX_REASONABLE_SPEED?\n(e.g., 100 GB/s)" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Success path
    return_speed [label="return speed\n(bytes per second)" shape=ellipse style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Zero return paths
    return_zero_bytes [label="return 0.0\n(no bytes transferred)" shape=ellipse style=filled fillcolor="#ff9800" fontcolor="white"];
    return_zero_time [label="return 0.0\n(invalid time)" shape=ellipse style=filled fillcolor="#ff9800" fontcolor="white"];
    return_zero_small_time [label="return 0.0\n(time too small)" shape=ellipse style=filled fillcolor="#ff9800" fontcolor="white"];
    
    // Error paths
    error_no_bytes [label="TypeError:\nNo bytes_transferred provided" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_no_time [label="TypeError:\nNo elapsed_time provided" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_invalid_bytes_type [label="TypeError:\nInvalid bytes_transferred type" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_invalid_time_type [label="TypeError:\nInvalid elapsed_time type" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_negative_bytes [label="ValueError:\nNegative bytes_transferred" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_overflow [label="OverflowError:\nNumerical overflow in calculation" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_unreasonable [label="ValueError:\nUnreasonably high speed" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    raise_error [label="Raise Exception" shape=ellipse style=filled fillcolor="#f44336" fontcolor="white"];
    
    // Main flow
    start -> check_bytes;
    check_bytes -> check_time [label="Yes" color="green"];
    check_time -> check_bytes_type [label="Yes" color="green"];
    check_bytes_type -> check_time_type [label="Yes" color="green"];
    check_time_type -> validate_bytes [label="Yes" color="green"];
    validate_bytes -> validate_time [label="Yes" color="green"];
    validate_time -> check_zero_bytes [label="Yes" color="green"];
    check_zero_bytes -> check_very_small_time [label="No" color="green"];
    check_very_small_time -> perform_division [label="No" color="green"];
    perform_division -> check_overflow;
    check_overflow -> check_reasonable [label="Yes" color="green"];
    check_reasonable -> return_speed [label="Yes" color="green"];
    
    // Zero return flows
    check_zero_bytes -> return_zero_bytes [label="Yes" color="orange"];
    validate_time -> return_zero_time [label="No" color="orange"];
    check_very_small_time -> return_zero_small_time [label="Yes" color="orange"];
    
    // Error flows
    check_bytes -> error_no_bytes [label="No" color="red" style=dashed];
    check_time -> error_no_time [label="No" color="red" style=dashed];
    check_bytes_type -> error_invalid_bytes_type [label="No" color="red" style=dashed];
    check_time_type -> error_invalid_time_type [label="No" color="red" style=dashed];
    validate_bytes -> error_negative_bytes [label="No" color="red" style=dashed];
    check_overflow -> error_overflow [label="No" color="red" style=dashed];
    check_reasonable -> error_unreasonable [label="No" color="red" style=dashed];
    
    error_no_bytes -> raise_error;
    error_no_time -> raise_error;
    error_invalid_bytes_type -> raise_error;
    error_invalid_time_type -> raise_error;
    error_negative_bytes -> raise_error;
    error_overflow -> raise_error;
    error_unreasonable -> raise_error;
}
{% endgraphviz %}

</div>

<script src="{{ "/assets/js/dark-mode.js" | relative_url }}"></script>