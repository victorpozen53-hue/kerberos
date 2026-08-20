/*
 * KERBEROS v4.1 — Règles Scripts Malveillants Inline
 * White hat only • GPLv3 • Local pur
 */

rule Obfuscated_JavaScript {
    meta:
        author = "Victor Pozen"
        k_score = 82
        description = "JavaScript fortement obfusqué (souvent malveillant)"
        category = "malicious_script"
    strings:
        $obf1 = "eval(" nocase
        $obf2 = "Function(" nocase
        $obf3 = "String.fromCharCode" nocase
        $obf4 = "atob(" nocase
        $obf5 = "btoa(" nocase
        $obf6 = "unescape(" nocase
        $obf7 = "escape(" nocase
        $obf8 = "base64" nocase
    condition:
        4 of ($obf*)
}

rule DriveBy_Download_Script {
    meta:
        author = "Victor Pozen"
        k_score = 92
        description = "Script qui télécharge automatiquement (drive-by download)"
        category = "malicious_script"
    strings:
        $drive1 = "window.location.href" nocase
        $drive2 = "document.location" nocase
        $drive3 = "iframe" nocase
        $drive4 = "src=" nocase
        $drive5 = ".exe" nocase
        $drive6 = ".zip" nocase
        $drive7 = ".rar" nocase
        $drive8 = "download" nocase
    condition:
        4 of ($drive*)
}

rule XSS_Attack_Script {
    meta:
        author = "Victor Pozen"
        k_score = 88
        description = "Script d'injection XSS (Cross-Site Scripting)"
        category = "malicious_script"
    strings:
        $xss1 = "<script>" nocase
        $xss2 = "document.write" nocase
        $xss3 = "innerHTML" nocase
        $xss4 = "outerHTML" nocase
        $xss5 = "eval(" nocase
        $xss6 = "alert(" nocase
        $xss7 = "prompt(" nocase
        $xss8 = "confirm(" nocase
    condition:
        4 of ($xss*)
}

rule CSRF_Attack_Script {
    meta:
        author = "Victor Pozen"
        k_score = 87
        description = "Script CSRF (Cross-Site Request Forgery)"
        category = "malicious_script"
    strings:
        $csrf1 = "XMLHttpRequest" nocase
        $csrf2 = "fetch(" nocase
        $csrf3 = "POST" nocase
        $csrf4 = "GET" nocase
        $csrf5 = "Cookie" nocase
        $csrf6 = "token" nocase
        $csrf7 = "session" nocase
        $csrf8 = "auth" nocase
    condition:
        4 of ($csrf*)
}

rule Clickjacking_Script {
    meta:
        author = "Victor Pozen"
        k_score = 86
        description = "Script clickjacking (superposition iframe)"
        category = "malicious_script"
    strings:
        $click1 = "iframe" nocase
        $click2 = "opacity" nocase
        $click3 = "z-index" nocase
        $click4 = "position" nocase
        $click5 = "absolute" nocase
        $click6 = "hidden" nocase
        $click7 = "transparent" nocase
        $click8 = "overlay" nocase
    condition:
        4 of ($click*)
}

rule Credential_Stealer_Script {
    meta:
        author = "Victor Pozen"
        k_score = 93
        description = "Script qui vole identifiants (credentials)"
        category = "malicious_script"
    strings:
        $cred1 = "username" nocase
        $cred2 = "password" nocase
        $cred3 = "login" nocase
        $cred4 = "submit" nocase
        $cred5 = "form" nocase
        $cred6 = "onsubmit" nocase
        $cred7 = "send" nocase
        $cred8 = "post" nocase
    condition:
        5 of ($cred*)
}

rule Ransomware_Script {
    meta:
        author = "Victor Pozen"
        k_score = 96
        description = "Script ransomware (chiffrement fichiers)"
        category = "malicious_script"
    strings:
        $ransom1 = "encrypt" nocase
        $ransom2 = "decrypt" nocase
        $ransom3 = "AES" nocase
        $ransom4 = "RSA" nocase
        $ransom5 = "key" nocase
        $ransom6 = "ransom" nocase
        $ransom7 = "bitcoin" nocase
        $ransom8 = "payment" nocase
    condition:
        4 of ($ransom*)
}

rule Spyware_Script {
    meta:
        author = "Victor Pozen"
        k_score = 91
        description = "Script spyware (surveillance utilisateur)"
        category = "malicious_script"
    strings:
        $spy1 = "geolocation" nocase
        $spy2 = "navigator" nocase
        $spy3 = "getUserMedia" nocase
        $spy4 = "camera" nocase
        $spy5 = "microphone" nocase
        $spy6 = "screen" nocase
        $spy7 = "clipboard" nocase
        $spy8 = "track" nocase
    condition:
        4 of ($spy*)
}