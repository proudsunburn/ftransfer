---
layout: default
title: main()
permalink: /main/
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

# main() Function

CLI entry point and argument parser.

## Overview

Main entry point that handles command-line argument parsing and dispatches to appropriate send or receive functions. Provides user interface for the Transfer Files system.

## Call Graph

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=LR;
    bgcolor="transparent";
    
    // Nodes
    cli [label="CLI execution" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    main [label="main()" shape=box style=filled fillcolor="#58a6ff" fontcolor="white" fontsize=12 penwidth=3];
    send_files [label="send_files()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    receive_files [label="receive_files()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    argparse [label="argparse.ArgumentParser()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    sys_exit [label="sys.exit()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    
    // Edges
    cli -> main [color="#6e7681"];
    main -> send_files [color="#6e7681"];
    main -> receive_files [color="#6e7681"];
    main -> argparse [color="#6e7681"];
    main -> sys_exit [color="#6e7681"];
}
{% endgraphviz %}
</div>

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `command` | `str` | Either "send" or "receive" |
| `files` | `List[str]` | Files/directories to send (send mode only) |
| `connection` | `str` | Connection string ip:token (receive mode only) |
| `--novenv` | `flag` | Exclude virtual environment and cache directories |
| `--resume` | `flag` | Resume interrupted transfers from .part files |
| `--pod` | `flag` | Bind to/accept connections from localhost (127.0.0.1) for containerized environments |

## Return Value

- **Type**: `None`
- **Description**: Function exits with status code 0 on success or raises SystemExit on failure

## Requirements

main() shall parse command-line arguments when program is executed where arguments determine send or receive operation mode.

main() shall invoke send_files() when command is "send" and file paths are provided where send mode transmits files to receiving peer.

main() shall invoke receive_files() when command is "receive" and connection string is provided where receive mode accepts files from sending peer.

main() shall validate command-line argument combinations when parsing completes where validation ensures required arguments are present.

main() shall exit with appropriate status codes when operations complete or fail where status codes indicate success or failure to shell.

<script src="{{ "/assets/js/dark-mode.js" | relative_url }}"></script>