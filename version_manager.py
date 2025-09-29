# version_manager.py
import re
from pathlib import Path
import sys


class VersionManager:
    VERSION_FILE = "version.txt"

    @staticmethod
    def parse_commit_type(commit_msg: str) -> str:
        """Parse commit message to determine version bump type."""
        if any(
            prefix in commit_msg.lower()
            for prefix in ["breaking change:", "feat!:", "!"]
        ):
            return "major"
        if commit_msg.lower().startswith(("feat:", "feature:")):
            return "minor"
        return "patch"

    @classmethod
    def get_current_version(cls) -> tuple:
        """Get current version from version.txt."""
        try:
            with open(cls.VERSION_FILE, "r") as f:
                version = f.read().strip()
                return tuple(map(int, version.split(".")))
        except (FileNotFoundError, ValueError):
            return (0, 1, 0)

    @classmethod
    def bump_version(cls, commit_msg: str) -> str:
        """Bump version based on commit message."""
        major, minor, patch = cls.get_current_version()
        bump_type = cls.parse_commit_type(commit_msg)

        if bump_type == "major":
            major += 1
            minor = patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        else:
            patch += 1

        new_version = f"{major}.{minor}.{patch}"

        # Save new version
        with open(cls.VERSION_FILE, "w") as f:
            f.write(new_version)

        return new_version


if __name__ == "__main__":
    commit_msg = sys.argv[1] if len(sys.argv) > 1 else ""
    # Chỉ in ra version number, không có text thừa
    print(VersionManager.bump_version(commit_msg), end="")
