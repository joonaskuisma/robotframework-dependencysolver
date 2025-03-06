*** Settings ***
Resource    resource.robot
#Test Tags    H

*** Test Cases ***
Test H1
    [Tags]    H1    ALL
    Log    message=test