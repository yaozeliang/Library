"""Production settings load DEBUG off and take SECRET_KEY from the environment."""

import os
import subprocess
import sys
import tempfile
import textwrap

from django.test import SimpleTestCase


class ProductionSettingsModuleTests(SimpleTestCase):
    def _run(self, env, code, hide_dotenv=False):
        clean = os.environ.copy()
        clean.pop("DATABASE_URL", None)
        clean.pop("DEBUG", None)
        clean.pop("SECRET_KEY", None)
        clean.update(env)
        clean["PYTHONPATH"] = os.getcwd()
        # decouple finds .env by walking up from core/settings.py, not cwd.
        # CI writes DEBUG=True there. Hide it when the case under test is
        # "the variable is absent".
        dotenv = os.path.join(os.getcwd(), ".env")
        hidden = dotenv + ".hidden-by-test"
        moved = False
        if hide_dotenv and os.path.isfile(dotenv):
            os.replace(dotenv, hidden)
            moved = True
        try:
            with tempfile.TemporaryDirectory() as empty:
                return subprocess.run(
                    [sys.executable, "-c", textwrap.dedent(code)],
                    capture_output=True,
                    text=True,
                    env=clean,
                    cwd=empty,
                    check=False,
                )
        finally:
            if moved:
                os.replace(hidden, dotenv)

    def test_debug_defaults_off_and_secret_key_comes_from_the_environment(self):
        result = self._run(
            {
                "DJANGO_SETTINGS_MODULE": "core.settings_production",
                "SECRET_KEY": "unit-test-unique-secret-not-a-placeholder",
            },
            """
            import django
            from django.conf import settings
            # Production logging writes to /var/log, which this process cannot create.
            # Swap the handler before setup so the assertions can load the module.
            settings.LOGGING = {"version": 1, "disable_existing_loggers": False}
            django.setup()
            assert settings.DEBUG is False
            assert settings.SECRET_KEY == "unit-test-unique-secret-not-a-placeholder"
            print("ok")
            """,
            hide_dotenv=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ok", result.stdout)

    def test_explicit_debug_true_is_honoured(self):
        result = self._run(
            {
                "DJANGO_SETTINGS_MODULE": "core.settings_production",
                "SECRET_KEY": "unit-test-unique-secret-not-a-placeholder",
                "DEBUG": "True",
            },
            """
            import django
            from django.conf import settings
            settings.LOGGING = {"version": 1, "disable_existing_loggers": False}
            django.setup()
            assert settings.DEBUG is True
            print("ok")
            """,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_secret_key_refuses_to_boot(self):
        result = self._run(
            {
                "DJANGO_SETTINGS_MODULE": "core.settings_production",
                "SECRET_KEY": "",
            },
            """
            import django
            from django.conf import settings
            settings.LOGGING = {"version": 1, "disable_existing_loggers": False}
            django.setup()
            """,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("SECRET_KEY", result.stderr)
