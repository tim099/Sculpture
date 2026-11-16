from pathlib import Path
import sys

path = Path(sys.argv[1])
probe = Path(sys.argv[2]).read_text(encoding="utf-8-sig").strip()
page = path.read_text(encoding="utf8")
closer = "})();\n</script>"
offset = page.find(closer, page.index("function simStep"))
assert offset != -1
hook = "\nif (DEBUG) window.galeaProbe = " + probe + ";\n"
out = path.with_name(path.stem + "-galea-probe.html")
out.write_text(page[:offset] + hook + page[offset:], encoding="utf8", newline="\n")
print(out)
