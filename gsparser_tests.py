import json
import gsconfig
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

with open("gsparser_test_cases.json", "r") as f:
    cases = json.load(f)

for case in cases:
    for s_in, s_out in case['data']:
        # Обычная версия
        # r = gsparser.jsonify(s_in, version=case['version'])
        
        # Версия на классах
        converter = gsconfig.ConfigJSONConverter({'parser_version': case['version']})
        r = converter.jsonify(s_in)

        try:
            assert json.dumps(r) == json.dumps(s_out)
        except AssertionError:
            print('='*30)
            print(f'{case["version"]}: {s_in}')
            print(json.dumps(r, indent = 4))
            print(json.dumps(s_out, indent = 4))
    else:
        print(f'{case["version"]}. Больше ничего нет? Значит все норм!')
