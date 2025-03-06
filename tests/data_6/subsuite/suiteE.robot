*** Settings ***
#Test Tags    G
Library    DependencyLibrary

*** Test Cases ***
TestG1
    [Tags]    G1
    Log    message=test

TestG2
    [Tags]    G2
    Log    message=test