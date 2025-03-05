*** Settings ***
#Test Tags    D
Library  DependencyLibrary

*** Test Cases ***
TestD1
    [Tags]    D1
    [Setup]    Depends On Suite    name=suiteE
    Log    message=test

TestD2
    [Tags]    D2
    Log    message=test
