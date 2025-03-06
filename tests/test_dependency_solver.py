"""Simple tests for DependencySolver. Runs with pytest. Run like: path/to/dependency_solver>pytest tests"""

from subprocess import call
import shutil, os

PROG_CALL = 'depsol'
PROG_NAME = f'DependencySolver.{PROG_CALL}'

TEST_OUTPUT_FOLDER = './test_output/'
BASE_COMMAND = [PROG_CALL, '--debug', '--without_timestamps']
TESTS_FOLDER = './tests/'

def read_log(name=PROG_CALL + '.log'):
    with open(name) as f:
        lines = [line.rstrip() for line in f]
        return lines


def copy_log(test_case: str, name=PROG_CALL + '.log'):
    src_file = './' + name
    dst_folder = TEST_OUTPUT_FOLDER + test_case.split(sep='/')[-1]
    folder_exists = os.path.exists(TEST_OUTPUT_FOLDER)
    if not folder_exists:
        os.makedirs(TEST_OUTPUT_FOLDER)
    shutil.copyfile(src=src_file, dst=dst_folder)
    print("Log copied to location", repr(dst_folder), "Check and compare content.")


def check_logs(command: list, reference_log: str):
    call(command)
    output = read_log()
    reference = read_log(reference_log)

    if len(output) != len(reference):
        print("Different number of lines.")
        print("The length of the reference is", len(reference))
        print("The length of the output was", len(output))
        copy_log(reference_log)
        return True
    for i in range(len(output)):
        if output[i] != reference[i]:
            print('Difference in line:', i + 1)
            print('Reference is: ', repr(reference[i]))
            print('Output was:   ', repr(output[i]))
            copy_log(reference_log)
            return True
    return False


def check_pabot_ordering(reference_txt: str):
    output = read_log(PROG_CALL + ".pabot.txt")
    reference = read_log(reference_txt)

    if len(output) != len(reference):
        print("Different number of lines.")
        print("The length of the reference is", len(reference))
        print("The length of the output was", len(output))
        copy_log(reference_txt, PROG_CALL + ".pabot.txt")
        return True
    for i in range(len(output)):
        if output[i] != reference[i]:
            print('Difference in line:', i + 1)
            print('Reference is: ', repr(reference[i]))
            print('Output was:   ', repr(output[i]))
            copy_log(reference_txt, PROG_CALL + ".pabot.txt")
            return True
    return False


class TestClass:

    def test_delete_previous_logs(self):
        try:
            shutil.rmtree(TEST_OUTPUT_FOLDER)
        except FileNotFoundError:
            print("Folder do not exists.")
        assert os.path.isdir(TEST_OUTPUT_FOLDER) == False


    def test_A3(self):
        """Basic Dependency: 
        A -> B -> C"""
        additional_command = [TESTS_FOLDER + 'data_1/', '-t', 'TestA3']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/TestA3.log') == False
        assert check_pabot_ordering(TESTS_FOLDER + 'pabot_ordering_references/TestA3.txt') == False


    def test_A3_long_call(self):
        """Basic Dependency:
        A -> B -> C"""
        subcommand = PROG_NAME + ':--test:TestA3:--debug:--without_timestamps:--fileloglevel:DEBUG:--consoleloglevel:INFO:--pabotlevel:GROUP'
        command = ['robot', '--prerunmodifier', subcommand, TESTS_FOLDER + 'data_1/']
        assert check_logs(command, TESTS_FOLDER + 'test_reflogs/TestA3_long_call.log') == False
        assert check_pabot_ordering(TESTS_FOLDER + 'pabot_ordering_references/TestA3_long_call.txt') == False


    def test_A6(self):
        """Merge:
        A -> B -> D ja A -> C -> D"""
        additional_command = [TESTS_FOLDER + 'data_1/', '-t', 'TestA6']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/TestA6.log') == False
        assert check_pabot_ordering(TESTS_FOLDER + 'pabot_ordering_references/TestA6.txt') == False


    def test_B3(self):
        """Depends test in another suite
        suiteB.testB1 -> suiteA.testA1"""
        additional_command = [TESTS_FOLDER + 'data_1/', '-i', 'B3']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/TestB3.log') == False
        assert check_pabot_ordering(TESTS_FOLDER + 'pabot_ordering_references/TestB3.txt') == False


    def test_B5(self):
        additional_command = [TESTS_FOLDER + 'data_1/', '-i', 'testB', '-e', 'B6']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/TestB5.log') == False
        assert check_pabot_ordering(TESTS_FOLDER + 'pabot_ordering_references/TestB5.txt') == False


    def test_exclude_explicit(self):
        additional_command = [TESTS_FOLDER + 'data_1/', '-i', 'A2', '-ee', 'A1']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/exclude_explicit.log') == False
        assert check_pabot_ordering(TESTS_FOLDER + 'pabot_ordering_references/exclude_explicit.txt') == False

    
    def test_complicated_call(self):
        additional_command = [TESTS_FOLDER + 'data_1/', '-t', 'suite*.T*t[AB]?', '-s', 'data_1.*[Aa]', '-i', 'allANDAORtestBNOTt3', '-e', 'allANDt2', '-e', 'NOT[AB]1', '-t', 'Test[!Bb]1', '-i', 't1ANDallANDA', '-t', 'Test[AB][!2-6]']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/complicated_call.log') == False
        assert check_pabot_ordering(TESTS_FOLDER + 'pabot_ordering_references/complicated_call.txt') == False


    def test_loop_check(self):
        """Loop: A -> B -> A"""
        additional_command = [TESTS_FOLDER + 'data_2/', '-i', 'C2']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/loop.log') == False


    def test_self_loop_check(self):
        """Loop: A -> A"""
        additional_command = [TESTS_FOLDER + 'data_2/', '-i', 'testC', '-e', 'C1', '-e', 'C2']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/self_loop.log') == False


    def test_does_not_exist(self):
        """A -> This_test_not_exist"""
        data_folder =  'data_3/'
        additional_command = [TESTS_FOLDER + data_folder, '-i', 'C2']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/not_exist.log') == False


    def test_suite_does_not_exist(self):
        """A -> This_suite_not_exist"""
        data_folder =  'data_3/'
        additional_command = [TESTS_FOLDER + data_folder, '-s', 'suiteC', '-e', 'C2']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/suite_not_exist.log') == False

    
    def test_call_suite_which_does_not_exist(self):
        data_folder =  'data_3/'
        additional_command = [TESTS_FOLDER + data_folder, '-s', 'suite_not_exist']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/suite_name_not_exist.log') == False


    def test_call_test_which_does_not_exist(self):
        data_folder =  'data_3/'
        additional_command = [TESTS_FOLDER + data_folder, '-t', 'test_not_exist']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/test_name_not_exist.log') == False


    def test_call_tag_which_does_not_exist(self):
        data_folder =  'data_3/'
        additional_command = [TESTS_FOLDER + data_folder, '-i', 'tag_not_exist']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/tag_name_not_exist.log') == False
        assert check_pabot_ordering(TESTS_FOLDER + 'pabot_ordering_references/tag_name_not_exist.txt') == False


    def test_call_only_exclude_tag_which_does_not_exist(self):
        data_folder =  'data_3/'
        additional_command = [TESTS_FOLDER + data_folder, '-e', 'tag_not_exist']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/exclude_tag_name_not_exist.log') == False


    def test_suite_loop(self):
        data_folder =  'data_4/'
        additional_command = [TESTS_FOLDER + data_folder, '-i', 'E']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/suite_loop.log') == False


    def test_name_dublicate(self):
        data_folder =  'data_5/'
        additional_command = [TESTS_FOLDER + data_folder, '-i', 'D2']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/test_duplicate.log') == False
        assert check_pabot_ordering(TESTS_FOLDER + 'pabot_ordering_references/test_duplicate.txt') == False


    def test_suite_name_dublicate(self):
        data_folder =  'data_6/'
        additional_command = [TESTS_FOLDER + data_folder, '-i', 'D']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/suite_duplicate.log') == False
        assert check_pabot_ordering(TESTS_FOLDER + 'pabot_ordering_references/suite_duplicate.txt') == False


    def test_rerun(self):
        data_folder =  'data_7/'
        first_command = [PROG_CALL, '--without_timestamps', TESTS_FOLDER + data_folder, '-i', 'ALL']
        call(first_command)
        second_command = [TESTS_FOLDER + data_folder, '-i', 'ALL', '--rerun']
        assert check_logs(BASE_COMMAND + second_command, TESTS_FOLDER + 'test_reflogs/rerun.log') == False
        assert check_pabot_ordering(TESTS_FOLDER + 'pabot_ordering_references/rerun.txt') == False


    def test_pabot_grouping(self):
        data_folder =  'data_8/'
        additional_command = [TESTS_FOLDER + data_folder, '-i', 'ALL']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/pabot_grouping.log') == False
        assert check_pabot_ordering(TESTS_FOLDER + 'pabot_ordering_references/pabot_grouping.txt') == False


    def test_setup_command(self):
        data_folder =  'data_9/'
        additional_command = [TESTS_FOLDER + data_folder, '-i', 'B4']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/robot_test_setup.log') == False
        assert check_pabot_ordering(TESTS_FOLDER + 'pabot_ordering_references/robot_test_setup.txt') == False


    def test_not_unambigous(self):
        data_folder =  'data_10/'
        additional_command = [TESTS_FOLDER + data_folder, '-i', 'A2']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/not_unambigous.log') == False
        assert check_pabot_ordering(TESTS_FOLDER + 'pabot_ordering_references/not_unambigous.txt') == False


    def test_keyword_in_suite_setup(self):
        data_folder =  'data_11/'
        additional_command = [TESTS_FOLDER + data_folder, '--suite', 'suite O']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/keyword_in_suite_setup.log') == False
        assert check_pabot_ordering(TESTS_FOLDER + 'pabot_ordering_references/keyword_in_suite_setup.txt') == False


    def test_different_test_names(self):
        data_folder =  'data_12/01__suite_A.robot'
        additional_command = [TESTS_FOLDER + data_folder, '-i', 'ALL']
        assert check_logs(BASE_COMMAND + additional_command, TESTS_FOLDER + 'test_reflogs/test_names.log') == False
        assert check_pabot_ordering(TESTS_FOLDER + 'pabot_ordering_references/test_names.txt') == False
