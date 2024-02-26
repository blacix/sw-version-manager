from version_file_parser import VersionFileParser
import semver
import xml.etree.ElementTree as ET
from lxml import etree


class RosPackageParser(VersionFileParser):
    LANGUAGES = ['ros']

    def __init__(self, version_file):
        super().__init__()
        self.version_file = version_file
        # self.xml_element_tree: ET.ElementTree = None
        # self.xml_version_tag: ET.Element = None
        self.lxml_tree: etree.ElementTree = None
        self.lxml_version_tag: etree.Element = None

    def parse(self) -> semver.Version:
        # Parse the XML data from the file
        # self.xml_element_tree = ET.parse(self.version_file)
        # root = self.xml_element_tree.getroot()
        # # Find the version tag and get its content
        # self.xml_version_tag = root.find('.//version')
        # return semver.Version.parse(self.xml_version_tag.text)
        self.lxml_tree = etree.parse(self.version_file)
        self.lxml_version_tag = self.lxml_tree.find('.//version')
        return semver.Version.parse(self.lxml_version_tag.text)

    def update(self, version: semver.Version):
        # if self.xml_element_tree is not None and self.xml_version_tag is not None:
        #     self.xml_version_tag.text = str(version)
        #     self.xml_element_tree.write(self.version_file, xml_declaration=True, encoding='utf-8')
        if self.lxml_tree is not None and self.lxml_version_tag is not None:
            original_encoding = self.lxml_tree.docinfo.encoding
            self.lxml_version_tag.text = str(version)
            self.lxml_tree.write(self.version_file, xml_declaration=True, method='xml', encoding=original_encoding,
                                 pretty_print=True)
