*** Settings ***
Resource    ../resource.robot
Test Tags    G

*** Test Cases ***
Test G1
    [Tags]    G1
    [Setup]    Depends On Suite    name=suite B
    Log    message=test
