# sw-version-manager
Minimalist and portable py script for automatically incrementing software version in a C header and update it in git as well.
It uses only stock python libraries, like os, sys, subprocess.

Works with Python version 3.3 and above.

Tested with Python 3.7.

- updates the desired version type in the version file passed as argument
- can commit and push the version file
- can creates a git tag with the version

# how to use
The script only works with C `#define` macros.
e.g: `#define APP_VERSION_MAJOR 3`
- create a preferably separate version file, e.g.: `version.h`
- create a config file based on the template provied
- run the script with the desired arguments

The script prints the version string to `stdout`, so the version string can be captured in a shell variable. See example scenario.

## how to run
`
python version.py version_file_path config_file_path [--update | --git | --read --output]
`
- 	--read: 
		reads the version file
		version file will not be updated if present
- 	--update:
		updates the version file
		this is the default if no extra args are provided
- 	--git:
		creates and pushes a git tag if configured
		commits and pushes the version file
		version file update will only be updated if --update is present
- 	--output:
		creates output file containing the version string
## how to configure
- add your version tags to `version_tags`
- create a preferably separate version file. e.g `version.h`
```json
{
  "version_tags" : [
    "APP_VERSION_MAJOR",
    "APP_VERSION_MINOR",
    "APP_VERSION_REV",
    "APP_VERSION_PATCH",
    "APP_VERSION_BUILD"
  ],
  "increment" : ["APP_VERSION_REV", "APP_VERSION_BUILD"],
  "language" : "C,",
  "create_git_tag" : true,
  "git_tag_prefix": "V",
  "output_file" : "version.txt",
  "commit_message" : "version ",
  "append_version" : true
}
```
- increment: version tags to be incremented in the version file.
- language: not implemented yet, only works with C `#define` macros
- create_git_tag: git tag is created and pushed to origin if true
The default git tag is the version string, e.g.: `1.0.0`
- git_tag_prefix: adds this prefix to the git tag, e.g.: `V1.0.0`
- output_file: if `--output` is provided as argument, the output file with this name, containing the version string is created
- commit_message: commit message when commiting the version file. e.g.: `"version: "`
- append_version: appends the version string to the commit message
- version_tags: the tags present in your version file, e.g.: `version.h`

## example scenario
```bash
cd <your project>
git clone https://github.com/blacix/sw-version-manager.git
# update version file
python sw-version-manager/version.py src/app_version.h version_config.json
# perform a build
# update git and save the version
version=$(python sw-version-manager/version.py src/app_version.h version_config.json --git)
mv <your_build_output> <your_build_output>_V$(version)
```


## extra args
- --notag: git tag will not be created
- --nocommit: version file will not be commited
