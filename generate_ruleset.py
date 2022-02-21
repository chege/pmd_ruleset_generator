#!/usr/bin/env python
import tempfile
from git import Repo
import xml.etree.ElementTree as ET
import re
import os


class cd:
    """Context manager for changing the current working directory"""

    def __init__(self, new_path):
        self.new_path = os.path.expanduser(new_path)

    def __enter__(self):
        self.saved_path = os.getcwd()
        os.chdir(self.new_path)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.saved_path)


def namespace(element):
    m = re.match(r'{(.*)}', element.tag)
    return m.group(1) if m else ''


def clone_branch(url, to_path, branch_name, **kwargs):
    Repo.clone_from(url, to_path, branch=branch_name, **kwargs)


def category_path(path):
    m = re.match(r'.*(category/.*)', path)
    return m.group(1) if m else None


def remove_all(tag_name, tree):
    parent = {c: p for p in tree.iter() for c in p}
    for rule in tree.getroot().findall(tag_name):
        parent[rule].remove(rule)


def rule_names(category_file):
    tree = ET.parse(category_file)
    ns = namespace(tree.getroot())
    rules = tree.getroot().findall(f'{{{ns}}}rule')
    return [rule.attrib['name'] for rule in rules]


def create_output_tree(file):
    tree = ET.parse(file)
    rule_tag_name = f'{{{namespace(tree.getroot())}}}rule'
    remove_all(rule_tag_name, tree)
    return tree


def main():
    with tempfile.TemporaryDirectory() as tempdir:
        repo_url = 'https://github.com/pmd/pmd.git'
        print(f"Cloning {repo_url}...")

        clone_branch(repo_url, tempdir, 'pmd_releases/6.42.0', depth=1)
        files = [f'{tempdir}/{path}' for path in [
            'pmd-java/src/main/resources/category/java/design.xml',
            'pmd-java/src/main/resources/category/java/multithreading.xml',
            'pmd-java/src/main/resources/category/java/bestpractices.xml',
            'pmd-java/src/main/resources/category/java/documentation.xml',
            'pmd-java/src/main/resources/category/java/errorprone.xml',
            'pmd-java/src/main/resources/category/java/codestyle.xml',
            'pmd-java/src/main/resources/category/java/performance.xml',
            'pmd-java/src/main/resources/category/java/security.xml',
        ]]

        print("Creating template XML tree...")
        tree = create_output_tree(files[0])

        ET.register_namespace('', namespace(tree.getroot()))

        print("Adding rules and excusions...")
        for file in files:
            rule_elm = ET.SubElement(tree.getroot(), 'rule')
            rule_elm.attrib['ref'] = category_path(file)

            for rule in rule_names(file):
                exclude_elm = ET.SubElement(rule_elm, 'exclude')
                exclude_elm.attrib['name'] = rule

        print("Pretty printing...")
        ET.indent(tree, '    ', 0)

        output_file = 'ruleset.xml'

        print(f"Writing to file {output_file}...")
        tree.write(output_file)

        print("Done!")


if __name__ == '__main__':
    main()
