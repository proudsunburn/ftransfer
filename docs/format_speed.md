---
layout: default
title: format_speed()
permalink: /format_speed/
---

<script>
document.documentElement.style.setProperty('--bg-color', '#0d1117');
document.body.style.backgroundColor = '#0d1117';
document.body.style.color = '#f0f6fc';
</script>

# format_speed()

*Human-readable network transfer speed formatting utility*

## Overview

Converts raw bytes-per-second transfer rates into human-readable speed representations with appropriate units (B/s, KB/s, MB/s, GB/s). This utility function provides consistent, user-friendly speed formatting for transfer progress displays and network performance reporting.

## Call Graph

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=LR;
    bgcolor="transparent";
    
    // Nodes
    send_files [label="send_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    receive_files [label="receive_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    format_speed [label="format_speed()" shape=box style=filled fillcolor="#58a6ff" fontcolor="white" fontsize=12 penwidth=3];
    calculate_speed [label="calculate_speed()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    
    // Edges
    send_files -> format_speed [color="#6e7681"];
    receive_files -> format_speed [color="#6e7681"];
    format_speed -> calculate_speed [color="#6e7681"];
}
{% endgraphviz %}

</div>

## Parameters

- **`bytes_per_second`** (float): Transfer rate in bytes per second
- **Range**: 0.0 to very large values (theoretically unlimited)
- **Precision**: Supports fractional bytes per second

## Return Value

- **Type**: `str`
- **Format**: `"{value:.1f} {unit}/s"` or `"{value:.0f} {unit}/s"` for large values
- **Units**: B/s, KB/s, MB/s, GB/s, TB/s
- **Examples**: `"1.5 MB/s"`, `"825.3 KB/s"`, `"45 B/s"`

## Requirements

format_speed() shall return human-readable speed string when bytes_per_second parameter is provided where the string includes appropriate units.

format_speed() shall select appropriate unit scale when formatting speed where units progress through B/s, KB/s, MB/s, GB/s based on value magnitude.

format_speed() shall round to one decimal place when speed value is less than 1000 units where rounding improves readability.

format_speed() shall return "0 B/s" when provided speed is zero or negative where this provides consistent output formatting.

format_speed() shall handle very large speeds when high-performance transfers are measured where formatting maintains appropriate precision.

## Algorithm Flow

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=TB;
    bgcolor="transparent";
    edge [color="#6e7681"];
    
    // Start
    start [label="Start: format_speed(bytes_per_second)" shape=ellipse style=filled fillcolor="#58a6ff" fontcolor="white"];
    
    // Input validation
    check_input [label="bytes_per_second provided?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    validate_type [label="isinstance(bytes_per_second, (int, float))?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    check_negative [label="bytes_per_second <= 0?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Unit determination
    init_speed [label="speed = float(bytes_per_second)\nunit_index = 0\nunits = ['B', 'KB', 'MB', 'GB', 'TB']" shape=box style=filled fillcolor="#2196f3" fontcolor="white"];
    
    // Scale determination loop
    check_scale [label="speed >= 1024 and\nunit_index < len(units)-1?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    scale_down [label="speed /= 1024\nunit_index += 1\nMove to next unit" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Precision determination
    determine_precision [label="speed >= 100?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    set_precision_0 [label="precision = 0\n(whole numbers for large values)" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    set_precision_1 [label="precision = 1\n(one decimal for small values)" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    
    // String formatting
    format_string [label="formatted = f'{speed:.{precision}f} {units[unit_index]}/s'\nCreate formatted string" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Result validation
    validate_result [label="len(formatted) > 0 and\nformatted contains '/s'?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Success path
    return_formatted [label="return formatted\n(e.g., '1.5 MB/s')" shape=ellipse style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Zero/negative path
    return_zero [label="return '0 B/s'\n(zero or negative input)" shape=ellipse style=filled fillcolor="#ff9800" fontcolor="white"];
    
    // Error paths
    error_no_input [label="TypeError:\nNo input provided" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_invalid_type [label="TypeError:\nInvalid input type" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_format [label="ValueError:\nString formatting failed" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_invalid_result [label="RuntimeError:\nInvalid formatted result" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    raise_error [label="Raise Exception" shape=ellipse style=filled fillcolor="#f44336" fontcolor="white"];
    
    // Main flow
    start -> check_input;
    check_input -> validate_type [label="Yes" color="green"];
    validate_type -> check_negative [label="Yes" color="green"];
    check_negative -> init_speed [label="No" color="green"];
    init_speed -> check_scale;
    check_scale -> scale_down [label="Yes" color="green"];
    scale_down -> check_scale [color="orange"];
    check_scale -> determine_precision [label="No" color="blue"];
    determine_precision -> set_precision_0 [label="Yes" color="green"];
    determine_precision -> set_precision_1 [label="No" color="green"];
    set_precision_0 -> format_string;
    set_precision_1 -> format_string;
    format_string -> validate_result;
    validate_result -> return_formatted [label="Yes" color="green"];
    
    // Zero return path
    check_negative -> return_zero [label="Yes" color="orange"];
    
    // Error flows
    check_input -> error_no_input [label="No" color="red" style=dashed];
    validate_type -> error_invalid_type [label="No" color="red" style=dashed];
    format_string -> error_format [color="red" style=dashed];
    validate_result -> error_invalid_result [label="No" color="red" style=dashed];
    
    error_no_input -> raise_error;
    error_invalid_type -> raise_error;
    error_format -> raise_error;
    error_invalid_result -> raise_error;
}
{% endgraphviz %}

</div>

<script src="{{ "/assets/js/dark-mode.js" | relative_url }}"></script>