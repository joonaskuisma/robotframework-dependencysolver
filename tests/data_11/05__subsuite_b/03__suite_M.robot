*** Settings ***
Resource    ../resource.robot
Test Tags    M

*** Test Cases ***
Test M1
    [Tags]    M1
    Log    message=test
