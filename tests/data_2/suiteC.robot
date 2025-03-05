*** Settings ***
#Resource    resource.robot
#Test Tags    testC
Library  DependencyLibrary

*** Test Cases ***
TestC1
    [Tags]    C1    testC
    [Setup]    Depends On Test    name=TestC2
    Log    message=test

TestC2
    [Tags]    C2    testC
    [Setup]    Depends On Test    name=TestC1
    Log    message=test

TestC3
    [Tags]    C3    testC
    [Setup]    Depends On Test    name=TestC3
    Log    message=test
