import semver


class VersionFileParser:
    LANGUAGES = []

    def __init__(self):
        self.pre_release_prefix = ''
        self.build_prefix = ''

    def parse(self) -> semver.Version:
        return None

    def update(self, version: semver.Version):
        pass
