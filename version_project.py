import sys
sys.path.append('./scripts/')

PROJECT_VERSION_TAGS = ['APP_VERSION_MAJOR', 'APP_VERSION_MINOR', 'APP_VERSION_PATCH']
GIT_TAG_PREFIX = 'V'

if __name__ == '__main__':
    import version
    sys.exit(version.update_versions(sys.argv, GIT_TAG_PREFIX, PROJECT_VERSION_TAGS))
