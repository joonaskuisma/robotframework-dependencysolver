*** Settings ***
Resource    ../resource.robot
#Test Tags    J

*** Test Cases ***
Test J1
    [Tags]    J1    ALL
    Log    message=test
