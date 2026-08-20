/*
 * Trackers : Google Analytics, Facebook Pixel, Hotjar...
 */
rule Google_Analytics_Universal {
    meta: k_score = 70
    strings:
        $ga1 = "google-analytics.com/analytics.js" nocase
        $ga2 = "www.google-analytics.com/analytics.js" nocase
        $ga3 = "ga('create'" nocase
    condition: 2 of ($ga*)
}
rule Facebook_Pixel {
    meta: k_score = 75
    strings:
        $fb1 = "connect.facebook.net/en_US/fbevents.js" nocase
        $fb2 = "fbq('init'" nocase
    condition: any of ($fb*)
}
rule Hotjar_Tracking {
    meta: k_score = 65
    strings:
        $hj1 = "static.hotjar.com/c/hotjar-" nocase
        $hj2 = "hj('trigger'" nocase
    condition: any of ($hj*)
}