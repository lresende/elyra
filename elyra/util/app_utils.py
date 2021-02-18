#
# Copyright 2018-2021 Elyra Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import ast
import logging
import sys

"""Utility functions and classes used for Elyra CLI applications and classes."""

logging.basicConfig(level=logging.INFO, format='[%(levelname)1.1s %(asctime)s.%(msecs).03d] %(message)s')


class Option(object):
    """
    Represents the base option class.
    """
    cli_option = None
    name = None
    description = None
    default_value = None
    required = False
    value = None
    type = None  # Only used by SchemaProperty instances for now
    processed = False

    def __init__(self, cli_option, name=None, description=None, default_value=None, one_of=None,
                 required=False, type="string"):
        self.cli_option = cli_option
        self.name = name
        self.description = description
        self.default_value = default_value
        self.value = default_value
        self.one_of = one_of
        self.required = required
        self.type = type

    def set_value(self, value):
        if self.type == 'array' or self.type == 'object':
            self.value = ast.literal_eval(value)
        elif self.type == 'integer':
            self.value = int(value)
        elif self.type == 'number':
            if "." in value:
                self.value = float(value)
            else:
                self.value = int(value)
        elif self.type == 'boolean':
            if isinstance(value, bool):
                self.value = value
            elif str(value).lower() in ("true", "1"):
                self.value = True
            elif str(value).lower() in ("false", "0"):
                self.value = False
            else:
                self.value = value  # let it take its course
        elif self.type == 'null':
            if str(value) in ("null", "None"):
                self.value = None
            else:
                self.value = value
        else:
            self.value = value

    def print_help(self):
        if isinstance(self, CliOption):
            print("{option}=<{type}>".format(option=self.cli_option, type=self.type))
        else:
            print(self.cli_option)
        self.print_description()

    def print_description(self):
        print("\t{}".format(self.description))

    def __str__(self):
        return f"Option: {self.cli_option}\n" \
               f"Name: {self.name}\n" \
               f"Description: {self.description}\n" \
               f"Value: {self.value}\n" \
               f"Required: {self.required}\n" \
               f"Type: {self.type}\n"


class CliOption(Option):
    """
    Represents a command-line option.
    """
    def __init__(self, cli_option, **kwargs):
        super(CliOption, self).__init__(cli_option, **kwargs)

    def __str__(self):
        return super(CliOption, self).__str__()


class Flag(Option):
    """
    Represents a command-line flag.  When present, the value used is `not default_value`.
    """
    def __init__(self, flag, **kwargs):
        super(Flag, self).__init__(flag, type="boolean", **kwargs)

    def __str__(self):
        return super(Flag, self).__str__()


class AppBase(object):
    """
    Base class for application-level classes.  Provides logging, arguments handling,
    help methods, and anything common to its derived classes.
    """
    name = None
    description = None
    subcommands = {}
    argv = []
    argv_mappings = {}  # Contains separation of argument name to value

    def __init__(self, **kwargs):
        self.argv = kwargs['argv']
        self._get_argv_mappings()
        self.log = logging.getLogger()  # setup logger so that metadata service logging is displayed

    def _get_argv_mappings(self):
        """
        Walk argv and build mapping from argument to value for later processing.
        """
        log_option = None
        for arg in self.argv:
            if '=' in arg:
                option, value = arg.split('=', 1)
            else:
                option, value = arg, None
            # Check for --debug or --log-level option.  if cound set, appropriate
            # log-level and skip.  Note this so we can alter self.argv after processing.
            if option == '--debug':
                log_option = arg
                logging.getLogger().setLevel(logging.DEBUG)
                continue
            elif option == '--log-level':
                log_option = arg
                logging.getLogger().setLevel(value)
                continue
            self.argv_mappings[option] = value
        if log_option:
            self.argv.remove(log_option)

    def log_and_exit(self, msg=None, exit_status=1, display_help=False):
        if msg:
            print(msg)
        if display_help:
            print()
            self.print_help()
        self.exit(exit_status)

    def get_subcommand(self):
        """Checks argv[0] to see if it matches one of the expected subcommands. If so,
           that item is removed from argv and that subcommand tuple (class, description)
           is returned.  If no an expected subcommand is not found (None, None) is returned.
        """
        if len(self.argv) > 0:
            arg = self.argv[0]
            if arg in self.subcommands.keys():
                subcommand = self.subcommands.get(arg)
                self._remove_argv_entry(arg)
                return subcommand

            if arg in ['--help', '-h']:
                self.log_and_exit(display_help=True)
            else:
                print("Subcommand '{}' is invalid.".format(self.argv[0]))
        return None

    def exit_no_subcommand(self):
        print("No subcommand specified. Must specify one of: %s" % list(self.subcommands))
        print()
        self.print_description()
        self.print_subcommands()
        self.exit(1)

    def process_cli_option(self, cli_option, check_help=False):
        """
        Check if the given option exists in the current arguments.  If found set its
        the Option instance's value to that of the argv.  Once processed, update the
        argv lists by removing the option.  If the option is a required property and
        is not in the argv lists or does not have a value, exit.
        """
        # if check_help is enabled, check the arguments for help options and
        # exit if found. This is only necessary when processing individual options.
        if check_help and self.has_help():
            self.log_and_exit(display_help=True)

        if cli_option.processed:
            return
        option = cli_option.cli_option
        if option in self.argv_mappings.keys():
            if isinstance(cli_option, Flag):  # flags set their value opposite their default
                cli_option.value = not cli_option.default_value
            else:  # this is a regular option, just set value
                cli_option.set_value(self.argv_mappings.get(option))
                if cli_option.required:
                    if not cli_option.value:
                        self.log_and_exit("Parameter '{}' requires a value.".
                                          format(cli_option.cli_option), display_help=True)
                    elif cli_option.one_of:  # ensure value is in set
                        if cli_option.value not in cli_option.one_of:
                            self.log_and_exit("Parameter '{}' requires one of the following values: {}".
                                              format(cli_option.cli_option, cli_option.one_of), display_help=True)

            self._remove_argv_entry(option)
        elif cli_option.required and cli_option.value is None:
            if cli_option.one_of is None:
                self.log_and_exit("'{}' is a required parameter.".
                                  format(cli_option.cli_option), display_help=True)
            else:
                self.log_and_exit("'{}' is a required parameter and must be one of the following values: {}.".
                                  format(cli_option.cli_option, cli_option.one_of), display_help=True)

        cli_option.processed = True

    def process_cli_options(self, cli_options):
        """
        For each Option instance in the list, process it according to the argv lists.
        After traversal, if arguments still remain, log help and exit.
        """
        # Since we're down to processing options (no subcommands), scan the arguments
        # for help entries and, if found, exit with the help message.
        if self.has_help():
            self.log_and_exit(display_help=True)

        for option in cli_options:
            self.process_cli_option(option)

        # Check if there are still unprocessed arguments.  If so, and fail_unexpected is true,
        # log and exit, else issue warning and continue.
        if len(self.argv) > 0:
            msg = "The following arguments were unexpected: {}".format(self.argv)
            self.log_and_exit(msg, display_help=True)

    def has_help(self):
        """
        Checks the arguments to see if any match the help options.
        We do this by converting two lists to sets and checking if
        there's an intersection.
        """
        helps = set(['--help', '-h'])
        args = set(self.argv_mappings.keys())
        help_list = list(helps & args)
        return len(help_list) > 0

    def _remove_argv_entry(self, cli_option):
        """
        Removes the argument entry corresponding to cli_option in both
        self.argv and self.argv_mappings
        """
        # build the argv entry from the mappings since it must be located with name=value
        if cli_option not in self.argv_mappings.keys():
            self.log_and_exit("Can't find option '{}' in argv!".format(cli_option))

        entry = cli_option
        value = self.argv_mappings.get(cli_option)
        if value:
            entry = entry + '=' + value
        self.argv.remove(entry)
        self.argv_mappings.pop(cli_option)

    def print_help(self):
        self.print_description()

    def print_description(self):
        print(self.description)

    def print_subcommands(self):
        print()
        print("Subcommands")
        print("-----------")
        print(f"Subcommands are launched as `{self.name} cmd [args]`. For information on")
        print(f"using subcommand 'cmd', run: `{self.name} cmd -h`.")
        print()
        for subcommand, desc in self.subcommands.items():
            print(subcommand)
            print("    {}".format(desc[1]))

    def exit(self, status):
        sys.exit(status)
