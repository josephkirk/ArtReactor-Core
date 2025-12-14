{{imports}}
from typing import Any

class {{class_name}}({{base_class}}):
    def __init__(self, manifest: PluginManifest, context: Any):
        super().__init__(manifest, context)

    async def initialize(self):
        pass

    async def shutdown(self):
        pass

{{extra_methods}}
