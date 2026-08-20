/*
 * KERBEROS v4.1 — Règles Publicités Web
 * White hat only • GPLv3 • Local pur
 */

rule Google_AdSense {
    meta:
        author = "Victor Pozen"
        k_score = 80
        description = "Google AdSense ads"
        category = "ad"
    strings:
        $ads1 = "pagead2.googlesyndication.com/pagead/js/adsbygoogle.js" nocase
        $ads2 = "adsbygoogle.push" nocase
        $ads3 = "google_ad_client" nocase
        $ads4 = "google_ad_slot" nocase
        $ads5 = "google_ad_width" nocase
        $ads6 = "google_ad_height" nocase
    condition:
        3 of ($ads*)
}

rule Taboola_Ads {
    meta:
        author = "Victor Pozen"
        k_score = 75
        description = "Taboola native ads"
        category = "ad"
    strings:
        $tab1 = "cdn.taboola.com/libtrc/" nocase
        $tab2 = "taboola.com/iframe" nocase
        $tab3 = "taboola.com/api" nocase
        $tab4 = "window._taboola" nocase
        $tab5 = "taboola.push" nocase
    condition:
        2 of ($tab*)
}

rule Outbrain_Ads {
    meta:
        author = "Victor Pozen"
        k_score = 75
        description = "Outbrain recommendation widgets"
        category = "ad"
    strings:
        $out1 = "widgets.outbrain.com/outbrain.js" nocase
        $out2 = "outbrain.com/widget" nocase
        $out3 = "outbrain.com/api" nocase
        $out4 = "OB_ADV_ID" nocase
        $out5 = "window._OB" nocase
    condition:
        2 of ($out*)
}

rule RevContent_Ads {
    meta:
        author = "Victor Pozen"
        k_score = 74
        description = "RevContent native ads"
        category = "ad"
    strings:
        $rc1 = "trends.revcontent.com" nocase
        $rc2 = "rcmd.revcontent.com" nocase
        $rc3 = "revcontent.com" nocase
        $rc4 = "window._rc" nocase
    condition:
        2 of ($rc*)
}

rule MGID_Ads {
    meta:
        author = "Victor Pozen"
        k_score = 73
        description = "MGID native ads"
        category = "ad"
    strings:
        $mgid1 = "mgid.com" nocase
        $mgid2 = "cm.mgid.com" nocase
        $mgid3 = "mgid.push" nocase
        $mgid4 = "window.mgid" nocase
    condition:
        2 of ($mgid*)
}

rule Bidvertiser_Ads {
    meta:
        author = "Victor Pozen"
        k_score = 72
        description = "Bidvertiser ads network"
        category = "ad"
    strings:
        $bid1 = "bdv.bidvertiser.com" nocase
        $bid2 = "bidvertiser.com" nocase
        $bid3 = "bidv.push" nocase
    condition:
        2 of ($bid*)
}

rule PropellerAds_Ads {
    meta:
        author = "Victor Pozen"
        k_score = 71
        description = "PropellerAds popunder/native ads"
        category = "ad"
    strings:
        $prop1 = "propellerads.com" nocase
        $prop2 = "propellerads.net" nocase
        $prop3 = "propeller.pop" nocase
        $prop4 = "window.propeller" nocase
    condition:
        2 of ($prop*)
}

rule PopAds_Ads {
    meta:
        author = "Victor Pozen"
        k_score = 76
        description = "PopAds popunder ads"
        category = "ad"
    strings:
        $pop1 = "popads.net" nocase
        $pop2 = "popads.direct" nocase
        $pop3 = "popunder" nocase
        $pop4 = "window.popns" nocase
    condition:
        2 of ($pop*)
}

rule Adsterra_Ads {
    meta:
        author = "Victor Pozen"
        k_score = 70
        description = "Adsterra popunder/banner ads"
        category = "ad"
    strings:
        $adst1 = "adsterra.com" nocase
        $adst2 = "adsterra.net" nocase
        $adst3 = "adst.pop" nocase
    condition:
        2 of ($adst*)
}