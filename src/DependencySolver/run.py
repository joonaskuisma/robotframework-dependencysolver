# Copyright 2024 Joonas Kuisma <kuisma.joonas@gmail.com>
"""Use 'depsol --help' command for help"""

import subprocess
import sys
import io
from .solver import CustomFormatter, DependencyArgumentParser, PROG_NAME, PROG_CALL, DESCRIPTION, EPILOG


class ExtendedDependencyArgumentParser(DependencyArgumentParser):
    def add_arguments(self):
        super().add_arguments()
        extra_otions = self.add_argument_group(f'{PROG_CALL} options', f'These additional options are used only when calling command \'{PROG_CALL}\' directly.')
        extra_otions.add_argument('--tool', choices=['robot', 'pabot'], default='robot', help='Tool to use: robot (default) or pabot.')


def build_command():
    parser = ExtendedDependencyArgumentParser(description=DESCRIPTION, formatter_class=CustomFormatter, epilog=EPILOG)
    parser.add_arguments()
    args, unknown = parser.parse_known_args()

    prerun_call = '--prerunmodifier'
    if args.tool == 'pabot':
        prerun_call = '--pabotprerunmodifier'
        unknown.extend(['--testlevelsplit', '--ordering', f'{PROG_CALL}.pabot.txt'])

    if not any(arg for arg in [args.test, args.suite, args.include, args.exclude, args.exclude_explicit, args.rerun, args.ui]):
        print(f"WARNING: To use '{PROG_CALL}', please provide a parameter related to test selection, for example '--test' or '--include'. See: '{PROG_CALL} --help'" )
    
    prerun_params = {
        'test': args.test,
        'suite': args.suite,
        'include': args.include,
        'exclude': args.exclude,
        'exclude_explicit': args.exclude_explicit,
        'rerun': args.rerun,
        'randomize': args.randomize,
        'reverse': args.reverse,
        'debug': args.debug,
        'without_timestamps': args.without_timestamps,
        'fileloglevel': args.fileloglevel,
        'consoleloglevel': args.consoleloglevel,
        'src_file': args.src_file,  # type: io.TextIOBase
        'pabotlevel': args.pabotlevel,
        'ui': args.ui,
    }

    command = [args.tool]

    prerun_modifier = ""
    for prerun_params, values in prerun_params.items():
        if isinstance(values, bool) and values:
            prerun_modifier += f'--{prerun_params}:'
        elif isinstance(values, str) and values:
            prerun_modifier += f'--{prerun_params}:{values}:'
        elif isinstance(values, tuple) and values:
            if values[1] is not None:
                prerun_modifier += f'--{prerun_params}:{values[0]};{str(values[1])}:'
            else:
                prerun_modifier += f'--{prerun_params}:{values[0]}:'
        elif isinstance(values, list) and values:
            for value in values:
                prerun_modifier += f'--{prerun_params}:{value}:'
        elif isinstance(values, io.TextIOBase) and values:
            prerun_modifier += f'--{prerun_params}:{values.name}:'
        elif values:
            raise ValueError(
                f"Option {repr(prerun_params)} with value {repr(values)} not handled correctly!\n"
                "Please report this issue in GitHub."
            )

    prerun_modifier_cmd = [prerun_call, f'{PROG_NAME}:{prerun_modifier[:-1]}']
    command.extend(prerun_modifier_cmd)
    command.extend(unknown)
    
    print(command)
    return command


def main():
    subprocess.call(build_command())


if __name__ == "__main__":
    sys.exit(main())