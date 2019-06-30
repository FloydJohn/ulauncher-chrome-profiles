import os
import subprocess
import json
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction


def scan_chrome_folder(chrome_config_folder):
    profiles = {}
    # First, let's extract profiles from Local State JSON
    with open(os.path.join(chrome_config_folder, 'Local State')) as f:
        local_state = json.load(f)
        cache = local_state['profile']['info_cache']
        for folder, profile_data in cache.items():
            profiles[folder] = {
                'name': profile_data['name'],
                'email': profile_data['user_name']
            }

    # Leave out every past profile which doesn't exist anymore
    for folder in list(profiles.keys()):
        try:
            os.listdir(os.path.join(chrome_config_folder, folder))
        except:
            profiles.pop(folder)

    return profiles


class DemoExtension(Extension):
    def __init__(self):
        super(DemoExtension, self).__init__()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())


class KeywordQueryEventListener(EventListener):
    def on_event(self, event, extension):
        chrome_config_folder = os.path.expanduser(extension.preferences['chrome_folder'])
        profiles = scan_chrome_folder(chrome_config_folder)

        # Filter by query if inserted
        query = event.get_argument()
        if query:
            query = query.strip().lower()
            for folder in list(profiles.keys()):
                name = profiles[folder]['name'].lower()
                if query not in name:
                    profiles.pop(folder)

        # Create launcher entries
        entries = []
        for folder in profiles:
            entries.append(ExtensionResultItem(
                icon='images/icon.png',
                name=profiles[folder]['name'],
                description=profiles[folder]['email'],
                on_enter=ExtensionCustomAction({
                    'chrome_cmd': extension.preferences['chrome_cmd'],
                    'opt': ['--profile-directory={0}'.format(folder)]
                }, keep_app_open=True)
            ))
        return RenderResultListAction(entries)


class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        # Open Chrome when user selects an entry
        data = event.get_data()
        chrome_path = data['chrome_cmd']
        opt = data['opt']
        subprocess.Popen([chrome_path] + opt)


if __name__ == '__main__':
    DemoExtension().run()
