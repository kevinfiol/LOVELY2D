import sublime
import sublime_plugin
import json, os

class LoveCommand(sublime_plugin.TextCommand):
    def run(self, edit, key):
        api = LoveListener.get_api()
        meta = api[key]['meta']
        content = ''
        content += '<div id="sublime_love_container" style="padding: 0.6rem">'
        content += f'<p><code style="background-color: color(black alpha(0.25)); padding: 0.4rem;">{key}</code></p>'
        content += f'<strong>{meta["prop_type"]}</strong><br />'

        if 'arguments' in meta:
            content += '<div id="sublime_love__args" style="padding: 0.6rem">'
            for arg in meta['arguments']:
                content += f'<em>@param</em> <code style="background-color: color(black alpha(0.25)); padding: 0 0.2rem;">{arg["name"]}</code> <strong>{arg["type"]}</strong>  — {arg["description"]} <br />'
            content += '</div>'

        if 'returns' in meta:
            content += '<div id="sublime_love__returns" style="padding: 0.6rem">'
            for var in meta['returns']:
                content += f'<em>@returns</em> <code style="background-color: color(black alpha(0.25)); padding: 0 0.2rem;">{var["name"]}</code> <strong>{var["type"]}</strong>  — {var["description"]} <br />'
            content += '</div>'

        content += f'<span>{meta["description"]}</span><br />'

        content += '</div>'
        self.view.show_popup(content, max_width=800, max_height=600, flags=sublime.COOPERATE_WITH_AUTO_COMPLETE)

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
        if not all(view.match_selector(pt, 'source.lua') for pt in locations):
            return None

        # get the last word
        keyword = ''
        i = locations[0] - 2
        ptr = view.substr(i)
        while ptr != ' ' and ptr != '\n' and ptr != '\t' and i > -1:
            keyword = ptr + keyword
            i = i - 1
            ptr = view.substr(i)

        if (keyword.split('.')[0] == 'love'):
            newCompletions = self.get_completions(keyword)
            self.completions.set_completions(newCompletions)
        else:
            self.completions.set_completions([])

        return self.completions


    def get_completions(self, prefix):
        cls = self.__class__

        words = prefix.split('.')
        if words[0] == 'love':
            completions = []

            for i, key in enumerate(cls.api.keys()):
                item = cls.api[key]

                description = item['meta']['description'].split('.')[0]
                prop_type = item['meta']['prop_type'] or 'variable'
                kind = self.kinds[prop_type]
                href = 'subl:love' + " " + sublime.encode_value({ "key": key })
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
