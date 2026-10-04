#!/usr/bin/env python3
"""Opt-in updater runner. OS locks survive slow clients and release on process exit."""
import fcntl
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def run(args):
    cache, client, binary, marketplace, plugin, debounce, max_bytes = args
    root = Path(cache)
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    root.chmod(0o700)
    os.umask(0o077)
    # Never unlink this inode: replacing an advisory-lock file splits the lock.
    with (root / "update.lockfile").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        stamp = root / "last-update"
        if stamp.exists() and time.time() - stamp.stat().st_mtime < int(debounce):
            return
        try:
            timeout = min(25, max(1, int(os.environ.get("AGENTIX_PLUGIN_AUTO_UPDATE_TIMEOUT_SEC", "20"))))
        except ValueError:
            timeout = 20
        deadline = time.monotonic() + timeout
        commands = [[binary, "plugin", "marketplace", "upgrade" if client == "codex" else "update", marketplace],
                    [binary, "plugin", "add" if client == "codex" else "update", plugin]]
        log_path = root / "update.log"
        try:
            with log_path.open("ab", buffering=0) as log:
                log.write((time.strftime("--- %Y-%m-%dT%H:%M:%SZ ---\n", time.gmtime())).encode())
                for command in commands:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        break
                    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                               start_new_session=True, pass_fds=(lock.fileno(),))
                    try:
                        process.wait(timeout=remaining)
                    except subprocess.TimeoutExpired:
                        log.write(b"Updater deadline reached.\n")
                        break
                    finally:
                        if process.poll() is None:
                            try:
                                os.killpg(process.pid, signal.SIGKILL)
                            except ProcessLookupError:
                                pass
                            process.wait()
        finally:
            # Bound the private log even on interruption; no output is sent to chat.
            if log_path.exists() and log_path.stat().st_size > int(max_bytes):
                with log_path.open("rb") as source:
                    source.seek(-int(max_bytes), os.SEEK_END)
                    tail = source.read()
                log_path.write_bytes(tail)
            temp = root / f"last-update.{os.getpid()}"
            temp.write_text(time.strftime("%Y-%m-%dT%H:%M:%SZ\n", time.gmtime()))
            temp.replace(stamp)


def interrupted(_signal, _frame):
    raise SystemExit(0)


if __name__ == "__main__":
    for item in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(item, interrupted)
    run(sys.argv[1:])
