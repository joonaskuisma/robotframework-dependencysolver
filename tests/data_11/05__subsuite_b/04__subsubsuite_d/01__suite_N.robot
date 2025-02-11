*** Settings ***
Resource    ../../resource.robot
Test Tags    N

*** Test Cases ***
Test N1
    [Tags]    N1
    Log    message=test
