*** Settings ***
Resource    ../../resource.robot
#Test Tags    K

*** Test Cases ***
Test K1
    [Tags]    K1    ALL
    Log    message=test
