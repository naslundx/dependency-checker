#! /usr/bin/env python3

from distutils.version import StrictVersion
import subprocess
import sys
import re
import argparse
import json
import logging
import os


# Parses incoming arguments
class DependencyCheckerArgumentParser(object):
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        self.parser.epilog = "Dependency Checker: Assert existence and versions of packages and libraries."
        format_group = self.parser.add_argument_group("Options")
        format_group.add_argument('--version', action='version', version='Dependency Checker 0.93')
        format_group.add_argument(
            "--verbose",
            action="store_true",
            help="Verbose output.")
        format_group.add_argument(
            "--silent",
            action="store_true",
            help="Produce no output.")
        format_group.add_argument(
            "--failfast",
            action="store_true",
            help="Stop on first error.")
        format_group.add_argument(
            "--onlyerrors",
            action="store_true",
            help="Only print errors.")
        format_group.add_argument(
            "--listerrors",
            action="store_true",
            help="List all found errors on exit.")
        format_group.add_argument(
            "--config",
            default=["config.json"],
            help="config file",
            nargs="*")
        format_group.add_argument(
            "executors",
            nargs="*")

    def parse(self, arguments):
        options = self.parser.parse_args(arguments)

        if options.verbose and options.silent:
            print("Cannot use --verbose with --silent!")
            sys.exit(1)

        if not options.executors:
            print("No executors given, nothing to do!")
            sys.exit(1)

        return options


# Represents a list of configuration files
class DependencyCheckerConfigurations(object):
    def __init__(self, filenames):
        self.data = []
        for filename in filenames:
            logging.info("Using configuration from {}".format(filename))
            self.data.append(json.load(open(filename)))

    def find_items(self, name):
        result = []
        for part in self.data:
            for item in part:
                if "name" in item and item["name"] == name:
                    result.append(item)
        logging.debug("Could not find item with name {}".format(name))
        return result

    def get_item_tag(self, name, tag):
        try:
            items = self.find_items(name)
            tags = [item[tag] for item in items]
            if len(set(tags)) > 1:
                logging.error("Conflicting tags found for {}, selecting {}".format(name, tags[0]))
            return tags[0]
        except Exception as e:
            logging.error("Tag {} not found for {}".format(tag, name))
            return None


# Runs command and checks regexp for required version
def check_version(name, command, regexp, required=None, maximum=None, contains=None):
    logging.debug("name={}, command=\"{}\", regexp=\"{}\", required={}, maximum={}, contains={}".format(name, command, regexp, required, maximum, contains))

    req_strings = []
    if required:
        req_strings.append("required: {}".format(required))
    if maximum:
        req_strings.append("maximum: {}".format(maximum))
    if contains:
        req_strings.append("contains: {}".format(contains))
    req_string = ", ".join(req_strings)
    if req_string:
        req_string = "({})".format(req_string)

    try:
        with open(os.devnull, 'w') as devnull:
            output = subprocess.check_output(command, shell=True, universal_newlines=True, stderr=devnull).strip()
        logging.debug("--- output:\n{}\n---".format(output))

    except subprocess.CalledProcessError:
        logging.error("[ERROR]\t{} - Not found! {}".format(name, req_string))
        return False

    matched_output = output
    version_satisfied = True
    try:
        if regexp:
            matched_output = re.search(regexp, output, re.MULTILINE).group(1)
            found_version = StrictVersion(matched_output)
            required_version = StrictVersion(required) if required else None
            maximum_version = StrictVersion(maximum) if maximum else None
            version_satisfied = ((required_version and found_version >= required_version) or (not required_version)) and \
                                ((maximum_version and found_version <= maximum_version) or (not maximum_version))
            logging.debug("found version {}".format(found_version))

    except (AttributeError, ValueError, UnboundLocalError) as e:
        logging.error("[ERROR]\t{} - Could not parse version! {}".format(name, req_string))
        return False

    version_satisfied = version_satisfied and ((contains and contains in matched_output) or (not contains))

    if version_satisfied:
        logging.info("[OK]\t{} {} {}".format(name, matched_output, req_string))
    else:
        logging.error("[ERROR]\t{} {} {}".format(name, matched_output, req_string))

    return version_satisfied


# Process executor
def process_executor(filename, options, config):
    executor = json.load(open(filename))
    errors = []

    for item in executor:
        name = item["name"]
        command = config.get_item_tag(name, "command")
        regexp = config.get_item_tag(name, "regexp")
        required = None
        maximum = None
        contains = None

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

        if "maximum" in item:
            maximum = item["maximum"]

        if "contains" in item:
            contains = item["contains"]

        result = check_version(name, command, regexp, required, maximum, contains)
        if not result:
            errors.append(name)
            if options.failfast:
                break

    return errors


# Main function
def main():
    # Parse options and setup logger
    options = DependencyCheckerArgumentParser().parse(sys.argv[1:])
    if options.verbose:
        level = logging.DEBUG
    elif options.silent:
        level = logging.CRITICAL
    elif options.onlyerrors:
        level = logging.WARNING
    else:
        level = logging.INFO
    logging.basicConfig(format='%(message)s', level=level)

    # Get config file
    config = DependencyCheckerConfigurations(options.config)

    # Run through executors
    errors = []
    for executor in options.executors:
        logging.info("{}:".format(executor))
        result = process_executor(executor, options, config)
        errors.extend(result)
        logging.info("")
        if options.failfast and len(errors) > 0:
            break

    # Print result
    if not errors:
        logging.info("Done. Everything OK.")

    # Print list of errors
    if options.listerrors and errors:
        logging.error("Errors:")
        for name in errors:
            logging.error("{}".format(name))

    # Exit
    return len(errors)


if __name__ == "__main__":
    sys.exit(main())
