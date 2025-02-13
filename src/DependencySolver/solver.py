# Copyright 2024 Joonas Kuisma <kuisma.joonas@gmail.com>
"""Robot Framework pre-run modifier. See DESCRIPTION or use as 'depsol --help' to see help."""

import logging.handlers
import robot
from robot.api import ExecutionResult
from robot.api import SuiteVisitor, ResultVisitor
from robot.model import TestCase, TestSuite, TagPatterns, Tags, namepatterns
from robot.utils import Matcher, MultiMatcher  # Use this in next version

from ._version import __version__

import argparse, os

#TODO:
# Add 6.0 robot support

rf_version = tuple(map(int, robot.__version__.split(".")))

if rf_version >= (7, 0):
    suite_name_attr = "full_name"
else:
    suite_name_attr = "longname"


def get_suite_name(suite):
    return getattr(suite, suite_name_attr, "Unknown")

def get_test_name(suite):
    return getattr(suite, suite_name_attr, "Unknown")


os.system('color')

PROG_CALL = "depsol"
NAME = __name__.split(".")[0] 
PROG_NAME = f"{NAME}.{PROG_CALL}"

DESCRIPTION = f"""Robot Framework pre-run modifier which is used to execute dependent test chains.

For example, if test C depends on test B, which in turn depends on A, you must run all three tests if you want to run test C successfully. 
If you run the command 'robot -t C <your test folder>', test fails because this command not select test B and A.

Usage:

The idea is that you should use the 'robotframework-dependencylibrary' and define the dependencies of each test in the [Setup] section by using 'Depends On Test' Keyword. 
You could use this keyword multiple times using Build-in 'Run Keywords' at first.
Then this prerunmodifier checks all test setup parts and solve dependencies before running tests.

Write test setup as follows:
========

*** Test cases ***
test A
    [Setup]    Do Something...
    [Tags]    tagA
    Do Something...

test B
    [Setup]    Run Keywords    Depends On Test    name=test A
    ...    AND    Do Something...
    [Tags]    tagB
    Do Something...

test C
    [Setup]    Run Keywords    Depends On Test    name=test B
    ...    AND    Do Something...
    [Tags]    tagC
    Do Something...

========

You could also use 'Depends On Test' and 'Depends On Suite' keywords in default setup with 'Test Setup' keyword or in 'Suite Setup':
========

*** Settings ***
Suite Setup    Depends On Suite    suite A
Test Setup    Depends On Test    test A

========

Please note that the tests must be in the folders in the desired run order.

See options and examples.
"""
EPILOG = f"""
Options that are marked with an asterisk (*) can be specified multiple times.
For example, `--test first --test third` selects test cases with name `first` and `third`.

Examples
========

# When you have written test dependencies in [Setup] sections like above, then by using this as prerunmodifier you could run whole dependency chain C -> B -> A by using command:
$ robot --prerunmodifier {PROG_NAME}:-t:"test C" <other_robot_commands> <your_test_folder>

# You can also use shortcut '{PROG_CALL}'. This actually calls 'robot' with --prerunmodifier, but it is propably more useful when you do not have any or at least many <other_robot_commands>:
$ {PROG_CALL} -t "test C" -f <your_test_folder>

# If you have already navigated to <your_test_folder>, you does not need to give -f option, because default is current directory:
$ {PROG_CALL} -t "test C"

# Additionally, you could use tags also (but only static, not dynamic tags):
$ robot --prerunmodifier {PROG_NAME}:-i:tagC <other_robot_commands> <your_test_folder>
# Or:
$ {PROG_CALL} -i "tagC"

========
"""
EPILOG_ADDITIONAL_INFO = f"""
Note that if you call '--help' or --version like 'robot --prerunmodifier {PROG_NAME}:-h .', you will get robot error:
[ ERROR ] Execution stopped by user.

This is because the robot execution stops at the prerunmodifier.

To avoid this, please use the correct help call:
'{PROG_CALL} -h' or '{PROG_CALL} --help'

========
"""
# These are copied from "robot --help" commands, so check that working as expected!
HELP_TEST = """Select tests by name or by long name containing also parent suite name like `Parent.Test`.
Name is case and space insensitive and it can also be a simple pattern where `*` matches anything, `?` matches any single character, and `[chars]` matches one character in brackets."""
HELP_INCLUDE = """Select tests by tag. Similarly as name with --test, tag is case and space insensitive and it is possible to use patterns with `*`, `?` and `[]` as wildcards.
Tags and patterns can also be combined together with `AND`, `OR`, and `NOT` operators.
Examples: --include foo --include bar*
          --include fooANDbar*"""
HELP_EXCLUDE = """Select test cases not to run by tag. These tests are not run even if included with --include. 
However, they will run if they are needed because some other test dependency chain. So this --exclude is like 'soft' version of exclude when compared to --exclude_explicit option.
Tags are matched using same rules as with --include."""
HELP_EXCLUDE_EXPLICIT = """Select test cases not to run by tag. These tests are not run in any circumstances. This may block some other desired tests to run. 
For example, if B depends on A and -ee A and -i B is given, neither of tests will not run. So this --exclude_explicit is like 'hard' version of exclude'. Tags are matched using same rules as with --include."""
HELP_SUITE = """Select suites by name. When this option is used with --test, --include or --exclude, only tests in matching suites and also matching other filtering criteria are selected.
Name can be a simple pattern similarly as with --test and it can contain parent name separated with a dot.
For example, `-s X.Y` selects suite `Y` only if its parent is `X`."""
HELP_REVERSE = """Option prints all tests that depend on the given test case.
Does not perform any tests, but is used to check which other tests may be affected by the change of the given test case."""
HELP_DEBUG = """If given, prevents the actual execution of the tests. Used for debugging this prerunmodifier."""
HELP_RERUN = """Reads robot parent_dependencies from the '--src_file' and selects all tests that ended up in fail or skip status and the dependencies they need to be executed again. If given, does not care -t, -s, -i, -e or -ee options."""
HELP_SCR_FILE = """The name of the file from which the parent_dependencies of the 'robot' command is read. By default, the robot's default file 'parent_dependencies.xml' in current directory is used."""
#HELP_DEST_FILE = """TODO: ADD DESCRIPTION"""
HELP_LOGLEVEL = """Defines the log level to be saved in file RunRobotWithDependencies.log. Default is DEBUG. NOTE: The new run overwrites the log in the same way as when executing the 'robot' command."""
HELP_CONSOLE_LOGLEVEL = """Defines the log level to be printed to console. Default is INFO."""
HELP_WITHOUT_TIMESTAMPS = """If given, omits timestamps from the saved log. Mainly used in the script's own tests."""
HELP_PABOT = f"""Controls the {PROG_CALL}.pabot.txt file needed to run 'pabot'. Default is FULL.
If NONE, file is not created. This can speed up DependencySolver a bit when running with 'robot'. Note that previous {PROG_CALL}.pabot.txt file is not deleted.
If GROUP, Groups the order of execution, but omits the dependencies when compared to FULL."""


def print_prog_name():
    print("==============================================================================")
    print(f"{NAME} {__version__}")
    print("==============================================================================")


class DependencyArgumentParser(argparse.ArgumentParser):
    def add_arguments(self) -> None:
        options = self.add_argument_group('robot-like options', 'These options are used like after \'robot\' command but they can work slightly differently.\nNote that the \'--test\', \'--suite\', \'--include\' and \'--exclude\' options define only the desired tests, but the final run also includes test cases according to dependency chains, which do not necessarily meet the conditions.')
        options.add_argument('-t', '--test', action='append', help=HELP_TEST, metavar='name *')
        options.add_argument('-s', '--suite', action='append', help=HELP_SUITE, metavar='name *')
        options.add_argument('-i', '--include', action='append', help=HELP_INCLUDE, metavar='tag *')
        options.add_argument('-e', '--exclude', action='append', help=HELP_EXCLUDE, metavar='tag *')
        options.add_argument('-ee', '--exclude_explicit', action='append', help=HELP_EXCLUDE_EXPLICIT, metavar='tag *')
        options.add_argument('-r', '--rerun', action='store_true', help=HELP_RERUN)

        solver_options = self.add_argument_group(f'{PROG_NAME} options', f'These options are used by \'{PROG_NAME}\'')
        solver_options.add_argument('-rv', '--reverse', action='store_true', help=HELP_REVERSE)
        solver_options.add_argument('-d', '--debug', action='store_true', help=HELP_DEBUG)
        solver_options.add_argument('--without_timestamps', action='store_true', help=HELP_WITHOUT_TIMESTAMPS)
        solver_options.add_argument('-l', '--loglevel', default='debug', choices=['ERROR', 'WARNING', 'INFO', 'DEBUG'], help=HELP_LOGLEVEL)
        solver_options.add_argument('-cl', '--consoleloglevel', default='info', choices=['ERROR', 'WARNING', 'INFO', 'DEBUG'], help=HELP_CONSOLE_LOGLEVEL)
        solver_options.add_argument('--src_file', action='store', type=argparse.FileType('r', encoding='utf-8'), help=HELP_SCR_FILE)
        solver_options.add_argument('-p', '--pabot', default='FULL', choices=['NONE', 'GROUP', 'FULL'], help=HELP_PABOT)
        # This command is not supported yet
        #solver_options.add_argument('--dest_file', action='store', type=argparse.FileType('w', encoding='utf-8'), default='rerun.xml', help=HELP_DEST_FILE)
        #self.add_argument('--version', action='version', version='%(prog)s ' + __version__)
        self.add_argument('--version', action='version', version='Running ' + repr(NAME) + ' from robotframework-dependencysolver ' + __version__)


class CustomFormatter(argparse.RawTextHelpFormatter):
    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)

            # if the Optional takes a value, format is:
            #    -s ARGS, --long ARGS
            # change to 
            #    -s, --long ARGS
            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    parts.append('%s' % option_string)
                parts[-1] += ' %s'%args_string
            return ', '.join(parts)


class CustomColorFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    green = "\033[92m"
    yellow = "\x1b[33;20m"
    red = "\033[91m"  #"\x1b[31;20m"
    bold_red = "\x1b[31;1m"

    def console_print(color) -> str:
        reset = "\x1b[0m"
        return '[ ' + color + '%(levelname)s' + reset + ' ] ' + '%(message)s'

    FORMATS = {
        logging.DEBUG: console_print(grey),
        logging.INFO: console_print(green),
        logging.WARNING: console_print(yellow),
        logging.ERROR: console_print(red),
        logging.CRITICAL: console_print(bold_red),
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class TestDependency:
    def __init__(self, tests: list[str] = [], suites: list[str] = []) -> None:
        self.tests = tests
        self.suites = suites

    def __str__(self) -> str:
        return f"tests:{self.tests}, suites:{self.suites}"


class DependencyTestCase:
    def __init__(self, name: str, full_name: str, id: str, tags: list[str], dependencies: TestDependency) -> None:
        self.name = name
        self.full_name = full_name
        self.id = id
        self.tags = tags
        self.dependencies = dependencies
        self.solved_test_dependencies = []
        self.direct_precondition_for_tests = []  # [full_name]
        self.group = ""

    def __str__(self) -> str:
        return f"name:{self.name}, id:{self.id}, tags:{self.tags}, dependencies:({self.dependencies}), solved test dependencies:{self.solved_test_dependencies}, precondition for:{self.direct_precondition_for_tests}, group:{self.group}"

    def add_solved_test_dependencies(self, full_name):
        self.solved_test_dependencies.append(full_name)

    def add_direct_precondition(self, full_name):
        self.direct_precondition_for_tests.append(full_name)

    def add_group(self, full_name: str):
        self.group = full_name


class ReRunTests(ResultVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.failed_tests, self.skipped_tests, self.passed_tests, self.rerun_these_tests = [], [], [], []

    def visit_test(self, test: TestCase):
        if test.status == 'FAIL':
            self.failed_tests.append(get_test_name(test))
        if test.status == 'SKIP':
            self.skipped_tests.append(get_test_name(test))
        if test.status == 'PASS':
            self.passed_tests.append(get_test_name(test))
        return super().visit_test(test)

    def end_result(self, result):
        for s in self.skipped_tests: self.rerun_these_tests.append(s)
        for f in self.failed_tests: self.rerun_these_tests.append(f)
        return super().end_result(result)


class DependencySolver(SuiteVisitor):

    def __init__(self, *options) -> None:
        self.parser = DependencyArgumentParser(description=DESCRIPTION, formatter_class=CustomFormatter, epilog=EPILOG + EPILOG_ADDITIONAL_INFO, prog=PROG_NAME)
        self.parser.add_arguments()
        self.args = self.parser.parse_args(args=options)
        print_prog_name()
        self.logger = logging.getLogger(__name__)
        format = '%(asctime)s [ %(levelname)s ] %(message)s'
        if self.args.without_timestamps:
            format = '[ %(levelname)s ] %(message)s'
        logging.basicConfig(handlers=[logging.FileHandler(filename=str(PROG_CALL + '.log'), mode='w', encoding='utf-8')], level=self.args.loglevel.upper(), format=format)
        self.logger.info("The following arguments were obtained: " + repr(options))
        stream_logger = logging.StreamHandler()
        stream_logger.setLevel(self.args.consoleloglevel.upper())
        stream_logger.setFormatter(CustomColorFormatter())
        self.logger.addHandler(stream_logger)

        self.error_occurs, self.check_done = False, False
        self.test_cases, self.suites, self.possible_loop, self.relation_chains = {}, {}, {}, {}
        self.list_of_running_tests_names, self.safe_values = [], []
        self.desired_tests = []
        self.tc_by_suite, self.tc_by_test, self.tc_by_include, self.tc_by_exclude, self.tc_by_exclude_explicit = [], [], [], [], []
        self.groups = {}  # key = test full name, content = [tests]

        if self.args.rerun:
            if self.args.src_file is None:
                output_file = 'output.xml'
            else:
                output_file = self.args.src_file
            result = ExecutionResult(output_file)
            ReRunner = ReRunTests()
            result.visit(ReRunner)
            rerun_these_tests = ReRunner.rerun_these_tests
            self.logger.info("Rerunner started")
            for test in rerun_these_tests: self.logger.debug('Re-running test case ' + repr(test))
            self.list_of_running_tests_names = rerun_these_tests


    def _matcher(self, name: str, list_of_names: list[str]) -> list[str]:
        long_name = '.'.join([TestSuite.name_from_source(n) for n in name.split('.')])
        matching_names = [value for value in list_of_names if Matcher('*.' + long_name).match(value) or Matcher(long_name).match(value)]
        return matching_names


    def _solve_dependencies(self, test_name: str, relation_chain: dict, loop_check_mode: bool = False, parent: str = "") -> dict:
        """Recursively examines the dependencies of the argument test_name. Returns dependencies (test ids and names) collected in dict.
        Restarts itself in loop checking mode if it finds a possible loop."""

        def _go_to_sub_suites(list_of_suites, tests = []):
            for suite_dependency in list_of_suites:
                if len(self.suites[suite_dependency.full_name].suites) > 0:
                    tests = tests + _go_to_sub_suites(self.suites[suite_dependency.full_name].suites, tests)
                else:
                    finded_test = [t for t in self.suites[suite_dependency.full_name].tests]
                    tests = tests + finded_test
            return tests

        test_name_list = self._matcher(test_name, self.test_cases)
        if len(test_name_list) == 0:
            message = "\'Depends On Test\' keyword refers to test " + repr(test_name) + " that does not exist. Check your spelling."
            raise RecursionError(message)
        else:
            if len(test_name_list) > 1:
                # TODO Test?
                if parent != "":
                    self.logger.warning("Dependence in test " + repr(parent) + " is " + repr(test_name) + " which is not unambiguous but refers to the following tests: " + repr(test_name_list))
                else:
                    # TODO is ?
                    self.logger.warning("TODO: NO PRINTING!")
            for t_name in test_name_list:
                id = self.test_cases[t_name].id
                if id in relation_chain:
                    if t_name in self.safe_values:
                        self.logger.debug(repr(t_name) + " has already been checked and does not contain a loop.")
                    else:
                        if loop_check_mode:
                            message = "Dependencies are cyclical! Test case " + repr(t_name) + " is already part of the relation chain: " + repr(relation_chain.values())
                            raise RecursionError(message)
                        self.logger.info("In test case " + repr(t_name) + " either the branches merge or it is a loop. Let's explore what we end up with if we start with this test.")
                        self.logger.info("Starting in loop check mode.")
                        self.possible_loop = self._solve_dependencies(t_name, relation_chain={}, loop_check_mode=True)
                        self.logger.info("It was a merge, so let's exit loop check mode:")
                        for value in self.possible_loop.values():
                            self.safe_values.append(value)
                        self.logger.debug("These tests are already check as loop safe: " + repr(self.safe_values))
                else:
                    relation_chain[id] = t_name

                for dependency in self.test_cases[t_name].dependencies.tests:
                    self.logger.debug("Dependency: " + repr(t_name) + " -> " + repr(dependency))
                    relation_chain = self._solve_dependencies(dependency, relation_chain=relation_chain, loop_check_mode=loop_check_mode, parent=t_name)

                for suite_dependency in self.test_cases[t_name].dependencies.suites:
                    self.logger.debug("Dependency: " + repr(t_name) + " -> " + repr(suite_dependency))
                    self.logger.debug('Transforming suite dependency to test dependencies...')
                    transformed_dependencies = self._matcher(suite_dependency, self.suites)
                    if len(transformed_dependencies) == 0:
                        message = "\'Depends On Suite\' keyword refers to suite " + repr(suite_dependency) + " that does not exist. Check your spelling."
                        raise RecursionError(message)
                    for d in transformed_dependencies:
                        _depends_these_tests = self.suites[d].tests
                        if len(_depends_these_tests) == 0:  # goes subsuites
                            _depends_these_tests = _go_to_sub_suites(self.suites[d].suites)
                        for test_dependency in _depends_these_tests:
                            self.logger.debug("Transformed dependency: " + repr(t_name) + " -> " + repr(test_dependency.full_name))
                            relation_chain = self._solve_dependencies(test_dependency.full_name, relation_chain=relation_chain, loop_check_mode=loop_check_mode, parent=t_name)

        return relation_chain


    def _find_dependencies(self, setup) -> TestDependency:
        """Finds all test dependencies in the [Setup] section of the test."""
        def clean_argument(argument: str) -> str:
            return argument.replace("name=", "")
        
        test_dependencies, suite_dependencies = [], []
        if setup.name == "Run Keywords":
            for i in range(len(setup.args)):
                if setup.args[i] == "Depends On Test":
                    test_dependencies.append(clean_argument(setup.args[i+1]))
                if setup.args[i] == "Depends On Suite":
                    suite_dependencies.append(clean_argument(setup.args[i+1]))
        if setup.name == "Depends On Test":
            test_dependencies.append(clean_argument(setup.args[0]))
        if setup.name == "Depends On Suite":
            suite_dependencies.append(clean_argument(setup.args[0]))
        return TestDependency(test_dependencies, suite_dependencies)
    

    def _find_suites(self, suite: TestSuite, suite_setup_dependencies: list = []):
        """Recursively searches the entire folder structure, i.e. all sub-suites and tests."""
        parent_dependencies = suite_setup_dependencies
        if suite.has_setup:
            new_dep = self._find_dependencies(suite.setup)
            if len(new_dep.tests) != 0 or len(new_dep.suites) != 0:
                parent_dependencies = parent_dependencies + [new_dep]
        for sub_suite in suite.suites:
            if sub_suite.full_name in self.suites:
                message = "Suite name: " + repr(sub_suite.full_name) + " is duplicated with locations: " + repr(sub_suite.full_name) + " and " + repr(self.suites[sub_suite.full_name].full_name) + ". Could not solve dependencies."
                raise NameError(message)
            else:
                self.suites[sub_suite.full_name] = sub_suite
            self.logger.debug("Investigating subsuite " + repr(sub_suite.full_name))
            self._find_suites(sub_suite, parent_dependencies)
            self._find_tests(sub_suite, parent_dependencies)
        self.check_done = True


    def _find_tests(self, suite: TestSuite, suite_setup_dependencies: list = []):
        """Searches for all tests in the given suite. Then creates DependencyTestCase objects."""
        for test in suite.tests:
            dependencies = TestDependency()
            if test.has_setup:
                dependencies = self._find_dependencies(test.setup)
            if len(suite_setup_dependencies) != 0:
                self.logger.debug("Merging depencencies in test " + repr(test.full_name) + " because " + repr(suite.full_name) + " or its parent suite has 'Suite Setup' with 'Depends On' keyword.")
                tests = dependencies.tests
                suites = dependencies.suites
                for suite_setup in suite_setup_dependencies:
                    tests = tests + suite_setup.tests
                    suites = suites + suite_setup.suites
                dependencies = TestDependency(tests, suites)
                self.logger.debug("Test " + repr(test.full_name) + " has dependencies for tests: " + repr(dependencies.tests) + " and suites: " + repr(dependencies.suites))
            if test.name in [ tc for tc in self.test_cases.values() ]:
                message = "Test name: " + repr(test.full_name) + " is duplicated with ids: " + repr(test.id) + " and " + repr(self.test_cases[test.full_name].id) + ". Could not solve dependencies."
                # This is not needed anymore!
                raise NameError(message)
            self.test_cases[test.full_name] = DependencyTestCase(test.name, test.full_name, test.id, test.tags, dependencies)


    def _check_one_relation_chain(self, test_name):
        """Takes one test name as argument and adds whole relation chain starting from this test to self.list_of_running_tests_names, but only if test names are not there already."""
        self.logger.info("Checking relation chain for test " + repr(test_name))

        self.relation_chains[test_name] = []
        if test_name in self.test_cases.keys():
            relation_chain = self._solve_dependencies(test_name, relation_chain={})

            chain_ok = True
            if len(self.tc_by_exclude_explicit) > 0:
                for d in relation_chain.values():
                    if len(self._matcher(d, self.tc_by_exclude_explicit)) > 0:
                        self.logger.info("Because --exclude_explicit argument, not requested test: " + repr(d) + ", so skipping this whole relation chain. Adding nothing and moving next relation chain...")
                        chain_ok = False
                        break
            if chain_ok:
                for t in relation_chain.values():
                    if not t in self.list_of_running_tests_names:
                        self.logger.debug("Adding " + repr(t))
                        self.list_of_running_tests_names.append(t)
                    else:
                        self.logger.debug(repr(t) + " is already added.")
                    self.relation_chains[test_name].append(t)
        else:
            message = "Argument: " + repr(test_name) + " not found in test cases."
            raise NameError(message)


    def _check_tag(self, tag: str, option=None):
        """Finds all test cases which has 'tag' in [Tags] section."""
        tag_found = False
        for t in self.test_cases.values():
            if TagPatterns(tag).match(t.tags):
                tag_found = True
                if option == 'include':
                    self.tc_by_include.append(t.full_name)
                    self.logger.debug('Requested test '+ repr(t.full_name) + ' because of --include option: ' + repr(tag))
                elif option == 'exclude':
                    self.tc_by_exclude.append(t.full_name)
                    self.logger.debug('Not requested test '+ repr(t.full_name) + ' because of --exclude option: ' + repr(tag))
                elif option == 'exclude_explicit':
                    self.tc_by_exclude_explicit.append(t.full_name)
                    self.logger.debug('Not requested test '+ repr(t.full_name) + ' in any case, because of --exclude_explicit option: ' + repr(tag))

        if not tag_found and option == 'include':
            self.logger.warning('Given tag: ' + repr(tag) + " not found from any tests. Check your spelling.")


    def _check_suite(self, suite_name: str, suite_found: bool = False):
        long_name = '.'.join([TestSuite.name_from_source(n) for n in suite_name.split('.')])
        for s in self.suites:
            # Rethink this ? -sign at start!
            if Matcher('*' + long_name).match(s) or Matcher('*.' + long_name).match(s):
                suite_found = True
                for sub_s in self.suites[s].suites:
                    self.logger.debug(repr(suite_name) + ' has subsuite ' + repr(sub_s.name) + '. Investigating...')
                    self._check_suite(sub_s.full_name, suite_found=suite_found)

                for t in self.suites[s].tests:
                    self.logger.debug('Requested test '+ repr(t.full_name) + ' because of subsuite or direct --suite option: ' + repr(suite_name))
                    self.tc_by_suite.append(t.full_name)

        if not suite_found:
            message = "Argument: " + repr(suite_name) + " not found in test suites."
            raise NameError(message)


    def _check_test(self, test_name: str):
        test_case_found = False
        long_name = '.'.join([TestSuite.name_from_source(n) for n in test_name.split('.')])
        self.logger.debug('Requested test '+ repr(test_name) + ' directly.')
        for t in self.test_cases:
            if Matcher('*.' + long_name).match(t) or Matcher(long_name).match(t):
                self.tc_by_test.append(t)
                test_case_found = True

        if not test_case_found:
            message = "Argument: " + repr(test_name) + " does not match any test case."
            raise NameError(message)


    def _define_running_tests(self):
        """Contains logic that defines the tests to be executed based on the given command line arguments."""
        if self.args.suite is not None:
            for suite in self.args.suite:
                self._check_suite(suite)

        if self.args.include is not None:
            for tag in self.args.include:
                self._check_tag(tag, option='include')

        if self.args.exclude is not None:
            for tag in self.args.exclude:
                self._check_tag(tag, option='exclude')

        if self.args.exclude_explicit is not None:
            for tag in self.args.exclude_explicit:
                self._check_tag(tag, option='exclude_explicit')

        if self.args.test is not None:
            for desired_test_name in self.args.test:
                self._check_test(desired_test_name)

        desired_test_set = set()
        list_of_desired_tcs = [set(self.tc_by_suite), set(self.tc_by_test), set(self.tc_by_include)]
        if any(list_of_desired_tcs):
            non_empties = [x for x in list_of_desired_tcs if len(x) > 0]
            desired_test_set = set.intersection(*non_empties)

        if self.args.exclude is not None:
            not_desired_test_set = set(self.tc_by_exclude)

            if len(desired_test_set) == 0:
                desired_test_set = set(self.test_cases)
                if len(not_desired_test_set) == 0:
                    self.logger.warning("Selecting all test cases in given folder, because only --exclude argument(s) given and it does not match any tags.")

            desired_test_set = desired_test_set.difference(not_desired_test_set)

        # Returning right order of test cases
        self.desired_tests = [t for t in self.test_cases if t in (desired_test_set)]

        if self.args.rerun:
            # This log message could be better and in different position.
            self.logger.debug('Rerun mode activated, so tests are only selected based on \'output.xml\' or another given file.')
            self.desired_tests = self.list_of_running_tests_names

        if len(self.desired_tests) > 0:
            if self.args.reverse:
                find_these_tests = self.desired_tests
                self.desired_tests = [ t.full_name for t in self.test_cases.values() ]

            self.logger.debug('These are tests which user requested: ' + repr(self.desired_tests))
            self.logger.info('Starting relation chain checking...')
            for desired_test_name in self.desired_tests:
                self._check_one_relation_chain(desired_test_name)

            if self.args.reverse:
                for find_this in find_these_tests:
                    print_list = []
                    for key in self.relation_chains:
                        values = self.relation_chains[key][1:]
                        if find_this in values:
                            print_list.append(key)

                    # These text are printed but not logged.
                    print()
                    print("If you change the implementation of test", repr(find_this), ", it may affect these tests:")
                    if len(print_list) > 0:
                        for p in print_list: print("   ", p)
                    else:
                        if find_this in self.test_cases:
                            print("    No effects, because nothing depends on the test", repr(find_this))
                        else:
                            print("    Test", repr(find_this), "not found. Check your spelling.")
                    print()

                self.list_of_running_tests_names = []

        if len(self.list_of_running_tests_names) == 0:
            # Could this be better?
            self.logger.warning("No tests chosen.")

        if self.args.pabot != 'NONE':
            self._write_depends_ordering()

        if self.args.debug:
            self.logger.info(str(len(self.list_of_running_tests_names)) + ' tests would have been chosen. List of test: ' + str(self.list_of_running_tests_names))
            self.logger.warning("DEBUG mode activated. Emptying test case list...")
            self.list_of_running_tests_names = []


    def _define_groups(self):
        ordered_list = [t for t in self.test_cases if t in self.list_of_running_tests_names]
        initial_tests = [t for t in ordered_list if len(self.test_cases[t].solved_test_dependencies) == 0]
        ending_tests = [t for t in ordered_list if len(self.test_cases[t].direct_precondition_for_tests) == 0]
        unique_tests = [t for t in initial_tests if t in ending_tests]
        for t in unique_tests:
            self.test_cases[t].add_group(t)
            self.groups[t] = [t]
        # Remove unique tests
        initial_tests = [t for t in initial_tests if t not in unique_tests]
        ending_tests = [t for t in ending_tests if t not in unique_tests]

        def _find_all_initial_test_starting_from(start_point, full_name):
            if full_name not in initial_tests:
                for tc in self.test_cases[full_name].solved_test_dependencies:
                    _find_all_initial_test_starting_from(start_point, tc)
            else:
                if full_name in self.initial_endings:
                    self.initial_endings[full_name].append(start_point)
                else:
                    self.initial_endings[full_name] = [start_point]

        def _find_all_ending_test_starting_from(start_point, full_name):
            if full_name not in ending_tests:
                for tc in self.test_cases[full_name].direct_precondition_for_tests:
                    _find_all_ending_test_starting_from(start_point, tc)
            else:
                if full_name in self.ending_initials:
                    self.ending_initials[full_name].append(start_point)
                else:
                    self.ending_initials[full_name] = [start_point]

        def _update_groups(full_name, group):
            tc = self.test_cases[full_name]
            if tc.group == "":
                tc.add_group(group)
                if group not in self.groups:
                    self.groups[group] = [full_name]
                else:
                    self.groups[group].append(full_name)
            for dep in tc.solved_test_dependencies:
                _update_groups(dep, group)

        def _find_first_initial_group(full_name, suggestion):
            these_are_defined = [suggestion]
            for i in self.ending_initials[full_name]:
                tc = self.test_cases[i]
                if tc.group != "":
                    these_are_defined.append(tc.group)
            for t in initial_tests:
                if t in these_are_defined:
                    return t

        self.initial_endings = {}
        self.ending_initials = {}

        for t in initial_tests:
            _find_all_ending_test_starting_from(t, t)
        for t in ending_tests:
            _find_all_initial_test_starting_from(t, t)

        these_are_checked = []
        for tc in initial_tests:
            for e in self.initial_endings[tc]:
                if e not in these_are_checked:
                    first = _find_first_initial_group(e, tc)
                    _update_groups(e, first)
                    these_are_checked.append(e)


    def _write_depends_ordering(self):
        """Used for pabot to write ordering.txt file as name PROG_NAME.pabot.txt."""
        all_text = ""
        ordered_list = [t for t in self.test_cases if t in self.list_of_running_tests_names]
        for r in ordered_list:
            for t in self.test_cases[r].dependencies.tests:
                for matching_t in self._matcher(t, self.test_cases):
                    self.test_cases[r].add_solved_test_dependencies(matching_t)
                    self.test_cases[matching_t].add_direct_precondition(r)
            for s in self.test_cases[r].dependencies.suites:
                for matching_s in self._matcher(s, self.suites):
                    for t_in_s in self.suites[matching_s].tests:
                        self.test_cases[r].add_solved_test_dependencies(t_in_s.full_name)
                        self.test_cases[t_in_s.full_name].add_direct_precondition(r)

        self._define_groups()

        for g in self.groups:
            group_text, group_end_text = "", ""
            if len(self.groups[g]) > 1:
                group_text = "{\n"
                group_end_text = "}\n"
            for tc in ordered_list:
                if tc in self.groups[g]:
                    test = f"--test {tc}"
                    if self.args.pabot == 'FULL':
                        for s in self.test_cases[tc].solved_test_dependencies:
                            test = test + " #DEPENDS " + s
                    group_text = group_text + test + "\n"
            group_text = group_text + group_end_text
            all_text = all_text + group_text

        with open(str(PROG_CALL + '.pabot.txt'), 'w') as f:
            f.write(all_text)


    def start_suite(self, suite: TestSuite) -> bool | None:
        """When suite starts, check if it is main suite/folder. If it is, loops through all test cases and finds all relation chains.
        After then it defines which test to execute."""
        if not self.error_occurs:
            self.logger.debug("Started suite: " + repr(suite.full_name))
        if not self.check_done:
            self.logger.info("Starting to explore the dependencies...")
            try:
                self.suites[suite.full_name] = suite
                self._find_suites(suite)
                self._define_running_tests()

            except (NameError, RecursionError) as err:
                # prints error message and emptying test cases so that robot does not start.
                self.logger.error(err.args[0] + " Execution of tests cannot be started!")
                self.list_of_running_tests_names = []
                self.error_occurs = True
            else:
                self.logger.info("Choosing tests...")


    def end_suite(self, suite: TestSuite) -> None:
        """Selects the tests and suites to be executed."""
        suite.tests = [t for t in suite.tests if t.full_name in self.list_of_running_tests_names]
        for t in suite.tests: self.logger.debug("Test " + repr(t.full_name) + " will be executed.")
        suite.suites = [s for s in suite.suites if s.test_count > 0]
        for s in suite.suites: self.logger.debug("Suite " + repr(s.full_name) + " will be executed.")
        if not self.error_occurs:
            self.logger.debug("Finishing suite: " + repr(suite.full_name))

