import pathlib, re

def test_no_hardcoded_paths():
    root = pathlib.Path(__file__).resolve().parents[1]
    offenders = []
    for p in root.rglob("*.py"):
        if p.name == "paths.py":
            continue
        txt = p.read_text(errors="ignore")
        if re.search(r'/home/[^"]+LeadVille/db|["\']leadville\.db["\']|["\']bt50_samples\.db["\']', txt):
            offenders.append(str(p))
    assert not offenders, f"Hardcoded DB paths found in: {offenders}"