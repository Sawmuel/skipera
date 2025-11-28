# https://github.com/serv0id/skipera

BASE_URL = "https://www.coursera.org/api/"
GRAPHQL_URL = "https://www.coursera.org/graphql-gateway"

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_MODEL = "sonar-pro"  # adjust this according to your preference
PERPLEXITY_API_KEY = "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"

HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    'x-coursera-application': 'ondemand',
    'x-coursera-version': '3bfd497de04ae0fef167b747fd85a6fbc8fb55df',
    'x-requested-with': 'XMLHttpRequest',
}

COOKIES = {
    'CAUTH': 'hbEIO3iPdNXTmnu3oadqOUMYF2LkCtdXTc0nokXej5nwF4wLeVv1xA-HrKw6vWcaSZtWCqwkgngox0qbpd4jkQ.VQT0W2snZIMKVwbiqE3EqA.3JfxfL_TcbZhEL8oDb_Yzs4OKicTVRlKVyDlGLqriQ9v9wueEy2nYexj3wm2nTD193WlJ2xIRLIHcywbHVxDYifH07IoWr2Plak9FT6-YjViXMN3XjQELfgw-0C8TDXqRWq_61FZoAsc8A34beQjCCpSD32xoogfgm4DzF9Cx63G9KAE9NEAquFbpI8HxDmthzNQgSLtldzcTjaiV7Snp-rQs_U8jR0GOGianl4uRXOrAm5STcASmmIJ8JDvlOYbo0e7IAZF3TwFQ8v4apDQhAxEGxnmBluBwZbdV6EDdpB8QRPvIwhgtEzOyOpQsEDyh_QGCaeR3cd8_a26ukWJBrrKZnHmro-u6Ndsjg2pONSoQh4fplh_bT2jkX434_f1B7lyc2d3x8UiDtwEddHM5MiM8rZf80gLCjPo_L3iOjDjHVHi1ycq3tSY0LM9iA9ZwBoPWK0Fzs7M6Kx4Yj61VuvKSKFOBecG9UTTk_OS6xs',
    '__204u': '7480175440-1742254135515',
    '__204v': 'a45752f7-ed9b-4f7a-8ece-698f1a0c2c56',
    '__400vt': '1764335592693',
    '_ga': 'GA1.1.839943232.1764305536',
    '_ga_7GZ59JSFWQ': 'GS2.1.s1764335504$o2$g1$t1764335525$j39$l0$h1846662229',
    'FPID': 'FPID2.2.eH1jFOr%2FEAvF6pZNR1iJwx98rBPyEA7spRsrkGKXjfI%3D.1764305536',
    'FPLC': 'kWgaBZf75mOH0imIVX2QuO2pEFCtBINBOaAlHLXkFT6hsMv89zC8Sg0r5GLRV6fX0AsMjujVGlBqaa7zW5sbuIw1gJmIgtx2IqL2J%2BJI6OSH75c1fTUmXO2CMKkb1A%3D%3D',
    'CSRF3-Token' : '1765169506.kdwojv4fvm0Mn0cs',
}

# Credentials
PERPLEXITY_API_KEY = ""
