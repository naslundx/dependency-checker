#! /usr/bin/env python3

from distutils.version import StrictVersion
import subprocess
import sys
import re
import argparse
import json
import logging


# Parses incoming arguments
class DependencyCheckerArgumentParser(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        self.parser.epilog = "Dependency Checker: Assert existence and versions of packages and libraries."
        format_group = self.parser.add_argument_group("Options")
        format_group.add_argument('--version', action='version', version='Dependency Checker 0.91')
        format_group.add_argument(
            "--verbose",
            action="store_true",
            help="Verbose output.")
        format_group.add_argument(
            "--silent",
            action="store_true",
            help="Produce no output.")
        format_group.add_argument(
            "--config",
            default="config.json",
            help="config file",
            nargs="*")
        format_group.add_argument(
            "executors",
            nargs="*")

    def parse(self, arguments):
        return self.parser.parse_args(arguments)


# Represents a list of configuration files
class DependencyCheckerConfigurations(object):
    def __init__(self, filenames):
        self.data = []
        for filename in filenames:
            logging.info("Using configuration from {}".format(filename))
            self.data.append(json.load(open(filename)))

    def get_command(self, name):
        for part in self.data:
            for item in part:
                if item["name"] == name:
                    return item["command"]
        return None

    def get_regexp(self, name):
        for part in self.data:
            for item in part:
                if item["name"] == name:
                    return item["regexp"]
        return None


# Runs command and checks regexp for required version
def check_version(name, command, regexp, required=None, maximum=None):
    logging.debug("name={}, command=\"{}\", regexp=\"{}\", required={}, maximum={}".format(name, command, regexp, required, maximum))
    
    if required and maximum:
        req_string = "(required: {}, maximum: {})".format(required, maximum)
    elif required:
        req_string = "(required: {})".format(required)
    elif maximum:
        req_string = "(maximum: {})".format(maximum)
    else:
        req_string = ""

    try:
        output = subprocess.check_output(command, shell=True, universal_newlines=True).strip()
        logging.debug("--- output:\n{}\n---".format(output))

    except subprocess.CalledProcessError:
        logging.error("[ERROR]\t{} not found! {}".format(name, req_string))

    try:
        version = re.search(regexp, output, re.MULTILINE).group(1)
        found_version = StrictVersion(version)
        required_version = StrictVersion(required) if required else None
        maximum_version = StrictVersion(maximum) if maximum else None
        logging.debug("found version {}".format(found_version))

    except (AttributeError, ValueError) as e:
        logging.error("Error reading version from {}".format(name))
        return False

    version_satisfied = ((required and found_version >= required_version) or (not required)) and \
                        ((maximum and found_version <= maximum_version) or (not maximum))

    if version_satisfied:
        logging.info("[OK]\t{} {} {}".format(name, version, req_string))
    else:
        logging.error("[ERROR]\t{} {} {}".format(name, version, req_string))

    return version_satisfied


# Process executor
def process_executor(filename, config):
    executor = json.load(open(filename))
    result = True

    for item in executor:
        name = item["name"]
        command = config.get_command(name)
        regexp = config.get_regexp(name)
        required = None

        logging.debug("{}:".format(name))

        if "command" in item:
            command = item["command"]
        elif not command:
            logging.debug("No command set or found! Setting command to name.")
            command = name

        if "regexp" in item:
            regexp = item["regexp"]

        if "required" in item:
            required = item["required"]

        result = check_version(name, command, regexp, required) and result

    return result


# Main function
def main():
    # Parse options and setup logger
    options = DependencyCheckerArgumentParser().parse(sys.argv[1:])
    if options.verbose:
        level = logging.DEBUG
    elif options.silent:
        level = logging.CRITICAL
    else:
        level = logging.INFO
    logging.basicConfig(format='%(message)s', level=level)

    # Get config file
    config = DependencyCheckerConfigurations(options.config)

    # Run through executors
    result = True
    for executor in options.executors:
        logging.info("Checking {}...".format(executor))
        result = process_executor(executor, config) and result
        logging.info("")

    if result:
        logging.info("Done. Everything OK.")
    else:
        logging.info("Done. Errors detected!")

    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
