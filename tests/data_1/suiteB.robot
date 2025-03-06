*** Settings ***
#Resource    resource.robot
#Test Tags    testB    all
Library  DependencyLibrary

*** Test Cases ***
TestB1
    [Tags]    B1    t1    all    testB
    [Setup]    Depends On Test    name=TestA5
    Log    message=test

TestB2
    [Tags]    B2    t1    all    testB
    [Setup]    Depends On Test    name=TestB1
    Log    message=test

TestB3
    [Tags]    B3    t2    all    testB
    [Setup]    Depends On Test    name=TestB2
    Log    message=test

TestB4
    [Tags]    B4    t2    all    testB
    [Setup]    Depends On Test    name=TestB2
    Log    message=test

TestB5
    [Tags]    B5    t3    all    testB
    [Setup]    Run Keywords    Depends On Test    name=TestB3
    ...    AND    Depends On Test    TestB4
    Log    message=test

TestB6
    [Tags]    B6    t3    all    testB
    [Setup]    Depends On Test    TestB5
    Log    message=test

