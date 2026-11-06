import hashlib
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ZIPS = ROOT / "zips"


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


if __name__ == "__main__":
	print(f"addons.xml md5={write_index()}")
