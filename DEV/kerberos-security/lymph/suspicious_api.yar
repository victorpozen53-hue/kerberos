rule Kerberos_Suspicious_API_Windows {
    meta:
        description = "API Windows suspectes (injection, hooking, etc.)"
        author = "Kerberos Security Team"
        date = "2025-02-22"
        threat_level = "medium"
    
    strings:
        $inject1 = "VirtualAllocEx" ascii wide
        $inject2 = "WriteProcessMemory" ascii wide
        $inject3 = "CreateRemoteThread" ascii wide
        $hook1 = "SetWindowsHookEx" ascii wide
        $hook2 = "UnhookWindowsHookEx" ascii wide
        $debug1 = "DebugActiveProcess" ascii wide
        $debug2 = "NtCreateThreadEx" ascii wide
        $hide1 = "ShowWindow" ascii wide
        $hide2 = "SW_HIDE" ascii wide
    
    condition:
        (any 2 of ($inject1, $inject2, $inject3)) or
        (any 2 of ($hook1, $hook2)) or
        (any 1 of ($debug1, $debug2)) or
        (any 2 of ($hide1, $hide2))
}