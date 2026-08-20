rule Kerberos_Keylogger_Generic {
    meta:
        description = "Détection générique de keyloggers"
        author = "Kerberos Security Team"
        date = "2025-02-22"
        license = "GPLv3"
        threat_level = "high"
    
    strings:
        $api1 = "SetWindowsHookEx" ascii wide
        $api2 = "GetAsyncKeyState" ascii wide
        $api3 = "GetKeyState" ascii wide
        $api4 = "RegisterHotKey" ascii wide
        $api5 = "keylog" ascii wide nocase
        $api6 = "keystroke" ascii wide nocase
    
    condition:
        (any 2 of ($api1, $api2, $api3, $api4)) or
        (any 2 of ($api5, $api6))
}

rule Kerberos_Keylogger_Python {
    meta:
        description = "Keylogger écrit en Python"
        author = "Kerberos Security Team"
        date = "2025-02-22"
        threat_level = "high"
    
    strings:
        $py1 = "import keyboard" ascii
        $py2 = "import pynput" ascii
        $py3 = "on_press" ascii
        $py4 = "on_release" ascii
        $py5 = "keyboardhook" ascii nocase
        $py6 = "log_key" ascii nocase
    
    condition:
        (any 2 of ($py1, $py2, $py3, $py4)) or
        (any 2 of ($py5, $py6))
}