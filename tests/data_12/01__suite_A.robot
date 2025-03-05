*** Settings ***
Test Tags    A    all
Library  DependencyLibrary

*** Test Cases ***
Test A 1
    [Tags]    A1    t1
    Log    message=test

Test A 2 long name
    [Tags]    A2    t1
    [Setup]    Depends On Test    name=Test A 1
    Log    message=test

Test_A_3_Name
    [Tags]    A3    t2
    [Setup]    Depends On Test    name=Test A 2 long name
    Log    message=test

Test__A4
    [Tags]    A4    t2
    [Setup]    Depends On Test    name=Test A 2 long name
    Log    message=test

TestA5 name
    [Tags]    A5    t3
    [Setup]    Run Keywords    Depends On Test    name=Test_A_3_Name
    ...    AND    Depends On Test    Test__A4
    Log    message=test

TestA6
    [Tags]    A6    t3
    [Setup]    Depends On Test    tESTa5 NAME
    Log    message=test
