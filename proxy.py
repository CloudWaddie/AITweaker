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
        self.gemini_url_pattern = re.compile(r'^https?:\/\/www\.gstatic\.com\/.*m=_b(\?.*)?$', re.S)
        self.gemini_module_pattern = re.compile(r'^https?:\/\/www\.gstatic\.com\/_\/mss\/boq-bard-web\/_\/js\/.*\/m=')
        self.copilot_url_pattern = re.compile(r'^https?:\/\/copilot\.microsoft\.com\/c\/api\/start.*')
        self.google_labs_url_pattern = re.compile(r'^https?:\/\/labs\.google\/fx\/_next\/static\/chunks\/pages\/index-.*\.js')
        self.google_labs_json_pattern = re.compile(r'^https?:\/\/labs\.google\/fx\/_next\/data\/.*\.json(\?.*)?$')

    def load_rules(self):
        try:
            mtime = os.path.getmtime(self.rules_path)
            if mtime > self.last_load_time:
                with open(self.rules_path, 'r') as f:
                    self.rules = json.load(f)
                self.last_load_time = mtime
                ctx.log.info("proxy.py: Reloaded rules.json.")
        except FileNotFoundError:
            if self.rules or self.last_load_time > 0:
                ctx.log.warn("proxy.py: rules.json not found. Clearing all rules.")
                self.rules = {"apps": {}}
                self.last_load_time = 0
        except Exception as e:
            ctx.log.error(f"Error checking/loading rules.json: {e}")

    def modify_gemini_script(self, flow: http.HTTPFlow):
        gemini_config = self.rules.get("apps", {}).get("gemini", {})
        if not gemini_config.get("enabled", False):
            return
        flags_to_inject = gemini_config.get("flags", [])
        if not flags_to_inject:
            return
        try:
            script = flow.response.get_text()
            regex = r'return\s*!\s*this\.\w+\s*\|\|\s*\w+(?:\.\w+)?\s*in\s*this\.(\w+)\s*\?\s*\w+(?:\.\w+)?\(this\.\w+\[\w+(?:\.\w+)?\]\)\s*:\s*\w+(?:\.\w+)?'
            match = re.search(regex, script)
            if match:
                alias = match.group(1)
                flags_string = json.dumps(flags_to_inject)
                replacement = f'''
                this.{alias}[45659183] = false;
                const ext_flags = {flags_string};
                for (const flag of ext_flags) {{
                    if (typeof flag === 'string' && flag.includes('-')) {{
                        const parts = flag.split('-');
                        const start = Number(parts[0]);
                        const end = Number(parts[1]);
                        if (a.key >= start && a.key <= end && a.key != 45659183) {{
                            return a.ctor(true);
                        }}
                    }} else {{
                        if (flag != 45659183) {{
                            const flagType = typeof this.{alias}[flag];
                            if (flagType === 'boolean' || flagType === 'undefined') {{
                                this.{alias}[flag] = true;
                            }}
                        }}
                    }}
                }}
                {match.group(0)}
                '''
                flow.response.text = script.replace(match.group(0), replacement)
                print(f"[TERMINAL_LOG] Modified Gemini script: {flow.request.pretty_url}")
            else:
                ctx.log.info("proxy.py: Target for Gemini modification not found in script.")
        except Exception as e:
            ctx.log.error(f"Error during Gemini script modification: {e}")

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
                ctx.log.info("Set 'allowBeta' to true in Copilot response.")

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
                    ctx.log.info(f"Injected {added_count} new Copilot flags.")
            
            if modified:
                flow.response.text = json.dumps(body)
                print(f"[TERMINAL_LOG] Modified Copilot response: {flow.request.pretty_url}")

        except Exception as e:
            ctx.log.error(f"Error modifying Copilot response: {e}")

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
                ctx.log.info("proxy.py: Target for MusicFX link replacement not found.")

        except Exception as e:
            ctx.log.error(f"Error during Google Labs script modification: {e}")

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
            ctx.log.info(f"proxy.py: Explicitly ignoring Gemini batchexecute URL to prevent modification.")
            return

        # Removed timewarp logic

        if self.gemini_url_pattern.match(flow.request.url):
            self.modify_gemini_script(flow)
        
        if self.copilot_url_pattern.match(flow.request.url):
            self.modify_copilot_response(flow)

        if self.google_labs_url_pattern.match(flow.request.url) or self.google_labs_json_pattern.match(flow.request.url):
            self.modify_google_labs_script(flow)

        self.modify_json_response(flow)

addons = [
    AITweaker()
]