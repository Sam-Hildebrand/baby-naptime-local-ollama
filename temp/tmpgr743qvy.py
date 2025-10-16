import traceback, sys
try:
    # Attempt to import the exploit code (the same as before) to see if it compiles
    import struct, subprocess, time
    print("Modules imported OK")
except Exception as e:
    traceback.print_exc()
