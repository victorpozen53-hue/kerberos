/**
 * 🫧 Bubble Shield Detection Rules
 * Détection menaces contre lesquelles Plasma/Bubble Shield protège
 * 
 * Compatible avec guard_plasma_shield.py
 * 
 * Copyright (C) 2025 Victor Pozen — GPLv3
 * https://github.com/victorpozen/kerberos-security
 */

// ─────────────────────────────────────────────────────────────────────────────
// RÈGLE 1 : Injection Mémoire (Bubble Shield Core)
// ─────────────────────────────────────────────────────────────────────────────
rule Bubble_Shield_Memory_Injection {
    meta:
        description = "Détection injection mémoire — protection Bubble Shield"
        author = "Victor Pozen — Kerberos Ultimate"
        date = "2025-02-28"
        license = "GPLv3"
        severity = "critical"
        reference = "https://github.com/victorpozen/kerberos-security"
        guard_compatible = "guard_plasma_shield.py"
    
    strings:
        // APIs injection classique
        $inject1 = "VirtualAllocEx" ascii
        $inject2 = "WriteProcessMemory" ascii
        $inject3 = "CreateRemoteThread" ascii
        $inject4 = "NtCreateThreadEx" ascii
        $inject5 = "RtlCreateUserThread" ascii
        
        // Shellcode patterns (NOP sleds)
        $nop_sled = { 90 90 90 90 90 90 90 90 }
        
        // Pattern shellcode Windows commun
        $shellcode_pattern = { 60 68 ?? ?? ?? ?? E8 ?? ?? ?? ?? 61 }
        
        // Processus système ciblés
        $target_proc1 = "lsass.exe" ascii wide
        $target_proc2 = "svchost.exe" ascii wide
        $target_proc3 = "explorer.exe" ascii wide
        $target_proc4 = "winlogon.exe" ascii wide
    
    condition:
        (
            (3 of ($inject*)) and (1 of ($target_proc*))
        ) or
        (
            $nop_sled and (2 of ($inject*))
        ) or
        $shellcode_pattern
}

// ─────────────────────────────────────────────────────────────────────────────
// RÈGLE 2 : Hooks Clavier/Souris (Keylogger Detection)
// ─────────────────────────────────────────────────────────────────────────────
rule Bubble_Shield_Hook_Detection {
    meta:
        description = "Détection hooks clavier/souris — protection Bubble Shield"
        author = "Victor Pozen — Kerberos Ultimate"
        license = "GPLv3"
        severity = "high"
        guard_compatible = "guard_plasma_shield.py"
    
    strings:
        // Hook APIs
        $hook_api1 = "SetWindowsHookEx" ascii
        $hook_api2 = "SetWinEventHook" ascii
        $hook_api3 = "GetAsyncKeyState" ascii
        $hook_api4 = "GetKeyState" ascii
        $hook_api5 = "MapVirtualKey" ascii
        
        // Hook types suspects
        $hook_type1 = "WH_KEYBOARD_LL" ascii
        $hook_type2 = "WH_MOUSE_LL" ascii
        $hook_type3 = "WH_GETMESSAGE" ascii
        
        // DLLs de hook connues
        $hook_dll1 = "hookapi.dll" ascii wide
        $hook_dll2 = "keyhook.dll" ascii wide
        $hook_dll3 = "spy.dll" ascii wide
        
        // Pattern nom suspect
        $suspicious_name = /(hook|spy|logger|record|capture|stealth)[a-z0-9]{4,}\.(dll|exe)/i
    
    condition:
        (
            $hook_api1 and ($hook_type1 or $hook_type2)
        ) or
        (
            (2 of ($hook_api*)) and (1 of ($hook_dll*) or $suspicious_name)
        )
}

// ─────────────────────────────────────────────────────────────────────────────
// RÈGLE 3 : Screenshot Automatique (Spyware)
// ─────────────────────────────────────────────────────────────────────────────
rule Bubble_Shield_Screenshot_Spyware {
    meta:
        description = "Détection capture écran automatique — protection Bubble Shield"
        author = "Victor Pozen — Kerberos Ultimate"
        license = "GPLv3"
        severity = "high"
        guard_compatible = "guard_plasma_shield.py"
    
    strings:
        // APIs capture
        $capture_api1 = "BitBlt" ascii
        $capture_api2 = "GetDC" ascii
        $capture_api3 = "CreateCompatibleDC" ascii
        $capture_api4 = "SelectObject" ascii
        $capture_api5 = "GetWindowDC" ascii
        
        // Formats image
        $img_header_png = { 89 50 4E 47 0D 0A 1A 0A }
        $img_header_jpg = { FF D8 FF }
        $img_header_bmp = { 42 4D }
        
        // Paths de sortie suspects
        $output_path1 = "\\Screenshots\\" ascii wide
        $output_path2 = "\\Capture\\" ascii wide
        $output_path3 = "\\Temp\\" ascii wide
        
        // Timer pour capture auto
        $timer_api1 = "SetTimer" ascii
        $timer_api2 = "CreateTimerQueueTimer" ascii
    
    condition:
        (
            (3 of ($capture_api*)) and ($img_header_png or $img_header_jpg or $img_header_bmp)
        ) or
        (
            (2 of ($capture_api*)) and ($timer_api1 or $timer_api2) and (1 of ($output_path*))
        )
}

// ─────────────────────────────────────────────────────────────────────────────
// RÈGLE 4 : Fileless Malware (Sans Fichier)
// ─────────────────────────────────────────────────────────────────────────────
rule Bubble_Shield_Fileless_Malware {
    meta:
        description = "Détection malware fileless — protection Bubble Shield"
        author = "Victor Pozen — Kerberos Ultimate"
        license = "GPLv3"
        severity = "critical"
        guard_compatible = "guard_plasma_shield.py"
    
    strings:
        // PowerShell commands suspects
        $ps_cmd1 = "powershell -enc" ascii wide
        $ps_cmd2 = "-EncodedCommand" ascii wide
        $ps_cmd3 = "Invoke-Expression" ascii wide
        $ps_cmd4 = "IEX(" ascii wide
        $ps_cmd5 = "DownloadString" ascii wide
        
        // WMI execution
        $wmi_cmd1 = "Win32_Process" ascii wide
        $wmi_cmd2 = "Create(" ascii
        $wmi_cmd3 = "wmic process call create" ascii wide
        
        // Memory-only patterns
        $mem_alloc1 = "MEM_COMMIT" ascii
        $mem_alloc2 = "PAGE_EXECUTE_READWRITE" ascii
        $mem_alloc3 = "VirtualProtect" ascii
        
        // Base64 encoded payloads
        $b64_long = /[A-Za-z0-9+\/]{100,}={0,2}/
    
    condition:
        (
            (1 of ($ps_cmd*)) and $b64_long
        ) or
        (
            (1 of ($wmi_cmd*)) and (1 of ($mem_alloc*))
        ) or
        (
            $mem_alloc1 and $mem_alloc2 and $mem_alloc3
        )
}

// ─────────────────────────────────────────────────────────────────────────────
// RÈGLE 5 : Processus Enfant Suspect (Parent Spoofing)
// ─────────────────────────────────────────────────────────────────────────────
rule Bubble_Shield_Suspicious_Child_Process {
    meta:
        description = "Détection processus enfant suspect — protection Bubble Shield"
        author = "Victor Pozen — Kerberos Ultimate"
        license = "GPLv3"
        severity = "high"
        guard_compatible = "guard_plasma_shield.py"
    
    strings:
        // Processus système souvent spoofés
        $parent_sys1 = "explorer.exe" ascii wide
        $parent_sys2 = "svchost.exe" ascii wide
        $parent_sys3 = "services.exe" ascii wide
        
        // Enfants suspects
        $child_sus1 = "cmd.exe" ascii wide
        $child_sus2 = "powershell.exe" ascii wide
        $child_sus3 = "mshta.exe" ascii wide
        $child_sus4 = "wscript.exe" ascii wide
        $child_sus5 = "cscript.exe" ascii wide
        $child_sus6 = "regsvr32.exe" ascii wide
        
        // APIs de création processus
        $create_api1 = "CreateProcess" ascii
        $create_api2 = "CreateProcessAsUser" ascii
        $create_api3 = "ShellExecute" ascii
        
        // Flags de dissimulation
        $hide_flag1 = "CREATE_NO_WINDOW" ascii
        $hide_flag2 = "SW_HIDE" ascii
    
    condition:
        (
            (1 of ($parent_sys*)) and (1 of ($child_sus*)) and (1 of ($create_api*))
        ) or
        (
            (1 of ($child_sus*)) and ($hide_flag1 or $hide_flag2)
        )
}