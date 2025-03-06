*** Settings ***
Resource    ../resource.robot
#Test Tags    D

*** Test Cases ***
Test D1
    [Tags]    D1    ALL
    [Setup]    Depends On Test    name=Test B2
    Log    message=test
