from __future__ import annotations

import json
import urllib.request
import urllib.error

from qtpy.QtCore import QThread, Signal


class OpenAIWorker(QThread):
    finished = Signal(str)
    errored = Signal(str)

    def __init__(self, prompt: str, api_key: str, model: str = 'gpt-4o-mini', temperature: float = 0.2):
        super().__init__()
        self.prompt = prompt
        self.api_key = api_key
        self.model = model
        self.temperature = temperature

    def run(self):
        try:
            url = 'https://api.openai.com/v1/chat/completions'
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            }
            payload = {
                'model': self.model,
                'temperature': self.temperature,
                'messages': [
                    {'role': 'system', 'content': 'You are a precise code generator for Ryven nodes.'},
                    {'role': 'user', 'content': self.prompt},
                ],
            }
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=120) as resp:
                resp_text = resp.read().decode('utf-8')
                parsed = json.loads(resp_text)
                content = parsed.get('choices', [{}])[0].get('message', {}).get('content', '')
                if not content:
                    raise RuntimeError('Empty content from OpenAI response')
                self.finished.emit(content)
        except urllib.error.HTTPError as e:
            try:
                detail = e.read().decode('utf-8')
            except Exception:
                detail = str(e)
            self.errored.emit(f'HTTPError {e.code}: {detail}')
        except Exception as e:
            self.errored.emit(str(e))


