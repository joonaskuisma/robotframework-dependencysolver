*** Settings ***
Resource    resource.robot
Test Tags    P
#Suite Setup    Depends On Suite    suite O
#Suite Setup    Depends On Suite    name=subsubsuite 1

*** Test Cases ***
Test P1
    [Tags]    P1
    [Setup]    Depends On Suite    name=subsubsuite D
    Log    message=test