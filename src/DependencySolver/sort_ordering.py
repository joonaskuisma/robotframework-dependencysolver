from robot.api import ExecutionResult, ResultVisitor


class ExecutionTimeChecker(ResultVisitor):
    def __init__(self):
        self.times_dict = {}

    def visit_test(self, test):
        self.times_dict[test.full_name] = (int(test.elapsedtime), test.status)

    def get_times_dict(self):
        return self.times_dict


def sort_by_output_xml(groups, inpath='output.xml'):
    result = ExecutionResult(inpath)
    checker = ExecutionTimeChecker()
    result.visit(checker)
    times_dict = checker.get_times_dict()
    
    all_groups = {}
    for group, tests in groups.items():
        group_time = 0
        group_status = 'PASS'
        for test_case in tests:
            if test_case in times_dict:
                time, status = times_dict[test_case]
                group_time += time
                if status != 'PASS':
                    group_status = 'FAIL'
        all_groups[group] = (group_time, group_status)
    
    sorted_by_time = dict(sorted(all_groups.items(), key=lambda x: x[1][0], reverse=True))
    sorted_by_status = dict(sorted(sorted_by_time.items(), key=lambda x: x[1][1]))
    
    return sorted_by_status
