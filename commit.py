# commit.py
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
        return stdout.strip().split('\n') if stdout.strip() else []

    def stage_files(self) -> bool:
        code, stdout, _ = self.run_command("git status --porcelain")
        if code != 0:
            return False

        files = [line[3:] for line in stdout.split('\n') if line]
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

            print(f"\n{Fore.CYAN}Commit message preview:")
            print(f"{Fore.WHITE}{full_message}")

            if not questionary.confirm("Confirm commit?").ask():
                return False

            print(f"\n{Fore.CYAN}Committing changes...")
            code, _, stderr = self.run_command(f'git commit -m "{full_message}"')
            if code != 0:
                print(f"{Fore.RED}Error during commit: {stderr}")
                return False

            if questionary.confirm("Push changes?", default=True).ask():
                print(f"\n{Fore.CYAN}Pushing changes...")
                code, _, stderr = self.run_command(f'git push origin {branch}')
                if code != 0:
                    print(f"{Fore.RED}Error during push: {stderr}")
                    return False
                print(f"{Fore.GREEN}Successfully pushed changes! 🎉")
            else:
                print(f"{Fore.YELLOW}Changes committed but not pushed.")

            return True

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Operation cancelled by user.")
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
