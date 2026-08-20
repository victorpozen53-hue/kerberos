rule Kerberos RAT_Generic {
    meta:
        description = "Détection générique de RAT (Remote Access Trojan)"
        author = "Kerberos Security Team"
        date = "2025-02-22"
        threat_level = "critical"
    
    strings:
        $cmd1 = "cmd.exe /c" ascii wide
        $cmd2 = "powershell -enc" ascii wide
        $cmd3 = "powershell -EncodedCommand" ascii wide
        $shell1 = "reverse_shell" ascii nocase
        $shell2 = "bind_shell" ascii nocase
        $shell3 = "shell_exec" ascii nocase
        $remote1 = "CreateRemoteThread" ascii wide
        $remote2 = "WriteProcessMemory" ascii wide
    
    condition:
        (any 1 of ($cmd1, $cmd2, $cmd3)) or
        (any 2 of ($shell1, $shell2, $shell3)) or
        (any 2 of ($remote1, $remote2))
}

rule Kerberos RAT_Python {
    meta:
        description = "RAT écrit en Python"
        author = "Kerberos Security Team"
        date = "2025-02-22"
        threat_level = "high"
    
    strings:
        $py1 = "import socket" ascii
        $py2 = "import subprocess" ascii
        $py3 = "sock.connect" ascii
        $py4 = "sock.send" ascii
        $py5 = "Popen" ascii
        $py6 = "check_output" ascii
    
    condition:
        (any 2 of ($py1, $py2, $py3, $py4)) and
        (any 1 of ($py5, $py6))
}