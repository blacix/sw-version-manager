import sys
import argparse
import semver
from common import *
from git_utils import GitUtils
from parsers.version_file_parser import VersionFileParser
from parsers.tag_file_parser import TagFileParser
from parsers.ros_package_parser import RosPackageParser
from parsers.string_file_parser import StringFileParser


class SoftwareVersion:
    VALID_BUMPS = [Common.TAG_MAJOR, Common.TAG_MINOR, Common.TAG_PATCH, Common.TAG_PRE_RELEASE, Common.TAG_BUILD]

    def __init__(self, language, version_file, to_bump=None, commit=False, create_git_tag=False, git_tag_prefix=None,
                 check_git_tag=False,
                 pre_release_prefix=None, build_prefix=None, repo_path='.'):

        self.language: str = language
        self.version_file: str = version_file
        self.to_bump: str = to_bump
        self.commit: bool = commit
        self.create_git_tag: bool = create_git_tag
        self.git_tag_prefix = git_tag_prefix
        self.git_tag = self.git_tag_prefix
        self.check_git_tag = check_git_tag
        self.pre_release_prefix = pre_release_prefix
        self.build_prefix = build_prefix
        self.repo_path = repo_path

        self.version: semver.Version = None

        self.git: GitUtils = None
        if (self.commit or self.create_git_tag or self.check_git_tag) and self.git is None:
            self.git = GitUtils(self.repo_path)

        if self.language in TagFileParser.LANGUAGES:
            self.parser = TagFileParser(self.language, self.version_file, self.pre_release_prefix, self.build_prefix)
        elif self.language in RosPackageParser.LANGUAGES:
            self.parser = RosPackageParser(self.version_file)
        elif self.language in StringFileParser.LANGUAGES:
            self.parser = StringFileParser(self.version_file)
        else:
            self.parser: VersionFileParser = VersionFileParser()
            print(f'no parser for language: {self.language}')

        self._parse()

    @staticmethod
    def parse_arguments():
        parser = argparse.ArgumentParser(description='Command-line arguments example')
        # Mandatory arguments
        parser.add_argument('--file', required=True, help='Specify the filename')
        parser.add_argument('--lang',
                            choices=TagFileParser.LANGUAGES + RosPackageParser.LANGUAGES + StringFileParser.LANGUAGES,
                            required=True, help='Specify the language')
        # Optional arguments without values
        parser.add_argument('--commit', action='store_true', help='commit the updated version file')
        parser.add_argument('--tag', action='store_true', help='add a tag with the version to git')
        parser.add_argument('--tag_prefix', default='', help='Prefix for git tag')
        parser.add_argument('--bump', choices=SoftwareVersion.VALID_BUMPS, help='Specify the tag to bump')
        parser.add_argument('--check_tag', action='store_true',
                            help='checks is the tag is already on the current commit')
        parser.add_argument('--pre_release_prefix', default=None, help='The prefix for the pre-release number part')
        parser.add_argument('--build_prefix', default=None, help='The prefix for the build number part')
        parser.add_argument('--repo', default=".", help='Path to the git repository')
        return parser.parse_args()

    def _parse(self):
        semver.VersionInfo.major
        self.version = self.parser.parse()
        # When a mandatory version is bumped with semver, the optional parts with the value 0
        # are emitted from the version object.
        # When a string contains the optional 0 parts, and it is parsed with semver, the version object will contain
        # the optional 0 parts.
        # This can be an issue when comparing git tags when we don't bump any version, just parse a string with
        # optional parts being 0, e.g. we can have a tag: 0.0.0-0+0
        self.version = Common.emit_optional_zero_parts(self.version)

    def _bump_version(self, bump):
        if self.version is None:
            return
        elif Common.TAG_MAJOR.lower() == bump.lower():
            self.version = self.version.bump_major()
        elif Common.TAG_MINOR.lower() == bump.lower():
            self.version = self.version.bump_minor()
        elif Common.TAG_PATCH.lower() == bump.lower():
            self.version = self.version.bump_patch()
        elif Common.TAG_PRE_RELEASE.lower() == bump.lower():
            if self.pre_release_prefix is not None:
                self.version = self.version.bump_prerelease(self.pre_release_prefix)
            else:
                self.version = self.version.bump_prerelease()
        elif Common.TAG_BUILD.lower() in bump.lower():
            if self.build_prefix is not None:
                self.version = self.version.bump_build(self.build_prefix)
            else:
                self.version = self.version.bump_build()
        else:
            print(f'unknown bump: {self.version}')
            pass

    def execute(self) -> int:
        if self.version is None:
            print('Parse error')
            return 1

        return_value = 0

        if self.check_git_tag:
            return_value = self._check_git_tag()

        self.git_tag = self.git_tag_prefix + str(self.version)
        if self.commit:
            try:
                self.git.commit_file(self.version_file, self.git_tag)
            except Exception as e:
                print(e)
                return_value = 3

        if self.to_bump:
            self.bump(self.to_bump)

        if self.create_git_tag:
            try:
                self.git.tag_repo(self.git_tag)
            except Exception as e:
                print(e)
                return_value = 4

        result = str(self.git_tag_prefix + str(self.version))
        print(result)
        return return_value

    def _check_git_tag(self):
        return_value = 0
        pre_bump_git_tag = self.git_tag_prefix + str(self.version)
        if self.git.check_tag_on_current_commit(pre_bump_git_tag):
            print(f'tag on current commit: {pre_bump_git_tag}')
            self.to_bump = False
            self.create_git_tag = False
            self.commit = False
            return_value = 2
        return return_value

    def bump(self, bump):
        self._bump_version(bump)
        self.parser.update(self.version)
        return self.version


if __name__ == '__main__':
    args = SoftwareVersion.parse_arguments()
    sys.exit(SoftwareVersion(args.lang, args.file, args.bump, args.commit, args.tag, args.tag_prefix, args.check_tag,
                             args.pre_release_prefix, args.build_prefix, args.repo).execute())
