*** Settings ***
Resource    ../../resource.robot
Test Tags    B
Test Setup    Depends On Test    name=Test B1

*** Test Cases ***
Test B1
    [Tags]    B1
    [Setup]
    Log    message=test

Test B2
    [Tags]    B2
    Log    message=test

Test B3
    [Tags]    B3
    [Setup]    Depends On Test    name=Test B2
    Log    message=test
