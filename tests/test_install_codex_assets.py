from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "install_codex_assets.py"
SPEC = importlib.util.spec_from_file_location("install_codex_assets", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class CodexAssetInstallerTests(unittest.TestCase):
    def test_convert_text_rewrites_claude_surfaces(self) -> None:
        potato_dir = Path("C:/Users/test/.codex/potato-kit")
        source = (
            "CLAUDE.md ~/.claude/packs /potato-eda "
            "claude mcp add -s user paper-search -- command WebSearch"
        )
        converted = MODULE.convert_text(source, potato_dir)
        self.assertIn("AGENTS.md", converted)
        self.assertIn("C:/Users/test/.codex/potato-kit/packs", converted)
        self.assertIn("$potato-eda", converted)
        self.assertIn("codex mcp add paper-search", converted)
        self.assertNotIn("claude mcp", converted)

    def test_managed_block_preserves_user_content_on_reinstall(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            agents = Path(tmp) / "AGENTS.md"
            agents.write_text("# My rules\n\nKeep this.\n", encoding="utf-8")
            first = f"{MODULE.START_MARK}\nfirst\n{MODULE.END_MARK}"
            second = f"{MODULE.START_MARK}\nsecond\n{MODULE.END_MARK}"

            changed, backup = MODULE.update_global_agents(agents, first)
            self.assertTrue(changed)
            self.assertIsNotNone(backup)
            changed, _ = MODULE.update_global_agents(agents, second)
            self.assertTrue(changed)

            result = agents.read_text(encoding="utf-8")
            self.assertIn("# My rules", result)
            self.assertIn("Keep this.", result)
            self.assertIn("second", result)
            self.assertNotIn("first", result)
            self.assertEqual(result.count(MODULE.START_MARK), 1)

    def test_legacy_block_keeps_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            agents = Path(tmp) / "AGENTS.md"
            agents.write_text(
                "# Existing\n\nKeep.\n\n<!-- potato-kit -->\nold generated block\n",
                encoding="utf-8",
            )
            block = f"{MODULE.START_MARK}\nnew\n{MODULE.END_MARK}"
            MODULE.update_global_agents(agents, block)
            result = agents.read_text(encoding="utf-8")
            self.assertIn("# Existing", result)
            self.assertIn("Keep.", result)
            self.assertNotIn("old generated block", result)
            self.assertIn("new", result)


if __name__ == "__main__":
    unittest.main()
