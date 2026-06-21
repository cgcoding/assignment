"""Problem 1 - JIT compilation with PyPy.

Run under pypy3 for the JIT parts (Q2-Q4):

    pypy3 q1.py                                   # Q2: hotspot iterations (compile hook)
    PYPYLOG=jit-log-opt:my_trace.log pypy3 q1.py  # Q3: optimized interpreter trace
    PYPYLOG=jit-backend:dump.asm   pypy3 q1.py    # Q4: backend machine code

Q1 (the `total1 += i` bytecode) can be inspected with CPython via `dis`.
"""

import time

try:
    import pypyjit
    HAVE_PYPY = True
except ImportError:  # CPython - JIT parts (Q2-Q4) are unavailable
    pypyjit = None
    HAVE_PYPY = False

loop2_counter = 0
loop3_counter = 0


def on_compile(info):
    print("JIT compiled loop: type=", getattr(info, "type", "?"),
          "no=", getattr(info, "loop_no", "unknown"))
    print("loop2_counter =", loop2_counter, "loop3_counter =", loop3_counter)


def two_loops_series(n):
    global loop2_counter, loop3_counter
    total1 = 0
    for i in range(n):           # Loop 2 - a hotspot
        loop2_counter += 1
        total1 += i
    mid = total1 * 2
    offset = mid + 7
    temp = offset - total1
    total2 = 0
    for j in range(n):           # Loop 3 - a hotspot
        loop3_counter += 1
        total2 += j * temp
    return total1, total2, temp


if __name__ == "__main__":
    if HAVE_PYPY:
        pypyjit.set_compile_hook(on_compile, False)
    for _ in range(5):           # Loop 1 - NOT a hotspot
        result = two_loops_series(300)
    end = time.time()
    print(f"Result: {result}")
