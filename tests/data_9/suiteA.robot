*** Settings ***
#Test Tags    A
Library  DependencyLibrary

*** Test Cases ***
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
