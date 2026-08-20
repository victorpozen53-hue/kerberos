/**
 * 🐸 Frogs-Toxic Detection Rules
 * Détection malware type "Grenouille Toxique"
 * 
 * Compatible avec guard_frog_toxic.py
 * 
 * Copyright (C) 2025 Victor Pozen — GPLv3
 * https://github.com/victorpozen/kerberos-security
 */

// ─────────────────────────────────────────────────────────────────────────────
// RÈGLE 1 : Signature PE suspecte + patterns Frog
// ─────────────────────────────────────────────────────────────────────────────
rule Frogs_Toxic_PE_Signature {
    meta:
        description = "Détection exécutable type Frogs-Toxic"
        author = "Victor Pozen — Kerberos Ultimate"
        date = "2025-02-28"
        license = "GPLv3"
        severity = "high"
        reference = "https://github.com/victorpozen/kerberos-security"
        guard_compatible = "guard_frog_toxic.py"
    
    strings:
        // Signature PE (MZ header)
        $mz_header = { 4D 5A }
        
        // Strings suspectes liées à Frogs-Toxic
        $frog_str1 = "frogs_payload" ascii wide
        $frog_str2 = "toxic_inject" ascii wide
        $frog_str3 = "frog_decrypt" ascii wide
        $frog_str4 = "toxic_encrypt" ascii wide
        
        // Patterns de nommage suspect
        $frog_regex = /frog[a-z0-9]{6,}\.exe/i
        $toxic_regex = /toxic[a-z0-9]{6,}\.(exe|dll|bat)/i
        
        // Comportement injection
        $inject_api1 = "VirtualAllocEx" ascii
        $inject_api2 = "WriteProcessMemory" ascii
        $inject_api3 = "CreateRemoteThread" ascii
    
    condition:
        // Fichier PE + 2 strings Frog OU pattern regex + API injection
        $mz_header at 0 and
        (
            (2 of ($frog_str*)) or
            (1 of ($frog_regex, $toxic_regex) and 2 of ($inject_api*))
        ) and
        filesize < 10MB
}

// ─────────────────────────────────────────────────────────────────────────────
// RÈGLE 2 : Comportement Keylogger/Spyware
// ─────────────────────────────────────────────────────────────────────────────
rule Frogs_Toxic_Keylogger_Behavior {
    meta:
        description = "Détection comportement keylogger (Frogs-Toxic variant)"
        author = "Victor Pozen — Kerberos Ultimate"
        license = "GPLv3"
        severity = "critical"
        guard_compatible = "guard_frog_toxic.py"
    
    strings:
        // APIs keylogger
        $key_api1 = "GetAsyncKeyState" ascii
        $key_api2 = "GetKeyState" ascii
        $key_api3 = "SetWindowsHookEx" ascii
        $key_api4 = "GetForegroundWindow" ascii
        
        // APIs capture écran
        $screen_api1 = "BitBlt" ascii
        $screen_api2 = "GetDC" ascii
        $screen_api3 = "CreateCompatibleDC" ascii
        
        // Strings spyware
        $spy_str1 = "keylog" ascii wide
        $spy_str2 = "screenshot" ascii wide
        $spy_str3 = "clipboard" ascii wide
        
        // Fichiers temporaires suspects
        $temp_pattern = /\\Temp\\[a-z0-9]{8,}\.(exe|dll|tmp)/i
    
    condition:
        (
            (2 of ($key_api*)) or
            (2 of ($screen_api*)) or
            (1 of ($spy_str*) and 1 of ($key_api*))
        ) and
        filesize < 5MB
}

// ─────────────────────────────────────────────────────────────────────────────
// RÈGLE 3 : Persistance Registry + Startup
// ─────────────────────────────────────────────────────────────────────────────
rule Frogs_Toxic_Persistence {
    meta:
        description = "Détection mécanismes de persistance Frogs-Toxic"
        author = "Victor Pozen — Kerberos Ultimate"
        license = "GPLv3"
        severity = "high"
        guard_compatible = "guard_frog_toxic.py"
    
    strings:
        // Clés de registre Run
        $reg_run1 = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run" ascii wide
        $reg_run2 = "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\RunOnce" ascii wide
        
        // Tâches planifiées
        $task_str1 = "schtasks" ascii
        $task_str2 = "/create" ascii
        $task_str3 = "/tr" ascii
        
        // Startup folder
        $startup_str = "Startup" ascii wide
        $startup_path = /Start Menu\\Programs\\Startup/i
        
        // Nom Frog/Toxic dans registry
        $frog_reg = /frog[a-z0-9]{4,}/i
        $toxic_reg = /toxic[a-z0-9]{4,}/i
    
    condition:
        (
            ($reg_run1 or $reg_run2) and ($frog_reg or $toxic_reg)
        ) or
        (
            $task_str1 and $task_str2 and $task_str3
        )
}

// ─────────────────────────────────────────────────────────────────────────────
// RÈGLE 4 : Network C2 Communication
// ─────────────────────────────────────────────────────────────────────────────
rule Frogs_Toxic_C2_Communication {
    meta:
        description = "Détection communication C2 (Frogs-Toxic)"
        author = "Victor Pozen — Kerberos Ultimate"
        license = "GPLv3"
        severity = "critical"
        guard_compatible = "guard_frog_toxic.py"
    
    strings:
        // APIs réseau
        $net_api1 = "InternetOpen" ascii
        $net_api2 = "HttpSendRequest" ascii
        $net_api3 = "URLDownloadToFile" ascii
        $net_api4 = "WinHttpOpen" ascii
        
        // Patterns d'URL suspects
        $url_pattern = /https?:\/\/[a-z0-9]{10,}\.(ru|cn|tk|ml|ga)/i
        $ip_pattern = /\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{4,}/
        
        // Encodage base64 (exfiltration)
        $base64_pattern = /[A-Za-z0-9+\/]{50,}={0,2}/
        
        // Strings C2
        $c2_str1 = "beacon" ascii wide
        $c2_str2 = "callback" ascii wide
        $c2_str3 = "exfil" ascii wide
    
    condition:
        (
            (2 of ($net_api*)) and ($url_pattern or $ip_pattern)
        ) or
        (
            (1 of ($c2_str*)) and $base64_pattern
        )
}