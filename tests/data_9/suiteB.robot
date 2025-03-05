*** Settings ***
#Test Tags    B
Test Setup    Depends On Suite    suiteA
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
