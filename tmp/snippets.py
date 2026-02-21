import re, sys, textwrap
from urllib.request import Request, urlopen

def fetch(url):
    req = Request(url, headers={"User-Agent":"Mozilla/5.0"})
    with urlopen(req, timeout=30) as r:
        return r.read().decode('utf-8','replace')

def strip_html(html):
    # crude tag stripper
    html = re.sub(r"(?is)<(script|style).*?>.*?</\\1>", " ", html)
    txt = re.sub(r"(?s)<.*?>", " ", html)
    txt = re.sub(r"&nbsp;", " ", txt)
    txt = re.sub(r"&amp;", "&", txt)
    txt = re.sub(r"&#39;", "'", txt)
    txt = re.sub(r"&quot;", '"', txt)
    txt = re.sub(r"\s+", " ", txt)
    return txt.strip()

def snippet(text, terms, window=200):
    low = text.lower()
    for term in terms:
        i = low.find(term.lower())
        if i!=-1:
            a = max(0, i-window)
            b = min(len(text), i+window)
            return text[a:b]
    return text[:400]

items = [
    ("CRA SR&ED main", "https://www.canada.ca/en/revenue-agency/services/scientific-research-experimental-development-tax-incentive-program.html", ["investment tax credit", "SR&ED", "scientific research" ]),
    ("CRA SR&ED overview", "https://www.canada.ca/en/revenue-agency/services/scientific-research-experimental-development-tax-incentive-program/sred-overview.html", ["35%", "3 million", "CCPC", "investment tax credit"]),
    ("Canada Health Act", "https://laws-lois.justice.gc.ca/eng/acts/C-6/", ["Canada Health Act", "insured health services"]),
    ("Health care system (HC)", "https://www.canada.ca/en/health-canada/services/canada-health-care-system.html", ["publicly funded", "Canada's health care system"]),
    ("Finance tax expenditures", "https://www.canada.ca/en/department-finance/services/publications/tax-expenditures.html", ["Tax expenditures", "report"]),
    ("CitizensInformation Ireland corp tax", "https://www.citizensinformation.ie/en/money-and-tax/tax/business-taxes-and-levies/corporation-tax/", ["12.5", "corporation tax"]),
    ("IDA Ireland corporate tax", "https://www.idaireland.com/invest-in-ireland/why-ireland/corporate-tax", ["12.5", "corporate tax"]),
]

for name,url,terms in items:
    try:
        html = fetch(url)
        txt = strip_html(html)
        snip = snippet(txt, terms)
        print("\n===",name,"===\nURL:",url,"\nSNIP:")
        print(textwrap.fill(snip, 110))
    except Exception as e:
        print("\n===",name,"===\nURL:",url,"\nERROR:",e)
