import hashlib
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZIPS = ROOT / "zips"
REPO_ADDON = ROOT / "repository.chapasaddons"
REPO_ADDON_ID = "repository.chapasaddons"


def bump_patch(version):
	major, minor, patch = version.split(".")
	return f"{major}.{minor}.{int(patch) + 1}"


def bump_repo_version():
	addon_xml = REPO_ADDON / "addon.xml"
	text = addon_xml.read_text(encoding="utf-8")
	match = re.search(r'(<addon id="%s"[^>]*?version=")([^"]+)(")' % REPO_ADDON_ID, text)
	new_version = bump_patch(match.group(2))
	text = text[:match.start(2)] + new_version + text[match.end(2):]
	addon_xml.write_text(text, encoding="utf-8")
	return new_version


def build_repo_zip(version):
	out_dir = ZIPS / REPO_ADDON_ID
	out_dir.mkdir(parents=True, exist_ok=True)
	for old in out_dir.glob("*.zip"):
		old.unlink()
	out_file = out_dir / f"{REPO_ADDON_ID}-{version}.zip"
	with zipfile.ZipFile(out_file, "w", zipfile.ZIP_DEFLATED) as archive:
		for path in REPO_ADDON.rglob("*"):
			if path.is_file():
				archive.write(path, f"{REPO_ADDON_ID}/{path.relative_to(REPO_ADDON).as_posix()}")


def read_addon_xml(zip_path):
	with zipfile.ZipFile(zip_path) as archive:
		entry = next(n for n in archive.namelist() if re.fullmatch(r"[^/]+/addon\.xml", n))
		text = archive.read(entry).decode("utf-8")
	return re.sub(r"^\s*<\?xml[^>]*\?>\s*", "", text).strip()


def write_index():
	entries = [read_addon_xml(z) for z in sorted(ZIPS.rglob("*.zip"))]
	xml = "<?xml version='1.0' encoding='UTF-8' standalone='yes'?>\n<addons>\n" + "\n".join(entries) + "\n</addons>\n"
	addons_xml = ZIPS / "addons.xml"
	addons_xml.write_bytes(xml.encode("utf-8"))
	md5 = hashlib.md5(addons_xml.read_bytes()).hexdigest()
	(ZIPS / "addons.xml.md5").write_text(md5, encoding="utf-8")
	return md5


def main():
	version = bump_repo_version()
	build_repo_zip(version)
	md5 = write_index()
	print(f"Published {REPO_ADDON_ID} {version} (addons.xml md5={md5})")


if __name__ == "__main__":
	main()
