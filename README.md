# robotframework-dependencysolver

[![PyPI - Version](https://img.shields.io/pypi/v/robotframework-dependencysolver)](https://pypi.org/project/robotframework-dependencysolver/)
[![PyPI Downloads](https://static.pepy.tech/badge/robotframework-dependencysolver)](https://pepy.tech/projects/robotframework-dependencysolver)

## Table of Contents

- [Introduction](#introduction)
- [Versioning](#versioning)
- [Dependencies](#dependencies)
- [Installation](#installation)
- [How define dependencies with DependencyLibrary](#how-define-dependencies-with-dependencylibrary)
- [Using DependencySolver](#using-dependencysolver)
- [Using with Pabot](#using-with-pabot)
- [Contributing](#contributing)

## Introduction

A [Robot Framework](https://robotframework.org/) prerunmodifier for interdependent test cases execution.

Ideally tests are independent, but when tests depend on earlier tests,
[DependencyLibrary](https://github.com/mentalisttraceur/robotframework-dependencylibrary) makes it easy to explicitly declare these dependencies
and have tests that depend on each other do the right thing.

The **DependencyLibrary** provides two Robot Framework keywords: `Depends On Test`
and `Depends On Suite` for defining dependencies between tests and suites. 

This **DependencySolver** is a pre-run modifier for Robot Framework, designed to 
execute dependent test chains. For instance, if Test C depends on Test B, 
and Test B in turn depends on Test A, then all three tests must be run to 
ensure Test C can execute successfully. However, if you run Robot Framework with
the command `robot -t 'test C' <path_to_your_test_folder>`, Test C will fail 
because this command does not select Tests B and A.

For more details on using the **DependencySolver**, please refer to the section 
[Using DependencySolver](#using-dependencysolver).

If you want to run tests parallel with [Pabot](https://pabot.org/), please 
refer to section [Using With Pabot](#using-with-pabot).

## Versioning

This library\'s version numbers follow the [SemVer 2.0.0
specification](https://semver.org/spec/v2.0.0.html).

## Dependencies

To function correctly, **DependencySolver** requires the following versions:

- **Python** >= 3.10  
- **Robot Framework** >= 5.0  
- **robotframework-dependencylibrary** >= 4.0  

Additionally, for parallel test execution, you can optionally use:  

- **robotframework-pabot** >= 4.1  

## Installation

If you already have [Python](https://www.python.org/) with [pip](https://pip.pypa.io/en/stable/) installed, you can simply run:

```cmd
pip install robotframework-dependencysolver
```

This will install the latest version of **robotframework-dependencysolver**, along with latest (or sufficiently recent if already installed) versions of **robotframework** and **robotframework-dependencylibrary**.

Additionally, if you are using the **pabot** library, you can ensure that you have a sufficiently recent version of **robotframework-pabot** by running:

```cmd
pip install robotframework-dependencysolver[pabot]
```

After desired installation command, you can verify a successful installation with the following command:

```cmd
depsol --version
```

## How define dependencies with DependencyLibrary

First, include the [DependencyLibrary](https://github.com/mentalisttraceur/robotframework-dependencylibrary) in your tests:

``` robotframework
*** Settings ***
Library    DependencyLibrary
```

Typical usage:

``` robotframework
*** Test cases ***
Passing Test
    No operation

A Test that Depends on "Passing Test"
    Depends On Test    Passing Test
    Log    The rest of the keywords in this test will run as normal.
```
> [!NOTE]
> `DependencySolver` recognizes only `Depends On` keywords defined in `[Setup]`
sections, even though these keywords can technically be used in other parts of 
the test. Therefore, it is recommended to specify all dependencies under the 
`[Setup]` section, using the built-in keyword `Run Keywords` if needed. 
Dependencies, after all, are prerequisites for running a test.

When you need to declare multiple dependencies, just repeat the keyword:

``` robotframework
*** Test cases ***
Another Passing Test
    No operation

A Test that Depends on Both "Passing Test" and "Another Passing Test"
    [Setup]    Run Keywords    Depends On Test    Passing Test
    ...    AND    Depends On Test    Another Passing Test
    Log    The rest of the keywords in this test will run as normal.
```

You can also depend on the statuses of entire test suites:

``` robotframework
*** Test cases ***
A Test that Depends on an Entire Test Suite Passing
    [Setup]    Depends On Suite    Some Test Suite Name
    Log    The rest of the keywords will run if that whole suite passed.
```

Note that to depend on a suite or a test from another suite, you must
either run Robot Framework with `--listener DependencyLibrary`, or that
suite must also include `DependencyLibrary` in its `*** Settings ***`. 
Additionally, you can define `DependencyLibrary` in a common 
`some_name.resource` file that is accessible across all suites.

### Skipped Dependencies

If a dependency was skipped, the depending test is also skipped:

``` robotframework
*** Test cases ***
Skipped Test
    Skip    This test is skipped for some reason.

A Test that Depends on "Skipped Test"
    [Setup]    Depends On Test    Skipped Test
    Log    The rest of the keywords (including this log) will NOT run!
```

The skip message follows this format:

    Dependency not met: test case 'Skipped Test' was skipped.

### Failing Dependencies

If a dependency failed, the depending test is skipped instead of
redundantly failing as well:

``` robotframework
*** Test cases ***
Failing Test
    Fail    This test failed for some reason.

A Test that Depends on "Failing Test"
    [Setup]    Depends On Test    Failing Test
    Log    The rest of the keywords (including this log) will NOT run!
```

The skip message follows this format:

    Dependency not met: test case 'Failing Test' failed.

### Mistake Warnings

If you depend on a test or suite that does not exist or has not run yet,

``` robotframework
*** Test cases ***
A Test that Depends on "Missing Test"
    Depends On Test    Missing Test
```

the test will warn and the warning message follows this format:

    Dependency not met: test case 'Missing Test' not found.

If you make a test depend on itself or on the suite that contains it,

``` robotframework
*** Test cases ***
Depends on Self
    Depends On Test    Depends on Self
```

the test will warn and the warning message follows this format:

    Dependency not met: test case 'Depends on Self' mid-execution.

## Using DependencySolver

After you have defined the dependencies of each test in the `[Setup]` section by
using `Depends On Test` or `Depends On Suite` keywords, then pre-run modifier 
`DependencySolver` checks all `[Setup]` sections and solve dependencies before 
running tests. You could use `Depends On Test` or `Depends On Suite` keywords 
multiple times and/or together with other setup keywords by using build-in 
`Run Keywords` at first.

Write test setup as follows:

```RobotFramework
*** Settings ***
Library    DependencyLibrary


*** Test cases ***
Test A
    [Setup]    Do Test Setup...
    [Tags]    tagA
    Do Something...

Test B
    [Setup]    Run Keywords    Depends On Test    name=Test A
    ...    AND    Do Test Setup...
    [Tags]    tagB
    Do Something...

Test C
    [Setup]    Run Keywords    Depends On Test    name=Test B
    ...    AND    Do Test Setup...
    [Tags]    tagC
    Do Something...

```

> [!IMPORTANT]
> `DependencySolver` does not impact the execution order of tests but simply includes the necessary tests and excludes the unnecessary ones. Dependencies can form any tree structure; however, cyclic dependencies (e.g., A -> B and B -> A) will result in an error.

When you have written test dependencies in `[Setup]` sections like above, then 
by using `DependencySolver` as `prerunmodifier` you could run whole dependency 
chain C -> B -> A by command:

```cmd
robot --prerunmodifier DependencySolver.depsol:-t:"Test C" <other_robot_commands> <your_test_folder>
```

Additionally, you could use tags also (but only static, not dynamic tags):
```cmd
robot --prerunmodifier DependencySolver.depsol:-i:tagC <other_robot_commands> <your_test_folder>
```

You can also use shortcut `depsol` directly. This internally calls `robot` 
with `--prerunmodifier` option. When using this shortcut, all options 
recognized by `depsol` are passed to `--prerunmodifier` instead of `robot`.

```cmd
depsol -t "test C" <other_robot_commands> <your_test_folder>
```
Or
```cmd
depsol -i "tagC" <other_robot_commands> <your_test_folder>
```
These commands will have the same effect as the two commands mentioned above.

**Note:** If you call `robot` directly, `<other_robot_commands>` should not 
include the options `--test`, `--suite`, `--include` or `--exclude`, as they 
will be executed before `--prerunmodifier`. This will cause **depsol** to 
function incorrectly. Instead, pass these options to `--prerunmodifier`, 
using `:` as a separator instead of a space. If the test name contains spaces, 
enclose it in `""`.

For example:
```cmd
robot --prerunmodifier DependencySolver.depsol:-i:tagC:-t:"Test B" <your_test_folder>
```

You can launch the simple UI of the Dependency Solver using the --ui parameter. 
This interface allows you to select tests for execution through a tree view and visualizes dependencies between tests using arrows.

**Note:** The UI is currently in Beta, so feedback and bug reports are very welcome. Its documentation will also improve over time.

For more options and help, please run

```cmd
depsol --help
```

`DependencySolver` generates the following two files in the current directory:

- **depsol.log**: An internal log showing the process of traversing and selecting dependencies.
- **depsol.pabot.txt**: A file for use with [Pabot](https://pabot.org/), detailing how the selected tests can be run in parallel while respecting dependencies.

## Using with Pabot

Please, read [Using DependencySolver](#using-dependencysolver) at first.

If you want to run tests with Pabot, you need at least version 4.1.0 of the 
[robotframework-pabot](https://pypi.org/project/robotframework-pabot/) library.
This version introduces the --pabotprerunmodifier feature, which functions 
similarly to prerunmodifier, but it is not passed down to subprocesses. 
Instead, it is executed only once in Pabot's main process.

Once the appropriate version is installed, using Pabot is quite 
straightforward. The simplest command is:

```cmd
pabot --testlevelsplit --pabotprerunmodifier DependencySolver.depsol:-i:tagC --ordering depsol.pabot.txt <other_pabot_commands> <your_test_folder>
```
Or you can use command:
```cmd
depsol --tool pabot -i tagC <other_pabot_commands> <your_test_folder>
```

However, note that since the example tests A, B, and C depend on each other, 
they are grouped together using the `--ordering` file so they are executed in 
the same process. The content of the `depsol.pabot.txt` file looks something 
like this:

```
{
--test Suite.Test A
--test Suite.Test B #DEPENDS Suite.Test A
--test Suite.Test C #DEPENDS Suite.Test B
}
```

## Contributing

If you would like to request a new feature or modification to existing 
functionality, or report a bug, you can open an issue on [GitHub](https://github.com/joonaskuisma/robotframework-dependencysolver/issues). 
For any issues, please create a bug report and reference the version in question. 

If you want to contribute and participate in the project, please read the 
[Developer Guide](README.dev.md) file first.
