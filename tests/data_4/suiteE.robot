*** Settings ***
#Test Tags    E
Library  DependencyLibrary

*** Test Cases ***
TestE1
    [Tags]    E1    E
    [Setup]    Depends On Test    name=TestD2
    Log    message=test

TestE2
    [Tags]    E2    E
    [Setup]    Depends On Suite    name=suiteD
    Log    message=test


