*** Settings ***
Resource    ../../resource.robot
#Test Tags    C

*** Test Cases ***
Test C1
    [Tags]    C1    ALL
    Log    message=test
