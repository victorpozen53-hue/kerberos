rule Kerberos_Downloader_Generic {
    meta:
        description = "Détection de téléchargeurs de malware"
        author = "Kerberos Security Team"
        date = "2025-02-22"
        threat_level = "high"
    
    strings:
        $url1 = "http://" ascii wide
        $url2 = "https://" ascii wide
        $download1 = "URLDownloadToFile" ascii wide
        $download2 = "InternetOpen" ascii wide
        $download3 = "HttpOpenRequest" ascii wide
        $exec1 = "WinExec" ascii wide
        $exec2 = "ShellExecute" ascii wide
        $temp = "%TEMP%" ascii wide
        $tmp = "\\tmp\\" ascii wide
    
    condition:
        (any 1 of ($url1, $url2)) and
        (any 1 of ($download1, $download2, $download3)) and
        (any 1 of ($exec1, $exec2)) and
        (any 1 of ($temp, $tmp))
}