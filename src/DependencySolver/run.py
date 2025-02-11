# Copyright 2024 Joonas Kuisma <kuisma.joonas@gmail.com>
"""Use 'DependencySolver -h' command for help"""

from subprocess import call
import sys
from .solver import CustomFormatter, DependencyArgumentParser, PROG_NAME, PROG_CALL, DESCRIPTION, EPILOG


HELP_FOLDER = """Folder where test are. Default is your current directory '.'"""
HELP_COMMANDS_TO_ROBOT = """These commands are given to 'robot' directly instead of --prerunmodifier. Give them in one sentence, like: -c '-v name1:value1 -v name2:value2'.
Do not use '-t', '-i', '-s' or etc. robot-like options, just give them to --prerunmodifier instead. If you need spaces, use like:  -c \"-v 'name with spaces:value with spaces'\""""


def main():
    parser = DependencyArgumentParser(description=DESCRIPTION, formatter_class=CustomFormatter, epilog=EPILOG, prog=PROG_NAME)

    # Adding local options:
    parser.add_arguments()
    group_local = parser.add_argument_group(f'{PROG_CALL} options', f'These additional options are used only when calling command \'{PROG_CALL}\' directly.')
    group_local.add_argument('-f', '--folder', help=HELP_FOLDER, default='.', metavar='<test_folder>')
    group_local.add_argument('-c', '--commands_to_robot', action='store', help=HELP_COMMANDS_TO_ROBOT, metavar='<commands>', nargs='*')
    args = vars(parser.parse_args(args=sys.argv[1:]))

    subcommand = PROG_NAME
    for option in args:
        if args[option] is not None and option in ['test', 'suite', 'include', 'exclude', 'exclude_explicit']:
            for value in args[option]:
                subcommand = subcommand + ':--' + option + ':' + value

    # Handle others --prerunmodifier options
    if args['debug']:
        subcommand = subcommand + ':--debug'
    if args['without_timestamps']:
        subcommand = subcommand + ':--without_timestamps'
    if args['reverse']:
        subcommand = subcommand + ':--reverse'
    if args['rerun']:
        subcommand = subcommand + ':--rerun'
    subcommand = subcommand + ':--loglevel:' + args['loglevel'].upper()
    subcommand = subcommand + ':--consoleloglevel:' + args['consoleloglevel'].upper()
    subcommand = subcommand + ':--pabot:' + args['pabot'].upper()
    if args['src_file']:
        subcommand = subcommand + ':--src_file:' + args['src_file'].name
    #subcommand = subcommand + ':--dest_file:' + args['dest_file'].name

    # Building robot command:
    command = ['robot', '--prerunmodifier', subcommand]

    if args['commands_to_robot'] is not None:
        for value in args['commands_to_robot']:
            for part in value.split('\''):
                if len(part) > 0:
                    if part.startswith('-'):
                        part = part.strip()
                    else:
                        part = '\'' + part + '\''
                    command.append(part)

    command.append(args['folder'])

    print("Executing this list of commands:", command)
    call(command)


if __name__ == "__main__":
    sys.exit(main())