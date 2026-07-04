import gdb


def _read_first_register(*names):
    for name in names:
        try:
            return int(gdb.parse_and_eval(f"${name}"))
        except gdb.error:
            continue
    raise gdb.error("No matching register found")


def _stack_bytes(addr):
    inferior = gdb.selected_inferior()
    return bytes(inferior.read_memory(addr, 8))


def _fmt_bytes(raw):
    return " ".join(f"{b:02x}" for b in raw)


def print_stack():
    try:
        # x86-64 uses rsp/rbp; AArch64 uses sp/x29 for stack/frame pointers.
        rsp = _read_first_register("rsp", "sp")
        rbp = _read_first_register("rbp", "x29", "fp")
    except gdb.error:
        return

    print(f"\nrsp = 0x{rsp:x}, rbp = 0x{rbp:x}")

    start = rsp
    end = rbp + 16
    if end < start:
        start, end = end, start

    addr = start
    while addr <= end:
        print("+-------------------------+")
        raw = _stack_bytes(addr)
        labels = []
        if addr == rsp:
            labels.append("rsp")
        if addr == rbp:
            labels.append("rbp")
        suffix = f" <- {' '.join(labels)}" if labels else ""
        print(f"| {_fmt_bytes(raw)} |{suffix}")
        addr += 8
    print("+-------------------------+")


def _on_stop(event):
    del event
    print_stack()


gdb.events.stop.connect(_on_stop)
print("[stack.py] Stack visualizer loaded. It will print the stack whenever execution stops.")
