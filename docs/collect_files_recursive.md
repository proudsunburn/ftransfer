---
layout: default
title: collect_files_recursive()
permalink: /collect_files_recursive/
---

<script>
document.documentElement.style.setProperty('--bg-color', '#0d1117');
document.body.style.backgroundColor = '#0d1117';
document.body.style.color = '#f0f6fc';
</script>

# collect_files_recursive()

*Recursive file system traversal and collection for comprehensive directory processing*

## Overview

Recursively traverses directory structures to collect all files with optional filtering capabilities. This utility function provides comprehensive file discovery with pattern matching, symbolic link handling, and access permission validation for building complete file inventories and transfer manifests.

## Call Graph

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=LR;
    bgcolor="transparent";
    
    // Nodes
    send_files [label="send_files()" shape=box style=filled fillcolor="#f78166" fontcolor="white" fontsize=11];
    collect_files_recursive [label="collect_files_recursive()" shape=box style=filled fillcolor="#58a6ff" fontcolor="white" fontsize=12 penwidth=3];
    os_walk [label="os.walk()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    os_path_join [label="os.path.join()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    fnmatch [label="fnmatch.fnmatch()" shape=box style=filled fillcolor="#56d364" fontcolor="black" fontsize=11];
    
    // Edges
    send_files -> collect_files_recursive [color="#6e7681"];
    collect_files_recursive -> os_walk [color="#6e7681"];
    collect_files_recursive -> os_path_join [color="#6e7681"];
    collect_files_recursive -> fnmatch [color="#6e7681"];
}
{% endgraphviz %}

</div>

## Parameters

- **`directory_path`** (str): Root directory path for recursive traversal
  - **Type**: String representing valid directory path
  - **Requirements**: Must exist and be accessible
- **`include_patterns`** (list, optional): Glob patterns for file inclusion
  - **Default**: None (include all files)
  - **Examples**: `['*.txt', '*.pdf']`, `['data_*.csv']`
- **`exclude_patterns`** (list, optional): Glob patterns for file exclusion
  - **Default**: None (no exclusions)
  - **Examples**: `['*.tmp', '__pycache__/*']`, `['.git/*']`

## Return Value

- **Type**: `list`
- **Content**: List of absolute file paths as strings
- **Ordering**: Typically sorted by path for consistent results
- **Empty**: Returns empty list if no files found or directory inaccessible

## Requirements

collect_files_recursive() shall traverse directory structure recursively when directory_path parameter is provided where traversal includes all subdirectories.

collect_files_recursive() shall collect all accessible files when traversing directories where files include regular files and exclude directories.

collect_files_recursive() shall apply include patterns when include_patterns parameter is provided where patterns use glob-style matching.

collect_files_recursive() shall apply exclude patterns when exclude_patterns parameter is provided where patterns filter out unwanted files.

collect_files_recursive() shall return list of absolute file paths when collection completes where paths are suitable for file operations.

## Algorithm Flow

<div class="butterfly-diagram">

{% graphviz %}
digraph {
    rankdir=TB;
    bgcolor="transparent";
    edge [color="#6e7681"];
    
    // Start
    start [label="Start: collect_files_recursive(directory_path, include_patterns, exclude_patterns)" shape=ellipse style=filled fillcolor="#58a6ff" fontcolor="white"];
    
    // Input validation
    check_directory [label="directory_path provided?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    validate_dir_exists [label="Directory exists and accessible?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    check_is_directory [label="Path is a directory?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Pattern validation
    validate_include_patterns [label="include_patterns valid?\n(None or list of strings)" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    validate_exclude_patterns [label="exclude_patterns valid?\n(None or list of strings)" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Initialize collection
    init_file_list [label="collected_files = []\nInitialize result list" shape=box style=filled fillcolor="#2196f3" fontcolor="white"];
    start_walk [label="Start os.walk(directory_path)\nBegin recursive traversal" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Directory traversal loop
    walk_loop [label="For each (root, dirs, files) in walk:" shape=box style=filled fillcolor="#ff9800" fontcolor="white"];
    process_directory [label="Process current directory:\nroot = current directory path" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    
    // File processing loop
    file_loop [label="For each filename in files:" shape=box style=filled fillcolor="#ff9800" fontcolor="white"];
    build_filepath [label="filepath = os.path.join(root, filename)\nBuild absolute file path" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // File validation
    check_is_file [label="os.path.isfile(filepath)?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    check_readable [label="File readable?\nos.access(filepath, os.R_OK)" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Pattern matching
    apply_include [label="include_patterns provided?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    check_include_match [label="Any include pattern matches?\nfnmatch.fnmatch()" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    apply_exclude [label="exclude_patterns provided?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    check_exclude_match [label="Any exclude pattern matches?\nfnmatch.fnmatch()" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // File collection
    add_file [label="collected_files.append(filepath)\nAdd file to collection" shape=box style=filled fillcolor="#4caf50" fontcolor="white"];
    more_files [label="More files in directory?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    more_directories [label="More directories to walk?" shape=diamond style=filled fillcolor="#ffeb3b" fontcolor="white"];
    
    // Finalization
    sort_results [label="Sort collected_files\nfor consistent ordering" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    validate_results [label="Remove duplicates and\ninvalid paths" shape=box style=filled fillcolor="#56d364" fontcolor="white"];
    return_files [label="return collected_files\nList of absolute file paths" shape=ellipse style=filled fillcolor="#4caf50" fontcolor="white"];
    
    // Error paths
    error_no_directory [label="ValueError:\nNo directory path provided" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_dir_not_exists [label="FileNotFoundError:\nDirectory does not exist" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_not_directory [label="NotADirectoryError:\nPath is not a directory" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_permission [label="PermissionError:\nDirectory access denied" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_invalid_patterns [label="ValueError:\nInvalid pattern format" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    error_walk [label="OSError:\nFile system traversal error" shape=box style=filled fillcolor="#f44336" fontcolor="white"];
    raise_error [label="Raise Exception" shape=ellipse style=filled fillcolor="#f44336" fontcolor="white"];
    
    // Main flow
    start -> check_directory;
    check_directory -> validate_dir_exists [label="Yes" color="green"];
    validate_dir_exists -> check_is_directory [label="Yes" color="green"];
    check_is_directory -> validate_include_patterns [label="Yes" color="green"];
    validate_include_patterns -> validate_exclude_patterns [label="Yes" color="green"];
    validate_exclude_patterns -> init_file_list [label="Yes" color="green"];
    init_file_list -> start_walk;
    start_walk -> walk_loop;
    walk_loop -> process_directory;
    process_directory -> file_loop;
    file_loop -> build_filepath;
    build_filepath -> check_is_file;
    check_is_file -> check_readable [label="Yes" color="green"];
    check_readable -> apply_include [label="Yes" color="green"];
    apply_include -> check_include_match [label="Yes" color="blue"];
    apply_include -> apply_exclude [label="No" color="green"];
    check_include_match -> apply_exclude [label="Yes" color="green"];
    apply_exclude -> check_exclude_match [label="Yes" color="blue"];
    apply_exclude -> add_file [label="No" color="green"];
    check_exclude_match -> add_file [label="No" color="green"];
    add_file -> more_files;
    more_files -> file_loop [label="Yes" color="orange"];
    more_files -> more_directories [label="No" color="green"];
    more_directories -> walk_loop [label="Yes" color="orange"];
    more_directories -> sort_results [label="No" color="green"];
    sort_results -> validate_results;
    validate_results -> return_files;
    
    // Error flows
    check_directory -> error_no_directory [label="No" color="red" style=dashed];
    validate_dir_exists -> error_dir_not_exists [label="No" color="red" style=dashed];
    check_is_directory -> error_not_directory [label="No" color="red" style=dashed];
    validate_dir_exists -> error_permission [color="red" style=dashed];
    validate_include_patterns -> error_invalid_patterns [label="No" color="red" style=dashed];
    validate_exclude_patterns -> error_invalid_patterns [label="No" color="red" style=dashed];
    start_walk -> error_walk [color="red" style=dashed];
    walk_loop -> error_walk [color="red" style=dashed];
    
    // Skip flows
    check_is_file -> more_files [label="No" color="gray"];
    check_readable -> more_files [label="No" color="gray"];
    check_include_match -> more_files [label="No" color="gray"];
    check_exclude_match -> more_files [label="Yes" color="gray"];
    
    error_no_directory -> raise_error;
    error_dir_not_exists -> raise_error;
    error_not_directory -> raise_error;
    error_permission -> raise_error;
    error_invalid_patterns -> raise_error;
    error_walk -> raise_error;
}
{% endgraphviz %}

</div>

## Security Considerations

### **Directory Traversal Security**
- **Path Validation**: Validates directory paths to prevent traversal attacks using "../" sequences
- **Absolute Path Resolution**: Converts all paths to absolute form to prevent relative path confusion
- **Symbolic Link Handling**: Safely processes symbolic links without following dangerous links outside intended scope
- **Access Control**: Respects file system permissions and only accesses authorized directories

### **File System Security**
- **Permission Checking**: Validates read permissions before attempting file operations
- **Safe Traversal**: Uses os.walk() which provides safe directory traversal with built-in protections
- **Error Handling**: Gracefully handles permission errors, broken links, and inaccessible files
- **Resource Limits**: Naturally limited by file system structure, preventing infinite recursion

### **Pattern Security**
- **Glob Pattern Validation**: Validates include/exclude patterns to prevent malicious pattern injection
- **Pattern Sanitization**: Uses fnmatch.fnmatch() which provides safe pattern matching
- **Case Sensitivity**: Handles case sensitivity consistently across different file systems
- **Special Character Handling**: Safely processes filenames with special characters and Unicode

### **Path Injection Prevention**
- **Input Sanitization**: Validates all input paths before processing
- **Path Canonicalization**: Resolves paths to canonical form to prevent ambiguous representations
- **Boundary Enforcement**: Ensures traversal stays within specified directory boundaries
- **Malicious Filename Handling**: Safely processes files with unusual names that might cause issues

### **Resource Protection**
- **Memory Management**: Efficiently handles large directory structures without excessive memory use
- **Traversal Limits**: Natural limits from file system structure prevent resource exhaustion
- **Handle Management**: Properly manages directory handles and file descriptors
- **Exception Safety**: Ensures resources are properly cleaned up on errors

### **Information Disclosure Prevention**
- **Access Control Respect**: Only returns information about accessible files
- **Error Message Safety**: Error messages don't reveal sensitive file system details
- **Directory Structure Protection**: Doesn't expose information about inaccessible directories
- **Metadata Security**: Only collects necessary path information, not sensitive metadata

### **Attack Surface Minimization**
- **Read-Only Operations**: Function only reads file system state, never modifies
- **Limited Scope**: Only operates on specified directories and their contents
- **No Network Operations**: Purely local file system operations with no external dependencies
- **Minimal System Calls**: Uses efficient system calls to minimize attack surface

### **File System Attack Mitigation**
- **Race Condition Resistance**: Uses atomic file system operations where possible
- **TOCTOU Protection**: Minimizes time between path validation and use
- **Symlink Attack Prevention**: Careful handling of symbolic links to prevent unauthorized access
- **Permission Bypass Prevention**: Validates permissions at each access point

### **Error Handling Security**
- **Fail-Safe Design**: Fails securely when encountering errors rather than exposing information
- **Exception Isolation**: Isolates exceptions to prevent information leakage
- **Consistent Error Response**: Provides consistent error handling across different failure modes
- **Recovery Safety**: Ensures partial results are properly cleaned up on failure

<script src="{{ "/assets/js/dark-mode.js" | relative_url }}"></script>