rule Kerberos_Password_Stealer {
    meta:
        description = "Détection de voleurs de mots de passe"
        author = "Kerberos Security Team"
        date = "2025-02-22"
        threat_level = "critical"
    
    strings:
        $chrome1 = "Chrome\\Login Data" ascii wide
        $chrome2 = "Chrome\\Web Data" ascii wide
        $firefox1 = "Firefox\\logins.json" ascii wide
        $firefox2 = "Firefox\\key4.db" ascii wide
        $vault = "Windows\\System32\\config\\SAM" ascii wide
        $cred = "Credentials\\Vault" ascii wide
    
    condition:
        (any 1 of ($chrome1, $chrome2)) and
        (any 1 of ($firefox1, $firefox2)) or
        (any 1 of ($vault, $cred))
}

rule Kerberos_Browser_Stealer {
    meta:
        description = "Voleur de données navigateurs"
        author = "Kerberos Security Team"
        date = "2025-02-22"
        threat_level = "high"
    
    strings:
        $browser1 = "Cookies" ascii wide
        $browser2 = "History" ascii wide
        $browser3 = "Local Storage" ascii wide
        $browser4 = "bookmarks" ascii wide
        $extract = "extract" ascii nocase
        $dump = "dump" ascii nocase
    
    condition:
        (any 2 of ($browser1, $browser2, $browser3, $browser4)) and
        (any 1 of ($extract, $dump))
}