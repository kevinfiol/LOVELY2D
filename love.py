import sublime
import sublime_plugin
import json, os

class LoveCommand(sublime_plugin.TextCommand):
    def run(self, edit, key, point, hide_on_mouse_move):
        api = LoveListener.get_api()
        meta = api[key]['meta']
        links = self.get_links(key, meta)

        if point == '':
            point = -1

        flags = sublime.HIDE_ON_MOUSE_MOVE_AWAY if hide_on_mouse_move else sublime.COOPERATE_WITH_AUTO_COMPLETE

        signature = None
        if meta["prop_type"] == 'function':
            signature = key
            if 'arguments' in meta:
                signature += '('
                for i, arg in enumerate(meta['arguments']):
                    signature += f'{arg["name"]}: {arg["type"]}'
                    if 'default' in arg: signature += f' = {arg["default"]}'
                    if i != len(meta['arguments']) - 1: signature += ', '
                signature += ')'
            else:
                signature += '()'

        content = ''
        content += '<div id="sublime_love_container" style="padding: 0.6rem">'
        content += f'<p><code style="background-color: color(black alpha(0.25)); padding: 0.4rem;">{signature or key}</code></p>'
        content += f'<strong>{meta["prop_type"]}</strong> <span style="font-size: 1.2rem">{meta["name"]}</span><br />'

        if 'arguments' in meta:
            content += '<div id="sublime_love__args" style="padding: 0.6rem">'
            for arg in meta['arguments']:
                content += '<div style="margin: 0.2rem 0">'
                default = f' (Default: <code style="background-color: color(black alpha(0.25)); padding: 0 0.2rem;">{arg["default"]}</code>)' if 'default' in arg else ''
                content += f'<em>@param</em> <code style="background-color: color(black alpha(0.25)); padding: 0 0.2rem;">{arg["name"]}</code> <strong>{arg["type"]}</strong>  —{default} {arg["description"]} <br />'
                content += '</div>'
            content += '</div>'

        if 'returns' in meta:
            content += '<div id="sublime_love__returns" style="padding: 0.6rem">'
            for var in meta['returns']:
                content += '<div style="margin: 0.2rem 0">'
                content += f'<em>@returns</em> <code style="background-color: color(black alpha(0.25)); padding: 0 0.2rem;">{var["name"]}</code> <strong>{var["type"]}</strong>  — {var["description"]} <br />'
                content += '</div>'
            content += '</div>'

        content += f'<div id="sublime_love__description" style="padding: 0.2rem 0;"><span>{meta["description"]}</span></div>'
        content += f'<div id="sublime_love__links"><a href="{links["wiki_link"]}">Wiki</a> | <a href="{links["api_link"]}">API</a></div>'

        content += '</div>'
        self.view.show_popup(
            content,
            max_width=1024,
            max_height=768,
            flags=flags,
            location=point
        )

    def get_links(self, key, meta):
        wiki_link = 'https://love2d.org/wiki/'
        api_link = 'https://love2d-community.github.io/love-api/#'

        fn = None
        module = None
        type_name = None

        if meta["prop_type"] == 'function':
            temp = key.split(':')
            fn = meta["name"]
            if len(temp) == 2:
                # it's a type func
                temp = temp[0]
                temp = temp.split('.')
                if len(temp) == 3:
                    module = temp[1]
                    type_name = temp[2]
                elif len(temp) == 2:
                    type_name = temp[1]
                wiki_link += f'{type_name}:{fn}'
                api_link += f'{type_name}_{fn}'
            elif len(temp) == 1:
                # it's a module func or top-level callback
                temp = temp[0]
                temp = temp.split('.')
                if len(temp) == 3:
                    module = temp[1]

                if module:
                    wiki_link += f'love.{module}.{fn}'
                    api_link += f'{module}_{fn}'
                else:
                    wiki_link += f'love.{fn}'
                    api_link += fn
        elif meta["prop_type"] == 'module':
            module = meta["name"]
            wiki_link += f'love.{module}'
            api_link += module
        elif meta["prop_type"] == 'type':
            temp = key.split('.')
            module = temp[1]
            type_name = meta["name"]
            wiki_link += type_name
            api_link += f'type_{type_name}'

        return { "wiki_link": wiki_link, "api_link": api_link }

class LoveListener(sublime_plugin.EventListener):
    api = None

    def __init__(self):
        cls = self.__class__
        self.completions = sublime.CompletionList()
        self.kinds = {
            'function': sublime.KIND_FUNCTION,
            'type': sublime.KIND_TYPE,
            'module': sublime.KIND_NAMESPACE,
            'variable': sublime.KIND_VARIABLE
        }

        # Load JSON
        script_dir = os.path.dirname(os.path.realpath(__file__))
        json_path = os.path.join(script_dir, 'love_api.json')
        with open(json_path) as api_json:
            cls.api = json.load(api_json)

    @classmethod
    def get_api(cls):
        return cls.api

    def on_query_completions(self, view, prefix, locations):
        if not all(view.match_selector(pt, 'source.lovely') for pt in locations):
            return None

        # get the last word
        keyword = ''
        i = locations[0] - 2
        ptr = view.substr(i)
        while ptr != ' ' and ptr != '\n' and ptr != '\t' and ptr != '(' and i > -1:
            keyword = ptr + keyword
            i = i - 1
            ptr = view.substr(i)

        if (keyword.split('.')[0] == 'love'):
            newCompletions = self.get_completions(keyword)
            self.completions.set_completions(newCompletions)
        else:
            self.completions.set_completions([])

        return self.completions

    def on_hover(self, view, point, hover_zone):
        cls = self.__class__

        if not view.match_selector(point, 'source.lovely'):
            return None

        word = view.word(point)
        # check namespaces
        prevs = ''
        i = word.a - 1
        ptr = view.substr(i)
        while ptr != ' ' and ptr != '\n' and ptr != '\t' and ptr != '(' and i > -1:
            prevs = ptr + prevs
            i = i - 1
            ptr = view.substr(i)
        key = prevs + view.substr(word)

        if key in cls.api:
            view.run_command('love', { "key": key, "point": point, "hide_on_mouse_move": True })

    def get_completions(self, prefix):
        cls = self.__class__

        words = prefix.split('.')
        if words[0] == 'love':
            completions = []

            for i, key in enumerate(cls.api.keys()):
                item = cls.api[key]

                description = item['meta']['description'].split('.')[0] + '.'
                prop_type = item['meta']['prop_type'] or 'variable'
                kind = self.kinds[prop_type]
                href = 'subl:love' + " " + sublime.encode_value({ "key": key, "point": "", "hide_on_mouse_move": False })
                completion_text = (key + '($0)') if prop_type == 'function' else key

                completion = sublime.CompletionItem(
                    key,
                    prop_type,
                    completion_text,
                    sublime.COMPLETION_FORMAT_SNIPPET,
                    kind,
                    f"<a href='{href}'>{description}</a>"
                )
                completions.append(completion)

            return completions

        return []