import os
import unittest
from pathlib import Path
from dotenv import load_dotenv

from geoagent.core.config import GeoAgentConfig, _default_provider_from_env, _PROJECT_ROOT, _ENV_PATH
from geoagent.core.model import resolve_model


class TestEnvAndModelConfiguration(unittest.TestCase):
    def setUp(self):
        self.orig_env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self.orig_env)
        test_file = _PROJECT_ROOT / ".env"
        if test_file.exists():
            test_file.unlink()

    def test_deterministic_root_path(self):
        expected_root = Path(__file__).resolve().parent.parent
        self.assertEqual(_PROJECT_ROOT, expected_root)
        self.assertEqual(_ENV_PATH, expected_root / ".env")

    def test_dotenv_loaded_without_overwriting_existing_env(self):
        # Set existing env variable in PowerShell/session
        os.environ["GROQ_API_KEY"] = "powershell_existing_key"
        
        # Write .env file
        test_file = _PROJECT_ROOT / ".env"
        test_file.write_text("GROQ_API_KEY=from_dotenv_key\nLITELLM_MODEL=groq/openai/gpt-oss-120b\n", encoding="utf-8")
        
        # Call load_dotenv with override=False
        load_dotenv(dotenv_path=_ENV_PATH, override=False)
        
        # Verify existing PowerShell env var takes precedence
        self.assertEqual(os.environ.get("GROQ_API_KEY"), "powershell_existing_key")
        self.assertEqual(os.environ.get("LITELLM_MODEL"), "groq/openai/gpt-oss-120b")

    def test_provider_inference_and_fallback(self):
        os.environ.clear()
        os.environ["GROQ_API_KEY"] = "dummy_key"
        self.assertEqual(_default_provider_from_env(), "litellm")

    def test_priority_explicit_client_args(self):
        os.environ["GROQ_API_KEY"] = "env_key"
        cfg = GeoAgentConfig(provider="litellm", client_args={"api_key": "explicit_key"})
        model = resolve_model(cfg)
        self.assertEqual(model.client_args.get("api_key"), "explicit_key")
        self.assertEqual(model.config.get("model_id"), "groq/openai/gpt-oss-120b")

    def test_priority_env_var_when_no_client_args(self):
        os.environ["GROQ_API_KEY"] = "env_key_only"
        cfg = GeoAgentConfig(provider="litellm")
        model = resolve_model(cfg)
        self.assertEqual(model.client_args.get("api_key"), "env_key_only")
        self.assertEqual(model.config.get("model_id"), "groq/openai/gpt-oss-120b")

    def test_model_preservation_groq_gpt_oss_120b(self):
        cfg = GeoAgentConfig(provider="litellm")
        model = resolve_model(cfg)
        self.assertEqual(model.config.get("model_id"), "groq/openai/gpt-oss-120b")


if __name__ == "__main__":
    unittest.main()
