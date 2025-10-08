from __future__ import annotations
import json
import urllib.request
import urllib.error
from qtpy.QtCore import QThread, Signal


class OpenAIWorkerGpt5(QThread):
    finished = Signal(str)
    errored = Signal(str)

    def __init__(self, prompt: str, api_key: str, model: str = 'gpt-5', temperature: float = 0.0):
        super().__init__()
        self.prompt = prompt
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        print("GPT-5 IN USE")

    def run(self):
        try:
            url = 'https://api.openai.com/v1/responses'
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
            }

            # The prompt template already enforces JSON output; responses API aggregates text in output_text.
            payload = {
                'model': self.model,
                'input': self.prompt,
                'max_output_tokens': 1800,
                'reasoning': {'effort': 'minimal'},
            }

            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            with urllib.request.urlopen(req, timeout=120) as resp:
                resp_text = resp.read().decode('utf-8')
                parsed = json.loads(resp_text)

                # Prefer convenience field when available
                content = parsed.get('output_text')

                # Fallback: Responses API structured output
                if not content:
                    try:
                        texts = []
                        output_items = parsed.get('output') or []
                        for item in output_items:
                            if not isinstance(item, dict):
                                continue
                            # Some variants may have direct text on the item
                            if 'text' in item and isinstance(item.get('text'), str):
                                texts.append(item.get('text'))
                            # Standard: message with content list
                            content_list = item.get('content')
                            if isinstance(content_list, list):
                                for c in content_list:
                                    if isinstance(c, dict):
                                        txt = c.get('text')
                                        if isinstance(txt, str):
                                            texts.append(txt)
                        content = ''.join(texts).strip()
                    except Exception:
                        content = ''

                if not content:
                    # Attach small snippet of raw response for debugging in UI logs
                    snippet = resp_text[:200].replace('\n', ' ')
                    raise RuntimeError(f'Empty content from OpenAI response (snippet): {snippet}')

                self.finished.emit(content)
        except urllib.error.HTTPError as e:
            try:
                detail = e.read().decode('utf-8')
            except Exception:
                detail = str(e)
            self.errored.emit(f'HTTPError {e.code}: {detail}')
        except Exception as e:
            self.errored.emit(str(e))


