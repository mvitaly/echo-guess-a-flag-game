import urllib.request
import urllib.parse
import json
import re
import sys


WIKIPEDIA_API_URL = 'https://en.wikipedia.org/w/api.php?action=query&titles={}&prop=revisions&rvprop=content&format=json'
WIKIPEDIA_FLAGS_PAGE_TITLE = 'Gallery of sovereign state flags'
WIKIPEDIA_FLAG_PAGE_TEMPLATE = 'Flag of {}'
WIKIPEDIA_COUNTRY_DATA_PAGE_TEMPLATE = 'Template:Country_data_{}'


country_list = [
    'Argentina',
    'Australia',
    'Belarus',
    'Belgium',
    'Brazil',
    'Bulgaria',
    'Canada',
    'China',
    'Denmark',
    'Estonia',
    'Finland',
    'France',
    'Georgia',
    'Germany',
    'Greece',
    'Hungary',
    # 'Ireland',
    'Israel',
    'Italy',
    'Jamaica',
    'Japan',
    'Kazakhstan',
    'North Korea',
    'South Korea',
    'Macedonia',
    'Mexico',
    'Moldova',
    'Nepal',
    'Netherlands',
    'New Zealand',
    'Norway',
    'Philippines',
    'Poland',
    'Portugal',
    'Romania',
    'Russia',
    'South Africa',
    'Sweden',
    'Switzerland',
    'Thailand',
    'Turkey',
    'Ukraine',
    'United Kingdom',
    'United States',
    'Vatican City'
]


flag_entry_re = re.compile(r'\{\{Flag entry\|Width=200\|Country=([^|}]+)[|}]')
redirect_entry_re = re.compile(r'^#REDIRECT\s*\[\[(.+?)\]\].*', re.IGNORECASE | re.DOTALL)
alias_re = re.compile(r'\|\s*alias\s*=\s*(.+?)\s*(\||$)', re.IGNORECASE | re.DOTALL)
design_re = re.compile(r'\|\s*design\s*=\s*(.+?)\s*((\|\s*[^={}\[\]]+=)|$)', re.IGNORECASE | re.DOTALL)


def find_section_end(page_src, start_index):
    layer = 1
    index = start_index + 2
    while True:
        next_open = page_src.find('{{', index)
        next_close = page_src.find('}}', index)
        if next_close < 0:
            raise Exception('no closing parenthesis')
        elif next_open >= 0 and next_open < next_close:
            layer = layer + 1
            index = next_open + 2
        elif next_open < 0 or next_close < next_open:
            layer = layer - 1
            if layer == 0:
                return next_close
            index = next_close + 2
        else:
            raise Exception('cannot find closing parenthesis')


def handle_page(page, page_src_handler):
    # print('Page: {}'.format(page))
    url = WIKIPEDIA_API_URL.format(urllib.parse.quote(page))
    print('URL: {}'.format(url), file=sys.stderr)
    with urllib.request.urlopen(url) as response:
        response_str = response.read().decode('utf-8')
        wiki_flags = json.loads(response_str)
        for (page_id, page) in wiki_flags['query']['pages'].items():
            page_src = page['revisions'][0]['*']
            # print(page_src)
            redirect_entry_m = redirect_entry_re.match(page_src)
            if redirect_entry_m is not None:
                redirect_page = redirect_entry_m.group(1)
                return handle_page(redirect_page, page_src_handler)
            else:
                return page_src_handler(page_src)
    return None


def parse_metawiki_line(line):
    # print(line)
    line_no_links = re.sub(r'\[\[([^]]+\|)?(.+?)\]\]',
        r'\2',
        line
    )
    # print(line_no_links)
    return line_no_links


def parse_flag_infobox(infobox):
    # print(infobox)
    design_m = design_re.search(infobox)
    if design_m is not None:
        return parse_metawiki_line(design_m.group(1))
    return 'NO_DESIGN_LINE'
    # infobox_lines = infobox.split('\n')
    # design_line = next(
    #     (design_m.group(1) for design_m in (
    #         design_re.match(line) for line in infobox_lines
    #         ) if design_m is not None
    #     ), None)
    # return parse_metawiki_line(design_line)


def parse_flag_page_src(page_src):
    # print(page_src)
    flag_infobox_idx = page_src.find('{{Infobox ')
    #print('flag_infobox_idx: {}'.format(flag_infobox_idx))
    if flag_infobox_idx >= 0:
        flag_infobox_start_idx = flag_infobox_idx + 2
        flag_infobox_end_idx = find_section_end(page_src, flag_infobox_idx)
        #print('start: {}'.format(flag_infobox_start_idx))
        #print('end: {}'.format(flag_infobox_end_idx))
        flag_infobox = page_src[flag_infobox_start_idx:flag_infobox_end_idx]
        return parse_flag_infobox(flag_infobox)
    return 'NO INFOBOX'


def parse_country_data_page_src(page_src):
    # print(page_src)
    alias_m = alias_re.search(page_src)
    if alias_m is None:
        return 'NO ALIAS'
    country_name = alias_m.group(1)
    wikipedia_country_flag = WIKIPEDIA_FLAG_PAGE_TEMPLATE.format(country_name)
    return wikipedia_country_flag



def parse_page_src(page_src):
    page_lines = page_src.split("\n")

    data = dict()

    for page_line in page_lines:
        flag_entry_m = flag_entry_re.match(page_line)
        if flag_entry_m is not None:
            country_name = flag_entry_m.group(1)
            # if country_name not in country_list:
            #     continue
            # if country_name != 'Georgia':
            #     continue
            # if country_name != 'Ireland':
            #     continue
            # print(page_line)
            if country_name == 'Ireland':
                wikipedia_country_flag = WIKIPEDIA_FLAG_PAGE_TEMPLATE.format(country_name)
            else:
                wikipedia_country_data = WIKIPEDIA_COUNTRY_DATA_PAGE_TEMPLATE.format(country_name)
                wikipedia_country_flag = handle_page(
                    wikipedia_country_data, parse_country_data_page_src)
            flag_design = handle_page(wikipedia_country_flag, parse_flag_page_src)
            country = {
                'county_names': [country_name],
                'flag_design': flag_design
            }
            data[country_name] = country
            print('Country: {}\nFlag: {}'.format(country_name, flag_design), file=sys.stderr)
            # if flag_design is None:
            #     print('NONE!\n\n')
        # if len(data) == 3:
        #     break

    print(json.dumps(data, indent=4))


handle_page(WIKIPEDIA_FLAGS_PAGE_TITLE, parse_page_src)
# wikipedia_flags_list_url = WIKIPEDIA_API_URL.format(urllib.parse.quote(WIKIPEDIA_FLAGS_PAGE_TITLE))
# with urllib.request.urlopen(wikipedia_flags_list_url) as response:
#     response_str = response.read().decode('utf-8')
#     wiki_flags = json.loads(response_str)
#     for (page_id, page) in wiki_flags['query']['pages'].items():
#         page_src = page['revisions'][0]['*']
#         parse_page_src(page_src)

#fp.close()
