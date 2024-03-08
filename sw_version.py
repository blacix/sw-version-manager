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

    def __init__(self):
        args = self._parse_arguments()

        self.language: str = args.lang
        self.version_file: str = args.file
        self.bump: str = args.bump
        self.commit: bool = args.commit
        self.create_git_tag: bool = args.tag
        self.git_tag_prefix = args.tag_prefix
        self.git_tag = self.git_tag_prefix
        self.check_git_tag = args.check_tag
        self.pre_release_prefix = args.pre_release_prefix
        self.build_prefix = args.build_prefix
        self.repo_path = args.repo

        self.version: semver.Version = None

        self.git: GitUtils = None

        if self.language in TagFileParser.LANGUAGES:
            self.parser = TagFileParser(self.language, self.version_file, self.pre_release_prefix, self.build_prefix)
        elif self.language in RosPackageParser.LANGUAGES:
            self.parser = RosPackageParser(self.version_file)
        elif self.language in StringFileParser.LANGUAGES:
            self.parser = StringFileParser(self.version_file)
        else:
            self.parser: VersionFileParser = VersionFileParser()
            print(f'no parser for language: {self.language}')

    def _parse_arguments(self):
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
        parser.add_argument('--bump', choices=self.VALID_BUMPS, help='Specify the tag to bump')
        parser.add_argument('--check_tag', action='store_true',
                            help='checks is the tag is already on the current commit')
        parser.add_argument('--pre_release_prefix', default=None, help='The prefix for the pre-release number part')
        parser.add_argument('--build_prefix', default=None, help='The prefix for the build number part')
        parser.add_argument('--repo', default=".", help='Path to the git repository')
        return parser.parse_args()

    def _bump(self):
        if self.version is None:
            return
        elif Common.TAG_MAJOR.lower() == self.bump.lower():
            self.version = self.version.bump_major()
        elif Common.TAG_MINOR.lower() == self.bump.lower():
            self.version = self.version.bump_minor()
        elif Common.TAG_PATCH.lower() == self.bump.lower():
            self.version = self.version.bump_patch()
        elif Common.TAG_PRE_RELEASE.lower() == self.bump.lower():
            if self.pre_release_prefix is not None:
                self.version = self.version.bump_prerelease(self.pre_release_prefix)
            else:
                self.version = self.version.bump_prerelease()
        elif Common.TAG_BUILD.lower() in self.bump.lower():
            if self.build_prefix is not None:
                self.version = self.version.bump_build(self.build_prefix)
            else:
                self.version = self.version.bump_build()
        else:
            print(f'unknown bump: {self.version}')
            pass

    def execute(self) -> int:
        self.version = self.parser.parse()
        if self.version is None:
            print('Parse error')
            return -1

        if (self.commit or self.create_git_tag or self.check_git_tag) and self.git is None:
            self.git = GitUtils(self.repo_path)

        if self.check_git_tag:
            pre_bump_git_tag = self.git_tag_prefix + str(self.version)
            if self.git.check_tag_on_current_commit(pre_bump_git_tag):
                print(f'tag on current commit: {pre_bump_git_tag}')
                self.bump = False
                self.create_git_tag = False
                self.commit = False

        if self.bump:
            self._bump()
            self.parser.update(self.version)
        else:
            # When a mandatory version is bumped with semver, the optional parts with the value 0
            # are emitted from the version object.
            # When a string contains the optional 0 parts, and it is parsed with semver, the version object will contain
            # the optional 0 parts.
            # This can be an issue when comparing git tags when we don't bump any version, just parse a string with
            # optional parts being 0, e.g. we can have a tag: 0.0.0-0+0
            self.version = Common.emit_optional_zero_parts(self.version)

        self.git_tag = self.git_tag_prefix + str(self.version)
        if self.commit:
            self.git.commit_file(self.version_file, self.git_tag)

        if self.create_git_tag:
            self.git.create_tag(self.git_tag)

        result = str(self.git_tag_prefix + str(self.version))
        print(result)
        return 0


if __name__ == '__main__':
    sys.exit(SoftwareVersion().execute())
