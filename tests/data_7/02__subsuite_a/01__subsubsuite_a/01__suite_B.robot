*** Settings ***
Resource    ../../resource.robot
#Test Tags    B

*** Test Cases ***
Test B1
    [Tags]    B1    ALL
    [Setup]    Depends On Suite    name=suite A
    Log    message=test

Test B2
    [Tags]    B2    ALL
    [Setup]    Depends On Test    name=Test A1
    Log    message=test
    Fail    msg=This will fail

Test B3
    [Tags]    B3    ALL
    Log    message=test
