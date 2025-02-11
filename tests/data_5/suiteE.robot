*** Settings ***
Test Tags    E
Library  DependencyLibrary

*** Test Cases ***
TestD1
    [Tags]    D1
    Log    message=test

TestE2
    [Tags]    E2
    Log    message=test