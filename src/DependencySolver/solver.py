# Copyright 2024 Joonas Kuisma <kuisma.joonas@gmail.com>
"""Robot Framework pre-run modifier. See DESCRIPTION or use as 'DependencySolver --help' to see help."""

import argparse
import logging
import robot
import time
import random
from robot.api import ExecutionResult, SuiteVisitor, ResultVisitor
from robot.model import TestCase, TestSuite, TagPatterns
from robot.utils import Matcher
from collections.abc import Iterable
from ._version import __version__
from .sort_ordering import sort_by_output_xml
from .ui import main_application


rf_version = tuple(map(int, robot.__version__.split(".")))

if rf_version >= (7, 0):
    name_attr = "full_name"
else:
    name_attr = "longname"

def get_name(item):
    return getattr(item, name_attr, "Unknown")


#os.system('color')

PROG_CALL = "depsol"
NAME = __name__.split(".")[0] 
PROG_NAME = f"{NAME}.{PROG_CALL}"

DESCRIPTION = f"""Robot Framework pre-run modifier which is used to execute dependent test chains.

For example, if test C depends on test B, which in turn depends on A, you must run all three tests if you want to run 
test C successfully. If you run the command 'robot -t C <your test folder>', test fails because this command not select 
test B and A.

Usage:

The idea is that you should use the 'robotframework-dependencylibrary' and define the dependencies of each test in the 
[Setup] section by using 'Depends On Test' Keyword. You could use this keyword multiple times using Build-in 
'Run Keywords' at first. Then this prerunmodifier checks all test setup parts and solve dependencies before running tests.

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

You could also use 'Depends On Test' and 'Depends On Suite' keywords in default setup with 'Test Setup' keyword 
or in 'Suite Setup':
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

# When you have written test dependencies in [Setup] sections like above, then by using this as prerunmodifier you could 
# run whole dependency chain C -> B -> A by using command:
$ robot --prerunmodifier {PROG_NAME}:-t:"test C" <other_robot_commands> <your_test_folder>

# You can also use shortcut '{PROG_CALL}'. This actually calls 'robot' with --prerunmodifier like above:
$ {PROG_CALL} -t "test C" <other_robot_commands> <your_test_folder>

# Additionally, you could use tags also (but only static, not dynamic tags):
$ robot --prerunmodifier {PROG_NAME}:-i:tagC <other_robot_commands> <your_test_folder>
# Or:
$ {PROG_CALL} -i tagC <other_robot_commands> <your_test_folder>

# If you want to run tests parallel with pabot, you could use command:
$ pabot --testlevelsplit --pabotprerunmodifier DependencySolver.depsol:-i:tagC --ordering depsol.pabot.txt <other_pabot_commands> <your_test_folder>
# Or:
$ {PROG_CALL} -i tagC --tool pabot <other_pabot_commands> <your_test_folder>

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
Name is case and space insensitive and it can also be a simple pattern where `*` matches anything, `?` matches any 
single character, and `[chars]` matches one character in brackets.
"""
HELP_INCLUDE = """Select tests by tag. Similarly as name with --test, tag is case and space insensitive and it is possible to use patterns 
with `*`, `?` and `[]` as wildcards. Tags and patterns can also be combined together with `AND`, `OR`, and `NOT` operators.
Examples: --include foo --include bar*
          --include fooANDbar*
"""
HELP_EXCLUDE = """Select test cases not to run by tag. These tests are not run even if included with --include. 
However, they will run if they are needed because some other test dependency chain. So this --exclude is like 'soft' 
version of exclude when compared to --exclude_explicit option. Tags are matched using same rules as with --include.
"""
HELP_EXCLUDE_EXPLICIT = """Select test cases not to run by tag. These tests are not run in any circumstances. This may block some other desired 
tests to run. For example, if B depends on A and -ee A and -i B is given, neither of tests will not run. 
So this --exclude_explicit is like 'hard' version of exclude'. Tags are matched using same rules as with --include.
"""
HELP_SUITE = """Select suites by name. When this option is used with --test, --include or --exclude, only tests in matching suites and 
also matching other filtering criteria are selected. Name can be a simple pattern similarly as with --test and it can 
contain parent name separated with a dot. For example, `-s X.Y` selects suite `Y` only if its parent is `X`.
"""
HELP_REVERSE = """Option prints all tests that depend on the given test case.
Does not perform any tests, but is used to check which other tests may be affected by the change of the given test case.
"""
HELP_DEBUG = """If given, prevents the actual execution of the tests. Used for debugging this prerunmodifier.
"""
HELP_RERUN = """Reads robot output from the '--src_file' and selects all tests that ended up in fail or skip status and the dependencies 
they need to be executed again. If given, does not care -t, -s, -i, -e or -ee options.
"""
HELP_SCR_FILE = """The name of the file from which the output of the 'robot' command is read. 
By default, the robot's default file 'output.xml' in current directory is used.
"""
#HELP_DEST_FILE = """TODO: ADD DESCRIPTION"""
HELP_FILE_LOGLEVEL = """Defines the log level to be saved in file RunRobotWithDependencies.log. Default is DEBUG. 
NOTE: The new run overwrites the log in the same way as when executing the 'robot' command.
"""
HELP_CONSOLE_LOGLEVEL = """Defines the log level to be printed to console. Default is INFO.
"""
HELP_WITHOUT_TIMESTAMPS = """If given, omits timestamps from the saved log. Mainly used in the script's own tests.
"""
HELP_PABOT = f"""Controls the {PROG_CALL}.pabot.txt file needed to run 'pabot'. Default is FULL.
If NONE, file is not created. This can speed up DependencySolver a bit when running with 'robot'.
Note that previous {PROG_CALL}.pabot.txt file is not deleted.
If GROUP, groups the order of execution, but omits the dependencies when compared to FULL.
If FULL, groups the order of execution and dependencies.
If OPTIMIZED, like FULL but in addition, attempt to read the durations and statuses of test executions from '--src_file' 
and then organize individual tests and groups in the ordering file so that execution starts with failed or skipped tests 
or groups containing such tests, followed by the slowest to the fastest. If 'output.xml' does not contain the execution 
time of a test, the test is considered skipped.
"""
HELP_RANDOMIZE = f"""The --randomize option allows users to randomize the execution order of tests and dependency groups (suites). 
It works quite similarly to the option in Robot Framework, providing the following RANDOMIZE behaviors:

NONE: No randomization (default).
TESTS: Randomizes the order of tests within each group, maintaining their dependencies.
SUITES: Randomizes the execution order of all test groups (suites).
ALL: Randomizes both tests and suites for maximum variation.

Optionally, a custom random seed can be provided using the syntax VALUE;SEED, where the seed must be an integer.
NOTE: Since the general delimiter for prerunmodifier arguments is `:`, unlike in the Robot Framework syntax, 
a semicolon `;` must be used as the delimiter instead.
"""
HELP_UI = """When enabled, launches a GUI for selecting and visualizing tests and their dependencies. 
Selected tests are incorporated into the Robot Framework execution upon closing the interface. 
Detailed GUI documentation is available via Help -> Info in the menu bar. 
Note that --test, --suite, --include, and --exclude options are applied first, serving as the initial selection for the GUI.
The --exclude_explicit option is applied after the GUI is closed.
"""


def print_prog_name():
    print("==============================================================================")
    print(f"{NAME} {__version__}")
    print("==============================================================================")


class DependencyArgumentParser(argparse.ArgumentParser):
    def add_arguments(self) -> None:

        def uppercase_type(value: str) -> str:
            return value.upper()
        
        def parse_randomize(value: str) -> tuple[str, int | None]:
            if ';' in value:
                option, seed = value.split(';')
                try:
                    seed = int(seed)
                except ValueError:
                    raise argparse.ArgumentTypeError(f"Invalid seed value: {seed}. It must be an integer.")
            else:
                option = value
                seed = None 
            option = uppercase_type(option)
            if option not in ['NONE', 'TESTS', 'SUITES', 'ALL']:
                raise argparse.ArgumentTypeError(f"Invalid randomize option: {option}")
            return option, seed
        
        options = self.add_argument_group(
            'robot-like options',
            'These options are used like after \'robot\' command but they can work slightly differently.\n'
            'Note that the \'--test\', \'--suite\', \'--include\' and \'--exclude\' options define only the desired tests,\n'
            'but the final run also includes test cases according to dependency chains, which do not necessarily meet the conditions.'
        )
        options.add_argument('-t', '--test', action='append', help=HELP_TEST, metavar='name *')
        options.add_argument('-s', '--suite', action='append', help=HELP_SUITE, metavar='name *')
        options.add_argument('-i', '--include', action='append', help=HELP_INCLUDE, metavar='tag *')
        options.add_argument('-e', '--exclude', action='append', help=HELP_EXCLUDE, metavar='tag *')
        options.add_argument('-ee', '--exclude_explicit', action='append', help=HELP_EXCLUDE_EXPLICIT, metavar='tag *')
        options.add_argument('--rerun', action='store_true', help=HELP_RERUN)
        options.add_argument('--randomize', default='NONE', type=parse_randomize, help=HELP_RANDOMIZE)

        solver_options = self.add_argument_group(
            f'{PROG_NAME} options',
            f'These options are used by \'{PROG_NAME}\''
        )
        solver_options.add_argument('--reverse', action='store_true', help=HELP_REVERSE)
        solver_options.add_argument('--debug', action='store_true', help=HELP_DEBUG)
        solver_options.add_argument('--without_timestamps', action='store_true', help=HELP_WITHOUT_TIMESTAMPS)
        solver_options.add_argument('--fileloglevel', default='DEBUG', type=uppercase_type, choices=['ERROR', 'WARNING', 'INFO', 'DEBUG'], help=HELP_FILE_LOGLEVEL)
        solver_options.add_argument('--consoleloglevel', default='INFO', type=uppercase_type, choices=['ERROR', 'WARNING', 'INFO', 'DEBUG'], help=HELP_CONSOLE_LOGLEVEL)
        solver_options.add_argument('--src_file', action='store', type=argparse.FileType('r', encoding='utf-8'), help=HELP_SCR_FILE)
        solver_options.add_argument('--pabotlevel', default='FULL', type=uppercase_type, choices=['NONE', 'GROUP', 'FULL', 'OPTIMIZED'], help=HELP_PABOT)
        solver_options.add_argument('--ui', action='store_true', help=HELP_UI)
        
        self.add_argument('--version', action='version', version=f'Running {repr(NAME)} from robotframework-dependencylibrary {__version__}')

    def parse_known_args(self, args=None, namespace=None):
        args, unknown = super().parse_known_args(args, namespace)
        return args, unknown

    
class CustomFormatter(argparse.RawTextHelpFormatter):
    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            if action.nargs == 0:
                parts.extend(action.option_strings)
            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    parts.append(f'{option_string}')
                parts[-1] += f' {args_string}'
            return ', '.join(parts)


class CustomColorFormatter(logging.Formatter):
    GREY = "\x1b[38;20m"
    GREEN = "\033[92m"
    YELLOW = "\x1b[33;20m"
    RED = "\033[91m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"

    def __init__(self):
        super().__init__()
        self.FORMATS = {
            logging.DEBUG: self.console_print(self.GREY),
            logging.INFO: self.console_print(self.GREEN),
            logging.WARNING: self.console_print(self.YELLOW),
            logging.ERROR: self.console_print(self.RED),
            logging.CRITICAL: self.console_print(self.BOLD_RED),
        }

    @staticmethod
    def console_print(color: str) -> str:
        return f'[ {color}%(levelname)s{CustomColorFormatter.RESET} ] %(message)s'

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class TestDependency:
    def __init__(self, tests: list[str] = None, suites: list[str] = None) -> None:
        self.tests = tests if tests is not None else []
        self.suites = suites if suites is not None else []

    def __str__(self) -> str:
        return f"tests:{self.tests}, suites:{self.suites}"


class DependencyTestCase:
    def __init__(self, name: str, full_name: str, id: str, tags: list[str], dependencies: TestDependency) -> None:
        self.name = name
        self.full_name = full_name
        self.longname = full_name   # This is for Robot < 7.0
        self.id = id
        self.tags = tags
        self.dependencies = dependencies
        self.solved_test_dependencies = []
        self.direct_precondition_for_tests = []
        self.group = ""

    def __str__(self) -> str:
        return (
            f"name:{self.name}, id:{self.id}, tags:{self.tags}, dependencies:({self.dependencies}), "
            f"solved test dependencies:{self.solved_test_dependencies}, precondition for:{self.direct_precondition_for_tests}, group:{self.group}"
        )

    def add_solved_test_dependencies(self, full_name: str) -> None:
        self.solved_test_dependencies.append(full_name)

    def add_direct_precondition(self, full_name: str) -> None:
        self.direct_precondition_for_tests.append(full_name)

    def add_group(self, full_name: str) -> None:
        self.group = full_name


class ReRunTests(ResultVisitor):
    def __init__(self) -> None:
        super().__init__()
        self.failed_tests = []
        self.skipped_tests = []
        self.passed_tests = []
        self.rerun_these_tests = []

    def visit_test(self, test: TestCase) -> None:
        if test.status == 'FAIL':
            self.failed_tests.append(get_name(test))
        elif test.status == 'SKIP':
            self.skipped_tests.append(get_name(test))
        elif test.status == 'PASS':
            self.passed_tests.append(get_name(test))
        super().visit_test(test)

    def end_result(self, result) -> None:
        self.rerun_these_tests.extend(self.skipped_tests)
        self.rerun_these_tests.extend(self.failed_tests)
        super().end_result(result)


class DependencySolver(SuiteVisitor):

    def __init__(self, *options) -> None:
        self.parser = DependencyArgumentParser(
            description=DESCRIPTION,
            formatter_class=CustomFormatter,
            epilog=EPILOG + EPILOG_ADDITIONAL_INFO,
            prog=PROG_NAME
        )
        self.parser.add_arguments()
        self.args = self.parser.parse_args(args=options)
        print_prog_name()
        self.start_time = time.time()
        self.logger = self._setup_logger()
        self.logger.info("The following arguments were obtained: " + repr(options))

        self.error_occurs = False
        self.check_done = False
        self.test_cases = {}  # test.full_name: DependencyTestCase
        self.suites = {}  # suite.full_name: TestSuite
        self.possible_loop = {}
        self.relation_chains = {}
        self.list_of_running_tests_names = []
        self.safe_values = []
        self.desired_tests = []
        self.tc_by_suite = []
        self.tc_by_test = []
        self.tc_by_include = []
        self.tc_by_exclude = []
        self.tc_by_exclude_explicit = []
        self.groups = {}  # test.full_name: [tests]
        self.main_suite_full_name = None

        if self.args.rerun:
            output_file = self.args.src_file or 'output.xml'
            result = ExecutionResult(output_file)
            rerunner = ReRunTests()
            result.visit(rerunner)
            self.list_of_running_tests_names = rerunner.rerun_these_tests
            self.logger.info("Rerunner started")
            for test in self.list_of_running_tests_names:
                self.logger.debug('Re-running test case ' + repr(test))


    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger(__name__)
        format = '%(asctime)s [ %(levelname)s ] %(message)s'
        if self.args.without_timestamps:
            format = '[ %(levelname)s ] %(message)s'
        logging.basicConfig(
            handlers=[logging.FileHandler(filename=f'{PROG_CALL}.log', mode='w', encoding='utf-8')],
            level=self.args.fileloglevel.upper(),
            format=format
        )
        stream_logger = logging.StreamHandler()
        stream_logger.setLevel(self.args.consoleloglevel.upper())
        stream_logger.setFormatter(CustomColorFormatter())
        logger.addHandler(stream_logger)
        return logger


    def _name_from_source_legacy(self, name: str) -> str:
        if '__' in name:
            name = name.split('__', 1)[1] or name
        name = name.replace('_', ' ').strip()
        return name.title() if name.islower() else name
    

    def _get_long_name(self, name: str) -> str:
        if rf_version >= (7, 0):
            return '.'.join([TestSuite.name_from_source(n) for n in name.split('.')])
        else:
            return '.'.join([self._name_from_source_legacy(n) for n in name.split('.')])


    def _matcher(self, name: str, list_of_names: Iterable[str]) -> list[str]:
        long_name = self._get_long_name(name)
        patterns = [f'*.{long_name}', long_name, name, f'*.{name}']

        return [value for value in list_of_names if any(Matcher(pattern).match(value) for pattern in patterns)]


    def _solve_dependencies(self, test_name: str, relation_chain: dict, loop_check_mode: bool = False, parent: str = "") -> dict:
        """Recursively examines the dependencies of the argument test_name. Returns dependencies (test ids and names) collected in dict.
        Restarts itself in loop checking mode if it finds a possible loop."""

        def _go_to_sub_suites(list_of_suites, tests=[]):
            for suite_dependency in list_of_suites:
                if self.suites[get_name(suite_dependency)].suites:
                    tests += _go_to_sub_suites(self.suites[get_name(suite_dependency)].suites, tests)
                else:
                    tests += self.suites[get_name(suite_dependency)].tests
            return tests

        test_name_list = self._matcher(test_name, self.test_cases)
        if not test_name_list:
            message = f"\'Depends On Test\' keyword refers to test {repr(test_name)} that does not exist. Check your spelling."
            raise RecursionError(message)

        if len(test_name_list) > 1:
            if parent:
                self.logger.warning(f"Dependence in test {repr(parent)} is {repr(test_name)} which is not unambiguous but refers to the following tests: {repr(test_name_list)}")

        for t_name in test_name_list:
            id = self.test_cases[t_name].id
            if id in relation_chain:
                if t_name in self.safe_values:
                    self.logger.debug(f"{repr(t_name)} has already been checked and does not contain a loop.")
                else:
                    if loop_check_mode:
                        message = f"Dependencies are cyclical! Test case {repr(t_name)} is already part of the relation chain: {repr(relation_chain.values())}"
                        raise RecursionError(message)
                    self.logger.debug(f"In test case {repr(t_name)} either the branches merge or it is a loop. Let's explore what we end up with if we start with this test.")
                    self.logger.debug("Starting in loop check mode.")
                    self.possible_loop = self._solve_dependencies(t_name, relation_chain={}, loop_check_mode=True)
                    self.logger.debug("It was a merge, so let's exit loop check mode:")
                    self.safe_values.extend(self.possible_loop.values())
                    self.logger.debug(f"These tests are already check as loop safe: {repr(self.safe_values)}")
            else:
                relation_chain[id] = t_name

            for dependency in self.test_cases[t_name].dependencies.tests:
                self.logger.debug(f"Dependency: {repr(t_name)} -> {repr(dependency)}")
                relation_chain = self._solve_dependencies(dependency, relation_chain=relation_chain, loop_check_mode=loop_check_mode, parent=t_name)

            for suite_dependency in self.test_cases[t_name].dependencies.suites:
                self.logger.debug(f"Dependency: {repr(t_name)} -> {repr(suite_dependency)}")
                self.logger.debug('Transforming suite dependency to test dependencies...')
                transformed_dependencies = self._matcher(suite_dependency, self.suites)
                if not transformed_dependencies:
                    message = f"\'Depends On Suite\' keyword refers to suite {repr(suite_dependency)} that does not exist. Check your spelling."
                    raise RecursionError(message)
                for d in transformed_dependencies:
                    depends_these_tests = self.suites[d].tests or _go_to_sub_suites(self.suites[d].suites)
                    for test_dependency in depends_these_tests:
                        self.logger.debug(f"Transformed dependency: {repr(t_name)} -> {repr(get_name(test_dependency))}")
                        relation_chain = self._solve_dependencies(get_name(test_dependency), relation_chain=relation_chain, loop_check_mode=loop_check_mode, parent=t_name)

        return relation_chain


    def _find_dependencies(self, setup) -> TestDependency:
        """Finds all test dependencies in the [Setup] section of the test."""
        def clean_argument(argument: str) -> str:
            return argument.replace("name=", "")
        
        test_dependencies = []
        suite_dependencies = []
        
        if setup.name == "Run Keywords":
            for i in range(len(setup.args)):
                if setup.args[i] == "Depends On Test":
                    test_dependencies.append(clean_argument(setup.args[i + 1]))
                elif setup.args[i] == "Depends On Suite":
                    suite_dependencies.append(clean_argument(setup.args[i + 1]))
        elif setup.name == "Depends On Test":
            test_dependencies.append(clean_argument(setup.args[0]))
        elif setup.name == "Depends On Suite":
            suite_dependencies.append(clean_argument(setup.args[0]))
        
        return TestDependency(test_dependencies, suite_dependencies)
    

    def _find_parent_dependendencies(self, suite: TestSuite, suite_setup_dependencies: list[str] = None) -> list[str]:
        if suite_setup_dependencies is None:
            suite_setup_dependencies = []

        parent_dependencies = suite_setup_dependencies[:]
        if suite.has_setup:
            new_dep = self._find_dependencies(suite.setup)
            if new_dep.tests or new_dep.suites:
                parent_dependencies.append(new_dep)
        return parent_dependencies


    def _find_suites(self, suite: TestSuite, suite_setup_dependencies: list[str] = None) -> None:
        """Recursively searches the entire folder structure, i.e. all sub-suites and tests."""
        parent_dependencies = self._find_parent_dependendencies(suite, suite_setup_dependencies)

        for sub_suite in suite.suites:
            if get_name(sub_suite) in self.suites:
                message = (
                    f"Suite name: {repr(get_name(sub_suite))} is duplicated with locations: "
                    f"{repr(get_name(sub_suite))} and {repr(get_name(self.suites[get_name(sub_suite)]))}. "
                    "Could not solve dependencies."
                )
                raise NameError(message)
            else:
                self.suites[get_name(sub_suite)] = sub_suite
            self.logger.debug(f"Investigating subsuite {repr(get_name(sub_suite))}")
            self._find_suites(sub_suite, parent_dependencies)
            self._find_tests(sub_suite, parent_dependencies)
        
        self.check_done = True


    def _find_tests(self, suite: TestSuite, suite_setup_dependencies: list[str] = None) -> None:
        """Searches for all tests in the given suite. Then creates DependencyTestCase objects."""
        if suite_setup_dependencies is None:
            suite_setup_dependencies = []

        for test in suite.tests:
            dependencies = TestDependency()
            if test.has_setup:
                dependencies = self._find_dependencies(test.setup)
            if suite_setup_dependencies:
                self.logger.debug(
                    f"Merging dependencies in test {repr(get_name(test))} because {repr(get_name(suite))} "
                    "or its parent suite has 'Suite Setup' with 'Depends On' keyword."
                )
                tests = dependencies.tests[:]
                suites = dependencies.suites[:]
                for suite_setup in suite_setup_dependencies:
                    tests.extend(suite_setup.tests)
                    suites.extend(suite_setup.suites)
                dependencies = TestDependency(tests, suites)
                self.logger.debug(
                    f"Test {repr(get_name(test))} has dependencies for tests: {repr(dependencies.tests)} "
                    f"and suites: {repr(dependencies.suites)}"
                )
            if test.name in [tc for tc in self.test_cases.values()]:
                message = (
                    f"Test name: {repr(get_name(test))} is duplicated with ids: {repr(test.id)} "
                    f"and {repr(self.test_cases[get_name(test)].id)}. Could not solve dependencies."
                )
                raise NameError(message)
            self.test_cases[get_name(test)] = DependencyTestCase(
                test.name, get_name(test), test.id, test.tags, dependencies
            )


    def _check_one_relation_chain(self, test_name: str) -> None:
        """Takes one test name as argument and adds whole relation chain starting from this test to self.list_of_running_tests_names, but only if test names are not there already."""
        self.logger.debug(f"Checking relation chain for test {repr(test_name)}")

        self.relation_chains[test_name] = []
        if test_name in self.test_cases:
            relation_chain = self._solve_dependencies(test_name, relation_chain={})

            chain_ok = True
            if self.tc_by_exclude_explicit:
                for d in relation_chain.values():
                    if self._matcher(d, self.tc_by_exclude_explicit):
                        self.logger.info(
                            f"Because --exclude_explicit argument, not requested test: {repr(d)}, "
                            "so skipping this whole relation chain. Adding nothing and moving next relation chain..."
                        )
                        chain_ok = False
                        break
            if chain_ok:
                for t in relation_chain.values():
                    if t not in self.list_of_running_tests_names:
                        self.logger.debug(f"Adding {repr(t)}")
                        self.list_of_running_tests_names.append(t)
                    else:
                        self.logger.debug(f"{repr(t)} is already added.")
                    self.relation_chains[test_name].append(t)
        else:
            message = f"Argument: {repr(test_name)} not found in test cases."
            raise NameError(message)


    def _check_tag(self, tag: str, option='include') -> list[str]:
        """Finds all test cases which have 'tag' in [Tags] section."""
        tag_found = False
        output = []
        for t in self.test_cases.values():
            if TagPatterns(tag).match(t.tags):
                tag_found = True
                if option == 'include':
                    self.logger.debug(f'Requested test {repr(get_name(t))} because of --include option: {repr(tag)}')
                elif option == 'exclude':
                    self.logger.debug(f'Not requested test {repr(get_name(t))} because of --exclude option: {repr(tag)}')
                elif option == 'exclude_explicit':
                    self.logger.debug(f'Not requested test {repr(get_name(t))} in any case, because of --exclude_explicit option: {repr(tag)}')
                output.append(get_name(t))
        if not tag_found and option == 'include':
            self.logger.warning(f'Given tag: {repr(tag)} not found from any tests. Check your spelling.')
        return output


    def _check_suite(self, suite_name: str, suite_found: bool = False) -> None:
        long_name = self._get_long_name(suite_name)
        for s in self.suites:
            if Matcher(f'*{long_name}').match(s) or Matcher(f'*.{long_name}').match(s):
                suite_found = True
                for sub_s in self.suites[s].suites:
                    self.logger.debug(f'{repr(suite_name)} has subsuite {repr(sub_s.name)}. Investigating...')
                    self._check_suite(get_name(sub_s), suite_found=suite_found)

                for t in self.suites[s].tests:
                    self.logger.debug(f'Requested test {repr(get_name(t))} because of subsuite or direct --suite option: {repr(suite_name)}')
                    self.tc_by_suite.append(get_name(t))

        if not suite_found:
            message = f"Argument: {repr(suite_name)} not found in test suites."
            raise NameError(message)


    def _check_test(self, test_name: str) -> list[str]:
        test_case_found = False
        output = []
        long_name = self._get_long_name(test_name)
        self.logger.debug(f'Requested test {repr(test_name)} directly.')
        for t in self.test_cases:
            if Matcher(f'*.{long_name}').match(t) or Matcher(long_name).match(t):
                output.append(t)
                test_case_found = True

        if not test_case_found:
            message = f"Argument: {repr(test_name)} does not match any test case."
            raise NameError(message)
        return output


    def _define_running_tests(self) -> None:
        """Contains logic that defines the tests to be executed based on the given command line arguments."""
        if self.args.suite:
            for suite in self.args.suite:
                self._check_suite(suite)

        if self.args.include:
            for tag in self.args.include:
                self.tc_by_include += self._check_tag(tag, option='include')

        if self.args.exclude:
            for tag in self.args.exclude:
                self.tc_by_exclude += self._check_tag(tag, option='exclude')

        if self.args.exclude_explicit:
            for tag in self.args.exclude_explicit:
                self.tc_by_exclude_explicit += self._check_tag(tag, option='exclude_explicit')

        if self.args.test:
            for desired_test_name in self.args.test:
                self.tc_by_test += self._check_test(desired_test_name)

        desired_test_set = set()
        list_of_desired_tcs = [set(self.tc_by_suite), set(self.tc_by_test), set(self.tc_by_include)]
        
        if any(list_of_desired_tcs):
            non_empties = [x for x in list_of_desired_tcs if x]
            desired_test_set = set.intersection(*non_empties)

        if self.args.exclude:
            not_desired_test_set = set(self.tc_by_exclude)

            if not desired_test_set:
                desired_test_set = set(self.test_cases)
                if not not_desired_test_set:
                    self.logger.warning(
                        "Selecting all test cases in given folder, because only --exclude argument(s) given and it does not match any tags."
                    )

            desired_test_set -= not_desired_test_set

        # Returning right order of test cases
        self.desired_tests = [t for t in self.test_cases if t in desired_test_set]

        if self.args.ui:
            self.logger.info(f"Initializing GUI...")
            self.ui_default_tc = self.desired_tests.copy()
            # Choosing all test
            self.desired_tests = [t for t in self.test_cases]

        if self.args.rerun:
            self.logger.debug(
                "Rerun mode activated, so tests are only selected based on 'output.xml' or another given file."
            )
            self.desired_tests = self.list_of_running_tests_names

        if self.desired_tests:
            if self.args.reverse:
                find_these_tests = self.desired_tests
                self.desired_tests = [get_name(t) for t in self.test_cases.values()]

            self.logger.debug(f'These are tests which user requested: {repr(self.desired_tests)}')
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
                    print(f"If you change the implementation of test {repr(find_this)}, it may affect these tests:")
                    if print_list:
                        for p in print_list:
                            print("   ", p)
                    else:
                        if find_this in self.test_cases:
                            print(f"    No effects, because nothing depends on the test {repr(find_this)}")
                        else:
                            print(f"    Test {repr(find_this)} not found. Check your spelling.")
                    print()

                self.list_of_running_tests_names = []

        if not self.list_of_running_tests_names:
            self.logger.warning("No tests chosen.")

        if self.args.ui:
            self.logger.info(f"Starting GUI with default tests: {self.ui_default_tc}")
            all_tests = self._write_depends_ordering(f'{PROG_CALL}.all_dependencies.txt')
            # Staring UI
            self.list_of_running_tests_names = main_application(all_tests, self.ui_default_tc)
            for t in self.test_cases:
                self.test_cases[t].solved_test_dependencies = [d for d in self.test_cases[t].solved_test_dependencies if d in self.list_of_running_tests_names]
                self.test_cases[t].direct_precondition_for_tests = [p for p in self.test_cases[t].direct_precondition_for_tests if p in self.list_of_running_tests_names]
            self.logger.info(f"Closing GUI. Chosen tests are: {self.list_of_running_tests_names}")

        if self.args.pabotlevel != 'NONE':
            self._write_depends_ordering()

        if self.args.debug:
            self.logger.info(
                f"{len(self.list_of_running_tests_names)} tests would have been chosen. List of test: {self.list_of_running_tests_names}"
            )
            self.logger.warning("DEBUG mode activated. Emptying test case list...")
            self.list_of_running_tests_names = []


    def _define_groups(self) -> None:
        ordered_list = [t for t in self.test_cases if t in self.list_of_running_tests_names]
        initial_tests = [t for t in ordered_list if not self.test_cases[t].solved_test_dependencies]
        ending_tests = [t for t in ordered_list if not self.test_cases[t].direct_precondition_for_tests]
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
                    if start_point not in self.initial_endings[full_name]:
                        self.initial_endings[full_name].append(start_point)
                else:
                    self.initial_endings[full_name] = [start_point]

        def _find_all_ending_test_starting_from(start_point, full_name):
            if full_name not in ending_tests:
                for tc in self.test_cases[full_name].direct_precondition_for_tests:
                    _find_all_ending_test_starting_from(start_point, tc)
            else:
                if full_name in self.ending_initials:
                    if start_point not in self.ending_initials[full_name]:
                        self.ending_initials[full_name].append(start_point)
                else:
                    self.ending_initials[full_name] = [start_point]

        def _update_groups(full_name, group):
            tc = self.test_cases[full_name]
            if not tc.group:
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
                if tc.group:
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


    def _write_depends_ordering(self, filename=f'{PROG_CALL}.pabot.txt') -> str:
        # TODO: Optimize!
        """Used for pabot to write ordering.txt file as name depsol.pabot.txt."""
        all_text = ""
        ordered_list = [t for t in self.test_cases if t in self.list_of_running_tests_names]

        if self.args.randomize:
            random_option, seed = self.args.randomize
            #self.logger.info(f"Randomization option: {random_option}, Seed: {seed}")

            if seed is not None:
                random.seed(int(seed))
                #self.logger.info(f"Random generator seeded with: {seed}")
            else:
                #self.logger.info("Random generator not seeded.")
                pass

        for r in ordered_list:
            for t in self.test_cases[r].dependencies.tests:
                for matching_t in self._matcher(t, self.test_cases):
                    self.test_cases[r].add_solved_test_dependencies(matching_t)
                    self.test_cases[matching_t].add_direct_precondition(r)
            for s in self.test_cases[r].dependencies.suites:
                for matching_s in self._matcher(s, self.suites):
                    for t_in_s in self.suites[matching_s].tests:
                        self.test_cases[r].add_solved_test_dependencies(get_name(t_in_s))
                        self.test_cases[get_name(t_in_s)].add_direct_precondition(r)

        self._define_groups()

        if self.args.pabotlevel == 'OPTIMIZED':
            sorted_groups = sort_by_output_xml(self.groups, inpath=self.args.src_file or 'output.xml')
        else:
            sorted_groups = self.groups

        if random_option in ['ALL', 'SUITES']:
            items = list(sorted_groups.items())
            random.shuffle(items)
            sorted_groups = dict(items)

        if random_option in ['ALL', 'TESTS']:
            random.shuffle(ordered_list)

        for g in sorted_groups:
            group_text, group_end_text = "", ""
            if len(self.groups[g]) > 1:
                group_text = "{\n"
                group_end_text = "}\n"
            for tc in ordered_list:
                if tc in self.groups[g]:
                    test = f"--test {tc}"
                    if self.args.pabotlevel in ['FULL', 'OPTIMIZED']:
                        for s in self.test_cases[tc].solved_test_dependencies:
                            test += f" #DEPENDS {s}"
                    group_text += test + "\n"
            group_text += group_end_text
            all_text += group_text

        with open(filename, 'w') as f:
            f.write(all_text)

        return all_text


    def start_suite(self, suite: TestSuite) -> None:
        """When suite starts, check if it is main suite/folder. If it is, loops through all test cases and finds all relation chains.
        After then it defines which test to execute."""
        if not self.error_occurs:
            self.logger.debug(f"Started suite: {repr(get_name(suite))}")
        if not self.check_done:
            self.logger.info("Starting to explore the dependencies...")
            self.main_suite_full_name = get_name(suite)
            try:
                self.suites[get_name(suite)] = suite
                if len(suite.suites) > 0:
                    self._find_suites(suite)
                else:
                    parent_dependencies = self._find_parent_dependendencies(suite)
                    self._find_tests(suite, parent_dependencies)
                self._define_running_tests()
            except (NameError, RecursionError) as err:
                self.logger.error(f"{err.args[0]} Execution of tests cannot be started!")
                self.list_of_running_tests_names = []
                self.error_occurs = True
            else:
                self.logger.info("Choosing tests...")


    def end_suite(self, suite: TestSuite) -> None:
        """Selects the tests and suites to be executed."""
        suite.tests = [t for t in suite.tests if get_name(t) in self.list_of_running_tests_names]
        for t in suite.tests:
            self.logger.debug(f"Test {repr(get_name(t))} will be executed.")
        suite.suites = [s for s in suite.suites if s.test_count > 0]
        for s in suite.suites:
            self.logger.debug(f"Suite {repr(get_name(s))} will be executed.")
        if not self.error_occurs:
            self.logger.debug(f"Finishing suite: {repr(get_name(suite))}")
            if not self.args.without_timestamps and get_name(suite) == self.main_suite_full_name:
                self.logger.info("All dependencies resolved in %s seconds." % str(time.time() - self.start_time))
