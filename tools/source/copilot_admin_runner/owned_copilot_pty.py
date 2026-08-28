from __future__ import annotations

import argparse
import ctypes
import json
import os
import queue
import subprocess
import sys
import threading
import time
import uuid
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from project_session_registry import mark_session_stopped, upsert_session


REPO_ROOT = Path(__file__).resolve().parents[3]
LOG_DIR = REPO_ROOT / "tmp" / "copilot_admin_runner_logs"
STATE_DIR = REPO_ROOT / "tmp" / "copilot_admin_runner_state"

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

HRESULT = ctypes.c_long
HPCON = wintypes.HANDLE
PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE = 0x00020016
EXTENDED_STARTUPINFO_PRESENT = 0x00080000
STARTF_USESTDHANDLES = 0x00000100
CREATE_UNICODE_ENVIRONMENT = 0x00000400


class COORD(ctypes.Structure):
    _fields_ = [("X", ctypes.c_short), ("Y", ctypes.c_short)]


class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [
        ("nLength", wintypes.DWORD),
        ("lpSecurityDescriptor", wintypes.LPVOID),
        ("bInheritHandle", wintypes.BOOL),
    ]


class STARTUPINFOEXW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("lpReserved", wintypes.LPWSTR),
        ("lpDesktop", wintypes.LPWSTR),
        ("lpTitle", wintypes.LPWSTR),
        ("dwX", wintypes.DWORD),
        ("dwY", wintypes.DWORD),
        ("dwXSize", wintypes.DWORD),
        ("dwYSize", wintypes.DWORD),
        ("dwXCountChars", wintypes.DWORD),
        ("dwYCountChars", wintypes.DWORD),
        ("dwFillAttribute", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("wShowWindow", wintypes.WORD),
        ("cbReserved2", wintypes.WORD),
        ("lpReserved2", ctypes.POINTER(ctypes.c_byte)),
        ("hStdInput", wintypes.HANDLE),
        ("hStdOutput", wintypes.HANDLE),
        ("hStdError", wintypes.HANDLE),
        ("lpAttributeList", wintypes.LPVOID),
    ]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("hProcess", wintypes.HANDLE),
        ("hThread", wintypes.HANDLE),
        ("dwProcessId", wintypes.DWORD),
        ("dwThreadId", wintypes.DWORD),
    ]


kernel32.CreatePipe.argtypes = [
    ctypes.POINTER(wintypes.HANDLE),
    ctypes.POINTER(wintypes.HANDLE),
    ctypes.POINTER(SECURITY_ATTRIBUTES),
    wintypes.DWORD,
]
kernel32.CreatePipe.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.CreatePseudoConsole.argtypes = [
    COORD,
    wintypes.HANDLE,
    wintypes.HANDLE,
    wintypes.DWORD,
    ctypes.POINTER(HPCON),
]
kernel32.CreatePseudoConsole.restype = HRESULT
kernel32.ClosePseudoConsole.argtypes = [HPCON]
kernel32.ClosePseudoConsole.restype = None
kernel32.InitializeProcThreadAttributeList.argtypes = [
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.DWORD,
    ctypes.POINTER(ctypes.c_size_t),
]
kernel32.InitializeProcThreadAttributeList.restype = wintypes.BOOL
kernel32.UpdateProcThreadAttribute.argtypes = [
    wintypes.LPVOID,
    wintypes.DWORD,
    ctypes.c_size_t,
    wintypes.LPVOID,
    ctypes.c_size_t,
    wintypes.LPVOID,
    ctypes.POINTER(ctypes.c_size_t),
]
kernel32.UpdateProcThreadAttribute.restype = wintypes.BOOL
kernel32.DeleteProcThreadAttributeList.argtypes = [wintypes.LPVOID]
kernel32.DeleteProcThreadAttributeList.restype = None
kernel32.CreateProcessW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.LPWSTR,
    wintypes.LPVOID,
    wintypes.LPVOID,
    wintypes.BOOL,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.LPCWSTR,
    ctypes.POINTER(STARTUPINFOEXW),
    ctypes.POINTER(PROCESS_INFORMATION),
]
kernel32.CreateProcessW.restype = wintypes.BOOL
kernel32.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
kernel32.WaitForSingleObject.restype = wintypes.DWORD
kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
kernel32.GetExitCodeProcess.restype = wintypes.BOOL
kernel32.TerminateProcess.argtypes = [wintypes.HANDLE, wintypes.UINT]
kernel32.TerminateProcess.restype = wintypes.BOOL
kernel32.WriteFile.argtypes = [
    wintypes.HANDLE,
    wintypes.LPCVOID,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPVOID,
]
kernel32.WriteFile.restype = wintypes.BOOL
kernel32.ReadFile.argtypes = [
    wintypes.HANDLE,
    wintypes.LPVOID,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPVOID,
]
kernel32.ReadFile.restype = wintypes.BOOL


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def win_error(message: str) -> OSError:
    return ctypes.WinError(ctypes.get_last_error(), message)


def check_bool(result: int, message: str) -> None:
    if not result:
        raise win_error(message)


def check_hr(hr: int, message: str) -> None:
    if hr < 0:
        raise OSError(hr, message)


def log_path() -> Path:
    return LOG_DIR / f"owned-copilot-pty-{datetime.now(timezone.utc).strftime('%Y%m%d')}.jsonl"


def log_event(event: str, details: dict[str, Any] | None = None) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": utc_now(),
        "event_id": uuid.uuid4().hex,
        "event": event,
        "pid": os.getpid(),
        "repo_root": str(REPO_ROOT),
        "details": details or {},
    }
    with log_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def quote_command(parts: list[str]) -> str:
    return subprocess.list2cmdline(parts)


class ConPtySession:
    def __init__(self, command_line: str, cols: int = 120, rows: int = 40) -> None:
        self.command_line = command_line
        self.cols = cols
        self.rows = rows
        self.hpc: HPCON | None = None
        self.pi = PROCESS_INFORMATION()
        self.h_in_write = wintypes.HANDLE()
        self.h_out_read = wintypes.HANDLE()
        self.output_queue: queue.Queue[bytes] = queue.Queue()
        self.reader_thread: threading.Thread | None = None

    def start(self) -> None:
        sa = SECURITY_ATTRIBUTES()
        sa.nLength = ctypes.sizeof(SECURITY_ATTRIBUTES)
        sa.bInheritHandle = True

        h_in_read = wintypes.HANDLE()
        h_out_write = wintypes.HANDLE()
        check_bool(kernel32.CreatePipe(ctypes.byref(h_in_read), ctypes.byref(self.h_in_write), ctypes.byref(sa), 0), "Create input pipe")
        check_bool(kernel32.CreatePipe(ctypes.byref(self.h_out_read), ctypes.byref(h_out_write), ctypes.byref(sa), 0), "Create output pipe")

        hpc = HPCON()
        hr = kernel32.CreatePseudoConsole(COORD(self.cols, self.rows), h_in_read, h_out_write, 0, ctypes.byref(hpc))
        check_hr(hr, "CreatePseudoConsole")
        self.hpc = hpc
        kernel32.CloseHandle(h_in_read)
        kernel32.CloseHandle(h_out_write)

        attr_size = ctypes.c_size_t(0)
        kernel32.InitializeProcThreadAttributeList(None, 1, 0, ctypes.byref(attr_size))
        attr_list = ctypes.create_string_buffer(attr_size.value)
        check_bool(kernel32.InitializeProcThreadAttributeList(attr_list, 1, 0, ctypes.byref(attr_size)), "InitializeProcThreadAttributeList")
        check_bool(
            kernel32.UpdateProcThreadAttribute(
                attr_list,
                0,
                PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE,
                hpc,
                ctypes.sizeof(hpc),
                None,
                None,
            ),
            "UpdateProcThreadAttribute",
        )

        si = STARTUPINFOEXW()
        si.cb = ctypes.sizeof(STARTUPINFOEXW)
        si.lpAttributeList = ctypes.cast(attr_list, wintypes.LPVOID)
        si.dwFlags = STARTF_USESTDHANDLES

        cmd = ctypes.create_unicode_buffer(self.command_line)
        success = kernel32.CreateProcessW(
            None,
            cmd,
            None,
            None,
            False,
            EXTENDED_STARTUPINFO_PRESENT | CREATE_UNICODE_ENVIRONMENT,
            None,
            str(REPO_ROOT),
            ctypes.byref(si),
            ctypes.byref(self.pi),
        )
        kernel32.DeleteProcThreadAttributeList(attr_list)
        check_bool(success, f"CreateProcessW: {self.command_line}")
        log_event("conpty_process_started", {"command_line": self.command_line, "process_id": int(self.pi.dwProcessId)})

        self.reader_thread = threading.Thread(target=self._read_output, daemon=True)
        self.reader_thread.start()

    def _read_output(self) -> None:
        buffer = ctypes.create_string_buffer(4096)
        while True:
            bytes_read = wintypes.DWORD(0)
            ok = kernel32.ReadFile(self.h_out_read, buffer, len(buffer), ctypes.byref(bytes_read), None)
            if not ok or bytes_read.value == 0:
                break
            data = bytes(buffer.raw[: bytes_read.value])
            self.output_queue.put(data)

    def write(self, text: str) -> None:
        data = text.encode("utf-8")
        written = wintypes.DWORD(0)
        check_bool(kernel32.WriteFile(self.h_in_write, data, len(data), ctypes.byref(written), None), "WriteFile")

    def wait(self, timeout_seconds: int) -> int | None:
        wait = kernel32.WaitForSingleObject(self.pi.hProcess, timeout_seconds * 1000)
        if wait == 0x102:
            return None
        exit_code = wintypes.DWORD(0)
        check_bool(kernel32.GetExitCodeProcess(self.pi.hProcess, ctypes.byref(exit_code)), "GetExitCodeProcess")
        return int(exit_code.value)

    def terminate(self) -> None:
        if self.pi.hProcess:
            kernel32.TerminateProcess(self.pi.hProcess, 1)

    def close(self) -> None:
        for handle in (self.h_in_write, self.h_out_read, self.pi.hThread, self.pi.hProcess):
            if handle:
                kernel32.CloseHandle(handle)
        if self.hpc:
            kernel32.ClosePseudoConsole(self.hpc)


def drain_output(session: ConPtySession, seconds: float, mirror: bool) -> str:
    end = time.time() + seconds
    chunks: list[bytes] = []
    while time.time() < end:
        try:
            data = session.output_queue.get(timeout=0.1)
        except queue.Empty:
            continue
        chunks.append(data)
        if mirror:
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
    return b"".join(chunks).decode("utf-8", errors="replace")


def run_probe(_: argparse.Namespace) -> int:
    session = ConPtySession(quote_command(["cmd.exe", "/d", "/c", "echo conpty-probe-ok"]))
    session.start()
    output = drain_output(session, 3, False)
    exit_code = session.wait(5)
    session.close()
    payload = {
        "status": "passed" if "conpty-probe-ok" in output and exit_code == 0 else "failed",
        "mode": "probe",
        "exit_code": exit_code,
        "output": output,
        "log_path": str(log_path()),
    }
    log_event("probe_completed", payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["status"] == "passed" else 1


def run_scripted(args: argparse.Namespace) -> int:
    if not args.command:
        raise ValueError("scripted requires a command after --")
    command_parts = args.command
    if command_parts and command_parts[0] == "--":
        command_parts = command_parts[1:]
    command = quote_command(command_parts)
    session = ConPtySession(command)
    session.start()
    output = drain_output(session, args.initial_wait, args.mirror)
    for line in args.send_line:
        session.write(line + "\r")
        output += drain_output(session, args.after_send_wait, args.mirror)
    exit_code = session.wait(args.exit_wait)
    output += drain_output(session, 1, args.mirror)
    if exit_code is None:
        session.terminate()
        log_event("scripted_timeout_terminated", {"command": command, "timeout_seconds": args.exit_wait})
    session.close()
    status = "completed" if exit_code is not None else "timeout_terminated"
    payload = {
        "status": status,
        "mode": "scripted",
        "command": command,
        "exit_code": exit_code,
        "captured_output_tail": output[-4000:],
        "log_path": str(log_path()),
        "conclusion": (
            "Runner-owned ConPTY stdin/stdout worked for this command."
            if exit_code is not None
            else "The command did not complete through ConPTY before timeout and was terminated."
        ),
    }
    log_event("scripted_completed", {k: v for k, v in payload.items() if k != "captured_output_tail"})
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def run_interactive(args: argparse.Namespace) -> int:
    command = quote_command(["copilot"])
    session = ConPtySession(command)
    session.start()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_path = STATE_DIR / "owned-copilot-conpty-session.json"
    session_key = f"owned-conpty::{state_path}"
    state_path.write_text(
        json.dumps(
            {
                "status": "running",
                "started_at": utc_now(),
                "repo_root": str(REPO_ROOT),
                "command": command,
                "log_path": str(log_path()),
                "mode": "interactive-conpty",
                "note": "This wrapper owns the ConPTY streams and mirrors output to this console. Type here to send input to Copilot.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    upsert_session(
        session_key,
        kind="owned-conpty",
        source="tools\\source\\copilot_admin_runner\\owned_copilot_pty.py",
        status="running",
        control_method="process-id",
        state_path=str(state_path),
        wrapper_pid=os.getpid(),
        process_id=int(session.pi.dwProcessId),
        note="interactive ConPTY Copilot POC",
    )
    log_event("interactive_started", {"command": command, "state_path": str(state_path)})

    def mirror_output() -> None:
        while True:
            try:
                data = session.output_queue.get(timeout=0.2)
            except queue.Empty:
                if session.wait(0) is not None:
                    break
                continue
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()

    thread = threading.Thread(target=mirror_output, daemon=True)
    thread.start()
    try:
        for line in sys.stdin:
            session.write(line.rstrip("\n") + "\r")
    except KeyboardInterrupt:
        log_event("interactive_keyboard_interrupt")
    finally:
        mark_session_stopped(session_key)
        session.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Windows ConPTY POC for runner-owned Copilot sessions.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    probe = subparsers.add_parser("probe", help="Run a safe ConPTY echo probe.")
    probe.set_defaults(func=run_probe)

    scripted = subparsers.add_parser("scripted", help="Run a command through ConPTY with optional scripted input.")
    scripted.add_argument("--send-line", action="append", default=[])
    scripted.add_argument("--initial-wait", type=float, default=1.0)
    scripted.add_argument("--after-send-wait", type=float, default=1.0)
    scripted.add_argument("--exit-wait", type=int, default=5)
    scripted.add_argument("--mirror", action="store_true")
    scripted.add_argument("command", nargs=argparse.REMAINDER)
    scripted.set_defaults(func=run_scripted)

    interactive = subparsers.add_parser("interactive-copilot", help="Start Copilot in a ConPTY wrapper.")
    interactive.set_defaults(func=run_interactive)
    return parser


def main() -> int:
    if os.name != "nt":
        raise RuntimeError("ConPTY POC requires Windows.")
    args = build_parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
