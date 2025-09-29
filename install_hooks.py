# install_hooks.py
import os
import shutil
from pathlib import Path
import json

COMMIT_SCRIPT = """# commit.py
import sys
import subprocess
from typing import Optional, List
import questionary
from colorama import init, Fore, Style
import os
import uuid
from pathlib import Path

init(autoreset=True)

class GitCommit:
    COMMIT_TYPES = [
        ('feat', '✨ New feature'),
        ('fix', '🐛 Bug fixes'),
        ('docs', '📚 Documentation'),
        ('style', '💎 Code style'),
        ('refactor', '♻️ Code refactoring'),
        ('test', '🧪 Tests'),
        ('chore', '🔧 Maintenance'),
        ('perf', '⚡ Performance'),
        ('ci', '👷 CI/CD changes'),
        ('revert', '⏪ Revert changes')
    ]

    SCOPES = [
        ('api', 'API related changes'),
        ('ui', 'UI/Frontend changes'),
        ('db', 'Database related'),
        ('auth', 'Authentication/Authorization'),
        ('core', 'Core functionality'),
        ('config', 'Configuration changes'),
        ('deps', 'Dependencies'),
        ('tests', 'Test related'),
        ('docs', 'Documentation'),
    ]

    def __init__(self):
        self.token = str(uuid.uuid4())

    def run_command(self, command: str) -> tuple:
        try:
            env = os.environ.copy()
            env['COMMIT_TOKEN'] = self.token

            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            stdout, stderr = process.communicate()
            return process.returncode, stdout, stderr
        except Exception as e:
            print(f"{Fore.RED}Error executing command: {e}")
            return 1, "", str(e)

    def get_current_branch(self) -> Optional[str]:
        code, stdout, _ = self.run_command("git branch --show-current")
        return stdout.strip() if code == 0 else None

    def get_staged_files(self) -> List[str]:
        code, stdout, _ = self.run_command("git diff --cached --name-only")
        return stdout.strip().split('\\n') if stdout.strip() else []

    def stage_files(self) -> bool:
        code, stdout, _ = self.run_command("git status --porcelain")
        if code != 0:
            return False

        files = [line[3:] for line in stdout.split('\\n') if line]
        if not files:
            print(f"{Fore.YELLOW}No changes to commit!")
            return False

        selected = questionary.checkbox(
            "Select files to stage:",
            choices=files
        ).ask()

        if not selected:
            return False

        for file in selected:
            code, _, stderr = self.run_command(f'git add "{file}"')
            if code != 0:
                print(f"{Fore.RED}Error staging {file}: {stderr}")
                return False

        return True

    def commit_and_push(self) -> bool:
        try:
            branch = self.get_current_branch()
            if not branch:
                print(f"{Fore.RED}Not in a git repository!")
                return False

            print(f"{Fore.CYAN}Current branch: {branch}")

            staged = self.get_staged_files()
            if not staged:
                print(f"{Fore.YELLOW}No staged files found.")
                if not self.stage_files():
                    return False

            type_choice = questionary.select(
                "Select type of change:",
                choices=[f"{type_} - {desc}" for type_, desc in self.COMMIT_TYPES]
            ).ask()

            commit_type = type_choice.split(' -')[0]

            scope_choice = questionary.select(
                "Select scope:",
                choices=[f"{scope} - {desc}" for scope, desc in self.SCOPES]
            ).ask()

            scope = scope_choice.split(' -')[0]

            message = questionary.text(
                "Enter commit message:",
                validate=lambda text: len(text.strip()) > 0
            ).ask()

            full_message = f"{commit_type}({scope}): {message}"

            print(f"\\n{Fore.CYAN}Commit message preview:")
            print(f"{Fore.WHITE}{full_message}")

            if not questionary.confirm("Confirm commit?").ask():
                return False

            print(f"\\n{Fore.CYAN}Committing changes...")
            code, _, stderr = self.run_command(f'git commit -m "{full_message}"')
            if code != 0:
                print(f"{Fore.RED}Error during commit: {stderr}")
                return False

            if questionary.confirm("Push changes?", default=True).ask():
                print(f"\\n{Fore.CYAN}Pushing changes...")
                code, _, stderr = self.run_command(f'git push origin {branch}')
                if code != 0:
                    print(f"{Fore.RED}Error during push: {stderr}")
                    return False
                print(f"{Fore.GREEN}Successfully pushed changes! 🎉")
            else:
                print(f"{Fore.YELLOW}Changes committed but not pushed.")

            return True

        except KeyboardInterrupt:
            print(f"\\n{Fore.YELLOW}Operation cancelled by user.")
            return False
        except Exception as e:
            print(f"{Fore.RED}An error occurred: {e}")
            return False

if __name__ == "__main__":
    try:
        commit = GitCommit()
        if not commit.commit_and_push():
            sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}Fatal error: {e}")
        sys.exit(1)
"""

HOOK_SCRIPT = """#!/usr/bin/env python3
import sys
import re
import os
from pathlib import Path

def is_merge_commit():
    commit_source = sys.argv[2] if len(sys.argv) > 2 else ''
    return commit_source in ['merge', 'message']

def check_commit_message(msg_file):
    try:
        if is_merge_commit():
            return 0

        with open(msg_file, 'r') as f:
            message = f.read().strip()

        if not os.environ.get('COMMIT_TOKEN'):
            print("\\n❌ Please use: python commit.py")
            return 1

        types = ['feat', 'fix', 'docs', 'style', 'refactor',
                'test', 'chore', 'perf', 'ci', 'revert']
        scopes = ['api', 'ui', 'db', 'auth', 'core',
                 'config', 'deps', 'tests', 'docs']

        types_pattern = '|'.join(types)
        scopes_pattern = '|'.join(scopes)
        pattern = f"^({types_pattern})\\\\(({scopes_pattern})\\\\): .+"

        if not re.match(pattern, message):
            print("\\n❌ Invalid commit message format!")
            print("📝 Format: type(scope): message")
            print(f"🔍 Types: {', '.join(types)}")
            print(f"🎯 Scopes: {', '.join(scopes)}")
            print("\\n❗ Examples:")
            print("   feat(api): add new endpoint")
            print("   fix(auth): fix login issue")
            return 1

        return 0

    except Exception as e:
        print(f"\\n❌ Error in commit hook: {str(e)}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Missing commit message file argument")
        sys.exit(1)
    sys.exit(check_commit_message(sys.argv[1]))
"""

REQUIREMENTS = """questionary==2.0.1
colorama==0.4.6
setuptools>=65.5.1
"""


def setup_git_hooks():
    """Set up all necessary files and configurations for git hooks."""
    try:
        # Create commit.py
        print("📝 Creating commit script...")
        with open("commit.py", "w", newline="\n") as f:
            f.write(COMMIT_SCRIPT)

        # Create requirements.txt if doesn't exist
        if not Path("requirements.txt").exists():
            print("📦 Creating requirements.txt...")
            with open("requirements.txt", "w", newline="\n") as f:
                f.write(REQUIREMENTS)

        # Setup git hooks directory
        hooks_dir = Path(".git/hooks")
        hooks_dir.mkdir(parents=True, exist_ok=True)

        # Create prepare-commit-msg hook
        print("🔨 Installing git hook...")
        hook_path = hooks_dir / "prepare-commit-msg"
        with open(hook_path, "w", newline="\n") as f:
            f.write(HOOK_SCRIPT)

        # Make hook executable on Unix systems
        if os.name != "nt":  # Not Windows
            os.chmod(hook_path, 0o755)

        # Install dependencies
        print("📥 Installing dependencies...")
        os.system("pip install -r requirements.txt")

        print(f"\\n{'='*50}")
        print("✅ Git hooks setup completed successfully!")
        print(f"{'='*50}")
        print("📝 Available commit types:")
        for type_, desc in [
            ("feat", "✨ New feature"),
            ("fix", "🐛 Bug fixes"),
            ("docs", "📚 Documentation"),
            ("style", "💎 Code style"),
            ("refactor", "♻️ Code refactoring"),
            ("test", "🧪 Tests"),
            ("chore", "🔧 Maintenance"),
            ("perf", "⚡ Performance"),
            ("ci", "👷 CI/CD changes"),
            ("revert", "⏪ Revert changes"),
        ]:
            print(f"• {type_}: {desc}")
        print(f"{'='*50}")
        print("💡 Usage:")
        print("1. Stage your changes: git add .")
        print("2. Commit using: python commit.py")
        print(f"{'='*50}\\n")

    except Exception as e:
        print(f"❌ Error during setup: {str(e)}")
        return False

    return True


if __name__ == "__main__":
    try:
        setup_git_hooks()
    except KeyboardInterrupt:
        print("\\n⚠️ Setup cancelled by user")
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
