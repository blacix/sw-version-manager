import re
from version_file_parser import VersionFileParser
import semver
from common import *

# [^\S] matches any char that is not a non-whitespace = any char that is whitespace
C_DEFINE_PATTERN = r"(.*#define)([^\S]+)(\S+)([^\S]+\"*)(\d+|[a-zA-Z]+)(\"*[^\S]*\n|$)"
# C_DEFINE_PATTERN = r"(.*#define)([^\S]+)(\S+)([^\S]+\"*)(\d+)(\"*[^\S]*\n|$)"
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

            # TODO get these in the for loop
            major = next((value for key, value in self.version_map.items() if Common.TAG_MAJOR.lower() in str(key).lower()), "")
            minor = next((value for key, value in self.version_map.items() if Common.TAG_MINOR.lower() in str(key).lower()), "")
            patch = next((value for key, value in self.version_map.items() if Common.TAG_PATCH.lower() in str(key).lower()), "")
            self.pre_release_prefix = next((value for key, value in self.version_map.items() if Common.TAG_PRE_RELEASE_PREFIX.lower() in str(key).lower()), "")
            pre_release = next((value for key, value in self.version_map.items() if Common.TAG_PRE_RELEASE.lower() in str(key).lower() and Common.TAG_PREFIX.lower() not in str(key).lower()), "")
            self.build_prefix = next((value for key, value in self.version_map.items() if Common.TAG_BUILD_PREFIX.lower() in str(key).lower()), "")
            build = next((value for key, value in self.version_map.items() if Common.TAG_BUILD.lower() in str(key).lower() and Common.TAG_PREFIX.lower() not in str(key).lower()), "")
            version_string = str(major) + "." + str(minor) + "." + str(patch)

            # When a mandatory version is bumped with semver, the optional parts with the value 0
            # are emitted from the version object.
            # When a string contains the optional 0 parts, and it is parsed with semver, the version object will contain
            # the optional 0 parts.
            # This can be an issue when comparing git tags.
            # The solution is that we also always omit the optional 0 parts when parsing a version file.

            # don't add optional 0 version to string, so git tag will not contain it
            if len(pre_release) > 0 and int(pre_release) != 0:
                version_string += "-"
                if len(self.pre_release_prefix) > 0:
                    version_string += self.pre_release_prefix + "."
                version_string += str(pre_release)
            # don't add optional 0 version to string, so git tag will not contain it
            if len(build) > 0 and int(build) != 0:
                version_string += "+"
                if len(self.build_prefix) > 0:
                    version_string += self.build_prefix + "."
                version_string += str(build)
            # print(version_string)
            ver = semver.Version.parse(version_string)
            return ver

    @staticmethod
    def _parse_line(line: str, parser_data: ()) -> (str, str):
        pattern, version_type_group, version_value_group = parser_data
        result = re.search(pattern, line)
        if result is not None:
            version_type = result[version_type_group]
            version_value = result[version_value_group]
            return version_type, version_value
        return None, None

    def _update_version_file(self, version: semver.Version):
        new_lines = []
        for line in self.version_file_content:
            version_type, version_value = self._parse_line(line, self.parser_data)
            if version_type is not None and version_value is not None:
                # update version map with new value
                # TODO separate method
                if Common.TAG_MAJOR.lower() in version_type.lower():
                    self.version_map[version_type] = version.major
                elif Common.TAG_MINOR.lower() in version_type.lower():
                    self.version_map[version_type] = version.minor
                elif Common.TAG_PATCH.lower() in version_type.lower():
                    self.version_map[version_type] = version.patch
                elif Common.TAG_PRE_RELEASE.lower() in version_type.lower() and Common.TAG_PREFIX.lower() not in version_type.lower():
                    if version.prerelease is not None:
                        numeric_prerelease = ""
                        for identifier in version.prerelease:
                            if identifier.isdigit():
                                numeric_prerelease += identifier
                        self.version_map[version_type] = numeric_prerelease
                    else:
                        self.version_map[version_type] = 0
                elif Common.TAG_BUILD.lower() in version_type.lower() and Common.TAG_PREFIX.lower() not in version_type.lower():
                    if version.build is not None:
                        numeric_build = ""
                        for identifier in version.build:
                            if identifier.isdigit():
                                numeric_build += identifier
                        self.version_map[version_type] = numeric_build
                    else:
                        self.version_map[version_type] = 0

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

    def update(self, version: semver.Version):
        self._update_version_file(version)
        # pass
