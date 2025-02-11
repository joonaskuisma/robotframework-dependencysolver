*** Settings ***
Resource    ../../resource.robot
Test Tags    F

*** Test Cases ***
Test F1
    [Tags]    F1
    Log    message=test
