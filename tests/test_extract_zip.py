import os
import stat
import zipfile

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
