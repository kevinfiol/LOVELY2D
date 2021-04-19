import sublime
import sublime_plugin
import json, os

class LoveCommand(sublime_plugin.TextCommand):
    def run(self, edit, key):
        content = ''
        print(key)
        content += (key + '<br>') * 6
        self.view.show_popup(content, sublime.COOPERATE_WITH_AUTO_COMPLETE)

class LoveListener(sublime_plugin.EventListener):
    def __init__(self):
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
            self.api = json.load(api_json)

    def on_query_completions(self, view, prefix, locations):
        if not all(view.match_selector(pt, 'source.lua') for pt in locations):
            return None

        self.completions.set_completions([])

        if (view.substr(locations[0] - 1) == '.'):
            keyword = ''
            i = locations[0] - 2
            ptr = view.substr(i)
            while ptr != ' ' and ptr != '\n' and i > -1:
                keyword = ptr + keyword
                i = i - 1
                ptr = view.substr(i)
            newCompletions = self.get_completions(keyword)
            self.completions.set_completions(newCompletions)

        return self.completions

    def get_completions(self, prefix):
        words = prefix.split('.')
        if words[0] == 'love':
            completions = []

            for i, key in enumerate(self.api.keys()):
                item = self.api[key]

                description = item['meta']['description'][:100] + '...'
                prop_type = item['meta']['prop_type'] or 'variable'
                kind = self.kinds[prop_type]
                href = 'subl:love' + " " + sublime.encode_value({"key": key})
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


# class LoveMoveCommand(sublime_plugin.TextCommand):
#     def run(self, edit, forward=True):
#         self.view.run_command("move", {"by": "lines", "forward": forward})
#         if LoveToggleCommand.enabled:  # TODO: use the enabled var of self.view
#             self.view.window().run_command("auto_complete_open_link")


# class LoveToggleCommand(sublime_plugin.TextCommand):
#     enabled = False

#     def run(self, edit):
#         cls = self.__class__
#         # TODO: make this use instance variable
#         cls.enabled = not cls.enabled
#         if cls.enabled:
#             self.view.run_command("auto_complete_open_link")
#         else:
#             self.view.run_command("hide_popup")


# class CompleteCloseListener(sublime_plugin.EventListener):
#     def on_post_text_command(self, view, command_name, args):
#         if command_name == "hide_auto_complete" or command_name == "commit_completion":
#             LoveToggleCommand.enabled = False


# class ShowPopupsCommand(sublime_plugin.TextCommand):
#     def run(self, edit, timeout_ms):
#         self.view.run_command('insert', {'characters': 'linewidth'})
#         self.view.run_command('auto_complete')
#         self.timeout_ms = timeout_ms
#         self.check()

#     def check(self):
#         if self.view.is_auto_complete_visible():
#             self.view.run_command('show_popups_iteration', {'index': 0, 'timeout_ms': self.timeout_ms})
#         else:
#             sublime.set_timeout(self.check, 100)


# class ShowPopupsIterationCommand(sublime_plugin.TextCommand):

#     def __init__(self, view):
#         super().__init__(view)
#         self.stop = False

#     def run(self, edit, index, timeout_ms, stop):
#         if stop is True:
#             self.stop = True
#             return
#         if self.stop is True:
#             self.stop = False
#             return
#         if not self.view.is_auto_complete_visible():
#             return

#         self.view.run_command('move', {'by': 'lines', 'forward': True})
#         self.view.run_command('auto_complete_open_link')
#         if index < COUNT:
#             def run_again_later():
#                 self.view.run_command('show_popups_iteration', {'index': index + 1, 'timeout_ms': timeout_ms})

#             sublime.set_timeout(run_again_later, timeout_ms)