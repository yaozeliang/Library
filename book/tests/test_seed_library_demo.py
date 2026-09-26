"""Seed script password behaviour: keep existing hashes unless reset is requested."""

import importlib.util
import os
import sys
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from book.models import Book, BorrowRecord

_SEED_PATH = Path(__file__).resolve().parents[2] / "scripts" / "seed_library_demo.py"


def _load_seed():
    spec = importlib.util.spec_from_file_location(
        "seed_library_demo_script", _SEED_PATH
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SeedPasswordTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.seed = _load_seed()

    def test_rerun_preserves_existing_passwords(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DEMO_ADMIN_PASSWORD", None)
            os.environ.pop("DEMO_RESET_PASSWORDS", None)
            self.seed.run(reset_passwords=False)

        admin = User.objects.get(username="admin")
        staff = User.objects.get(username="staff")
        self.assertTrue(admin.check_password("admin"))
        self.assertTrue(staff.check_password("staff"))
        self.assertTrue(admin.is_superuser)
        self.assertTrue(staff.is_staff)
        self.assertFalse(staff.is_superuser)
        self.assertEqual(Book.objects.count(), 20)
        self.assertEqual(
            BorrowRecord.objects.filter(created_by="seed_demo").count(), 15
        )

        admin.set_password("replaced-out-of-band")
        staff.set_password("staff-replaced-out-of-band")
        admin.save()
        staff.save()

        with patch.dict(
            os.environ,
            {"DEMO_ADMIN_PASSWORD": "later-env-value-must-not-apply"},
            clear=False,
        ):
            os.environ.pop("DEMO_RESET_PASSWORDS", None)
            self.seed.run(reset_passwords=False)

        admin.refresh_from_db()
        staff.refresh_from_db()
        self.assertTrue(admin.check_password("replaced-out-of-band"))
        self.assertTrue(staff.check_password("staff-replaced-out-of-band"))
        self.assertFalse(admin.check_password("admin"))
        self.assertFalse(admin.check_password("later-env-value-must-not-apply"))
        self.assertTrue(admin.is_superuser)
        self.assertEqual(Book.objects.count(), 20)
        self.assertEqual(
            BorrowRecord.objects.filter(created_by="seed_demo").count(), 15
        )

    def test_demo_admin_password_used_for_new_admin(self):
        with patch.dict(
            os.environ,
            {"DEMO_ADMIN_PASSWORD": "from-demo-admin-password-env"},
            clear=False,
        ):
            os.environ.pop("DEMO_RESET_PASSWORDS", None)
            self.seed.run(reset_passwords=False)

        admin = User.objects.get(username="admin")
        staff = User.objects.get(username="staff")
        self.assertTrue(admin.check_password("from-demo-admin-password-env"))
        self.assertFalse(admin.check_password("admin"))
        self.assertTrue(staff.check_password("staff"))
        self.assertTrue(admin.is_superuser)

    def test_blank_demo_admin_password_uses_local_default(self):
        with patch.dict(os.environ, {"DEMO_ADMIN_PASSWORD": "   "}, clear=False):
            os.environ.pop("DEMO_RESET_PASSWORDS", None)
            self.seed.run(reset_passwords=False)

        admin = User.objects.get(username="admin")
        self.assertTrue(admin.check_password("admin"))

    def test_reset_passwords_flag_resets(self):
        self.seed.run(reset_passwords=False)
        admin = User.objects.get(username="admin")
        staff = User.objects.get(username="staff")
        admin.set_password("replaced-out-of-band")
        staff.set_password("staff-replaced-out-of-band")
        admin.save()
        staff.save()

        with patch.dict(
            os.environ,
            {"DEMO_ADMIN_PASSWORD": "from-env-should-not-apply-on-reset"},
            clear=False,
        ):
            os.environ.pop("DEMO_RESET_PASSWORDS", None)
            with patch.object(
                sys,
                "argv",
                ["scripts/seed_library_demo.py", "--reset-passwords"],
            ):
                self.seed.run()

        admin.refresh_from_db()
        staff.refresh_from_db()
        self.assertTrue(admin.check_password("admin"))
        self.assertFalse(
            admin.check_password("from-env-should-not-apply-on-reset")
        )
        self.assertTrue(staff.check_password("staff"))
        self.assertFalse(staff.check_password("staff-replaced-out-of-band"))

    def test_demo_reset_passwords_env_resets(self):
        self.seed.run(reset_passwords=False)
        admin = User.objects.get(username="admin")
        admin.set_password("replaced-out-of-band")
        admin.save()

        with patch.dict(os.environ, {"DEMO_RESET_PASSWORDS": "1"}, clear=False):
            os.environ.pop("DEMO_ADMIN_PASSWORD", None)
            self.seed.run()

        admin.refresh_from_db()
        self.assertTrue(admin.check_password("admin"))
        self.assertFalse(admin.check_password("replaced-out-of-band"))
