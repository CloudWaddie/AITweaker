import json
import re
from mitmproxy import http, ctx

class AITweaker:
    def __init__(self):
        self.rules = {}
        self.gemini_url_pattern = re.compile(r'^https?:\/\/www\.gstatic\.com\/.*m=_b(\?.*)?$', re.S)
        self.copilot_url_pattern = re.compile(r'^https?:\/\/copilot\.microsoft\.com\/c\/api\/start.*')

    def load_rules(self):
        try:
            with open('rules.json', 'r') as f:
                self.rules = json.load(f)
        except Exception as e:
            ctx.log.error(f"Error loading rules.json: {e}")
            self.rules = {"apps": {}}

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
                const ext_flags = {flags_string};
                for (const flag of ext_flags) {{
                    if (!this.{alias}[flag]) {{
                        this.{alias}[flag] = true;
                    }}
                }}
                {match.group(0)}
                '''
                flow.response.text = script.replace(match.group(0), replacement)
                ctx.log.info("proxy.py: Injected Gemini flags into script.")
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

        except Exception as e:
            ctx.log.error(f"Error modifying Copilot response: {e}")

    def response(self, flow: http.HTTPFlow) -> None:
        self.load_rules()
        
        if self.gemini_url_pattern.match(flow.request.url):
            self.modify_gemini_script(flow)
        
        if self.copilot_url_pattern.match(flow.request.url):
            self.modify_copilot_response(flow)

addons = [
    AITweaker()
]