*** Settings ***
Resource    ../resource.robot
Test Tags    D

*** Test Cases ***
Test D1
    [Tags]    D1
    [Setup]    Depends On Test    name=Test B2
    Log    message=test
