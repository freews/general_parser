import json
import pprint

with open('o_tcg_opal_v2p30/deepseek_layout.json') as f:
    d = json.load(f)

for page in ['34', '35', '36']:
    if page in d:
        print(f"Page {page} layout structure sample:")
        # if it's a dict, print a subset
        if isinstance(d[page], dict):
            for k, v in list(d[page].items())[:2]:
                print(f"  {k}: {v}")
        elif isinstance(d[page], list):
            pprint.pprint(d[page][:2])
        else:
            print("  Primitive or string type:", type(d[page]))
