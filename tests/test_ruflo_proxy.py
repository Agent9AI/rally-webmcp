import io
import json
import os
import stat
import sys
import tempfile
import textwrap
import unittest
from unittest import mock


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import ruflo_proxy as proxy  # noqa: E402


FAKE_RUFLO = r'''#!/usr/bin/env python3
import json
import os
import pathlib
import sys

profile = pathlib.Path(os.environ["HOME"]).parent
(profile / "child-env.json").write_text(json.dumps(dict(os.environ)), encoding="utf-8")
forwarded = profile / "forwarded.jsonl"
with forwarded.open("a", encoding="utf-8") as log:
    for line in sys.stdin:
        message = json.loads(line)
        log.write(json.dumps(message) + "\n")
        log.flush()
        method = message.get("method")
        if method == "notifications/initialized":
            continue
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "fake-ruflo", "version": "3.38.20"},
                "capabilities": {"tools": {}},
            }
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            names = [
                "guidance_recommend", "guidance_workflow", "guidance_quickref",
                "hooks_route", "memory_store", "memory_retrieve", "memory_search",
                "memory_search_unified", "terminal_execute", "agent_execute",
            ]
            result = {"tools": [
                {"name": name, "description": name, "inputSchema": {"type": "object"}}
                for name in names
            ]}
        elif method == "tools/call":
            result = {"content": [{"type": "text", "text": message["params"]["name"]}]}
        else:
            result = {}
        print(json.dumps({"jsonrpc": "2.0", "id": message.get("id"), "result": result}), flush=True)
(profile / "child-eof.marker").write_text("eof", encoding="utf-8")
'''


class RufloProxyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.run_id = "r-20260901-ruflo-test"
        self.run_dir = os.path.join(self.temporary.name, self.run_id)
        self.workspace = os.path.join(self.run_dir, "workspace")
        self.profile = os.path.join(self.run_dir, "research")
        os.makedirs(self.workspace)
        os.makedirs(self.profile)
        with open(os.path.join(self.run_dir, "state.json"), "w", encoding="utf-8") as handle:
            json.dump({"run_id": self.run_id}, handle)
        self.mcp_config = os.path.join(self.run_dir, "research-mcp.json")
        with open(self.mcp_config, "w", encoding="utf-8") as handle:
            json.dump({"mcpServers": {}}, handle)
        self.fake_ruflo = os.path.join(self.temporary.name, "fake-ruflo")
        with open(self.fake_ruflo, "w", encoding="utf-8") as handle:
            handle.write(textwrap.dedent(FAKE_RUFLO))
        os.chmod(self.fake_ruflo, 0o700)
        self.authority = {
            "schema_version": proxy.AUTHORITY_SCHEMA,
            "run_id": self.run_id,
            "mode": "ruflo",
            "server": proxy.RUFLO_SERVER,
            "version": proxy.RUFLO_VERSION,
            "run_dir": os.path.realpath(self.run_dir),
            "workspace": os.path.realpath(self.workspace),
            "profile_dir": os.path.realpath(self.profile),
            "allowed_tools": list(proxy.RESEARCH_TOOLS),
            "daemon": False,
            "federation": False,
            "persistent_cross_run_memory": False,
            "ruflo_binary": os.path.realpath(self.fake_ruflo),
            "mcp_config_path": os.path.realpath(self.mcp_config),
        }
        self.write_authority()

    def write_authority(self):
        with open(
            os.path.join(self.profile, "research-authority.json"),
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(self.authority, handle)

    @staticmethod
    def message(method, request_id=None, params=None):
        value = {"jsonrpc": "2.0", "method": method}
        if request_id is not None:
            value["id"] = request_id
        if params is not None:
            value["params"] = params
        return json.dumps(value)

    def test_facade_filters_tools_rejects_bypasses_and_scrubs_environment(self):
        requests = "\n".join([
            self.message("initialize", 1),
            self.message("notifications/initialized"),
            self.message("tools/list", 2),
            self.message("tools/call", 3, {"name": "terminal_execute", "arguments": {}}),
            self.message("tools/call", 4, {"name": "agent_execute", "arguments": {}}),
            self.message("tools/call", 5, {"name": "guidance_recommend", "arguments": {}}),
            self.message("resources/list", 6),
            self.message("ping", 7),
            self.message(
                "tools/call", 8, {"name": "memory_search_unified", "arguments": {}}
            ),
        ]) + "\n"
        output = io.StringIO()

        with mock.patch.dict(os.environ, {
            "ANTHROPIC_API_KEY": "must-not-leak",
            "OPENROUTER_API_KEY": "must-not-leak",
            "RUFLO_PROVIDER": "must-not-leak",
        }, clear=False):
            result = proxy.serve(
                self.profile,
                self.workspace,
                os.path.realpath(self.fake_ruflo),
                stdin=io.StringIO(requests),
                stdout=output,
            )

        self.assertEqual(result, 0)
        responses = {
            message["id"]: message
            for message in map(json.loads, output.getvalue().splitlines())
        }
        self.assertEqual(set(responses), {1, 2, 3, 4, 5, 6, 7, 8})
        listed = responses[2]["result"]["tools"]
        self.assertEqual([item["name"] for item in listed], list(proxy.RESEARCH_TOOLS))
        self.assertEqual(responses[3]["error"]["code"], -32601)
        self.assertEqual(responses[4]["error"]["code"], -32601)
        self.assertEqual(responses[6]["error"]["code"], -32601)
        self.assertEqual(responses[8]["error"]["code"], -32601)
        self.assertEqual(
            responses[5]["result"]["content"][0]["text"],
            "guidance_recommend",
        )

        with open(os.path.join(self.profile, "forwarded.jsonl"), encoding="utf-8") as handle:
            forwarded = [json.loads(line) for line in handle]
        forwarded_calls = [
            item["params"]["name"]
            for item in forwarded
            if item.get("method") == "tools/call"
        ]
        self.assertEqual(forwarded_calls, ["guidance_recommend"])
        self.assertNotIn("resources/list", [item.get("method") for item in forwarded])

        with open(os.path.join(self.profile, "child-env.json"), encoding="utf-8") as handle:
            environment = json.load(handle)
        for secret in ("ANTHROPIC_API_KEY", "OPENROUTER_API_KEY", "RUFLO_PROVIDER"):
            self.assertNotIn(secret, environment)
        expected_environment = {
            "PATH", "HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME",
            "XDG_STATE_HOME", "XDG_RUNTIME_DIR", "TMPDIR", "RUFLO_DAEMON_AUTOSTART",
            "CLAUDE_FLOW_HTTP_FETCH_ALLOW_PRIVATE", "CLAUDE_FLOW_HTTP_FETCH_ALLOW_AUTH",
            "CLAUDE_FLOW_MCP_TOOLS",
        }
        platform_locale = {"LC_CTYPE", "__CF_USER_TEXT_ENCODING"}
        self.assertEqual(set(environment) - platform_locale, expected_environment)
        self.assertEqual(environment["PATH"], proxy.MINIMAL_PATH)
        self.assertEqual(environment["RUFLO_DAEMON_AUTOSTART"], "0")
        self.assertEqual(environment["CLAUDE_FLOW_HTTP_FETCH_ALLOW_PRIVATE"], "0")
        self.assertEqual(environment["CLAUDE_FLOW_HTTP_FETCH_ALLOW_AUTH"], "0")
        self.assertEqual(
            environment["CLAUDE_FLOW_MCP_TOOLS"],
            ",".join(proxy.RESEARCH_TOOLS),
        )
        for name in (
            "HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME",
            "XDG_STATE_HOME", "XDG_RUNTIME_DIR", "TMPDIR",
        ):
            self.assertEqual(
                os.path.commonpath((os.path.realpath(environment[name]), os.path.realpath(self.profile))),
                os.path.realpath(self.profile),
            )
            self.assertEqual(stat.S_IMODE(os.stat(environment[name]).st_mode), 0o700)
        with open(os.path.join(self.profile, "child-eof.marker"), encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "eof")

    def test_authority_tampering_fails_before_child_start(self):
        cases = {
            "extra tool": lambda value: value["allowed_tools"].append("agent_execute"),
            "daemon": lambda value: value.update(daemon=True),
            "wrong workspace": lambda value: value.update(workspace=self.temporary.name),
            "wrong binary": lambda value: value.update(ruflo_binary="/usr/bin/false"),
            "unknown field": lambda value: value.update(extra=True),
        }
        for label, mutate in cases.items():
            with self.subTest(label=label):
                candidate = json.loads(json.dumps(self.authority))
                mutate(candidate)
                self.authority = candidate
                self.write_authority()
                with self.assertRaises(proxy.RufloProxyError):
                    proxy.serve(
                        self.profile,
                        self.workspace,
                        os.path.realpath(self.fake_ruflo),
                        stdin=io.StringIO(""),
                        stdout=io.StringIO(),
                    )
                self.assertFalse(os.path.exists(os.path.join(self.profile, "child-env.json")))
                self.authority = {
                    key: value for key, value in self.authority.items() if key != "extra"
                }
                self.authority.update({
                    "workspace": os.path.realpath(self.workspace),
                    "allowed_tools": list(proxy.RESEARCH_TOOLS),
                    "daemon": False,
                    "ruflo_binary": os.path.realpath(self.fake_ruflo),
                })
                self.write_authority()

    def test_cli_has_no_tool_override_or_abbreviated_security_flags(self):
        for arguments in (
            ["--profile", self.profile, "--workspace", self.workspace,
             "--ruflo-bin", self.fake_ruflo, "--tools", "all"],
            ["--profile", self.profile, "--workspace", self.workspace,
             "--ruflo", self.fake_ruflo],
        ):
            with self.subTest(arguments=arguments), \
                    mock.patch("sys.stderr", new=io.StringIO()):
                with self.assertRaises(SystemExit):
                    proxy.build_parser().parse_args(arguments)


if __name__ == "__main__":
    unittest.main()
