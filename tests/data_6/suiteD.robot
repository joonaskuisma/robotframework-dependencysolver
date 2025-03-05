*** Settings ***
#Test Tags    D
Library  DependencyLibrary

*** Test Cases ***
TestD1
    [Tags]    D1    D
    Log    message=test

TestD2
    [Tags]    D2    D
    Log    message=test