rule Kerberos_CryptoMiner_Generic {
    meta:
        description = "Détection de mineurs de cryptomonnaie"
        author = "Kerberos Security Team"
        date = "2025-02-22"
        threat_level = "medium"
    
    strings:
        $pool1 = "stratum+tcp://" ascii
        $pool2 = "stratum://" ascii
        $pool3 = "cryptonight" ascii nocase
        $pool4 = "moneropool" ascii nocase
        $pool5 = "nicehash" ascii nocase
        $miner1 = "cpu_miner" ascii nocase
        $miner2 = "gpu_miner" ascii nocase
        $miner3 = "xmrig" ascii nocase
    
    condition:
        (any 1 of ($pool1, $pool2, $pool3, $pool4, $pool5)) or
        (any 1 of ($miner1, $miner2, $miner3))
}