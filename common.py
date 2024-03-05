import semver


class Common:
    TAG_MAJOR = 'major'
    TAG_MINOR = 'minor'
    TAG_PATCH = 'patch'
    TAG_PRE_RELEASE = 'prerelease'
    TAG_BUILD = 'build'
    TAG_PREFIX = 'prefix'
    TAG_PRE_RELEASE_PREFIX = TAG_PRE_RELEASE + "_" + TAG_PREFIX
    TAG_BUILD_PREFIX = TAG_BUILD + "_" + TAG_PREFIX

    # gets numeric part from pre-release or build part
    @staticmethod
    def get_numeric(semver_optional: str) -> int:
        numeric_part = ""
        for identifier in semver_optional:
            if identifier.isdigit():
                numeric_part += identifier
        return int(numeric_part)

    # emits optional zero parts
    @staticmethod
    def emit_optional_zero_parts(version: semver.Version) -> semver.Version:
        version_dict = version.to_dict()
        numeric_pre_release = Common.get_numeric(version_dict[Common.TAG_PRE_RELEASE])
        if numeric_pre_release == 0:
            version_dict[Common.TAG_PRE_RELEASE] = None

        numeric_build = Common.get_numeric(version_dict[Common.TAG_BUILD])
        if numeric_build == 0:
            version_dict[Common.TAG_BUILD] = None
        return semver.Version(**version_dict)

