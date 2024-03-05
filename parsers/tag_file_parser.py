import re
import semver
from common import *
from parsers.version_file_parser import VersionFileParser


class TagFileParser(VersionFileParser):
    LANGUAGES = ['c', 'cpp', 'android']

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

    def __init__(self, language: str, version_file: str, pre_release_prefix: str, build_prefix: str):
        super().__init__(pre_release_prefix, build_prefix)
        self.language = language
        self.version_file = version_file
        self.version_file_content = []
        self.version_map = {}

        if self.language == 'c':
            self.parser_data = self.C_PARSER_DATA
            self._create_line_dynamic = self._create_c_line
        elif self.language == 'cpp':
            pass
        elif self.language == 'android':
            self.parser_data = self.ANDROID_PARSER_DATA
            self._create_line_dynamic = self._create_android_line
        else:
            raise Exception(f'unknown language: {self.language}')

    def parse(self) -> semver.Version:
        version: semver.Version = None
        with open(self.version_file, 'r') as file:
            for line in file:
                version_type, version_value = self._parse_line(line, self.parser_data)
                if version_type is not None and version_value is not None:
                    self.version_map[version_type] = version_value
                self.version_file_content.append(line)

            # TODO get these in the for loop
            # get mandatory parts of the version
            major = next(
                (value for key, value in self.version_map.items() if Common.TAG_MAJOR.lower() in str(key).lower()), "")
            minor = next(
                (value for key, value in self.version_map.items() if Common.TAG_MINOR.lower() in str(key).lower()), "")
            patch = next(
                (value for key, value in self.version_map.items() if Common.TAG_PATCH.lower() in str(key).lower()), "")
            version_string = str(major) + "." + str(minor) + "." + str(patch)

            # get optional parts of the version
            # if the header file contains a prefix, save it even if it is not specified
            if self.pre_release_prefix is None:
                self.pre_release_prefix = next((value for key, value in self.version_map.items() if
                                                Common.TAG_PRE_RELEASE_PREFIX.lower() in str(key).lower()), "")
            pre_release = next((value for key, value in self.version_map.items() if
                                Common.TAG_PRE_RELEASE.lower() in str(
                                    key).lower() and Common.TAG_PREFIX.lower() not in str(key).lower()), "")
            # if the header file contains a prefix, save it even if it is not specified
            if self.build_prefix is None:
                self.build_prefix = next((value for key, value in self.version_map.items() if
                                          Common.TAG_BUILD_PREFIX.lower() in str(key).lower()), "")
            build = next((value for key, value in self.version_map.items() if
                          Common.TAG_BUILD.lower() in str(key).lower() and Common.TAG_PREFIX.lower() not in str(
                              key).lower()), "")
            # add the optional part to the version string
            if len(pre_release) > 0:
                version_string += "-"
                if self.pre_release_prefix is not None and len(self.pre_release_prefix) > 0:
                    version_string += self.pre_release_prefix + "."
                version_string += str(pre_release)
            if len(build) > 0:
                version_string += "+"
                if self.build_prefix is not None and len(self.build_prefix) > 0:
                    version_string += self.build_prefix + "."
                version_string += str(build)
            try:
                version = semver.Version.parse(version_string)
            except (ValueError, TypeError) as e:
                print(e)
            return version

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
                elif Common.TAG_PRE_RELEASE_PREFIX.lower() in version_type.lower():
                    if self.pre_release_prefix is not None:
                        self.version_map[version_type] = self.pre_release_prefix
                elif Common.TAG_PRE_RELEASE.lower() in version_type.lower() and Common.TAG_PREFIX.lower() not in version_type.lower():
                    if version.prerelease is not None:
                        numeric_prerelease = ""
                        for identifier in version.prerelease:
                            if identifier.isdigit():
                                numeric_prerelease += identifier
                        self.version_map[version_type] = numeric_prerelease
                    else:
                        self.version_map[version_type] = 0
                elif Common.TAG_BUILD_PREFIX.lower() in version_type.lower():
                    if self.build_prefix is not None:
                        self.version_map[version_type] = self.build_prefix
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
    def _create_c_line(self, line: str, version: int):
        return re.sub(pattern=self.C_DEFINE_PATTERN,
                      repl=fr'\g<1>\g<2>\g<3>\g<4>{version}\g<6>',
                      string=line)

    def _create_android_line(self, line: str, version: int):
        return re.sub(pattern=self.ANDROID_DEFINE_PATTERN,
                      repl=fr'\g<1>\g<2>\g<3>{str(version)}\n',
                      string=line)

    def update(self, version: semver.Version):
        self._update_version_file(version)
        # pass
