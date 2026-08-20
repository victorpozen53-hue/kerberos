/*
 * KERBEROS v4.1 — Règles Extensions Malveillantes Navigateurs
 * White hat only • GPLv3 • Local pur
 */

rule Browser_Hijacker_Extension {
    meta:
        author = "Victor Pozen"
        k_score = 90
        description = "Extension qui modifie la page d'accueil/search"
        category = "malicious_extension"
    strings:
        $hijack1 = "chrome_settings_overrides" nocase
        $hijack2 = "homepage_url" nocase
        $hijack3 = "search_provider" nocase
        $hijack4 = "default_search_provider" nocase
        $hijack5 = "new_tab_page" nocase
        $hijack6 = "override" nocase
    condition:
        3 of ($hijack*)
}

rule Adware_Extension {
    meta:
        author = "Victor Pozen"
        k_score = 85
        description = "Extension qui injecte des pubs"
        category = "malicious_extension"
    strings:
        $adware1 = "content_scripts" nocase
        $adware2 = "matches" nocase
        $adware3 = "*://*/*" nocase
        $adware4 = "run_at" nocase
        $adware5 = "document_end" nocase
        $adware6 = "document_start" nocase
        $adware7 = "js" nocase
        $adware8 = "inject" nocase
    condition:
        5 of ($adware*)
}

rule Keylogger_Extension {
    meta:
        author = "Victor Pozen"
        k_score = 95
        description = "Extension keylogger (capture clavier)"
        category = "malicious_extension"
    strings:
        $key1 = "chrome.input.ime" nocase
        $key2 = "onKeyPress" nocase
        $key3 = "addEventListener" nocase
        $key4 = "keydown" nocase
        $key5 = "keyup" nocase
        $key6 = "keypress" nocase
        $key7 = "send" nocase
        $key8 = "log" nocase
    condition:
        4 of ($key*)
}

rule Data_Stealer_Extension {
    meta:
        author = "Victor Pozen"
        k_score = 93
        description = "Extension qui vole données (cookies, passwords)"
        category = "malicious_extension"
    strings:
        $steal1 = "chrome.cookies" nocase
        $steal2 = "chrome.passwords" nocase
        $steal3 = "chrome.history" nocase
        $steal4 = "chrome.bookmarks" nocase
        $steal5 = "chrome.tabs" nocase
        $steal6 = "chrome.storage" nocase
        $steal7 = "send" nocase
        $steal8 = "post" nocase
    condition:
        3 of ($steal*)
}

rule Redirect_Extension {
    meta:
        author = "Victor Pozen"
        k_score = 88
        description = "Extension qui redirige vers sites malveillants"
        category = "malicious_extension"
    strings:
        $redir1 = "chrome.webNavigation" nocase
        $redir2 = "onBeforeNavigate" nocase
        $redir3 = "onCommitted" nocase
        $redir4 = "redirectUrl" nocase
        $redir5 = "http://" nocase
        $redir6 = "https://" nocase
        $redir7 = "replace" nocase
    condition:
        4 of ($redir*)
}

rule Fake_Antivirus_Extension {
    meta:
        author = "Victor Pozen"
        k_score = 89
        description = "Extension fausse antivirus (scareware)"
        category = "malicious_extension"
    strings:
        $fake1 = "virus" nocase
        $fake2 = "malware" nocase
        $fake3 = "threat" nocase
        $fake4 = "scan" nocase
        $fake5 = "detected" nocase
        $fake6 = "remove" nocase
        $fake7 = "clean" nocase
        $fake8 = "warning" nocase
    condition:
        5 of ($fake*)
}

rule Cryptojacking_Extension {
    meta:
        author = "Victor Pozen"
        k_score = 94
        description = "Extension qui mine cryptos en arrière-plan"
        category = "malicious_extension"
    strings:
        $crypto1 = "miner" nocase
        $crypto2 = "hash" nocase
        $crypto3 = "worker" nocase
        $crypto4 = "webworker" nocase
        $crypto5 = "start" nocase
        $crypto6 = "stop" nocase
        $crypto7 = "cpu" nocase
        $crypto8 = "hashes" nocase
    condition:
        4 of ($crypto*)
}