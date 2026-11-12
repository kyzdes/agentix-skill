"""Updater tests invoke only local fake CLIs, including the real hook command."""
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AutoUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="agentix-updater-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.calls = self.root / "calls"
        mock = self.bin / "codex"
        mock.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "$AGENTIX_TEST_CALLS_PATH"\nsleep "${AGENTIX_TEST_SLEEP:-0}"\n')
        mock.chmod(0o700)
        self.env = {**os.environ, "PATH": f"{self.bin}:{os.environ['PATH']}",
                    "PLUGIN_DATA": str(self.root / "data"), "AGENTIX_PLUGIN_AUTO_UPDATE": "1",
                    "AGENTIX_PLUGIN_CACHE_ROOT": str(self.root / "cache"),
                    "AGENTIX_TEST_CALLS_PATH": str(self.calls)}
        self.command = ["bash", str(ROOT / "scripts/auto-update.sh")]

    def run_update(self, **changes):
        return subprocess.run(self.command, env={**self.env, **changes}, capture_output=True, timeout=6, check=True)

    def wait_started(self):
        until = time.monotonic() + 3
        while not self.calls.exists() and time.monotonic() < until:
            time.sleep(.02)
        self.assertTrue(self.calls.exists())

    def update_once_lock_frees(self):
        # The killed client group shares the lock; it frees a moment after the owner exits.
        until = time.monotonic() + 3
        while len(self.calls.read_text().splitlines()) < 3 and time.monotonic() < until:
            self.run_update(AGENTIX_PLUGIN_AUTO_UPDATE_INTERVAL_SEC="0")
            time.sleep(.05)

    def test_opt_in_and_debounce(self):
        self.run_update(AGENTIX_PLUGIN_AUTO_UPDATE="0")
        self.assertFalse(self.calls.exists())
        self.run_update()
        self.run_update()
        self.assertEqual(self.calls.read_text().splitlines(), ["plugin marketplace upgrade agentix", "plugin add agentix@agentix"])

    def test_hook_handles_root_with_spaces(self):
        plugin = self.root / "plugin with spaces"
        plugin.symlink_to(ROOT, target_is_directory=True)
        hook = json.loads((ROOT / "hooks/hooks.json").read_text())["hooks"]["SessionStart"][0]["hooks"][0]["command"]
        subprocess.run(["bash", "-c", hook], env={**self.env, "PLUGIN_ROOT": str(plugin)}, timeout=6, check=True)
        self.assertEqual(len(self.calls.read_text().splitlines()), 2)

    def test_slow_owner_keeps_lock_and_deadline_stops_client(self):
        proc = subprocess.Popen(self.command, env={**self.env, "AGENTIX_TEST_SLEEP": "5", "AGENTIX_PLUGIN_AUTO_UPDATE_TIMEOUT_SEC": "1"})
        try:
            self.wait_started()
            # Age cannot revoke an OS lock held by a live updater.
            lock = self.root / "cache/update.lockfile"
            os.utime(lock, (1, 1))
            self.run_update(AGENTIX_PLUGIN_AUTO_UPDATE_INTERVAL_SEC="0")
            self.assertEqual(len(self.calls.read_text().splitlines()), 1)
            proc.wait(timeout=4)
            self.assertIn("deadline", (self.root / "cache/update.log").read_text())
            self.update_once_lock_frees()
            self.assertEqual(len(self.calls.read_text().splitlines()), 3)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()

    def test_interrupted_owner_releases_lock(self):
        proc = subprocess.Popen(self.command, env={**self.env, "AGENTIX_TEST_SLEEP": "5"})
        try:
            self.wait_started()
            proc.send_signal(signal.SIGTERM)
            proc.wait(timeout=3)
            self.update_once_lock_frees()
            self.assertEqual(len(self.calls.read_text().splitlines()), 3)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()


if __name__ == "__main__":
    unittest.main()
