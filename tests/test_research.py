import json
import os
import stat
import sys
import tempfile
import unittest
from unittest import mock


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))

import research  # noqa: E402
import ruflo_proxy  # noqa: E402


class ResearchAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.run_id = "r-20260901-d3042d73-9378-4516-8e63-5960d47db896"
        self.run_dir = os.path.join(self.temp.name, self.run_id)
        self.workspace = os.path.join(self.run_dir, "workspace")
        os.makedirs(self.workspace)
        with open(os.path.join(self.run_dir, "state.json"), "w") as handle:
            json.dump({"run_id": self.run_id}, handle)
        self.ruflo = os.path.realpath(os.path.join(self.temp.name, "ruflo"))
        with open(self.ruflo, "w") as handle:
            handle.write("#!/bin/sh\nexit 0\n")
        os.chmod(self.ruflo, 0o700)
        self.connector_mcp = os.path.join(self.run_dir, "connector-mcp.json")
        with open(self.connector_mcp, "w") as handle:
            json.dump({"mcpServers": {"rally-connectors": {
                "type": "stdio", "command": "/rally-connectors", "args": [],
                "env": {"RALLY_CONNECTOR_POLICY": "/policy.json"},
            }}}, handle)
        self.cfg = {
            "research": {
                "enabled": True,
                "executable": self.ruflo,
                "allowed_tools": list(research.REVIEWED_ALLOWED_TOOLS),
                "disabled_global_server_names": ["figma"],
            }
        }

    def version_result(self, version="3.38.20", stderr="", code=0):
        return mock.Mock(
            returncode=code, stdout="ruflo v%s\n" % version, stderr=stderr
        )

    def prepare(self, **overrides):
        kwargs = {
            "mode": "ruflo",
            "connector_mcp_path": self.connector_mcp,
            "disabled_global_server_names": ["figma"],
        }
        kwargs.update(overrides)
        with mock.patch.object(
            research.subprocess, "run", return_value=self.version_result()
        ):
            return research.prepare_run(
                self.run_id, self.run_dir, self.workspace, self.cfg, **kwargs
            )

    def test_standard_mode_is_a_zero_write_fast_path(self):
        before = sorted(os.listdir(self.run_dir))
        self.assertEqual(
            research.prepare_run("bad", "relative", "relative", None, mode="standard"),
            {},
        )
        self.assertEqual(sorted(os.listdir(self.run_dir)), before)

    def test_mode_is_closed_and_case_normalized(self):
        self.assertEqual(research.normalize_mode(None), "standard")
        self.assertEqual(research.normalize_mode(" RUFLO "), "ruflo")
        for invalid in ("all", "", 1, True):
            with self.subTest(invalid=invalid):
                with self.assertRaises(research.ResearchConfigError):
                    research.normalize_mode(invalid)

    def test_prepare_writes_one_proxy_bound_authority_and_combined_mcp(self):
        authority = self.prepare()
        self.assertEqual(authority["allowed_tools"], list(ruflo_proxy.RESEARCH_TOOLS))
        self.assertEqual(
            authority["profile_dir"],
            os.path.realpath(os.path.join(self.run_dir, "research")),
        )
        self.assertEqual(stat.S_IMODE(os.stat(authority["profile_dir"]).st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(os.stat(authority["authority_path"]).st_mode), 0o600)

        validated = ruflo_proxy.load_authority(
            authority["profile_dir"], self.workspace, self.ruflo
        )
        self.assertEqual(validated.run_id, self.run_id)
        with open(authority["mcp_config_path"]) as handle:
            servers = json.load(handle)["mcpServers"]
        self.assertEqual(set(servers), {"rally-connectors", "ruflo-research"})
        self.assertEqual(
            servers["ruflo-research"]["args"],
            ["--profile", authority["profile_dir"], "--workspace",
             os.path.realpath(self.workspace),
             "--ruflo-bin", self.ruflo],
        )

    def test_agy_config_disables_known_globals_and_is_restored(self):
        authority = self.prepare(disabled_global_server_names=["figma", "cmc-skill-hub"])
        agy_path = authority["agy_mcp_config_path"]
        with open(agy_path, "w") as handle:
            json.dump({"mcpServers": {"attacker": {"command": "bad"}}}, handle)
        restored = research.materialize_agy_config(
            self.workspace, authority["mcp_config_path"], ["figma", "cmc-skill-hub"]
        )
        with open(restored) as handle:
            servers = json.load(handle)["mcpServers"]
        self.assertEqual(
            set(servers),
            {"rally-connectors", "ruflo-research", "figma", "cmc-skill-hub"},
        )
        self.assertEqual(servers["figma"], {"disabled": True})
        self.assertEqual(servers["cmc-skill-hub"], {"disabled": True})
        self.assertEqual(stat.S_IMODE(os.stat(restored).st_mode), 0o600)

    def test_requested_profile_never_silently_narrows_or_widens_tools(self):
        for tools in (
            list(research.REVIEWED_ALLOWED_TOOLS[:-1]),
            list(research.REVIEWED_ALLOWED_TOOLS) + ["terminal_execute"],
        ):
            cfg = {"research": {**self.cfg["research"], "allowed_tools": tools}}
            with self.subTest(tools=tools), mock.patch.object(
                research.subprocess, "run", return_value=self.version_result()
            ):
                with self.assertRaisesRegex(
                    research.ResearchConfigError, "exactly match"
                ):
                    research.prepare_run(
                        self.run_id, self.run_dir, self.workspace, cfg,
                        mode="ruflo", connector_mcp_path=self.connector_mcp,
                    )

    def test_version_pin_fails_closed_before_authority_publication(self):
        with mock.patch.object(
            research.subprocess, "run", return_value=self.version_result("3.39.0")
        ):
            with self.assertRaisesRegex(research.ResearchConfigError, "version mismatch"):
                research.prepare_run(
                    self.run_id, self.run_dir, self.workspace, self.cfg,
                    mode="ruflo", connector_mcp_path=self.connector_mcp,
                )
        self.assertFalse(os.path.exists(os.path.join(self.run_dir, "research")))

    def test_ungoverned_connector_server_is_rejected(self):
        with open(self.connector_mcp, "w") as handle:
            json.dump({"mcpServers": {"surprise": {"command": "bad"}}}, handle)
        with self.assertRaisesRegex(research.ResearchConfigError, "ungoverned server"):
            self.prepare()

    def test_prompt_makes_ruflo_subordinate_and_run_only(self):
        prompt = research.prompt_text(self.prepare())
        for phrase in (
            "subordinate", "not a Rally worker", "cannot own", "run only",
            "shell", "browser", "GitHub", "connector credentials",
        ):
            self.assertIn(phrase, prompt)

    def test_preflight_checks_pin_without_creating_run_files(self):
        with mock.patch.object(
            research.subprocess, "run", return_value=self.version_result()
        ):
            receipt = research.preflight(self.cfg)
        self.assertEqual(receipt["version"], "3.38.20")
        self.assertEqual(receipt["allowed_tools"], list(research.REVIEWED_ALLOWED_TOOLS))
        self.assertFalse(os.path.exists(os.path.join(self.run_dir, "research")))


if __name__ == "__main__":
    unittest.main()
