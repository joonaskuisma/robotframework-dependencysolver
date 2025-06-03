*** Settings ***
Test Tags    ALL
Library    DependencyLibrary

*** Variables ***
# These variables will present a whole system global state in this simple example.
${TEXT}    Nothing done yet.
${TEXT1}    Nothing done yet.
${TEXT2}    Nothing done yet.
${TEXT3}    Nothing done yet.

*** Test Cases ***
Test A1
    [Tags]    A1
    Should Be Equal    first=${TEXT}    second=Nothing done yet.
    VAR    ${TEXT}    A1 ready.    scope=GLOBAL
    Should Be Equal    first=${TEXT}    second=A1 ready.

Test A2
    [Tags]    A2
    [Setup]    Depends On Test    name=Test A1
    Should Be Equal    first=${TEXT}    second=A1 ready.
    VAR    ${TEXT}    A2 ready.    scope=GLOBAL
    Should Be Equal    first=${TEXT}    second=A2 ready.

Test A3
    [Tags]    A3
    [Setup]    Depends On Test    name=Test A2
    Should Be Equal    first=${TEXT}    second=A2 ready.
    VAR    ${TEXT}    A3 ready.    scope=GLOBAL
    Should Be Equal    first=${TEXT}    second=A3 ready.

Test A4
    [Tags]    A4
    [Setup]    Depends On Test    name=Test A3
    Should Be Equal    first=${TEXT}    second=A3 ready.
    VAR    ${TEXT}    A4 ready.    scope=GLOBAL
    Should Be Equal    first=${TEXT}    second=A4 ready.

Test A5
    [Tags]    A5
    Log    This test is independent.

Test A6
    [Tags]    A6
    Log    This test is independent.

Test A7
    [Tags]    A7
    Log    This test is independent.

Test A8
    [Tags]    A8
    Should Be Equal    first=${TEXT1}    second=Nothing done yet.
    Should Be Equal    first=${TEXT2}    second=Nothing done yet.
    Should Be Equal    first=${TEXT3}    second=Nothing done yet.
    VAR    ${TEXT1}    A8 ready.    scope=GLOBAL
    VAR    ${TEXT2}    A8 ready.    scope=GLOBAL
    VAR    ${TEXT3}    A8 ready.    scope=GLOBAL
    Should Be Equal    first=${TEXT1}    second=A8 ready.
    Should Be Equal    first=${TEXT2}    second=A8 ready.
    Should Be Equal    first=${TEXT3}    second=A8 ready.

Test A9
    [Tags]    A9
    [Setup]    Depends On Test    name=Test A8
    Should Be Equal    first=${TEXT1}    second=A8 ready.
    VAR    ${TEXT1}    A9 ready.    scope=GLOBAL
    Should Be Equal    first=${TEXT1}    second=A9 ready.

Test A10
    [Tags]    A10
    [Setup]    Depends On Test    name=Test A8
    Should Be Equal    first=${TEXT2}    second=A8 ready.
    VAR    ${TEXT2}    A10 ready.    scope=GLOBAL
    Should Be Equal    first=${TEXT2}    second=A10 ready.

Test A11
    [Tags]    A11
    [Setup]    Depends On Test    name=Test A8
    Should Be Equal    first=${TEXT3}    second=A8 ready.
    VAR    ${TEXT3}    A11 ready.    scope=GLOBAL
    Should Be Equal    first=${TEXT3}    second=A11 ready.

Test A12
    [Tags]    A12
    [Setup]    Run Keywords    Depends On Test    name=Test A9
    ...    AND    Depends On Test    name=Test A10
    ...    AND    Depends On Test    name=Test A11
    Should Be Equal    first=${TEXT1}    second=A9 ready.
    Should Be Equal    first=${TEXT2}    second=A10 ready.
    Should Be Equal    first=${TEXT3}    second=A11 ready.
