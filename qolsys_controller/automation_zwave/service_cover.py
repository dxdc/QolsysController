import logging
from typing import TYPE_CHECKING

from qolsys_controller.automation.service_cover import CoverService

if TYPE_CHECKING:
    from qolsys_controller.automation.device import QolsysAutomationDevice


LOGGER = logging.getLogger(__name__)


class CoverServiceZwave(CoverService):
    def __init__(
        self,
        automation_device: "QolsysAutomationDevice",
        endpoint: int,
    ) -> None:
        super().__init__(automation_device=automation_device, endpoint=endpoint)

    async def open(self) -> None:
        pass

    async def close(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def set_current_position(self) -> None:
        pass

    def supports_open(self) -> bool:
        return True

    def supports_close(self) -> bool:
        return True

    def supports_stop(self) -> bool:
        return False

    def supports_position(self) -> bool:
        return False

    def update_automation_service(self) -> None:
        super().update_automation_service()
