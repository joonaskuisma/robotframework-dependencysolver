*** Settings ***
#Test Tags    A    all
Library  DependencyLibrary

*** Test Cases ***
TestA1
    [Tags]    A1    t1    all    A
    Log    message=test

TestA2
    [Tags]    A2    t1    all    A
    [Setup]    Depends On Test    name=TestA1
    Log    message=test

TestA3
    [Tags]    A3    t2    all    A
    [Setup]    Depends On Test    name=TestA2
    Log    message=test

TestA4
    [Tags]    A4    t2    all    A
    [Setup]    Depends On Test    name=TestA2
    Log    message=test

TestA5
    [Tags]    A5    t3    all    A
    [Setup]    Run Keywords    Depends On Test    name=TestA3
    ...    AND    Depends On Test    TestA4
    Log    message=test

TestA6
    [Tags]    A6    t3    all    A
    [Setup]    Depends On Test    TestA5
    Log    message=test
