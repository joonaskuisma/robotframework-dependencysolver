*** Settings ***
Resource    resource.robot
#Test Tags    A

*** Test Cases ***
Test A1
    [Tags]    A1    ALL
    Log    message=test

Test A2
    [Tags]    A2    ALL
    [Setup]    Depends On Test    name=Test A1
    Log    message=test
