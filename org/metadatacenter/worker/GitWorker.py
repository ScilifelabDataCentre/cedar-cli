from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.table import Table

from org.metadatacenter.ReposFactory import ReposFactory
from org.metadatacenter.util.Util import Util
from org.metadatacenter.worker.Worker import Worker

console = Console()

GIT_STATUS_CHAR_LIMIT = 300


class GitWorker(Worker):

    def __init__(self):
        super().__init__()

    def register_active_repo(self, triple, table, active_repos, suggestion):
        table.add_row(triple.repo.name, triple.out[0:GIT_STATUS_CHAR_LIMIT] + '...' if len(triple.out) > 0 else '', "[red]" + triple.err,
                      suggestion)
        active_repos.append(triple.repo)

    def render_status_table(self, result):
        active_repos = []
        table = Table("Repo", "Output", "Error", "Suggested", show_lines=True, title="Repos that require attention")
        cnt = 0
        for triple in result.results:
            if "our branch is behind" in triple.out:
                self.register_active_repo(triple, table, active_repos, "Pull")
                cnt += 1
            elif "ntracked files" in triple.out:
                self.register_active_repo(triple, table, active_repos, "Add, Commit, Push")
                cnt += 1
            elif "hanges not staged" in triple.out:
                self.register_active_repo(triple, table, active_repos, "Add, Commit, Push")
                cnt += 1
            elif "hanges to be committed" in triple.out:
                self.register_active_repo(triple, table, active_repos, "Commit, Push")
                cnt += 1
            elif "our branch is ahead of" in triple.out:
                self.register_active_repo(triple, table, active_repos, "Push")
                cnt += 1
            elif len(triple.err) > 0:
                self.register_active_repo(triple, table, active_repos, "Handle error")
                cnt += 1
        if cnt > 0:
            table.caption = str(cnt) + " repos to act on"
            table.style = Style(color="red")
            console.print()
            console.print(table)
        else:
            console.print(Panel("Nothing to add, commit or push, all changes are published", style=Style(color="green")))
        return active_repos

    def branch(self):
        self.execute_shell_on_all_repos_with_table(
            command_list=["echo $(git rev-parse --abbrev-ref HEAD)"],
            headers=["Repo", "Branch", "Error"],
            show_lines=False,
            status_line="Checking",
        )

    def pull(self):
        self.execute_shell_on_all_repos_with_table(
            command_list=["git pull"],
            status_line="Pulling",
        )

    def fetch(self):
        self.execute_shell_on_all_repos_with_table(
            command_list=["git fetch"],
            status_line="Fetching",
        )

    def status(self):
        result = self.execute_shell_on_all_repos_with_table(
            command_list=["git status"],
        )
        return self.render_status_table(result)

    def checkout(self, branch: str):
        self.execute_shell_on_all_repos_with_table(
            command_list=["git checkout " + branch],
            status_line="Checking out",
        )

    def clone_docker(self):
        self.execute_shell_on_all_repos_with_table(
            status_line="Cloning",
            repo_list=self.repos.get_for_docker_list(),
            command_list=["git clone " + ReposFactory.git_base + "{0}"],
            cwd_is_home=True,
        )

    def clone_all(self):
        self.execute_shell_on_all_repos_with_table(
            status_line="Cloning",
            command_list=["git clone " + ReposFactory.git_base + "{0}"],
            cwd_is_home=True,
        )

    def next(self):
        active_repos = self.status()
        if len(active_repos) > 0:
            last_repo_path = Util.read_cedar_file('last_git_repo')
            found_idx = -1

            if last_repo_path is not None:
                for idx, repo in enumerate(active_repos):
                    if Util.get_wd(repo) == last_repo_path:
                        found_idx = idx

            found_idx += 1
            if found_idx >= len(active_repos):
                found_idx = 0
            next_repo = active_repos[found_idx]
            path = Util.get_wd(next_repo)
            console.print("Found repo with activity, changing current working directory to: " + path)
            Util.write_cedar_file(Util.LAST_GIT_FILE, path + "\n")
            Util.write_cedar_file(Util.NEXT_GIT_FILE, path + "\n")
        else:
            Util.delete_cedar_file(Util.LAST_GIT_FILE)
            Util.delete_cedar_file(Util.NEXT_GIT_FILE)

    def remote(self):
        self.execute_shell_on_all_repos_with_table(
            status_line="Checking remote",
            command_list=["git remote -v"],
        )

    def list_tag(self):
        self.execute_shell_on_all_repos_with_table(
            command_list=[
                "echo Local\n" +
                "git --no-pager branch --sort=-creatordate | head -4\n" +
                "echo Remote\n" +
                "git --no-pager ls-remote --tag --sort=-creatordate | head -4 | awk '{{ print \" \",$2}}'"
            ],
            status_line="Listing tags",
        )

    def list_branch(self):
        self.execute_shell_on_all_repos_with_table(
            command_list=[
                "echo Local\n" +
                "git --no-pager branch --sort=-creatordate | head -4\n" +
                "echo Remote\n" +
                "git --no-pager branch -r --sort=-creatordate | head -4"
            ],
            status_line="Listing branches",
        )
