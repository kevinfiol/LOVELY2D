import sublime
import sublime_plugin
import json, os

class LoveCommand(sublime_plugin.TextCommand):
    def __init__(self, view):
        sublime_plugin.TextCommand.__init__(self, view)
        self.api = LoveListener.get_api()
        self.contentCache = {}

    def addToCache(self, key, content):
        if len(self.contentCache) == 10:
            self.contentCache.popitem()
        self.contentCache[key] = content

    def run(self, edit, key, point, hide_on_mouse_move):
        flags = sublime.HIDE_ON_MOUSE_MOVE_AWAY if hide_on_mouse_move else sublime.COOPERATE_WITH_AUTO_COMPLETE
        content = None
        if point == '': point = -1

        if key in self.contentCache:
            content = self.contentCache[key]
        else:
            meta = self.api[key]['meta']
            links = self.get_links(key, meta)

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

                signature += ' -> '
                if 'returns' in meta:
                    for i, arg in enumerate(meta['returns']):
                        signature += '{}: {}'.format(arg['name'], arg['type'])
                        if i != len(meta['returns']) - 1: signature += ', '
                else:
                    signature += 'nil'

            content = (
                '<div id="sublime_love_container" style="padding: 0.4rem">' +
                    '<p style="background-color: color(black alpha(0.25)); padding: 0.6rem; margin: 0 0 0.4rem 0; font-size: 0.9rem;"><code>{}</code></p>'
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

            self.addToCache(key, content)

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
        sublime_plugin.EventListener.__init__(self)
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

        while ptr not in set([' ', '\n', '\t', '(']) and (i > -1):
            keyword = ptr + keyword
            i = i - 1
            ptr = view.substr(i)

        if (keyword.split('.')[0] == 'love'):
            newCompletions = self.get_completions(keyword)
            self.loveCompletions.completions = None
            self.loveCompletions.set_completions(newCompletions, flags=sublime.INHIBIT_REORDER)
        else:
            self.loveCompletions.completions = None
            self.loveCompletions.set_completions([])

        # hide autocomplete if you just autocompleted a function
        if view.substr(locations[0] - 1) == '(':
            view.run_command('hide_auto_complete')

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
        while ptr not in set([' ', '\n', '\t', '(']) and (i > -1):
            prevs = ptr + prevs
            i = i - 1
            ptr = view.substr(i)
        key = prevs + view.substr(word)

        if key in cls.api:
            view.run_command('love', { "key": key, "point": point, "hide_on_mouse_move": True })

    def get_completions(self, prefix):
        cls = self.__class__

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

class LoveTextListener(sublime_plugin.TextChangeListener):
    def __init__(self):
        sublime_plugin.TextChangeListener.__init__(self)
        self.api = LoveListener.get_api()

    def on_text_changed(self, changes):
        change = changes[0]
        view = self.buffer.primary_view()
        point = change.a.pt
        if not view.match_selector(point, 'source.lovely'):
            return None

        # am i inside a function?
        i = point - 1
        j = point
        minI = view.full_line(point).a
        maxJ = view.full_line(point).b - 1
        ptr1 = view.substr(i)
        ptr2 = view.substr(j)

        while ptr1 not in set(['\n', '\t', '(']) and (i >= minI):
            i = i - 1
            ptr1 = view.substr(i)
        while ptr2 not in set(['\n', '\t', ')']) and (j <= maxJ):
            j = j + 1
            ptr2 = view.substr(j)

        if ptr1 == '(' and ptr2 == ')' and change.str != '':
            # you're in a function call!
            # let's get all of the text between the parentheses
            # at this point, i and j should be at the positions of the beginning and end of parentheses respectively
            # we can use this to get the position of the currently changed param
            paramStr = view.substr(sublime.Region(i + 1, change.a.pt))
            pos = len(paramStr.split(',')) - 1

            # get the actual function name, e.g., `love.graphics.rectangle`
            i = i - 1
            keyPtr = view.substr(i)
            keyword = ''
            while keyPtr not in set(['\n', '\t', ' ']) and (i >= minI):
                keyword = keyPtr + keyword
                i = i - 1
                keyPtr = view.substr(i)

            # use the function name to get the metadata for that function to build the signature popup
            if keyword in self.api and self.api[keyword]['meta']['prop_type'] == 'function':
                content = self.get_content_for_keyword(keyword, pos)
                if not view.is_popup_visible():
                    view.show_popup(content, max_width=640, location=change.a.pt)
                else:
                    view.hide_popup()
                    view.show_popup(content, max_width=640, location=change.a.pt)

    def get_content_for_keyword(self, keyword, pos):
        meta = self.api[keyword]['meta']
        signature = keyword
        if 'arguments' in meta:
            signature += '('
            for i, arg in enumerate(meta['arguments']):
                template = '<strong style="text-decoration: underline;">{}: {}</strong>' if i == pos else '{}: {}'
                signature += template.format(arg['name'], arg['type'])
                if 'default' in arg: signature += ' = {}'.format(arg['default'])
                if i != len(meta['arguments']) - 1: signature += ', '
            signature += ')'
        else:
            signature += '()'

        signature += ' -> '
        if 'returns' in meta:
            for i, arg in enumerate(meta['returns']):
                signature += '{}: {}'.format(arg['name'], arg['type'])
                if i != len(meta['returns']) - 1: signature += ', '
        else:
            signature += 'nil'

        content = (
            '<div id="sublime_lovesignature_container" style="padding: 0.4rem">' +
                '<p style="background-color: color(black alpha(0.25)); padding: 0.6rem; margin: 0 0 0.4rem 0; font-size: 0.9rem;"><code>{}</code></p>'
                    .format((signature or key)) +
            '</div>'
        )

        return content