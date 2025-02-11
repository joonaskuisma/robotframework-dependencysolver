*** Settings ***
Resource    ../../resource.robot
Test Tags    E

*** Test Cases ***
Test E1
    [Tags]    E1
    Log    message=test
