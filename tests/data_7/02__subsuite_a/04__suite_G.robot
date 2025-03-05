*** Settings ***
Resource    ../resource.robot
#Test Tags    G

*** Test Cases ***
Test G1
    [Tags]    G1    ALL
    [Setup]    Depends On Suite    name=suite B
    Log    message=test
