*** Settings ***
Resource    ../../resource.robot
#Test Tags    L

*** Test Cases ***
Test L1
    [Tags]    L1    ALL
    Log    message=test
