*** Settings ***
Resource    ../../resource.robot
Test Tags    O

*** Test Cases ***
Test O1
    [Tags]    O1
    Log    message=test
