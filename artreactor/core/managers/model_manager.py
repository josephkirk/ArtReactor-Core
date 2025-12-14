from typing import Dict, Any, Optional
from artreactor.core.interfaces.model_plugin import ModelPlugin
import logging

logger = logging.getLogger(__name__)


class ModelManager:
    def __init__(self):
        self._models: Dict[str, Any] = {}
        self._plugins: Dict[str, ModelPlugin] = {}

    async def register_plugin(self, plugin: ModelPlugin):
        """Registers a ModelPlugin and instantiates the model."""
        if plugin.model_id in self._plugins:
            logger.warning(f"Model {plugin.model_id} already registered. Overwriting.")

        self._plugins[plugin.model_id] = plugin
        try:
            model = plugin.get_model()
            self._models[plugin.model_id] = model
            logger.info(f"Successfully registered model: {plugin.model_id}")
        except Exception as e:
            logger.error(f"Failed to load model {plugin.model_id}: {e}")
            if plugin.model_id in self._plugins:
                del self._plugins[plugin.model_id]
            raise e

    def get_model(self, model_id: str) -> Optional[Any]:
        return self._models.get(model_id)

    def list_models(self) -> Dict[str, str]:
        return {pid: p.backend for pid, p in self._plugins.items()}
