import hashlib
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZIPS = ROOT / "zips"
REPO_ADDON_ID = "repository.chapasaddons"


def bump_patch(version):
	major, minor, patch = version.split(".")
	return f"{major}.{minor}.{int(patch) + 1}"


def bump_addon_xml(text):
	match = re.search(r'(<addon [^>]*?version=")([^"]+)(")', text)
	new_version = bump_patch(match.group(2))
	return text[:match.start(2)] + new_version + text[match.end(2):], new_version


def bump_addon_zip(zip_path):
	with zipfile.ZipFile(zip_path) as archive:
		names = archive.namelist()
		infos = {info.filename: info for info in archive.infolist()}
		contents = {name: archive.read(name) for name in names}
	addon_xml_name = next(n for n in names if re.fullmatch(r"[^/]+/addon\.xml", n))
	addon_id = addon_xml_name.split("/")[0]
	text, new_version = bump_addon_xml(contents[addon_xml_name].decode("utf-8"))
	contents[addon_xml_name] = text.encode("utf-8")
	out_file = zip_path.parent / f"{addon_id}-{new_version}.zip"
	with zipfile.ZipFile(out_file, "w", zipfile.ZIP_DEFLATED) as archive:
		for name in names:
			archive.writestr(infos[name], contents[name], compress_type=zipfile.ZIP_DEFLATED)
	zip_path.unlink()
	return addon_id, new_version


def bump_hosted_addons():
	bumped = []
	for addon_dir in sorted(p for p in ZIPS.iterdir() if p.is_dir() and p.name != REPO_ADDON_ID):
		for zip_path in sorted(addon_dir.glob("*.zip")):
			bumped.append(bump_addon_zip(zip_path))
	return bumped


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
	bumped = bump_hosted_addons()
	md5 = write_index()
	for addon_id, version in bumped:
		print(f"Published {addon_id} {version}")
	print(f"addons.xml md5={md5}")


if __name__ == "__main__":
	main()
