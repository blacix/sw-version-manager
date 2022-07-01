import os
import sys
import re
import subprocess
import json

MIN_ARG_CNT = 3

# [^\S] matches any char that is not a non-whitespace = any char that is whitespace
C_DEFINE_PATTERN = r"(.*#define)([^\S]+)(\S+)([^\S]+)(\d+)([^\S]*\n)"
C_VERSION_TYPE_GROUP = 3
C_VERSION_VALUE_GROUP = 5

ANDROID_DEFINE_PATTERN = r"([^\S]*)(\S+)(=)([^\S]*)(\d+)([^\S]*\n)"
ANDROID_VERSION_TYPE_GROUP = 2
ANDROID_VERSION_VALUE_GROUP = 5

C_REGEX = (C_DEFINE_PATTERN, C_VERSION_TYPE_GROUP, C_VERSION_VALUE_GROUP)
ANDROID_REGEX = (ANDROID_DEFINE_PATTERN, ANDROID_VERSION_TYPE_GROUP, ANDROID_VERSION_VALUE_GROUP)


class VersionManager:
    def __init__(self):
        self.version_file = None
        self.config_json = None
        self.version_tags = []
        self.increment_tags = []
        self.version_map = {}
        self.update_version_file = False
        self.commit_version_file = False
        self.increment_version = False
        self.create_git_tag = False
        self.git_tag_prefix = ""
        self.git_tag = ""
        self.version_string = ""
        self.version_output_file = None
        self.commit_message = ""
        self.append_version = True
        self.create_output_files = False
        self.parser_data = None
        self._create_line = None

    # can throw FileNotFoundError
    def _load_config(self):
        self.version_file = sys.argv[1]
        self.config_json = sys.argv[2]
        # load json config
        # print('loading config')
        config_json = json.load(open(self.config_json))
        self.version_tags = config_json["version_tags"]
        self.increment_tags = config_json["increment"]
        self.git_tag_prefix = config_json["git_tag_prefix"]
        self.version_output_file = config_json["output_file"]
        self.commit_message = config_json["commit_message"]
        self.append_version = config_json["append_version"]
        self.version_map = {self.version_tags[i]: 0 for i in range(0, len(self.version_tags))}

        # language setup
        self.language = str(config_json["language"]).strip().lower()
        if self.language == 'c':
            self.parser_data = C_REGEX
            self._create_line = self._create_c_line
        elif self.language == 'cpp':
            pass
        elif self.language == 'android':
            self.parser_data = ANDROID_REGEX
            self._create_line = self._create_android_line
        else:
            raise Exception(f'unknown language: {self.language}')

        # apply arguments
        # Note: arguments can override settings
        self.increment_version = '--update' in sys.argv
        self.update_version_file = self.increment_version
        self.commit_version_file = '--commit' in sys.argv or '--git' in sys.argv
        self.create_git_tag = '--tag' in sys.argv or '--git' in sys.argv
        self.create_output_files = '--output' in sys.argv

    @staticmethod
    def print_usage():
        print(f'usage:')
        print(f'python {os.path.basename(sys.argv[0])} version_file_path config_file_path [--update | --git | --read | --output]')
        print('\t--read: ')
        print('\t\treads the version file')
        print('\t\tversion file will not be updated if present')
        print('\t--update:')
        print('\t\tupdates the version file')
        print('\t\tthis is the default if no extra args are provided')
        print('\t--git:')
        print('\t\tcreates and pushes a git tag if configured')
        print('\t\tcommits and pushes the version file')
        print('\t\tversion file update will only be updated if --update is present')
        print('\t--output:')
        print('\t\tcreates output file containing the version string')

    def execute(self):
        if len(sys.argv) < MIN_ARG_CNT:
            self.print_usage()
            return -1
        try:
            self._load_config()
            self._check_version_tags()
            self._parse_version_file()
            self._create_version_string()
            self._git_update()
            self._create_output_files()
        except subprocess.CalledProcessError as se:
            print(se, file=sys.stderr)
            return -1
        except json.JSONDecodeError as je:
            print('config JSON parse error!', file=sys.stderr)
            print(je, file=sys.stderr)
        except FileNotFoundError as fe:
            print(fe, file=sys.stderr)
            return -1
        except Exception as e:
            # print('unknown error!')
            print(e, file=sys.stderr)
            return -1
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

    # TODO error when valid version tag is missing from the version file
    def _parse_version_file(self):
        # print(f'updating {str(self.increment_tags)}')
        new_lines = []
        with open(self.version_file, 'r') as file:
            for line in file:
                version_type, version_value = self._parse_line(line, self.parser_data)
                if version_type is not None and version_value is not None:
                    if version_type in self.increment_tags and self.increment_version:
                        version_value += 1
                    self.version_map[version_type] = version_value
                    new_line = self._create_line(line, version_value)
                    new_lines.append(new_line)
                else:
                    new_lines.append(line)

        if len(self.increment_tags) > 0 and self.update_version_file:
            with open(self.version_file, 'w') as file:
                file.writelines(new_lines)

    @staticmethod
    def _parse_line(line: str, parser_data: ()):
        pattern, version_type_group, version_value_group = parser_data
        result = re.search(pattern, line)
        if result is not None:
            version_type = result[version_type_group]
            version_value = int(result[version_value_group])
            return version_type, version_value
        return None, None

    # TODO does not work with inline comments
    @staticmethod
    def _create_c_line(line: str, version: int):
        return re.sub(pattern=C_DEFINE_PATTERN,
                      repl=fr'\g<1>\g<2>\g<3>\g<4>{version}\g<6>',
                      string=line)

    # TODO put back last groups of regex instead of '\n'
    @staticmethod
    def _create_android_line(line: str, version: int):
        return re.sub(pattern=ANDROID_DEFINE_PATTERN,
                      repl=fr'\g<1>\g<2>\g<3>{str(version)}\n',
                      string=line)

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
                # print(f'git tag: {self.git_tag}')
                self._update_git_tag(self.git_tag)

    # can throw subprocess.CalledProcessError
    @staticmethod
    def _commit_version_file(version_file: str, commit_message: str):
        subprocess.run(f'git add {version_file}', check=True, shell=True)
        # check if added
        # returns non-zero if there is something to commit
        proc = subprocess.run(f'git diff-index --cached --quiet HEAD', check=False, shell=True,
                              stdout=subprocess.DEVNULL)
        if proc.returncode == 0:
            raise Exception(f'git add {version_file} failed')
        commit_cmd = f'git commit -m "{commit_message}"'
        # print(commit_cmd)
        subprocess.run(commit_cmd, check=True, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(f'git push', check=True, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # can throw subprocess.CalledProcessError
    @staticmethod
    def _update_git_tag(tag_name):
        # print(tag_name)
        # proc = subprocess.Popen('git tag', stdout=subprocess.PIPE)
        # output = proc.stdout.readlines()

        # proc = subprocess.run('git tag', check=True, capture_output=True, shell=True)
        # output = proc.stdout
        # print(output)
        # if bytes(f'{tag_name}\n', 'utf-8') not in output:
        subprocess.run(f'git tag {tag_name}', check=True, shell=True, stdout=subprocess.DEVNULL)
        # subprocess.run(f'git push origin tag {tag_name}', check=True, shell=True)
        subprocess.run(f'git push origin --tags', check=True, shell=True, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL)
        # else:
        #     print(f'tag {tag_name} already exists')

    def _create_output_files(self):
        if self.create_output_files:
            with open(self.version_output_file, 'w') as file:
                file.write(self.version_string)


if __name__ == '__main__':
    sys.exit(VersionManager().execute())
