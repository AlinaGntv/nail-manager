import asyncio
from datetime import datetime

import gspread
from gspread import Worksheet

from app.database.models import Lead
from app.utils.logger import logger


class GoogleSheetsService:
    """Service for appending appointment leads to Google Sheets."""

    def __init__(
        self,
        service_account_file: str,
        sheet_id: str,
        worksheet_name: str = "Leads",
    ) -> None:
        self._service_account_file = service_account_file
        self._sheet_id = sheet_id
        self._worksheet_name = worksheet_name

    async def append_lead(self, lead: Lead) -> None:
        """Append a lead row to Google Sheets without blocking the event loop."""
        await asyncio.to_thread(self._append_lead_sync, lead)

    def _append_lead_sync(self, lead: Lead) -> None:
        """Synchronously append a lead using gspread."""
        worksheet = self._get_worksheet()
        row = [
            datetime.utcnow().isoformat(timespec="seconds"),
            lead.full_name or "",
            lead.phone or "",
            lead.service or "",
            lead.desired_datetime or "",
            lead.status,
            lead.username or "",
            str(lead.telegram_id),
        ]
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        logger.info("Lead id={} appended to Google Sheets", lead.id)

    def _get_worksheet(self) -> Worksheet:
        """Open the configured worksheet, creating it when missing."""
        client = gspread.service_account(filename=self._service_account_file)
        spreadsheet = client.open_by_key(self._sheet_id)
        try:
            return spreadsheet.worksheet(self._worksheet_name)
        except gspread.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(
                title=self._worksheet_name,
                rows=1000,
                cols=8,
            )
            worksheet.append_row(
                ["Дата", "Имя", "Телефон", "Услуга", "Желаемое время", "Статус", "Username", "Telegram ID"],
                value_input_option="USER_ENTERED",
            )
            return worksheet
