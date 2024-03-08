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

    @staticmethod
    def _create_tag(repo: git.Repo, tag_name):
        # print(f'tagging {repo} with {tag_name}')
        repo.create_tag(tag_name, message=tag_name)
        repo.git.push('origin', tag_name)
        print(f'{tag_name}')

    def tag_repo(self, tag_name):
        self._create_tag(self.repo, tag_name)

    def tag_submodules(self, tag_name):
        for submodule in self.repo.submodules:
            self._create_tag(git.Repo(submodule.abspath), tag_name)

    @staticmethod
    def _delete_tag(repo: git.Repo, tag_name):
        print(f'deleting {tag_name} from {repo}')
        try:
            local_tag = repo.tags[tag_name]
            repo.delete_tag(local_tag)
            repo.remotes.origin.push(f':refs/tags/{tag_name}')
        except Exception as e:
            print(e)

    def delete_tags(self, tag_name):
        self._delete_tag(self.repo, tag_name)
        for submodule in self.repo.submodules:
            self._delete_tag(git.Repo(submodule.abspath), tag_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Git utility for tagging repos')
    parser.add_argument('--repo', default=".", help='Path to the git repository')
    parser.add_argument('--tag', required=True, help='Name of the git tag')

    parser.add_argument('--tag_repo', action='store_true',
                        help='creates tag in the repo on the current commit')
    parser.add_argument('--tag_submodules', action='store_true', help='tag submodules')
    parser.add_argument('--delete', action='store_true', help='delete tags')

    return_value = 0
    args = parser.parse_args()
    gitUtils = GitUtils(args.repo)
    if args.tag_repo:
        try:
            gitUtils.tag_repo(args.tag)
        except Exception as e:
            print(e)
            return_value = 1

    if args.tag_submodules:
        try:
            gitUtils.tag_submodules(args.tag)
        except Exception as e:
            print(e)
            return_value = 2

    if not args.tag_repo and not args.tag_submodules and not args.delete:
        if not gitUtils.check_tag_on_current_commit(args.tag):
            return_value = 3

    if args.delete:
        gitUtils.delete_tags(args.tag)

    sys.exit(return_value)
