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
        if meta['prop_type'] == 'function':
            signature = key
            if 'arguments' in meta:
                signature += '('
                for i, arg in enumerate(meta['arguments']):
                    signature += '{}: {}'.format(arg['name'], arg['type'])
                    if 'default' in arg: signature += ' = {}'.format(arg['default'])
                    if i != len(meta['arguments']) - 1: signature += ', '
                signature += ')'
            else:
                signature += '()'

        content = (
            '<div id="sublime_love_container" style="padding: 0.6rem">' +
                '<p style="background-color: color(black alpha(0.25)); padding: 0.6rem; margin: 0 0 0.4rem 0;"><code>{}</code></p>'
                    .format((signature or key)) +
                '<strong>{}</strong> <span style="font-size: 1.2rem">{}</span><br />'
                    .format(meta['prop_type'], meta['name'])
        )

        if 'arguments' in meta:
            content += '<div id="sublime_love__args" style="padding: 0.6rem">'
            for arg in meta['arguments']:
                default = ''
                if 'default' in arg:
                    default = ' (Default: <code style="background-color: color(black alpha(0.25)); padding: 0 0.2rem;">{}</code>)'.format(arg['default'])

                content += (
                    '<div style="margin: 0.2rem 0">' +
                        '<em>@param</em> <code style="background-color: color(black alpha(0.25)); padding: 0 0.2rem;">{}</code> <strong>{}</strong>  —{} {} <br />'
                            .format(arg['name'], arg['type'], default, arg['description']) +
                    '</div>'
                )
            content += '</div>'

        if 'returns' in meta:
            content += '<div id="sublime_love__returns" style="padding: 0.6rem">'
            for var in meta['returns']:
                content += (
                    '<div style="margin: 0.2rem 0">' +
                        '<em>@returns</em> <code style="background-color: color(black alpha(0.25)); padding: 0 0.2rem;">{}</code> <strong>{}</strong>  — {} <br />'
                            .format(var['name'], var['type'], var['description']) +
                    '</div>'
                )
            content += '</div>'

        content += (
            '<div id="sublime_love__description" style="padding: 0.2rem 0;"><span>{}</span></div>'
                .format(meta['description']) +
                '<div id="sublime_love__links"><a href="{}">Wiki</a> | <a href="{}">API</a></div>'
                    .format(links['wiki_link'], links['api_link']) +
            '</div>'
        )

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

        if meta['prop_type'] == 'function':
            temp = key.split(':')
            fn = meta['name']
            if len(temp) == 2:
                # it's a type func
                temp = temp[0]
                temp = temp.split('.')
                if len(temp) == 3:
                    module = temp[1]
                    type_name = temp[2]
                elif len(temp) == 2:
                    type_name = temp[1]
                wiki_link += '{}:{}'.format(type_name, fn)
                api_link += '{}_{}'.format(type_name, fn)
            elif len(temp) == 1:
                # it's a module func or top-level callback
                temp = temp[0]
                temp = temp.split('.')
                if len(temp) == 3:
                    module = temp[1]

                if module:
                    wiki_link += 'love.{}.{}'.format(module, fn)
                    api_link += '{}_{}'.format(module, fn)
                else:
                    wiki_link += 'love.{}'.format(fn)
                    api_link += fn
        elif meta['prop_type'] == 'module':
            module = meta['name']
            wiki_link += 'love.{}'.format(module)
            api_link += module
        elif meta['prop_type'] == 'type':
            temp = key.split('.')
            module = temp[1]
            type_name = meta['name']
            wiki_link += type_name
            api_link += 'type_{}'.format(type_name)

        return { "wiki_link": wiki_link, "api_link": api_link }

class LoveListener(sublime_plugin.EventListener):
    api = None

    def __init__(self):
        cls = self.__class__
        self.loveCompletions = sublime.CompletionList()
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
            self.loveCompletions.completions = None
            self.loveCompletions.set_completions(newCompletions)
        else:
            self.loveCompletions.completions = None
            self.loveCompletions.set_completions([])

        return self.loveCompletions

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
            loveCompletions = []

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
                    '''<a href='{}'>{}</a>'''.format(href, description)
                )
                loveCompletions.append(completion)

            return loveCompletions

        return []