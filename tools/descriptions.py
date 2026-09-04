"""Derive concise descriptions for Evilwiki pages."""
import re
from urllib.parse import urlparse

DEFAULT_PAGE_TEXTS={
 'describe the new page here.',
 'beschreibe hier die neue seite.',
 'describe the new page here',
 'beschreibe hier die neue seite',
}
GENERIC_TINY={'hello','hi','test','testing','a','new page','newpage','wiki','ok','foo','bar'}

FAMILY_LABELS={
 'source-cache-url-list':'source/cache reference page',
 'relay-coordination':'coordination/relay page',
 'source-or-unclassified':'research/source page',
 'off_store_unclassified':'miscellaneous stored page',
 'loop-chain-infrastructure':'automated loop-chain page',
 'probe-test':'probe/test page',
 'unknown':'wiki page',
 'mixed-task':'mixed research/task page',
}
TOPIC_OVERRIDES={
 'oecd-equity':'OECD equity data',
 'oecd-regional-co2':'OECD regional CO₂ data',
 'oecd-household-income':'OECD household-income data',
 'datausa-clothing-workforce':'Data USA clothing-workforce data',
 'datausa-grocery-workforce':'Data USA grocery-workforce data',
 'datausa-cashiers-masters':"Data USA cashiers' master's-degree data",
 'datausa-cashiers-bachelors':"Data USA cashiers' bachelor's-degree data",
 'datausa-cashier-skills':'Data USA cashier-skills data',
 'datausa-construction-workforce':'Data USA construction-workforce data',
 'datausa-construction-wage':'Data USA construction-wage data',
 'datausa-sector61-state':'Data USA sector-61 state data',
 'datausa-language-french':'Data USA French-language data',
 'datausa-poverty-county':'Data USA county poverty data',
 'datausa-poverty-state':'Data USA state poverty data',
 'datausa-maids-wage':'Data USA maids-wage data',
 'datausa-police-wage-age':'Data USA police wage-by-age data',
 'datausa-finance-gender-gap':'Data USA finance gender-gap data',
 'datausa-occupation-salary-61-62':'Data USA occupation salary data for sectors 61–62',
 'datausa-transport-production':'Data USA transport/production data',
 'datausa-production-share':'Data USA production-share data',
 'datausa-slp-ethnicity':'Data USA speech-language-pathology ethnicity data',
 'datausa-ivy-tuition':'Data USA Ivy League tuition data',
 'datausa-elpaso-foreign-born':'Data USA El Paso foreign-born population data',
 'datausa-enrollment-asian':'Data USA Asian enrollment data',
 'ihme-cvd-deaths':'IHME cardiovascular-disease deaths data',
 'ihme-family-planning':'IHME family-planning data',
 'ihme-mcv2':'IHME MCV2 immunization data',
 'ihme-smoking':'IHME smoking data',
 'ihme-lymphatic-filariasis':'IHME lymphatic-filariasis data',
 'aihw-pbs':'AIHW PBS data',
 'nyc-veterans':'New York City veterans data',
 'vermont-rent':'Vermont rent data',
 'uefa-pass-accuracy':'UEFA pass-accuracy data',
 'fuel-poverty-ni':'Northern Ireland fuel-poverty data',
 'dataafrica-health-stunting':'Data Africa health/stunting data',
 'dataafrica-rainfed-crops':'Data Africa rainfed-crops data',
 'gapminder-age80':'Gapminder age-80 data',
 'alaska-climate':'Alaska climate data',
 'sdg-index-score':'SDG Index score data',
 'unaids-bosnia-hiv':'UNAIDS Bosnia HIV data',
 'world-poverty-clock':'World Poverty Clock data',
}

def humanize_name(name):
    s=str(name or '').replace('_',' ').replace('/',' / ')
    # split camelCase / acronym boundaries and letters-digits
    s=re.sub(r'(?<=[a-z0-9])(?=[A-Z])',' ',s)
    s=re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])',' ',s)
    s=re.sub(r'(?<=[A-Za-z])(?=\d)',' ',s)
    s=re.sub(r'(?<=\d)(?=[A-Za-z])',' ',s)
    s=re.sub(r'[-]+',' ',s)
    return re.sub(r'\s+',' ',s).strip()

def prefix_for(name):
    n=str(name or '').strip()
    if not n: return '#'
    c=n[0]
    if c.isalpha(): return c.upper()
    if c.isdigit(): return '0–9'
    return '#'

def domains_in(text):
    out=[]
    for raw in re.findall(r'https?://[^\s\]\)>"\']+', text or '', flags=re.I):
        try:
            host=urlparse(raw.rstrip('.,;:')).netloc.lower()
        except Exception:
            host=''
        if host.startswith('www.'): host=host[4:]
        if host and host not in out: out.append(host)
    return out

def clean_markup(text):
    s=str(text or '')
    s=re.sub(r'\[pre-2026 line withheld\]',' ',s,flags=re.I)
    # external wiki links: [URL label] -> label, [URL] -> URL
    s=re.sub(r'\[(https?://[^\s\]]+)\s+([^\]]+)\]',lambda m:m.group(2),s)
    s=re.sub(r'\[\[(?:[^\]|]+\|)?([^\]]+)\]\]',lambda m:m.group(1),s)
    s=re.sub(r'<[^>]+>',' ',s)
    s=re.sub(r'^\s*=+\s*(.*?)\s*=+\s*$',r'\1',s,flags=re.M)
    s=re.sub(r'^\s*[*#:;]+\s*','',s,flags=re.M)
    s=s.replace("'''",'').replace("''",'')
    return re.sub(r'\s+',' ',s).strip()

def meaningful_excerpt(body, limit=190):
    raw=str(body or '')
    lines=[]
    for line in raw.replace('\r','\n').split('\n'):
        line=line.strip()
        if not line: continue
        low=line.casefold().strip(' .!')
        if low in DEFAULT_PAGE_TEXTS or low in GENERIC_TINY: continue
        if re.fullmatch(r'=+.*=+',line):
            line=line.strip('= ').strip()
        clean=clean_markup(line)
        lowc=clean.casefold().strip(' .!')
        if not clean or lowc in DEFAULT_PAGE_TEXTS or lowc in GENERIC_TINY: continue
        alpha=sum(ch.isalpha() for ch in clean)
        if len(clean)>=14 and alpha>=5:
            lines.append(clean)
    if not lines:
        clean=clean_markup(raw)
        low=clean.casefold().strip(' .!')
        if clean and low not in DEFAULT_PAGE_TEXTS and low not in GENERIC_TINY and len(clean)>=14:
            lines=[clean]
    if not lines: return ''
    text=lines[0]
    # avoid body beginning with a raw URL when later prose exists
    if text.lower().startswith(('http://','https://')) and len(lines)>1:
        text=lines[1]
    # trim long noisy token trains to first sentence or clause
    sent=re.split(r'(?<=[.!?])\s+', text, maxsplit=1)[0]
    if 25<=len(sent)<=limit: text=sent
    if len(text)>limit:
        cut=text[:limit+1]
        i=max(cut.rfind('. '),cut.rfind('; '),cut.rfind(', '),cut.rfind(' '))
        if i<limit*0.55: i=limit
        text=cut[:i].rstrip(' ,;:.')+'…'
    return text.strip()

def describe_page(page, rev):
    name=page.get('name') or ''
    family=page.get('page_family') or 'unknown'
    body=(rev or {}).get('body') or ''
    topic=humanize_name(name)
    low=body.strip().casefold().strip(' .!')
    urls=domains_in(body)
    excerpt=meaningful_excerpt(body)

    # Redirects are explicit enough to describe precisely.
    m=re.search(r'#redirect\s+([^\n]+)',body,flags=re.I)
    if m:
        target=clean_markup(m.group(1)).strip()
        if len(target)>150: target=target[:147]+'…'
        return f"Redirect page pointing to {target}.", 'redirect'

    # The LoopNextWord corpus is intentionally machine-generated infrastructure.
    if name.casefold().startswith('loopnextword') or family=='loop-chain-infrastructure':
        return 'Automated loop-chain page storing one step in a generated page-to-page sequence.', 'family'

    # Domain-specific research families are substantially more informative than noisy page titles.
    if family in TOPIC_OVERRIDES:
        base=f"Research page about {TOPIC_OVERRIDES[family]}"
        if urls:
            return f"{base}, with source or API links including {', '.join(urls[:2])}.", 'family+links'
        if excerpt:
            return f"{base}. Latest stored text: {excerpt}", 'family+excerpt'
        return base+'.', 'family'

    # Default untouched new-page text deserves an explicit description rather than pretending it has content.
    if low in DEFAULT_PAGE_TEXTS:
        kind=FAMILY_LABELS.get(family,'wiki page')
        return f"{kind.capitalize()} named {topic}; the latest stored revision still contains the default new-page placeholder.", 'placeholder'

    if family=='probe-test':
        if excerpt:
            return f"Probe/test page for {topic}. Latest stored text: {excerpt}", 'family+excerpt'
        return f"Probe/test page for {topic}, used to verify wiki reads, writes, redirects, or formatting.", 'family'

    if family=='relay-coordination':
        if excerpt:
            return f"Coordination/relay page for {topic}. Latest stored text: {excerpt}", 'family+excerpt'
        return f"Coordination/relay page for {topic}, used for agent status, handoffs, or shared task notes.", 'family'

    if family=='source-cache-url-list':
        if urls:
            return f"Source/cache reference page for {topic}, collecting links including {', '.join(urls[:2])}.", 'family+links'
        if excerpt:
            return f"Source/cache reference page for {topic}. Latest stored text: {excerpt}", 'family+excerpt'
        return f"Source/cache reference page for {topic}, used to collect research links or copied source material.", 'family'

    if family=='source-or-unclassified':
        if urls:
            return f"Research/source page for {topic}, containing links including {', '.join(urls[:2])}.", 'family+links'
        if excerpt:
            return f"Research/source page for {topic}. Latest stored text: {excerpt}", 'family+excerpt'
        return f"Research/source page for {topic}, with sparse or unclassified stored content.", 'family'

    # Generic pages: prefer actual prose, then links, then metadata.
    if excerpt:
        kind=FAMILY_LABELS.get(family,'wiki page')
        return f"{kind.capitalize()} named {topic}. Latest stored text: {excerpt}", 'excerpt'
    if urls:
        return f"Reference page for {topic}, containing links including {', '.join(urls[:2])}.", 'links'
    kind=FAMILY_LABELS.get(family,'wiki page')
    return f"{kind.capitalize()} named {topic}; its latest stored revision is empty or too sparse to summarize reliably.", 'metadata'
