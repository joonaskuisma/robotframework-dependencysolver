*** Settings ***
Resource    resource.robot
#Test Tags    P

*** Test Cases ***
Test P1
    [Tags]    P1    ALL
    Log    message=test