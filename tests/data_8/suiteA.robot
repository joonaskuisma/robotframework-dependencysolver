*** Settings ***
Test Tags    A
Library  DependencyLibrary

*** Test Cases ***
TestA0
    [Tags]    A0
    Log    message=test

TestA1
    [Tags]    A1
    Log    message=test

TestA2
    [Tags]    A2
    Log    message=test

TestA3
    [Tags]    A3
    [Setup]    Run Keywords    Depends On Test    name=TestA1
    ...    AND    Depends On Test    TestA2
    Log    message=test

TestA4
    [Tags]    A4
    [Setup]    Depends On Test    name=TestA0
    Log    message=test

TestA5
    [Tags]    A5
    Log    message=test

TestA6
    [Tags]    A6
    [Setup]    Depends On Test    TestA5
    Log    message=test

