*** Settings ***
Resource    ../../resource.robot
Suite Setup    Run Keywords    Depends On Suite    suite E
...    AND    Depends On Suite    suite F