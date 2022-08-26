import os
import sys
import re
import subprocess
import json


def tag_on_current_commit(git_tag: str):
    tag_on_commit = False
    tag_commit_hash = subprocess.run(f'git rev-list -n 1 {git_tag}', check=False, shell=True, capture_output=True)
    if tag_commit_hash.returncode == 0:
        current_commit_hash = subprocess.run(f'git rev-parse HEAD', check=True, shell=True, capture_output=True)
        tag_on_commit = tag_commit_hash.stdout == current_commit_hash.stdout
    return tag_on_commit


# can throw subprocess.CalledProcessError
def commit_version_file(version_file: str, commit_message: str):
    subprocess.run(f'git add {version_file}', check=True, shell=True, stdout=subprocess.DEVNULL)
    # check if added
    # returns non-zero if there is something to commit
    proc = subprocess.run(f'git diff-index --cached --quiet HEAD', check=False, shell=True,
                          stdout=subprocess.DEVNULL)
    if proc.returncode == 0:
        raise Exception(f'git add {version_file} failed')
    commit_cmd = f'git commit -m "{commit_message}"'
    subprocess.run(commit_cmd, check=True, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(f'git push', check=True, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# can throw subprocess.CalledProcessError
def update_git_tag(tag_name):
    subprocess.run(f'git tag {tag_name}', check=True, shell=True, stdout=subprocess.DEVNULL)
    # subprocess.run(f'git push origin tag {tag_name}', check=True, shell=True)
    subprocess.run(f'git push origin --tags', check=True, shell=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)