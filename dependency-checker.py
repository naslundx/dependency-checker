#! /usr/bin/env python3

from distutils.version import StrictVersion
import subprocess
import sys
import re
import argparse
import json


# Parses incoming arguments
class DependencyCheckerArgumentParser(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        self.parser.epilog = "..."
        format_group = self.parser.add_argument_group("Options")
        format_group.add_argument(
            '--config',
            default="config.json",
            help='config file')
        format_group.add_argument(
            "executors",
            nargs="*")

    def parse(self, arguments):
        return self.parser.parse_args(arguments)


# Represents a configuration file
class DependencyCheckerConfiguration(object):
    def __init__(self, filename):
        self.data = json.load(open(filename))

    def get_command(self, name):
        for item in self.data:
            if item["name"] == name:
                return item["command"]
        return None

    def get_regexp(self, name):
        for item in self.data:
            if item["name"] == name:
                return item["regexp"]
        return None


# Runs command and checks regexp for required version
def check_version(name, command, regexp, required):
    try:
        output = subprocess.check_output(command, shell=True, universal_newlines=True).strip()

    except subprocess.CalledProcessError:
        if required:
            print("[ERROR]\t{} not found! (required: {})".format(name, required))
        else:
            print("[ERROR]\t{} not found!".format(name))

    try:
        version = re.search(regexp, output, re.MULTILINE).group(1)
        found_version = StrictVersion(version)
        required_version = StrictVersion(required)
    except (AttributeError, ValueError) as e:
        print("Error reading version from {}".format(name))
        return False

    if required:
        result = found_version >= required_version
        status = "[OK]" if result else "[ERROR]"
        print("{}\t{} {} (required: {})".format(status, name, version, required))
        return result
    if not required:
        print("{}\t{} {}".format("[OK]", name, version))
        return True

    return False


# Process executor
def process_executor(filename, config):
    executor = json.load(open(filename))
    result = True

    for item in executor:
        name = item["name"]

        if "command" in item:
            command = item["command"]
        else:
            command = config.get_command(name)

        if "regexp" in item:
            regexp = item["regexp"]
        else:
            regexp = config.get_regexp(name)

        if "required" in item:
            required = item["required"]
        else:
            required = None

        result = check_version(name, command, regexp, required) and result
    
    return result


# Main function
def main():
    options = DependencyCheckerArgumentParser().parse(sys.argv[1:])
    config = DependencyCheckerConfiguration(options.config)

    result = True
    for executor in options.executors:
        print("Checking {}...".format(executor))
        result = process_executor(executor, config) and result
        print("")

    if result:
        print("Done. Everything OK.")
    else:
        print("Done. Errors detected!")

    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
