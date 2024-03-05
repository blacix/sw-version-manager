import os
import sys
import subprocess
import json


def tag_on_current_commit(tag: str):
    tag_on_commit = False
    tag_commit_hash = subprocess.run(f'git rev-list -n 1 {tag}', check=False, shell=True, capture_output=True)
    if tag_commit_hash.returncode == 0:
        current_commit_hash = subprocess.run(f'git rev-parse HEAD', check=True, shell=True, capture_output=True)
        tag_on_commit = tag_commit_hash.stdout == current_commit_hash.stdout
    return tag_on_commit


# can throw subprocess.CalledProcessError
def commit_file(file_name: str, commit_message: str):
    subprocess.run(f'git add {file_name}', check=True, shell=True, stdout=subprocess.DEVNULL)
    # check if added
    # returns non-zero if there is something to commit
    proc = subprocess.run(f'git diff-index --cached --quiet HEAD', check=False, shell=True,
                          stdout=subprocess.DEVNULL)
    if proc.returncode == 0:
        raise Exception(f'git add {file_name} failed')
    commit_cmd = f'git commit -m "{commit_message}"'
    subprocess.run(commit_cmd, check=True, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(f'git push', check=True, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


# can throw subprocess.CalledProcessError
def create_git_tag(tag_name: str):
    subprocess.run(f'git tag {tag_name}', check=True, shell=True, stdout=subprocess.DEVNULL)
    # subprocess.run(f'git push origin tag {tag_name}', check=True, shell=True)
    subprocess.run(f'git push origin --tags', check=True, shell=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)


def print_usage():
    print(f'usage:')
    print(f'python {os.path.basename(sys.argv[0])} git_tag [--check]')


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(-1)
    try:
        git_tag = sys.argv[1]
        action = ""
        if len(sys.argv) >= 3:
            action = sys.argv[2]
        if action == "--check" and not tag_on_current_commit(git_tag) or action != "--check":
            create_git_tag(git_tag)
    except subprocess.CalledProcessError as se:
        print(se, file=sys.stderr)
        sys.exit(-2)
    except json.JSONDecodeError as je:
        print('config JSON parse error!', file=sys.stderr)
        print(je, file=sys.stderr)
        sys.exit(-3)
    except FileNotFoundError as fe:
        print(fe, file=sys.stderr)
        sys.exit(-4)
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(-5)
    sys.exit(0)
