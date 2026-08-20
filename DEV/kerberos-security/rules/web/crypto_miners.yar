/*
 * KERBEROS v4.1 — Règles Crypto Miners Malveillants
 * White hat only • GPLv3 • Local pur
 * Score élevé = menace critique
 */

rule Coinhive_CryptoMiner {
    meta:
        author = "Victor Pozen"
        k_score = 95
        description = "Coinhive JavaScript miner (malware)"
        category = "crypto_miner"
    strings:
        $ch1 = "coinhive.com/lib/coinhive.min.js" nocase
        $ch2 = "coinhive.com/captcha" nocase
        $ch3 = "CoinHive.Anonymous" nocase
        $ch4 = "CoinHive.Token" nocase
        $ch5 = "startMining()" nocase
        $ch6 = "stopMining()" nocase
        $ch7 = "isRunning()" nocase
        $ch8 = "getHashesPerSecond()" nocase
    condition:
        2 of ($ch*)
}

rule CryptoLoot_CryptoMiner {
    meta:
        author = "Victor Pozen"
        k_score = 95
        description = "CryptoLoot miner (malware)"
        category = "crypto_miner"
    strings:
        $cl1 = "cryptoloot.pro/lib/miner.min.js" nocase
        $cl2 = "cryptoloot.pro/captcha" nocase
        $cl3 = "CryptoLoot.Anonymous" nocase
        $cl4 = "CryptoLoot.Token" nocase
        $cl5 = "start()" nocase
        $cl6 = "stop()" nocase
    condition:
        2 of ($cl*)
}

rule JSECoin_CryptoMiner {
    meta:
        author = "Victor Pozen"
        k_score = 94
        description = "JSEcoin JavaScript miner"
        category = "crypto_miner"
    strings:
        $jse1 = "load.jsecoin.com" nocase
        $jse2 = "jsecoin.com" nocase
        $jse3 = "jseMiner" nocase
        $jse4 = "startMiner" nocase
    condition:
        2 of ($jse*)
}

rule MinerGate_CryptoMiner {
    meta:
        author = "Victor Pozen"
        k_score = 93
        description = "MinerGate JavaScript miner"
        category = "crypto_miner"
    strings:
        $mg1 = "minergate.com" nocase
        $mg2 = "minergate.me" nocase
        $mg3 = "minergate.start" nocase
        $mg4 = "minergate.stop" nocase
    condition:
        2 of ($mg*)
}

rule AuthedMine_CryptoMiner {
    meta:
        author = "Victor Pozen"
        k_score = 92
        description = "AuthedMine Coinhive fork (requires user consent)"
        category = "crypto_miner"
    strings:
        $am1 = "authedmine.com" nocase
        $am2 = "authedmine.eu" nocase
        $am3 = "AuthedMine.Anonymous" nocase
        $am4 = "AuthedMine.Token" nocase
    condition:
        2 of ($am*)
}

rule WebMine_CryptoMiner {
    meta:
        author = "Victor Pozen"
        k_score = 91
        description = "WebMinePool Coinhive fork"
        category = "crypto_miner"
    strings:
        $wm1 = "webminepool.com" nocase
        $wm2 = "webminepool.tk" nocase
        $wm3 = "webminepool.org" nocase
        $wm4 = "WebMinePool" nocase
    condition:
        2 of ($wm*)
}

rule CoinIMP_CryptoMiner {
    meta:
        author = "Victor Pozen"
        k_score = 90
        description = "CoinIMP Coinhive clone"
        category = "crypto_miner"
    strings:
        $ci1 = "coinimp.com" nocase
        $ci2 = "coinimp.net" nocase
        $ci3 = "CoinIMP" nocase
        $ci4 = "start()" nocase
    condition:
        2 of ($ci*)
}