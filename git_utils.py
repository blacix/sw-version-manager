import git


class GitUtils:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)

    def check_tag_on_current_commit(self, tag_name_to_check: str) -> bool:
        current_commit = self.repo.head.commit
        tag_on_current_commit = any(
            tag.commit == current_commit for tag in self.repo.tags if tag.name == tag_name_to_check)
        return tag_on_current_commit

    def commit_file(self, file_name: str, commit_message: str):
        print(f'commit_file: {file_name} {commit_message}')
        self.repo.index.add(file_name)
        self.repo.index.commit(commit_message)
        self.repo.git.push('origin', self.repo.active_branch.name)

    def create_tag(self, tag_name):
        print(f'tag: {tag_name}')
        self.repo.create_tag(tag_name, message=tag_name)
        self.repo.git.push('origin', tag_name)
