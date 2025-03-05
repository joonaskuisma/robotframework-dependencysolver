*** Settings ***
Resource    resource.robot
#Test Tags    I

*** Test Cases ***
Test I1
    [Tags]    I1    ALL
    Log    message=test