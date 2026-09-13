"""Compare native Python to MSYS grep argument and stdin transport."""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def main():
    binary = shutil.which("grep")
    assert binary, "An actual grep binary is required"
    print(json.dumps({"grep": binary}))
    cases = [
        (r"^foo\(bar\)\+$", "foo(bar)+\n", "foobar\n"),
        (r"^(foo|bar)+[0-9]{2}$", "FooBAR12\n", "foo12 extra\n"),
        ("", "content\n", "other\n"),
        ("foo\n", "unrelated\n", "other\n"),
    ]
    for pattern, matching, other in cases:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "matching.txt").write_text(matching)
            (root / "other.txt").write_text(other)
            expected = (
                ["matching.txt", "other.txt"]
                if pattern in ("", "foo\n")
                else ["matching.txt"]
            )
            for method in ("argv", "stdin"):
                cmd = [binary, "-E", "-R", "-I", "-l", "-i"]
                kwargs = {}
                if method == "stdin":
                    cmd.extend(["-f", "-"])
                    kwargs["input"] = pattern + "\n"
                else:
                    cmd.append(pattern)
                cmd.append(str(root))
                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=False, **kwargs
                )
                matches = sorted(Path(p).name for p in result.stdout.splitlines())
                print(
                    json.dumps(
                        {
                            "pattern": pattern,
                            "method": method,
                            "returncode": result.returncode,
                            "matches": matches,
                            "stderr": result.stderr,
                            "expected": expected,
                        }
                    )
                )
                if method == "stdin":
                    assert result.returncode == 0 and matches == expected


if __name__ == "__main__":
    main()
