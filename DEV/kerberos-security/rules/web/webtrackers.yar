/*
 * KERBEROS v4.1 — Règles Trackers Web
 * White hat only • GPLv3 • Local pur
 * Détection comportementale — pas de faux positifs
 */

rule Google_Analytics_Universal {
    meta:
        author = "Victor Pozen"
        k_score = 70
        description = "Google Analytics Universal Analytics (analytics.js)"
        category = "tracker"
    strings:
        $ga1 = "google-analytics.com/analytics.js" nocase
        $ga2 = "www.google-analytics.com/analytics.js" nocase
        $ga3 = "ga('create'" nocase
        $ga4 = "ga('send'" nocase
        $ga5 = "GoogleAnalyticsObject" nocase
    condition:
        2 of ($ga*)
}

rule Google_Analytics_Gtag {
    meta:
        author = "Victor Pozen"
        k_score = 70
        description = "Google Analytics gtag.js (Global Site Tag)"
        category = "tracker"
    strings:
        $gtag1 = "googletagmanager.com/gtag/js" nocase
        $gtag2 = "www.googletagmanager.com/gtag/js" nocase
        $gtag3 = "gtag('js'" nocase
        $gtag4 = "gtag('config'" nocase
        $gtag5 = "dataLayer" nocase
    condition:
        2 of ($gtag*)
}

rule Facebook_Pixel {
    meta:
        author = "Victor Pozen"
        k_score = 75
        description = "Facebook Pixel tracking"
        category = "tracker"
    strings:
        $fb1 = "connect.facebook.net/en_US/fbevents.js" nocase
        $fb2 = "connect.facebook.net/signals/config/" nocase
        $fb3 = "fbq('init'" nocase
        $fb4 = "fbq('track'" nocase
        $fb5 = "_fbq" nocase
    condition:
        2 of ($fb*)
}

rule Hotjar_Tracking {
    meta:
        author = "Victor Pozen"
        k_score = 65
        description = "Hotjar heatmaps & session recording"
        category = "tracker"
    strings:
        $hj1 = "static.hotjar.com/c/hotjar-" nocase
        $hj2 = "hotjar.com/recording" nocase
        $hj3 = "hj('trigger'" nocase
        $hj4 = "_hjSettings" nocase
        $hj5 = "hj('event'" nocase
    condition:
        2 of ($hj*)
}

rule LinkedIn_Insight_Tag {
    meta:
        author = "Victor Pozen"
        k_score = 72
        description = "LinkedIn Insight Tag tracking"
        category = "tracker"
    strings:
        $li1 = "snap.licdn.com/li.lms-analytics/insight.min.js" nocase
        $li2 = "dc.ads.linkedin.com" nocase
        $li3 = "_linkedin_data_partner_id" nocase
        $li4 = "Analytics" nocase
    condition:
        2 of ($li*)
}

rule Twitter_Pixel {
    meta:
        author = "Victor Pozen"
        k_score = 70
        description = "Twitter Universal Website Tag"
        category = "tracker"
    strings:
        $tw1 = "static.ads-twitter.com/uwt.js" nocase
        $tw2 = "analytics.twitter.com" nocase
        $tw3 = "twttr.conversion" nocase
        $tw4 = "twq('track'" nocase
    condition:
        2 of ($tw*)
}

rule Pinterest_Tag {
    meta:
        author = "Victor Pozen"
        k_score = 68
        description = "Pinterest Tag tracking"
        category = "tracker"
    strings:
        $pin1 = "static.pinsight.com/pin.js" nocase
        $pin2 = "ct.pinterest.com" nocase
        $pin3 = "pintrk('track'" nocase
        $pin4 = "_pinData" nocase
    condition:
        2 of ($pin*)
}

rule Amplitude_Tracking {
    meta:
        author = "Victor Pozen"
        k_score = 67
        description = "Amplitude analytics"
        category = "tracker"
    strings:
        $amp1 = "cdn.amplitude.com/libs/amplitude-" nocase
        $amp2 = "amplitude.com" nocase
        $amp3 = "amplitude.getInstance()" nocase
        $amp4 = "logEvent" nocase
    condition:
        2 of ($amp*)
}

rule Mixpanel_Tracking {
    meta:
        author = "Victor Pozen"
        k_score = 66
        description = "Mixpanel analytics"
        category = "tracker"
    strings:
        $mp1 = "cdn.mxpnl.com/libs/mixpanel-" nocase
        $mp2 = "api.mixpanel.com" nocase
        $mp3 = "mixpanel.init" nocase
        $mp4 = "mixpanel.track" nocase
    condition:
        2 of ($mp*)
}

rule Segment_IO {
    meta:
        author = "Victor Pozen"
        k_score = 73
        description = "Segment.io customer data platform"
        category = "tracker"
    strings:
        $seg1 = "cdn.segment.com/analytics.js" nocase
        $seg2 = "cdn.segment.io" nocase
        $seg3 = "analytics.load" nocase
        $seg4 = "analytics.track" nocase
        $seg5 = "segment.com" nocase
    condition:
        2 of ($seg*)
}