*** Setting ***
Resource          resource2.robot
Resource          resource3.robot
Resource          resource.robot

*** Variable ***
${RESOURCE var}    Foo

*** Keyword ***
Resource UK
    [Documentation]    This is a user keyword from resource file
    [Timeout]
    No Operation

Parametrized UK
    [Arguments]    ${arg}    ${defarg}=def val    @{vararg}
    [Timeout]
    Log Many    ${arg}    ${defarg}    @{vararg}

Funny Def Value
    [Arguments]    ${arg}=${None}    ${urg}=${myvar=foo}
    [Timeout]
    Log Many    ${arg}    ${urg}

Duplicate UK
    No Operation
