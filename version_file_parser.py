import semver


class VersionFileParser:
    LANGUAGES = []

    def __init__(self, pre_release_prefix: str = '', build_prefix: str = ''):
        self.pre_release_prefix = pre_release_prefix
        self.build_prefix = build_prefix

    def parse(self) -> semver.Version:
        return None

    def update(self, version: semver.Version):
        pass
