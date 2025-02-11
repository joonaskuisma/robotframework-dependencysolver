*** Settings ***
Resource    ../../resource.robot
Test Tags    O
Test Setup    Depends On Suite    name=Suite K

*** Test Cases ***
Test O1
    [Tags]    O1
    Log    message=test
