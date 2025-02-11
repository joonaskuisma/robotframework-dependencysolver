*** Settings ***
#Resource    resource.robot
Test Tags    B
Library  DependencyLibrary

*** Test Cases ***
TestB1
    [Tags]    B1
    Log    message=test

TestB2
    [Tags]    B2
    Log    message=test

TestB3
    [Tags]    B3
    Log    message=test

TestB4
    [Tags]    B4
    [Setup]    Depends On Test    name=TestB3
    Log    message=test

TestB5
    [Tags]    B5
    [Setup]    Run Keywords    Depends On Test    name=TestB1
    ...    AND    Depends On Test    TestA2
    ...    AND    Depends On Test    TestA0
    Log    message=test

TestB6
    [Tags]    B6
    Log    message=test

