# TailscaleDetector.get_tailscale_ip()

Static method for obtaining the local Tailscale IP address.

## Overview

Executes the `tailscale ip --4` command to retrieve the local machine's Tailscale IPv4 address. This method provides the primary mechanism for determining the sender's network endpoint when establishing file transfer connections over Tailscale networks.

## Call Graph

```mermaid
graph LR
    send_files["send_files()"]
    get_tailscale_ip["get_tailscale_ip()"]
    subprocess_run["subprocess.run()"]

    send_files --> get_tailscale_ip
    get_tailscale_ip --> subprocess_run
```

## Parameters

**None** - This is a static method that requires no instance or parameters.

## Return Value

- **Type**: `Optional[str]`
- **Success**: IPv4 address string in dotted decimal notation (e.g., `"100.101.29.44"`)
- **Failure**: `None` if Tailscale is unavailable, stopped, or command execution fails

## Requirements

get_tailscale_ip() shall execute "tailscale ip --4" command when method is invoked where the command retrieves the local IPv4 address.

get_tailscale_ip() shall return IPv4 address string when Tailscale command succeeds where the address is in dotted decimal notation.

get_tailscale_ip() shall return None when Tailscale is not installed or not running where failure indicates unavailable service.

get_tailscale_ip() shall validate IP address format when command output is received where validation ensures proper IPv4 format.

get_tailscale_ip() shall timeout after 5 seconds when command execution hangs where timeout prevents indefinite blocking.
