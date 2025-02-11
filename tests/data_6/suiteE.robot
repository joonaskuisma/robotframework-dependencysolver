*** Settings ***
Test Tags    E
Library  DependencyLibrary

*** Test Cases ***
TestE1
    [Tags]    E1
    Log    message=test

TestE2
    [Tags]    E2
    Log    message=test