import os
import sys
import re
import subprocess
import json

ARG_CNT = 3

# [^\S] matches any char that is not a non-whitespace = any char that is whitespace
C_DEFINE_PATTERN = r"(.*#define)([^\S]+)(\S+)([^\S]+)(\d+)([^\S]*\n)"
VERSION_TYPE_GROUP = 3
VERSION_VALUE_GROUP = 5


class VersionManager:
    def __init__(self, sys_args: []):
        self.sys_args = sys_args
        self.version_file = None
        self.config_json = None
        self.version_tags = []
        self.increment_tags = []
        self.version_map = {}
        self.update_version_file = False
        self.commit_version_file = False
        self.read_only = False
        self.create_git_tag = False
        self.git_tag_prefix = ""
        self.git_tag = ""
        self.version_string = ""
        self.version_output_file = None
        self.commit_message = ""
        self.append_version = True

    # can throw FileNotFoundError
    def _load_config(self):
        self.version_file = sys.argv[1]
        self.config_json = sys.argv[2]
        # print('loading config')
        config_json = json.load(open(self.config_json))
        self.version_tags = config_json["version_tags"]
        self.increment_tags = config_json["increment"]
        self.create_git_tag = config_json["create_git_tag"]
        self.git_tag_prefix = config_json["git_tag_prefix"]
        self.version_output_file = config_json["output_file"]
        self.commit_message = config_json["commit_message"]
        self.append_version = config_json["append_version"]
        self.version_map = {self.version_tags[i]: 0 for i in range(0, len(self.version_tags))}

        self.read_only = '--read' in sys.argv
        self.update_version_file = '--noupdate' not in sys.argv and not self.read_only
        self.commit_version_file = '--nocommit' not in sys.argv and self.update_version_file and not self.read_only
        self.create_git_tag = '--notag' not in sys.argv and not self.read_only

        # print('config done')
        # print(f'used by project: {self.version_tags}')
        if not self.read_only:
            print(f'increment: {self.increment_tags}')

    def execute(self):
        if len(self.sys_args) < ARG_CNT:
            print(f'usage: {self.sys_args[0]} version_file_path')
            return -1
        try:
            self._load_config()
            self._check_version_tags()
            self._update_versions()
            self._create_version_string()
            self._git_update()
            self._create_output_files()
        except subprocess.CalledProcessError as se:
            print(se)
            return -1
        except json.JSONDecodeError as je:
            print('config JSON parse error!')
            print(je)
        except FileNotFoundError as fe:
            print(fe)
            return -1
        except Exception as e:
            print('unknown error!')
            print(e)
        return 0

    # throws exception on error
    def _check_version_tags(self):
        # # contains only valid project tags
        # filtered_project_versions = [item for item in
        #                              filter(lambda x: x in self.VERSION_TAGS, project_versions)]

        # check if every tag to be incremented are valid
        filtered_versions_to_increment = [item for item in
                                          self.increment_tags if item in self.version_tags]
        # print(filtered_versions_to_increment)
        if len(filtered_versions_to_increment) != len(self.increment_tags):
            invalid_versions = [item for item in
                                self.increment_tags if item not in self.version_tags]
            print(f'print invalid version type(s) to increment: {invalid_versions}')
            raise Exception("invalid version type(s) found. Check your config!")

    def _update_versions(self):
        # print(f'updating {str(self.increment_tags)}')
        new_lines = []
        with open(self.version_file, 'r') as file:
            for line in file:
                new_line = self._process_c_line(line)
                new_lines.append(new_line)

        if len(self.increment_tags) > 0 and self.update_version_file:
            with open(self.version_file, 'w') as file:
                file.writelines(new_lines)

    def _process_c_line(self, line: str):
        result = re.search(C_DEFINE_PATTERN, line)
        if result is not None:
            version_type = result[VERSION_TYPE_GROUP]
            new_version = int(result[VERSION_VALUE_GROUP])
            if version_type in self.increment_tags and version_type in self.version_tags:
                new_version += 1
                # print(f"{version_type} {int(result[5]) + 1}")
                # replace \\4 and \\5 with a space and a tab and the new value
                new_line = re.sub(pattern=C_DEFINE_PATTERN,
                                  repl=f"\\1\\2\\3 {new_version}\\6",
                                  string=line)
            else:
                new_line = line
            # update version object
            self.version_map[version_type] = new_version
            # print(new_line.strip())
        else:
            new_line = line
        return new_line

    def _create_version_string(self):
        # iterate through VERSION_TAGS so the order will be correct
        self.version_string = ".".join([str(self.version_map[item]) for item in self.version_tags])
        print(f'{self.version_string}')

    # can throw subprocess.CalledProcessError, FileNotFoundError, Exception
    def _git_update(self):
        if len(self.increment_tags) > 0:
            if self.commit_version_file:
                if self.append_version:
                    self.commit_message += f'{self.version_string}'
                self._commit_version_file(self.version_file, self.commit_message)
            if self.create_git_tag:
                self.git_tag = f'{self.git_tag_prefix}{self.version_string}'
                print(f'git tag: {self.git_tag}')
                self._update_git_tag(self.git_tag)

    # can throw subprocess.CalledProcessError
    @staticmethod
    def _commit_version_file(version_file: str, commit_message: str):
        subprocess.run(f'git add {version_file}', check=True, shell=True)
        # check if added
        # returns non-zero if there is something to commit
        proc = subprocess.run(f'git diff-index --cached --quiet HEAD', check=False, shell=True)
        if proc.returncode == 0:
            raise Exception(f'git add {version_file} failed')
        commit_cmd = f'git commit -m "{commit_message}"'
        # print(commit_cmd)
        subprocess.run(commit_cmd, check=True, shell=True)
        subprocess.run(f'git push', check=True, shell=True)

    # can throw subprocess.CalledProcessError
    @staticmethod
    def _update_git_tag(tag_name):
        print(tag_name)
        # proc = subprocess.Popen('git tag', stdout=subprocess.PIPE)
        # output = proc.stdout.readlines()
        proc = subprocess.run('git tag', check=True, capture_output=True, shell=True)
        output = proc.stdout
        # print(output)
        if bytes(f'{tag_name}\n', 'utf-8') not in output:
            subprocess.run(f'git tag {tag_name}', check=True, shell=True)
            # subprocess.run(f'git push origin tag {tag_name}', check=True, shell=True)
            subprocess.run(f'git push origin --tags', check=True, shell=True)
        else:
            print(f'tag {tag_name} already exists')

    def _create_output_files(self):
        with open(self.version_output_file, 'w') as file:
            file.write(self.version_string)


if __name__ == '__main__':
    sys.exit(VersionManager(sys.argv).execute())
