import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from src.utils.incremental import get_last_load_timestamp, detect_changes


class TestIncrementalLoading(unittest.TestCase):
    """Test incremental loading utilities"""

    @patch('src.utils.incremental.get_connection')
    def test_get_last_load_timestamp_with_data(self, mock_get_connection):
        """Test retrieving last load timestamp when data exists"""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock result
        expected_timestamp = datetime(2025, 1, 15, 10, 30, 0)
        mock_cursor.fetchone.return_value = (expected_timestamp,)

        # Execute
        result = get_last_load_timestamp('fact_encounters', 'created_at')

        # Assert
        self.assertEqual(result, expected_timestamp)
        mock_cursor.execute.assert_called_once()

    @patch('src.utils.incremental.get_connection')
    def test_get_last_load_timestamp_empty_table(self, mock_get_connection):
        """Test retrieving timestamp from empty table returns None"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock empty result
        mock_cursor.fetchone.return_value = (None,)

        # Execute
        result = get_last_load_timestamp('fact_encounters')

        # Assert
        self.assertIsNone(result)

    @patch('src.utils.incremental.get_connection')
    def test_detect_changes_new_records(self, mock_get_connection):
        """Test detecting new records"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock no existing records
        mock_cursor.fetchall.return_value = []

        # Source data
        source_data = [
            {'patient_id': 'p1', 'address': '123 Main St', 'city': 'Boston'}
        ]

        # Execute
        changes = detect_changes(
            'dim_patients',
            source_data,
            key_column='patient_id',
            compare_columns=['address', 'city']
        )

        # Assert
        self.assertEqual(len(changes['new']), 1)
        self.assertEqual(len(changes['updated']), 0)
        self.assertEqual(len(changes['unchanged']), 0)

    @patch('src.utils.incremental.get_connection')
    def test_detect_changes_updated_records(self, mock_get_connection):
        """Test detecting updated records"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock existing record with different values
        mock_cursor.fetchall.return_value = [
            ('p1', '123 Old St', 'Cambridge')  # key, address, city
        ]

        # Source data with updated values
        source_data = [
            {'patient_id': 'p1', 'address': '123 New St', 'city': 'Boston'}
        ]

        # Execute
        changes = detect_changes(
            'dim_patients',
            source_data,
            key_column='patient_id',
            compare_columns=['address', 'city']
        )

        # Assert
        self.assertEqual(len(changes['new']), 0)
        self.assertEqual(len(changes['updated']), 1)
        self.assertEqual(len(changes['unchanged']), 0)

    @patch('src.utils.incremental.get_connection')
    def test_detect_changes_unchanged_records(self, mock_get_connection):
        """Test detecting unchanged records"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock existing record with same values
        mock_cursor.fetchall.return_value = [
            ('p1', '123 Main St', 'Boston')
        ]

        source_data = [
            {'patient_id': 'p1', 'address': '123 Main St', 'city': 'Boston'}
        ]

        changes = detect_changes(
            'dim_patients',
            source_data,
            key_column='patient_id',
            compare_columns=['address', 'city']
        )

        self.assertEqual(len(changes['new']), 0)
        self.assertEqual(len(changes['updated']), 0)
        self.assertEqual(len(changes['unchanged']), 1)

    @patch('src.utils.incremental.get_connection')
    def test_detect_changes_empty_source(self, mock_get_connection):
        """Test detect_changes with empty source data returns empty categories"""
        mock_conn = MagicMock()
        mock_get_connection.return_value = mock_conn

        changes = detect_changes(
            'dim_patients',
            source_data=[],
            key_column='patient_id',
            compare_columns=['address', 'city']
        )

        self.assertEqual(len(changes['new']), 0)
        self.assertEqual(len(changes['updated']), 0)
        self.assertEqual(len(changes['unchanged']), 0)
        # Should not hit the database for empty input
        mock_conn.cursor.assert_not_called()


if __name__ == '__main__':
    unittest.main()
