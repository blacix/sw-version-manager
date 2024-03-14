import git
import argparse
import sys


class GitUtils:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)

    def checkout_branch(self, branch_name, new_branch=False):
        local_branches = [b.name for b in self.repo.heads]
        # print(local_branches)
        # remote_branches = [b.name for b in self.repo.references]
        # print(remote_branches)
        if branch_name in local_branches:
            self.repo.git.checkout(branch_name)
        else:
            # If the branch doesn't exist locally, fetch from origin and checkout
            self.repo.remotes.origin.fetch()
            if new_branch:
                self.repo.git.checkout('-b', branch_name)
            else:
                self.repo.git.checkout('-b', branch_name, f'origin/{branch_name}')

    def check_tag_on_current_commit(self, tag_name_to_check: str) -> bool:
        current_commit = self.repo.head.commit
        tag_on_current_commit = any(
            tag.commit == current_commit for tag in self.repo.tags if tag.name == tag_name_to_check)
        if tag_on_current_commit:
            print(tag_name_to_check)
        else:
            print("")
        return tag_on_current_commit

    def commit_file(self, file_path: str, commit_message: str, push=False):
        if self.repo.is_dirty(path=file_path):
            # print(f'commit_file: {file_path} {commit_message}')
            self.repo.index.add(file_path)
            commit = self.repo.index.commit(commit_message)
            if push:
                self.repo.git.push('origin', self.repo.active_branch.name)

    @staticmethod
    def _create_tag(repo: git.Repo, tag_name, push=False):
        # print(f'tagging {repo} with {tag_name}')
        repo.create_tag(tag_name, message=tag_name)
        if push:
            repo.git.push('origin', tag_name)
        print(f'{tag_name}')

    def tag_repo(self, tag_name, push=False):
        self._create_tag(self.repo, tag_name, push)

    def tag_submodules(self, tag_name, push=False):
        for submodule in self.repo.submodules:
            self._create_tag(git.Repo(submodule.abspath), tag_name, push)

    @staticmethod
    def _delete_tag(repo: git.Repo, tag_name):
        # print(f'deleting {tag_name} from {repo}')
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

    subparsers = parser.add_subparsers(dest='group', help='Choose a group (required)')

    parser_tag = subparsers.add_parser('tag')
    parser_tag.add_argument('--repo', default=".", help='Path to the git repository')
    parser_tag.add_argument('--name', required=True, help='Name of the git tag')
    tag_group = parser_tag.add_mutually_exclusive_group(required=True)
    tag_group.add_argument('--check', action='store_true', help='Name of the git tag')
    tag_group.add_argument('--delete', action='store_true', help='tag submodules')
    tag_group.add_argument('--create', action='store_true', help='Name of the git tag')
    parser_tag.add_argument('--submodules', action='store_true', help='tag submodules')

    return_value = 0
    args = parser.parse_args()
    gitUtils = GitUtils(args.repo)
    if args.group == 'tag':
        if args.create:
            try:
                gitUtils.tag_repo(args.name)
            except Exception as e:
                print(e)
                return_value = 1

            if args.submodules:
                try:
                    gitUtils.tag_submodules(args.name)
                except Exception as e:
                    print(e)
                    return_value = 2

        if args.delete:
            gitUtils.delete_tags(args.name)

        if args.check:
            if not gitUtils.check_tag_on_current_commit(args.name):
                return_value = 3

    sys.exit(return_value)
