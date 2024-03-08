import git
import argparse
import sys


class GitUtils:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)

    def check_tag_on_current_commit(self, tag_name_to_check: str) -> bool:
        current_commit = self.repo.head.commit
        tag_on_current_commit = any(
            tag.commit == current_commit for tag in self.repo.tags if tag.name == tag_name_to_check)
        if tag_on_current_commit:
            print(tag_name_to_check)
        else:
            print("")
        return tag_on_current_commit

    def commit_file(self, file_path: str, commit_message: str):
        if self.repo.is_dirty(path=file_path):
            # print(f'commit_file: {file_path} {commit_message}')
            self.repo.index.add(file_path)
            commit = self.repo.index.commit(commit_message)
            self.repo.git.push('origin', self.repo.active_branch.name)

    def create_tag(self, tag_name):
        self.repo.create_tag(tag_name, message=tag_name)
        self.repo.git.push('origin', tag_name)
        print(f'{tag_name}')


def bash_exit(result: bool):
    if result:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Command-line arguments example')
    parser.add_argument('--repo', default=".", help='Path to the git repository')
    parser.add_argument('--tag', required=True, help='Name of the git tag')
    parser.add_argument('--check', action='store_true', help='checks if the tag provided is on the current commit')
    parser.add_argument('--create', action='store_true', help='creates tag on the current commit')
    args = parser.parse_args()
    gitUtils = GitUtils(args.repo)
    if args.create:
        try:
            gitUtils.create_tag(args.tag)
            bash_exit(True)
        except Exception as e:
            print(e)
            bash_exit(False)

    if args.check:
        bash_exit(gitUtils.check_tag_on_current_commit(args.tag))

    bash_exit(True)
