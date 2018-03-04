# dependency-checker (version 0.9)
Verify the existence and versions of installed dependencies using regex.
Released under the MIT license.

## Usecase
Often, when setting up a new private workstation, or maintaining multiple computers or servers in a workplace, certain packages must be installed and must be of certain versions to be compatible with specific tasks. This script provides an automated way of checking that.

Packages to be checked and versions to be asserted are written in a json script. See "How does it work?" for instructions.

## How does it work?
Setup a JSON file (called executor) with a single unnamed array. Each element in this array should specify the packages to check with a "name" tag.

For example, `{"name":"gcc"}` will assert that `gcc` is installed. This works because the global config file (`config.json` by default, or specify your own with `--config` flag) has a listing of a command to run associated with `gcc`, `gcc --version`.

To check that `gcc` also has a minimum version: `{"name":"gcc", "required":"4.9"}`. Again, this works because the global config file has a regular expression that selects the part of the output from `gcc --version` that describes the installed version.

The `config.json` contained here contains commands for common packages. You can add to this list, or write `"command"` and `"regexp"` contains directly in your executor file.

This repository contains an `example.json` for an example executor. You can specify more than one executor on the command line to `dependency-checker.py`.

## Contribute
Feel free to contribute! This is a new project and it's still uncertain where it will go.


## Future features
Features:
 - support just "contains" instead of regexp matching
 - support multiple config files
 - support asserting max version
 - assert version only if installed

Usability:
 - more arguments (silent, verbose, list all errors on exit, stop at first error)
 - support pipe to script
 - run via CLI arguments
 - if no command found (and required not specified, assert existence by just calling the name)

Other:
 - better error checking
 - add more to config file
 - documentation

