"""Run-scoped, deny-by-default MCP facade for Rally's Ruflo research tools.

Ruflo's own tool selector narrows discovery but does not reject a direct call
to an unadvertised tool.  This facade is the authority boundary: it validates
the immutable run profile, gives the child a scrubbed per-run environment, and
forwards only the small research surface Rally has reviewed.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, TextIO


AUTHORITY_SCHEMA = "rally.research-authority/v1"
RUFLO_SERVER = "ruflo-research"
RUFLO_VERSION = "3.38.20"
RUN_ID_RE = re.compile(r"^r-[0-9a-z-]{3,77}$")
RESEARCH_TOOLS = (
    "guidance_recommend",
    "guidance_workflow",
    "guidance_quickref",
    "hooks_route",
    "memory_store",
    "memory_retrieve",
    "memory_search",
)
RESEARCH_TOOL_SET = frozenset(RESEARCH_TOOLS)
ALLOWED_METHODS = frozenset({
    "initialize",
    "notifications/initialized",
    "ping",
    "tools/list",
    "tools/call",
})
AUTHORITY_FIELDS = frozenset({
    "schema_version",
    "run_id",
    "mode",
    "server",
    "version",
    "run_dir",
    "workspace",
    "profile_dir",
    "allowed_tools",
    "daemon",
    "federation",
    "persistent_cross_run_memory",
    "ruflo_binary",
    "mcp_config_path",
})
MINIMAL_PATH = "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin"
MAX_MESSAGE_BYTES = 1024 * 1024
MAX_CHILD_NOISE_LINES = 64


class RufloProxyError(RuntimeError):
    """A safe startup or relay failure at the Ruflo authority boundary."""


@dataclass(frozen=True)
class ResearchAuthority:
    run_id: str
    run_dir: str
    workspace: str
    profile_dir: str
    ruflo_binary: str
    mcp_config_path: str


def _real_directory(path: Any, label: str) -> str:
    if not isinstance(path, str) or not os.path.isabs(path):
        raise RufloProxyError(f"{label} must be an absolute directory")
    resolved = os.path.realpath(path)
    if os.path.islink(path) or not os.path.isdir(resolved):
        raise RufloProxyError(f"{label} is not a safe directory")
    return resolved


def _real_file(path: Any, label: str, executable: bool = False) -> str:
    if not isinstance(path, str) or not os.path.isabs(path):
        raise RufloProxyError(f"{label} must be an absolute file")
    resolved = os.path.realpath(path)
    if os.path.islink(path) or not os.path.isfile(resolved):
        raise RufloProxyError(f"{label} is not a safe regular file")
    if executable and not os.access(resolved, os.X_OK):
        raise RufloProxyError(f"{label} is not executable")
    return resolved


def _is_within(path: str, parent: str) -> bool:
    try:
        return os.path.commonpath((path, parent)) == parent
    except ValueError:
        return False


def load_authority(profile: str, workspace: str, ruflo_bin: str) -> ResearchAuthority:
    """Load and validate the complete authority binding for one run."""
    profile_real = _real_directory(profile, "profile")
    workspace_real = _real_directory(workspace, "workspace")
    binary_real = _real_file(ruflo_bin, "ruflo binary", executable=True)
    if os.path.abspath(ruflo_bin) != binary_real:
        raise RufloProxyError("ruflo binary must be passed as its resolved absolute path")

    authority_path = os.path.join(profile_real, "research-authority.json")
    if os.path.islink(authority_path):
        raise RufloProxyError("research authority cannot be a symlink")
    try:
        with open(authority_path, encoding="utf-8") as handle:
            authority = json.load(handle)
    except (OSError, ValueError) as exc:
        raise RufloProxyError("research authority could not be read") from exc
    if not isinstance(authority, dict) or set(authority) != AUTHORITY_FIELDS:
        raise RufloProxyError("research authority has an invalid shape")
    if authority.get("schema_version") != AUTHORITY_SCHEMA:
        raise RufloProxyError("research authority schema is unsupported")
    run_id = authority.get("run_id")
    if not isinstance(run_id, str) or not RUN_ID_RE.fullmatch(run_id):
        raise RufloProxyError("research authority has an invalid run id")
    if authority.get("mode") != "ruflo" or authority.get("server") != RUFLO_SERVER:
        raise RufloProxyError("research authority does not enable the Ruflo facade")
    if authority.get("version") != RUFLO_VERSION:
        raise RufloProxyError("research authority uses an unreviewed Ruflo version")
    if authority.get("allowed_tools") != list(RESEARCH_TOOLS):
        raise RufloProxyError("research authority tool allowlist does not match Rally policy")
    if authority.get("daemon") is not False:
        raise RufloProxyError("Ruflo daemon mode is forbidden")
    if authority.get("federation") is not False:
        raise RufloProxyError("Ruflo federation is forbidden")
    if authority.get("persistent_cross_run_memory") is not False:
        raise RufloProxyError("cross-run Ruflo memory is forbidden")

    run_dir = _real_directory(authority.get("run_dir"), "authority run directory")
    if os.path.basename(run_dir) != run_id:
        raise RufloProxyError("research authority run directory is not bound to its run id")
    state_path = os.path.join(run_dir, "state.json")
    if os.path.islink(state_path) or not os.path.isfile(state_path):
        raise RufloProxyError("research authority run has no authoritative state")
    try:
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
    except (OSError, ValueError) as exc:
        raise RufloProxyError("authoritative run state could not be read") from exc
    if not isinstance(state, dict) or state.get("run_id") != run_id:
        raise RufloProxyError("research authority does not match authoritative run state")
    expected_profile = os.path.join(run_dir, "research")
    expected_workspace = os.path.join(run_dir, "workspace")
    if profile_real != os.path.realpath(expected_profile):
        raise RufloProxyError("profile must be the run's research directory")
    if workspace_real != os.path.realpath(expected_workspace):
        raise RufloProxyError("workspace must be the run's isolated workspace")
    if os.path.realpath(str(authority.get("profile_dir") or "")) != profile_real:
        raise RufloProxyError("CLI profile does not match research authority")
    if os.path.realpath(str(authority.get("workspace") or "")) != workspace_real:
        raise RufloProxyError("CLI workspace does not match research authority")
    if os.path.realpath(str(authority.get("ruflo_binary") or "")) != binary_real:
        raise RufloProxyError("CLI Ruflo binary does not match research authority")
    if os.path.realpath(str(authority.get("run_dir") or "")) != run_dir:
        raise RufloProxyError("research authority run directory is inconsistent")

    mcp_config = _real_file(authority.get("mcp_config_path"), "research MCP config")
    if not _is_within(mcp_config, run_dir):
        raise RufloProxyError("research MCP config escaped its run directory")
    if _is_within(mcp_config, workspace_real):
        raise RufloProxyError("research MCP config cannot be agent-writable")

    return ResearchAuthority(
        run_id=run_id,
        run_dir=run_dir,
        workspace=workspace_real,
        profile_dir=profile_real,
        ruflo_binary=binary_real,
        mcp_config_path=mcp_config,
    )


def _private_directory(profile: str, name: str) -> str:
    path = os.path.join(profile, name)
    if os.path.lexists(path) and (os.path.islink(path) or not os.path.isdir(path)):
        raise RufloProxyError(f"run-private {name} path is unsafe")
    os.makedirs(path, mode=0o700, exist_ok=True)
    os.chmod(path, 0o700)
    resolved = os.path.realpath(path)
    if not _is_within(resolved, profile):
        raise RufloProxyError(f"run-private {name} path escaped its profile")
    return resolved


def child_environment(authority: ResearchAuthority) -> Dict[str, str]:
    """Return a deliberately non-inheriting environment for the Ruflo child."""
    private = {
        "HOME": _private_directory(authority.profile_dir, "home"),
        "XDG_CONFIG_HOME": _private_directory(authority.profile_dir, "xdg-config"),
        "XDG_CACHE_HOME": _private_directory(authority.profile_dir, "xdg-cache"),
        "XDG_DATA_HOME": _private_directory(authority.profile_dir, "xdg-data"),
        "XDG_STATE_HOME": _private_directory(authority.profile_dir, "xdg-state"),
        "XDG_RUNTIME_DIR": _private_directory(authority.profile_dir, "xdg-runtime"),
        "TMPDIR": _private_directory(authority.profile_dir, "tmp"),
    }
    return {
        "PATH": MINIMAL_PATH,
        **private,
        "RUFLO_DAEMON_AUTOSTART": "0",
        "CLAUDE_FLOW_HTTP_FETCH_ALLOW_PRIVATE": "0",
        "CLAUDE_FLOW_HTTP_FETCH_ALLOW_AUTH": "0",
        "CLAUDE_FLOW_MCP_TOOLS": ",".join(RESEARCH_TOOLS),
    }


def _json_line(stream: TextIO, payload: Dict[str, Any]) -> None:
    stream.write(json.dumps(payload, separators=(",", ":"), ensure_ascii=False) + "\n")
    stream.flush()


def _error(request_id: Any, code: int, message: str) -> Dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def _filtered_tool_response(response: Dict[str, Any]) -> Dict[str, Any]:
    if "error" in response:
        return response
    result = response.get("result")
    if not isinstance(result, dict) or not isinstance(result.get("tools"), list):
        raise RufloProxyError("Ruflo returned an invalid tools/list response")
    by_name: Dict[str, Dict[str, Any]] = {}
    for tool in result["tools"]:
        if isinstance(tool, dict) and tool.get("name") in RESEARCH_TOOL_SET:
            by_name[tool["name"]] = tool
    # Stable ordering makes the reviewed surface deterministic even when an
    # upstream Ruflo release changes registry order.
    filtered = [by_name[name] for name in RESEARCH_TOOLS if name in by_name]
    return {**response, "result": {**result, "tools": filtered}}


def _child_response(child: subprocess.Popen, request_id: Any) -> Dict[str, Any]:
    if child.stdout is None:
        raise RufloProxyError("Ruflo stdout is unavailable")
    skipped = 0
    while True:
        line = child.stdout.readline()
        if line == "":
            raise RufloProxyError("Ruflo exited before answering the request")
        if len(line.encode("utf-8", errors="replace")) > MAX_MESSAGE_BYTES:
            raise RufloProxyError("Ruflo returned an oversized message")
        try:
            response = json.loads(line)
        except ValueError:
            skipped += 1
            if skipped > MAX_CHILD_NOISE_LINES:
                raise RufloProxyError("Ruflo emitted too many non-protocol lines")
            continue
        if not isinstance(response, dict):
            skipped += 1
            if skipped > MAX_CHILD_NOISE_LINES:
                raise RufloProxyError("Ruflo returned an invalid protocol response")
            continue
        if response.get("id") == request_id:
            return response
        # Do not let child-originated notifications or unrelated responses widen
        # the facade. The supported request/response exchange is sequential.
        skipped += 1
        if skipped > MAX_CHILD_NOISE_LINES:
            raise RufloProxyError("Ruflo response did not match the pending request")


def _close_child(child: subprocess.Popen) -> None:
    if child.stdin is not None:
        try:
            child.stdin.close()
        except OSError:
            pass
    try:
        child.wait(timeout=3)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(child.pid, signal.SIGTERM)
        except (OSError, ProcessLookupError):
            child.terminate()
        try:
            child.wait(timeout=2)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except (OSError, ProcessLookupError):
                child.kill()
            child.wait(timeout=2)
    finally:
        for stream in (child.stdout, child.stderr):
            if stream is not None:
                try:
                    stream.close()
                except OSError:
                    pass


def serve(
    profile: str,
    workspace: str,
    ruflo_bin: str,
    stdin: TextIO = sys.stdin,
    stdout: TextIO = sys.stdout,
) -> int:
    """Relay one MCP stdio session through Rally's research authority."""
    authority = load_authority(profile, workspace, ruflo_bin)
    command = [authority.ruflo_binary, "mcp", "start"]
    child = subprocess.Popen(
        command,
        cwd=authority.workspace,
        env=child_environment(authority),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        bufsize=1,
        start_new_session=True,
    )
    try:
        for raw_line in stdin:
            if len(raw_line.encode("utf-8", errors="replace")) > MAX_MESSAGE_BYTES:
                _json_line(stdout, _error(None, -32600, "Invalid Request"))
                continue
            try:
                request = json.loads(raw_line)
            except ValueError:
                _json_line(stdout, _error(None, -32700, "Parse error"))
                continue
            if (
                not isinstance(request, dict)
                or request.get("jsonrpc") != "2.0"
                or not isinstance(request.get("method"), str)
            ):
                _json_line(stdout, _error(None, -32600, "Invalid Request"))
                continue
            method = request["method"]
            request_id = request.get("id") if "id" in request else None
            if method not in ALLOWED_METHODS:
                if "id" in request:
                    _json_line(stdout, _error(request_id, -32601, "Method not found"))
                continue
            if method == "notifications/initialized":
                if "id" in request:
                    _json_line(stdout, _error(request_id, -32600, "Invalid Request"))
                    continue
                if child.stdin is None:
                    raise RufloProxyError("Ruflo stdin is unavailable")
                _json_line(child.stdin, request)
                continue
            if "id" not in request:
                _json_line(stdout, _error(None, -32600, "Invalid Request"))
                continue
            if method == "tools/call":
                params = request.get("params")
                tool_name = params.get("name") if isinstance(params, dict) else None
                if tool_name not in RESEARCH_TOOL_SET:
                    _json_line(stdout, _error(request_id, -32601, "Tool not found"))
                    continue
            if child.stdin is None:
                raise RufloProxyError("Ruflo stdin is unavailable")
            _json_line(child.stdin, request)
            response = _child_response(child, request_id)
            if method == "tools/list":
                response = _filtered_tool_response(response)
            _json_line(stdout, response)
    finally:
        _close_child(child)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rally-ruflo",
        description="Run Rally's isolated Ruflo research MCP facade.",
        allow_abbrev=False,
    )
    parser.add_argument("--profile", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--ruflo-bin", required=True)
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    os.umask(0o077)
    try:
        return serve(args.profile, args.workspace, args.ruflo_bin)
    except (OSError, RufloProxyError, subprocess.SubprocessError) as exc:
        print(f"rally-ruflo: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
