from version_file_parser import VersionFileParser
import semver
import re


class StringFileParser(VersionFileParser):
    LANGUAGES = ['c_str']
    C_DEFINE_PATTERN = r'(.*#define\s+\w+VERSION\s+)(")(\S+)(")(\s+\n|$)'
    C_VERSION_STRING_GROUP = 3

    def __init__(self, version_file):
        super().__init__()
        self.version_file = version_file
        self.version: semver.Version = None
        self.version_file_content: [str] = []

    def parse(self) -> semver.Version:
        version: semver.Version = None
        pattern = re.compile(self.C_DEFINE_PATTERN, re.IGNORECASE)
        version_string = ''
        with open(self.version_file, 'r') as file:
            for line in file:
                match = re.match(pattern, line)
                if match:
                    version_string = match.group(self.C_VERSION_STRING_GROUP)
                self.version_file_content.append(line)
            try:
                version = semver.Version.parse(version_string)
            except (ValueError, TypeError) as e:
                print(e)
        return version

    def update(self, version: semver.Version):
        new_lines = []
        pattern = re.compile(self.C_DEFINE_PATTERN, re.IGNORECASE)
        for line in self.version_file_content:
            if re.match(pattern, line):
                line = re.sub(pattern=self.C_DEFINE_PATTERN,
                              repl=fr'\g<1>\g<2>{str(version)}\g<4>\g<5>',
                              string=line)
            new_lines.append(line)
        with open(self.version_file, 'w') as file:
            file.writelines(new_lines)
