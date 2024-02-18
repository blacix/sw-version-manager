import os
import sys
import re
import subprocess
import json
import git_utils
from version_file_parser import VersionFileParser
import semver

# [^\S] matches any char that is not a non-whitespace = any char that is whitespace
C_DEFINE_PATTERN = r"(.*#define)([^\S]+)(\S+)([^\S]+\"*)((\d+)|[a-zA-Z]+)(\"*[^\S]*\n|$)"
C_VERSION_TYPE_GROUP = 3
C_VERSION_VALUE_GROUP = 5

ANDROID_DEFINE_PATTERN = r"([^\S]*)(\S+)(=)([^\S]*)(\d+)([^\S]*\n|$)"
ANDROID_VERSION_TYPE_GROUP = 2
ANDROID_VERSION_VALUE_GROUP = 5

C_PARSER_DATA = (C_DEFINE_PATTERN, C_VERSION_TYPE_GROUP, C_VERSION_VALUE_GROUP)
ANDROID_PARSER_DATA = (ANDROID_DEFINE_PATTERN, ANDROID_VERSION_TYPE_GROUP, ANDROID_VERSION_VALUE_GROUP)


class RegexParser(VersionFileParser):
    LANGUAGES = ['c', 'cpp', 'android']

    def __init__(self, language: str, version_file: str):
        super().__init__()
        self.language = language
        self.version_file = version_file
        self.version_file_content = []
        # all tags from config
        self.version_tags = []
        self.version_map = {}

        if self.language == 'c':
            self.parser_data = C_PARSER_DATA
            self._create_line_dynamic = self._create_c_line
        elif self.language == 'cpp':
            pass
        elif self.language == 'android':
            self.parser_data = ANDROID_PARSER_DATA
            self._create_line_dynamic = self._create_android_line
        else:
            raise Exception(f'unknown language: {self.language}')

    def parse(self) -> semver.Version:
        with open(self.version_file, 'r') as file:
            for line in file:
                version_type, version_value = self._parse_line(line, self.parser_data)
                if version_type is not None and version_value is not None:
                    self.version_map[version_type] = version_value
                self.version_file_content.append(line)

            major = next((value for key, value in self.version_map.items() if "major" in str(key).lower()), "")
            minor = next((value for key, value in self.version_map.items() if "minor" in str(key).lower()), "")
            patch = next((value for key, value in self.version_map.items() if "patch" in str(key).lower()), "")
            pre_release_prefix = next((value for key, value in self.version_map.items() if "pre_release_prefix" in str(key).lower()), "")
            pre_release = next((value for key, value in self.version_map.items() if "pre_release" in str(key).lower() and "prefix" not in str(key).lower()), "")
            build_prefix = next((value for key, value in self.version_map.items() if "build_prefix" in str(key).lower()), "")
            build = next((value for key, value in self.version_map.items() if "build" in str(key).lower() and "prefix" not in str(key).lower()), "")
            version_string = str(major) + "." + str(minor) + "." + str(patch) + "-" + pre_release_prefix + "." + str(pre_release) + "+" + build_prefix + "." + str(build)
            print(version_string)
            ver = semver.Version.parse(version_string)
            return ver
    @staticmethod
    def _parse_line(line: str, parser_data: ()):
        pattern, version_type_group, version_value_group = parser_data
        result = re.search(pattern, line)
        if result is not None:
            version_type = result[version_type_group]
            version_value = result[version_value_group]
            return version_type, version_value
        return None, None

    def _update_version_file(self):
        new_lines = []
        for line in self.version_file_content:
            version_type, version_value = self._parse_line(line, self.parser_data)
            if version_type is not None and version_value is not None:
                new_lines.append(self._create_line_dynamic(line, self.version_map[version_type]))
            else:
                new_lines.append(line)

        with open(self.version_file, 'w') as file:
            file.writelines(new_lines)

    # TODO does not work with inline comments
    @staticmethod
    def _create_c_line(line: str, version: int):
        return re.sub(pattern=C_DEFINE_PATTERN,
                      repl=fr'\g<1>\g<2>\g<3>\g<4>{version}\g<6>',
                      string=line)

    @staticmethod
    def _create_android_line(line: str, version: int):
        return re.sub(pattern=ANDROID_DEFINE_PATTERN,
                      repl=fr'\g<1>\g<2>\g<3>{str(version)}\n',
                      string=line)