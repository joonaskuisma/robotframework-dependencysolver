*** Settings ***
#Resource    resource.robot
Test Tags    testC
Library  DependencyLibrary

*** Test Cases ***
TestC1
    [Tags]    C1
    Log    message=test

TestC2
    [Tags]    C2
    [Setup]    Depends On Test    name=Test_Does_Not_Exist
    Log    message=test

TestC3
    [Tags]    C3
    [Setup]    Depends On Suite    name=Suite_Does_Not_Exist
    Log    message=test
