from version_file_parser import VersionFileParser
import semver
import re


class StringFileParser(VersionFileParser):
    LANGUAGES = ['c_str']

    def __init__(self, version_file):
        super().__init__()
        self.version_file = version_file
        self.version: semver.Version = None
        self.version_file_content: [str] = []

    def parse(self) -> semver.Version:
        pattern = re.compile(r'(.*#define\s+\w+VERSION\s+)(")(\S+)(")(\s+\n|$)', re.IGNORECASE)
        version_string = ''
        with open(self.version_file, 'r') as file:
            for line in file:
                match = re.match(pattern, line)
                if match:
                    version_string = match.group(3)
                    print(f"Version String: {version_string}")
                self.version_file_content.append(line)
        return semver.Version.parse(version_string)

    def update(self, version: semver.Version):
        pass
