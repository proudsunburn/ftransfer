# FileWriter Class

Manages incremental file writing with hash tracking and automatic resume capability.

## Overview

Core class responsible for efficient, memory-safe file writing during transfers. Implements `.part` file management, SHA-256 hash tracking, automatic conflict resolution, and seamless integration with the TransferLockManager for resume functionality. Ensures files are written incrementally to disk without RAM accumulation.

## Class Definition

```python
class FileWriter:
    """Manages incremental file writing with hash tracking for resume capability"""

    def __init__(self, filename: str, size: int, offset: int,
                 lock_manager: 'TransferLockManager' = None,
                 overwrite_mode: bool = False):
        self.filename = filename
        self.size = size
        self.offset = offset
        self.written = 0
        self.hasher = hashlib.sha256()
        self.part_file = Path(f"{filename}.part")
        self.is_complete = False
        self.lock_manager = lock_manager
        self.needs_rehash = False
        self.overwrite_mode = overwrite_mode
```

## Key Methods

### open_for_writing()
Prepares file for writing with optional resume from specific byte offset.

**Parameters:**
- `resume_bytes` (int): Number of bytes already written (from lock file)

**Features:**
- Creates parent directories automatically
- Validates partial file size against expected resume position
- Sets `needs_rehash` flag when resuming to verify existing data
- Handles size mismatches by starting fresh
- Marks file as complete if already fully transferred

### write_chunk()
Writes data chunk to disk and updates hash incrementally.

**Parameters:**
- `data` (bytes): Chunk of data to write

**Returns:** `int` - Number of bytes actually written

**Features:**
- **Immediate Disk Write**: Opens file, writes data, closes immediately (no lingering handles)
- **Memory Efficient**: No buffering - data written directly to disk
- **Hash Tracking**: Updates SHA-256 hash for integrity verification
- **Partial Resume Support**: Handles both fresh writes (`wb`) and resume appends (`ab`)
- **Automatic Completion**: Calls `complete_file()` when size reached
- **Lock Integration**: Updates TransferLockManager with progress
- **Error Resilient**: Gracefully handles OSError with warning logging

### complete_file()
Finalizes file by moving from `.part` to final name with conflict resolution.

**Features:**
- **Overwrite Mode**: Removes existing files/directories when enabled
- **Conflict Resolution**: Adds `_1`, `_2`, etc. suffixes to avoid overwrites
- **Atomic Rename**: Uses `.part` to final rename for safety
- **Hash Finalization**: Stores final SHA-256 hash in lock file
- **Status Update**: Marks file as "completed" in TransferLockManager

**Conflict Resolution Logic:**
```python
# Non-overwrite mode (default):
document.pdf       # If exists
document_1.pdf     # Creates this
document_2.pdf     # If _1 also exists

# Overwrite mode:
document.pdf       # Removes existing
document.pdf       # Creates new version
```

### _ensure_resume_hash()
Verifies existing partial data by rehashing (called once on first write).

**Features:**
- **Deferred Hashing**: Only hashes when first chunk is written
- **Efficiency**: Rehashing happens in background, not at startup
- **Integrity**: Ensures resumed data matches expected hash
- **Fallback**: Starts fresh if rehashing fails
- **Lock Update**: Stores partial hash in lock file for verification

### reset_for_retry()
Resets file writer state for retry after integrity failure.

**Features:**
- Clears hash and written byte counter
- Removes corrupted `.part` file
- Updates lock file to "pending" status
- Prepares for clean retransfer

### needs_data()
Checks if this file needs data at given stream position.

**Parameters:**
- `stream_position` (int): Current position in unified stream

**Returns:** `bool` - True if this file needs data at position

**Use Case:** Multi-file transfers with streaming protocol

### get_hash()
Returns current SHA-256 hash of written data.

**Returns:** `str` - Hexadecimal hash string

### close()
Closes file handle (no-op since handles never kept open).

## Memory-Efficient Architecture

### No File Handle Lingering
```python
# Traditional approach (WRONG - keeps file open):
self.file_handle = open(filename, 'wb')
self.file_handle.write(data)
# Handle stays open!

# FileWriter approach (CORRECT - immediate close):
with open(self.part_file, 'ab') as f:
    f.write(chunk_to_write)
    f.flush()  # Ensure disk write
# Handle closed immediately
```

### Benefits
- **No FD Exhaustion**: Can handle thousands of files without hitting OS limits
- **Immediate Persistence**: Data on disk immediately, survives crashes
- **No RAM Accumulation**: Memory usage constant regardless of transfer size
- **Clean State**: No cleanup required, files always in consistent state

## Part File System

### File Lifecycle
```mermaid
graph LR
    start["Start transfer"]
    create["Create filename.part"]
    write["Write chunks incrementally"]
    verify["Verify final hash"]
    rename["Rename to filename"]

    start --> create
    create --> write
    write --> verify
    verify --> rename
```

### Resume Lifecycle
```mermaid
graph LR
    resume["Resume transfer"]
    check["Check filename.part"]
    rehash["Rehash existing data"]
    continue["Continue writing"]
    verify["Verify final hash"]
    rename["Rename to filename"]

    resume --> check
    check --> rehash
    rehash --> continue
    continue --> verify
    verify --> rename
```

## Hash Verification System

### Incremental Hashing
- **Real-Time**: Hash updated with each chunk write
- **Resume Safe**: Rehashes existing data when resuming
- **Verification**: Final hash compared with sender's hash
- **Retry Capable**: Failed verification triggers retry (up to 3 attempts)

### Hash Storage
```python
# Lock file stores two types of hashes:
"files": {
  "document.pdf": {
    "partial_hash": "abc123...",  # Hash of partial .part file
    "original_hash": "def456..."  # Hash of complete source file
  }
}
```

## Conflict Resolution

### Default Behavior (overwrite_mode=False)
Preserves existing files by adding numeric suffixes:
- Detects existing `filename.ext`
- Creates `filename_1.ext`
- If that exists, creates `filename_2.ext`
- Continues until unique name found

### Overwrite Mode (overwrite_mode=True)
Replaces existing files:
- Removes existing file/directory
- Creates new version with original name
- Falls back to suffix mode if removal fails

## Error Handling

### Write Errors
- **OSError during write**: Logged to `transfer_warnings.log`, returns 0 bytes written
- **Permission denied**: Logged, transfer continues (skips file)
- **Disk full**: Caught and logged, transfer stops gracefully

### Completion Errors
- **Rename failures**: Logged, falls back to suffix conflict resolution
- **Overwrite failures**: Falls back to non-overwrite mode with warning

### Resume Errors
- **Size mismatch**: Starts fresh automatically
- **Rehash failure**: Starts fresh automatically
- **Corrupted .part file**: Removed and retransferred

## Integration Points

### TransferLockManager Integration
- **Progress Tracking**: Every chunk write updates lock file (batched)
- **Status Updates**: "pending" → "in_progress" → "completed"
- **Hash Storage**: Partial and final hashes stored in lock
- **Resume Coordination**: Lock provides resume byte offset

### Receiver Integration
- **Creation**: Receiver creates FileWriter for each incoming file
- **Resume**: Lock manager provides resume offset to constructor
- **Progress Display**: Written bytes used for progress calculation
- **Completion**: Triggers next file in sequence

## Performance Optimizations

### Batched Lock Updates
Lock file not updated on every single chunk:
- Updates batched (150 pending updates or 2 second intervals)
- Reduces disk I/O overhead by 95%+
- Maintains accurate resume state

### Immediate Flush
```python
f.flush()  # Forces OS to write data to disk
```
- Ensures crash resilience
- Data persisted immediately, not buffered
- Critical for resume functionality

### No Buffering
- No in-memory accumulation
- Each chunk written directly to disk
- Memory usage: ~64KB constant (chunk size)

## Security Features

### Path Traversal Protection
- `Path()` normalization prevents `../../etc/passwd` attacks
- Parent directory validation before write
- Safe filename handling

### Integrity Verification
- SHA-256 hash verification on completion
- Automatic retry on hash mismatch (up to 3 attempts)
- Partial hash verification on resume

### Atomic Operations
- `.part` file ensures incomplete transfers never masquerade as complete
- Rename operation is atomic on POSIX systems
- No partial-state confusion

## Example Usage

### Basic Usage
```python
# Create writer
writer = FileWriter("document.pdf", size=1234567, offset=0)
writer.open_for_writing()

# Write chunks
while data := receive_chunk():
    bytes_written = writer.write_chunk(data)

# Automatic completion when size reached
```

### Resume Usage
```python
# Load resume state from lock
resume_bytes = lock_manager.get_resume_bytes("document.pdf")

# Create writer with lock manager
writer = FileWriter("document.pdf", size=1234567, offset=0,
                   lock_manager=lock_manager)
writer.open_for_writing(resume_bytes=resume_bytes)

# Continue from where we left off
while data := receive_chunk():
    bytes_written = writer.write_chunk(data)
```

### Retry Usage
```python
# If hash verification fails
if writer.get_hash() != expected_hash:
    writer.reset_for_retry()
    # Retransfer the file
```
