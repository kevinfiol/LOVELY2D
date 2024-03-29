import sublime
import sublime_plugin
import json, os, re

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
                        .format(meta['wiki_link'], meta['api_link']) +
                '</div>'
            )

            self.addToCache(key, content)

        if self.view.is_popup_visible(): # for reference hover overrides
            self.view.hide_popup()

        self.view.show_popup(
            content,
            max_width=1024,
            max_height=768,
            flags=flags,
            location=point
        )

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
        if not all(view.match_selector(pt, 'source.lua.lovely') for pt in locations):
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

        if not view.match_selector(point, 'source.lua.lovely'):
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

    def check_function_bounds(self, view, cursor_point):
        # am i inside a function?
        i = cursor_point - 1
        j = cursor_point

        minI = view.full_line(cursor_point).a
        maxJ = view.full_line(cursor_point).b - 1
        ptr1 = view.substr(i)
        ptr2 = view.substr(j)

        sub_funcs = 0
        while ptr1 not in set(['\n', '\t']) and (i >= minI) and not (ptr1 == '(' and sub_funcs == 0):
            if ptr1 == ')': sub_funcs += 1
            if ptr1 == '(' and sub_funcs > 0: sub_funcs -= 1
            i = i - 1
            ptr1 = view.substr(i)
        while ptr2 not in set(['\n', '\t', ')']) and (j <= maxJ):
            j = j + 1
            ptr2 = view.substr(j)

        print(i)
        print(j)

        is_inside_func = (ptr1 == '(' and ptr2 == ')' and sub_funcs == 0)

        return [is_inside_func, i, j, minI, maxJ]

    def get_function_name(self, view, i, minI):
        # i would be the position of the '(' parentheses
        i = i - 1
        keyPtr = view.substr(i)
        keyword = ''
        while keyPtr not in set(['\n', '\t', ' ', '(']) and (i >= minI):
            keyword = keyPtr + keyword
            i = i - 1
            keyPtr = view.substr(i)

        return keyword

    def show_popup(self, keyword, pos, view, cursor_point):
        content = self.get_content_for_keyword(keyword, pos)
        if not view.is_popup_visible():
            view.show_popup(content, max_width=640, location=cursor_point)
        else:
            view.hide_popup()
            view.show_popup(content, max_width=640, location=cursor_point)

    def on_text_changed(self, changes):
        change = changes[0]
        view = self.buffer.primary_view()
        point = change.a.pt
        if not view.match_selector(point, 'source.lua.lovely'):
            return None

        cursor_point = view.sel()[0].b
        [is_inside_func, i, j, minI, maxJ] = self.check_function_bounds(view, cursor_point)

        if is_inside_func:
            # you're in a function call!
            # let's get all of the text between the parentheses
            # at this point, i and j should be at the positions of the beginning and end of parentheses respectively
            # we can use this to get the position of the currently changed param
            # get all typed text up until where the user made a change
            pos = None
            use_async_popup = False
            if change.a.pt < i:
                # autocompleted
                use_async_popup = True
                pos = 0
            elif change.str == ',':
                fn_pattern = r'[a-zA-Z]+\([^\)]*\)(\.[^\)]*\))?'
                paramStr = view.substr(sublime.Region(i + 1, j))
                paramStr = re.sub(fn_pattern, '', paramStr) # removes function calls
                pos = len(paramStr.split(',')) - 1
            else:
                fn_pattern = r'[a-zA-Z]+\([^\)]*\)(\.[^\)]*\))?'
                paramStr = view.substr(sublime.Region(i + 1, change.a.pt))
                paramStr = re.sub(fn_pattern, '', paramStr) # removes function calls
                print(paramStr)
                pos = len(paramStr.split(',')) - 1
                if change.str == '': use_async_popup = True

            # get the actual function name, e.g., `love.graphics.rectangle`
            keyword = self.get_function_name(view, i, minI)
            print(keyword)

            def async_show_popup():
                self.show_popup(keyword, pos, view, cursor_point)

            # use the function name to get the metadata for that function to build the signature popup
            if keyword in self.api and self.api[keyword]['meta']['prop_type'] == 'function':
                if use_async_popup:
                    sublime.set_timeout(async_show_popup, 50)
                else:
                    self.show_popup(keyword, pos, view, cursor_point)

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