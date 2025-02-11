*** Settings ***
#Resource    resource.robot
Test Tags    testC
Library  DependencyLibrary

*** Test Cases ***
TestC1
    [Tags]    C1
    [Setup]    Depends On Test    name=TestC2
    Log    message=test

TestC2
    [Tags]    C2
    [Setup]    Depends On Test    name=TestC1
    Log    message=test

TestC3
    [Tags]    C3
    [Setup]    Depends On Test    name=TestC3
    Log    message=test
