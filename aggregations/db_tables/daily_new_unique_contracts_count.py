import datetime

from . import DAY_LEN_SECONDS, daily_start_of_range, time_range_json
from ..periodic_aggregations import PeriodicAggregations


# This metric is computed based on `deployed_contracts` table in Analytics DB
class DailyNewUniqueContractsCount(PeriodicAggregations):
    def dependencies(self) -> list:
        return ["deployed_contracts"]

    @property
    def sql_create_table(self):
        # For September 2021, we have 10^6 accounts on the Mainnet.
        # It means we fit into integer (10^9)
        return """
            CREATE TABLE IF NOT EXISTS daily_new_unique_contracts_count
            (
                collected_for_day          DATE PRIMARY KEY,
                new_unique_contracts_count INTEGER NOT NULL
            )
        """

    @property
    def sql_drop_table(self):
        return """
            DROP TABLE IF EXISTS daily_new_unique_contracts_count
        """

    @property
    def sql_select(self):
        raise NotImplementedError(
            "No requests to Indexer DB needed for daily_new_unique_contracts_count"
        )

    @property
    def sql_insert(self):
        return """
            INSERT INTO daily_new_unique_contracts_count VALUES %s
            ON CONFLICT DO NOTHING
        """

    def collect(self, requested_timestamp: int) -> list:
        new_unique_hashes_select = """
            SELECT COUNT(code_sha256)
            FROM deployed_contracts
            WHERE first_created_by_block_timestamp >= %(from_timestamp)s
                AND first_created_by_block_timestamp < %(to_timestamp)s
        """

        from_timestamp = self.start_of_range(requested_timestamp)
        with self.analytics_connection.cursor() as analytics_cursor:
            analytics_cursor.execute(
                new_unique_hashes_select,
                time_range_json(from_timestamp, self.duration_seconds),
            )
            result = analytics_cursor.fetchall()
            return self.prepare_data(result, start_of_range=from_timestamp)

    @property
    def duration_seconds(self):
        return DAY_LEN_SECONDS

    def start_of_range(self, timestamp: int) -> int:
        return daily_start_of_range(timestamp)
