import json
import re
import os
import time
from mitmproxy import http, ctx
from bs4 import BeautifulSoup, FeatureNotFound

class AITweaker:
    def __init__(self):
        self.rules = {}
        self.rules_path = 'rules.json'
        self.last_load_time = 0
        self.load_rules()

        self.gemini_html_pattern = re.compile(r'^https?:\/\/gemini\.google\.com\/.*')
        # Match ANY gemini.gstatic.com or www.gstatic.com URL that serves Bard JS modules
        # The m= parameter at end of path identifies the module file (e.g., m=LQaXg, m=_b)
        # We intercept ANY module JS file from the boq-bard-web path
        self.gemini_url_pattern = re.compile(r'^https?:\/\/(www|gemini)\.gstatic\.com\/_\/mss\/boq-bard-web\/_\/js\/.*\/m=\w+(\?.*)?$', re.S)
        self.gemini_module_pattern = re.compile(r'^https?:\/\/(www|gemini)\.gstatic\.com\/_\/mss\/boq-bard-web\/_\/js\/.*\/m=')
        self.copilot_url_pattern = re.compile(r'^https?:\/\/copilot\.microsoft\.com\/c\/api\/start.*')
        self.grok_url_pattern = re.compile(r'^https?:\/\/(www\.)?grok\.com\/.*')
        self.google_labs_url_pattern = re.compile(r'^https?:\/\/labs\.google\/fx\/_next\/static\/chunks\/pages\/index-.*\.js')
        self.google_labs_json_pattern = re.compile(r'^https?:\/\/labs\.google\/fx\/_next\/data\/.*\.json(\?.*)?$')

    def load_rules(self):
        try:
            mtime = os.path.getmtime(self.rules_path)
            if mtime > self.last_load_time:
                with open(self.rules_path, 'r') as f:
                    self.rules = json.load(f)
                self.last_load_time = mtime
                print(f"[TERMINAL_LOG] proxy.py: Reloaded rules.json.")
        except FileNotFoundError:
            if self.rules or self.last_load_time > 0:
                print(f"[TERMINAL_LOG] proxy.py: rules.json not found. Clearing all rules.")
                self.rules = {"apps": {}}
                self.last_load_time = 0
        except Exception as e:
            print(f"[TERMINAL_LOG] Error checking/loading rules.json: {e}")

    def modify_gemini_script(self, flow: http.HTTPFlow):
        gemini_config = self.rules.get("apps", {}).get("gemini", {})
        if not gemini_config.get("enabled", False):
            return
        flags_to_inject = gemini_config.get("flags", [])
        if not flags_to_inject:
            return
        try:
            script = flow.response.get_text()
            # Build a JavaScript function to check if a flag key is in our list (supports ranges)
            # flags_to_inject can contain: numbers (exact match) or "start-end" strings (range)
            exact_flags = []
            range_flags = []
            for flag in flags_to_inject:
                flag_str = str(flag)
                if '-' in flag_str:
                    range_flags.append(flag_str)
                else:
                    exact_flags.append(flag_str)
            
            exact_flags_js = json.dumps(exact_flags)
            range_flags_js = json.dumps(range_flags)
            
            # JavaScript check function
            js_check = f'''(function(key) {{
                if ({exact_flags_js}.includes(key)) return !0;
                var ranges = {range_flags_js};
                for (var i = 0; i < ranges.length; i++) {{
                    var parts = ranges[i].split('-');
                    var start = Number(parts[0]);
                    var end = Number(parts[1]);
                    if (key >= start && key <= end) return !0;
                }}
                return !1;
            }})'''
            
            # Find and replace ctor method
            ctor_pattern = r'ctor\(a\)\{return typeof a===\"boolean\"\?a:this\.defaultValue\}'
            match = re.search(ctor_pattern, script)
            if match:
                original_ctor = match.group(0)
                new_ctor = f'ctor(a){{if({js_check}(this.key))return!0;return typeof a==="boolean"?a:this.defaultValue}}'
                script = script.replace(original_ctor, new_ctor, 1)
                flow.response.text = script
                print(f"[TERMINAL_LOG] Modified Gemini ctor for flags: exact={exact_flags}, ranges={range_flags}")
            else:
                print(f"[TERMINAL_LOG] [WARN] ctor method not found in {flow.request.pretty_url}")
        except Exception as e:
            print(f"[TERMINAL_LOG] [ERROR] Error modifying Gemini script: {e}")

    def modify_copilot_response(self, flow: http.HTTPFlow):
        copilot_config = self.rules.get("apps", {}).get("copilot", {})
        if not copilot_config.get("enabled", False):
            return

        try:
            body = json.loads(flow.response.get_text())
            modified = False

            # Modify allowBeta field
            if copilot_config.get("allow_beta", False) and body.get("allowBeta") is not True:
                body["allowBeta"] = True
                modified = True
                print(f"[TERMINAL_LOG] Set 'allowBeta' to true in Copilot response.")

            # Modify feature flags
            flags_to_add = copilot_config.get("flags", [])
            if flags_to_add and "features" in body and isinstance(body["features"], list):
                existing_features = set(body["features"])
                initial_count = len(existing_features)
                for flag in flags_to_add:
                    existing_features.add(flag)
                
                if len(existing_features) > initial_count:
                    body["features"] = list(existing_features)
                    modified = True
                    added_count = len(existing_features) - initial_count
                    print(f"[TERMINAL_LOG] Injected {added_count} new Copilot flags.")
            
            if modified:
                flow.response.text = json.dumps(body)
                print(f"[TERMINAL_LOG] Modified Copilot response: {flow.request.pretty_url}")

        except Exception as e:
            print(f"[TERMINAL_LOG] Error modifying Copilot response: {e}")

    def modify_google_labs_script(self, flow: http.HTTPFlow):
        google_labs_config = self.rules.get("apps", {}).get("google_labs", {})
        if not google_labs_config.get("enabled", False):
            return

        replacement = google_labs_config.get("music_fx_replace", "None")
        if replacement == "None" or not replacement:
            return

        try:
            script = flow.response.get_text()
            original_link = "/tools/music-fx"
            # The replacement value from rules.json has the leading '/' stripped by the GUI.
            new_link = f"/{replacement}"
            
            old_code_single = f"'link':'{original_link}'"
            new_code_single = f"'link':'{new_link}'"
            old_code_double = f'"link":"{original_link}"'
            new_code_double = f'"link":"{new_link}"'

            if old_code_single in script:
                flow.response.text = script.replace(old_code_single, new_code_single)
                print(f"[TERMINAL_LOG] Modified Google Labs script (MusicFX link): {flow.request.pretty_url}")
            elif old_code_double in script:
                flow.response.text = script.replace(old_code_double, new_code_double)
                print(f"[TERMINAL_LOG] Modified Google Labs script (MusicFX link): {flow.request.pretty_url}")
            else:
                print(f"[TERMINAL_LOG] proxy.py: Target for MusicFX link replacement not found.")

        except Exception as e:
            print(f"[TERMINAL_LOG] Error during Google Labs script modification: {e}")

    def modify_grok_response(self, flow: http.HTTPFlow):
        grok_config = self.rules.get("apps", {}).get("grok", {})
        if not grok_config.get("enabled", False):
            return

        html = flow.response.get_text()
        modified = False

        # Handle Config JSON replacement
        custom_json_str = grok_config.get("config_json", "{}")
        if custom_json_str and custom_json_str != "{}":
            try:
                # Simple regex replacement for speed
                pattern = r'(<script type="application/json" id="server-client-data-experimentation">)(.*?)(</script>)'
                
                if re.search(pattern, html, re.DOTALL):
                    try:
                        minified_json = json.dumps(json.loads(custom_json_str))
                        new_html = re.sub(pattern, lambda m: f'{m.group(1)}{minified_json}{m.group(3)}', html, count=1, flags=re.DOTALL)
                        if new_html != html:
                            html = new_html
                            modified = True
                            print(f"[TERMINAL_LOG] Modified Grok configuration: {flow.request.pretty_url}")
                    except json.JSONDecodeError:
                        print(f"[TERMINAL_LOG] proxy.py: Invalid JSON in Grok configuration rules.")
            except Exception as e:
                print(f"[TERMINAL_LOG] Error during Grok config modification: {e}")

        # Handle Subscription Spoofing
        if grok_config.get("spoof_subscription", False):
            try:
                # Replace false with true for specific keys
                subs_replacements = [
                    (r'"isSuperGrokUser":false', r'"isSuperGrokUser":true'),
                    (r'"isSuperGrokProUser":false', r'"isSuperGrokProUser":true'),
                    (r'"isEnterpriseUser":false', r'"isEnterpriseUser":true'),
                    (r'"xSubscriptionType":"[^"]*"', r'"xSubscriptionType":"SuperGrok"')
                ]
                
                for pattern, replacement in subs_replacements:
                    if re.search(pattern, html):
                        html = re.sub(pattern, replacement, html)
                        modified = True
                        print(f"[TERMINAL_LOG] Spoofed Grok subscription ({pattern} -> {replacement})")
            except Exception as e:
                print(f"[TERMINAL_LOG] Error during Grok subscription spoofing: {e}")

        if modified:
            flow.response.text = html

    def modify_json_response(self, flow: http.HTTPFlow):
        google_labs_config = self.rules.get("apps", {}).get("google_labs", {})
        if not google_labs_config.get("enabled", False) or not google_labs_config.get("bypass_not_found", False):
            return
        
        if flow.response and "application/json" in flow.response.headers.get("content-type", ""):
            if flow.response.text == '{"notFound":true}':
                flow.response.text = '{"notFound":false}'
                print(f"[TERMINAL_LOG] Bypassed notFound=true for: {flow.request.pretty_url}")

        if flow.response.status_code == 404 and re.match(r"^https://labs\.google/fx/_next/data/.*\.json(\?.*)?$", flow.request.url):
            flow.response.status_code = 200
            flow.response.text = '{"notFound":false}'
            flow.response.headers["Content-Type"] = "application/json"
            print(f"[TERMINAL_LOG] Overwrote 404 response for: {flow.request.pretty_url}")



    def request(self, flow: http.HTTPFlow) -> None:
        self.load_rules()

        # Removed timewarp and module redirect logic

        google_labs_config = self.rules.get("apps", {}).get("google_labs", {})
        if google_labs_config.get("bypass_not_found", False):
            if flow.request.method == "HEAD" and re.match(r"^https://labs\.google/fx/_next/data/.*\.json(\?.*)?$", flow.request.url):
                flow.request.method = "GET"
                print(f"[TERMINAL_LOG] Converted HEAD to GET for: {flow.request.pretty_url}")

    def response(self, flow: http.HTTPFlow) -> None:
        self.load_rules()

        if "batchexecute" in flow.request.url and "gemini.google.com" in flow.request.url:
            print(f"[TERMINAL_LOG] proxy.py: Explicitly ignoring Gemini batchexecute URL to prevent modification.")
            return

        # Removed timewarp logic

        if self.gemini_url_pattern.match(flow.request.url):
            self.modify_gemini_script(flow)
        
        if self.copilot_url_pattern.match(flow.request.url):
            self.modify_copilot_response(flow)

        if self.grok_url_pattern.match(flow.request.url):
            self.modify_grok_response(flow)

        if self.google_labs_url_pattern.match(flow.request.url) or self.google_labs_json_pattern.match(flow.request.url):
            self.modify_google_labs_script(flow)

        self.modify_json_response(flow)

addons = [
    AITweaker()
]