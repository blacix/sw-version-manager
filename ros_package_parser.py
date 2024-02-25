from version_file_parser import VersionFileParser
import semver
import xml.etree.ElementTree as ET


class RosPackageParser(VersionFileParser):
    LANGUAGES = ['ros']

    def __init__(self, version_file):
        super().__init__()
        self.version_file = version_file
        self.version: semver.Version = None
        self.xml_element_tree: ET.ElementTree = None
        self.xml_version_tag: ET.Element = None

    def parse(self) -> semver.Version:
        # Parse the XML data from the file
        self.xml_element_tree = ET.parse(self.version_file)
        root = self.xml_element_tree.getroot()

        # Find the version tag and get its content
        self.xml_version_tag = root.find('.//version')
        return semver.Version.parse(self.xml_version_tag.text)

    def update(self, version: semver.Version):
        if self.xml_element_tree is not None and self.xml_version_tag is not None:
            self.xml_version_tag.text = str(version)
            self.xml_element_tree.write(self.version_file)
