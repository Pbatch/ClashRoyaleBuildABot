import hashlib
import os
import stat
import zipfile

import pytest

from clashroyalebuildabot import install
from clashroyalebuildabot.install import extract_zip


def test_extract_zip_keeps_executable_bit(tmp_path):
    zip_path = tmp_path / "tools.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        exe = zipfile.ZipInfo("platform-tools/adb")
        exe.external_attr = (stat.S_IFREG | 0o755) << 16
        zf.writestr(exe, "binary")
        zf.writestr("platform-tools/NOTICE.txt", "text")

    extract_zip(zip_path, tmp_path / "out")

    assert os.access(tmp_path / "out/platform-tools/adb", os.X_OK)
    notice = tmp_path / "out/platform-tools/NOTICE.txt"
    assert notice.read_text() == "text"


def _fake_platform_tools(path, version=install.ADB_VERSION):
    with zipfile.ZipFile(path, "w") as zf:
        exe = zipfile.ZipInfo("platform-tools/adb")
        exe.external_attr = (stat.S_IFREG | 0o755) << 16
        zf.writestr(exe, "binary")
        zf.writestr(
            "platform-tools/source.properties",
            f"Pkg.UserSrc=false\nPkg.Revision={version}\n",
        )


class _FakeResponse:
    def __init__(self, data):
        self.data = data
        self.headers = {"content-length": str(len(data))}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def raise_for_status(self):
        pass

    def iter_content(self, chunk_size):
        for i in range(0, len(self.data), chunk_size):
            yield self.data[i : i + chunk_size]


def _patch_install(monkeypatch, tmp_path, data, sha256):
    adb_dir = tmp_path / "platform-tools"
    monkeypatch.setattr(install, "APP_DIR", str(tmp_path))
    monkeypatch.setattr(install, "ADB_DIR", str(adb_dir))
    monkeypatch.setattr(install, "ADB_PATH", str(adb_dir / "adb"))
    monkeypatch.setattr(install, "ADB_SHA256", sha256)
    monkeypatch.setattr(
        install.requests, "get", lambda *a, **k: _FakeResponse(data)
    )
    return adb_dir


def test_install_adb_moves_platform_tools_into_place(monkeypatch, tmp_path):
    src = tmp_path / "src.zip"
    _fake_platform_tools(src)
    data = src.read_bytes()
    adb_dir = _patch_install(
        monkeypatch, tmp_path, data, hashlib.sha256(data).hexdigest()
    )
    # Left over from an interrupted install by an earlier version.
    adb_dir.mkdir()
    (adb_dir / "NOTICE.txt").write_text("partial")

    install.install_adb()

    assert install.adb_installed()
    assert not (adb_dir / "NOTICE.txt").exists()
    # Only the source zip and the installed folder are left.
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "platform-tools",
        "src.zip",
    ]


def test_install_adb_rejects_wrong_checksum(monkeypatch, tmp_path):
    src = tmp_path / "src.zip"
    _fake_platform_tools(src)
    adb_dir = _patch_install(monkeypatch, tmp_path, src.read_bytes(), "0")

    with pytest.raises(ValueError, match="SHA-256"):
        install.install_adb()

    assert not adb_dir.exists()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["src.zip"]


def test_emulator_installs_missing_adb(monkeypatch):
    from clashroyalebuildabot import emulator
    from clashroyalebuildabot.utils.error_handling import WikifiedError

    calls = []
    monkeypatch.setattr(emulator, "adb_up_to_date", lambda: False)
    monkeypatch.setattr(emulator, "adb_installed", lambda: False)
    monkeypatch.setattr(emulator, "install_adb", lambda: calls.append(1))
    emulator.Emulator.__new__(emulator.Emulator)._check_adb()
    assert calls == [1]

    def fail():
        raise OSError("no internet")

    monkeypatch.setattr(emulator, "install_adb", fail)
    with pytest.raises(WikifiedError, match="no internet"):
        emulator.Emulator.__new__(emulator.Emulator)._check_adb()


def test_install_adb_replaces_other_version(monkeypatch, tmp_path):
    src = tmp_path / "src.zip"
    _fake_platform_tools(src)
    data = src.read_bytes()
    adb_dir = _patch_install(
        monkeypatch, tmp_path, data, hashlib.sha256(data).hexdigest()
    )
    extract_zip(_old_zip(tmp_path), tmp_path)
    assert install.installed_adb_version() == "1.0.0"
    assert not install.adb_up_to_date()

    install.install_adb()

    assert install.installed_adb_version() == install.ADB_VERSION
    assert install.adb_up_to_date()
    assert (adb_dir / "adb").read_text() == "binary"


def test_install_adb_keeps_current_version(monkeypatch, tmp_path):
    src = tmp_path / "src.zip"
    _fake_platform_tools(src)
    _patch_install(monkeypatch, tmp_path, b"", "0")
    extract_zip(src, tmp_path)

    def no_download(*args, **kwargs):
        raise AssertionError("downloaded an installed version")

    monkeypatch.setattr(install.requests, "get", no_download)
    install.install_adb()
    assert install.adb_up_to_date()


def test_emulator_keeps_old_adb_if_update_fails(monkeypatch):
    from clashroyalebuildabot import emulator

    def fail():
        raise OSError("no internet")

    monkeypatch.setattr(emulator, "adb_up_to_date", lambda: False)
    monkeypatch.setattr(emulator, "adb_installed", lambda: True)
    monkeypatch.setattr(emulator, "install_adb", fail)
    emulator.Emulator.__new__(emulator.Emulator)._check_adb()


def _old_zip(tmp_path):
    path = tmp_path / "old" / "old.zip"
    path.parent.mkdir()
    with zipfile.ZipFile(path, "w") as zf:
        exe = zipfile.ZipInfo("platform-tools/adb")
        exe.external_attr = (stat.S_IFREG | 0o755) << 16
        zf.writestr(exe, "old binary")
        zf.writestr("platform-tools/source.properties", "Pkg.Revision=1.0.0\n")
    return path
