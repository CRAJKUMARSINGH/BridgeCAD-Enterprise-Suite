#!/usr/bin/env python3
"""
Enhanced I/O Utilities for Bridge GAD Generator
Intelligent input processing with format detection and auto-conversion
Integrates best practices from BridgeGAD-00, BridgeGADdrafter, and BridgeDraw
"""

import pandas as pd
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging

logger = logging.getLogger(__name__)


class SmartInputProcessor:
    """Intelligent input processor with format detection and conversion"""

    # Default parameters for bridge design
    DEFAULT_PARAMETERS = {
        'SCALE1': 186,
        'SCALE2': 100,
        'SKEW': 0,
        'DATUM': 100,
        'TOPRL': 110,
        'CCBR': 7500,
        'SLABTH': 200,
        'WCTH': 75,
        'LASLAB': 50000,
        'ABTLEN': 10000,
        'ABTH': 3000,
        'ABTW': 1000,
        'FUTW': 2000,
        'FUTD': 1500,
        'PIERTW': 1000,
        'PIERTH': 2000,
        'CAPB': 1500,
        'CAPH': 500,
    }

    def __init__(self):
        self.format_type = None
        self.parameters = {}

    def read_input(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Smart input reader with automatic format detection

        Supports:
        - Excel (.xlsx) - key-value, span data, standard 3-column
        - CSV (.csv) - various formats
        - JSON (.json) - structured data
        - YAML (.yaml, .yml) - configuration files
        - Text (.txt) - simple key-value pairs
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")

        logger.info(f"Reading input file: {file_path}")

        # Determine file type and read accordingly
        suffix = file_path.suffix.lower()

        if suffix in ['.xlsx', '.xls']:
            return self._read_excel_smart(file_path)
        elif suffix == '.csv':
            return self._read_csv_smart(file_path)
        elif suffix == '.json':
            return self._read_json(file_path)
        elif suffix in ['.yaml', '.yml']:
            return self._read_yaml(file_path)
        elif suffix == '.txt':
            return self._read_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

    def _read_excel_smart(self, file_path: Path) -> Dict[str, Any]:
        """
        Intelligent Excel reader with format detection

        Detects and handles:
        1. Key-value format (key, value columns)
        2. Span data format (Length, Width, Thickness, etc.)
        3. Standard 3-column format (Value, Variable, Description)
        4. Multi-sheet workbooks
        """
        try:
            # Try reading first sheet
            df = pd.read_excel(file_path, sheet_name=0)

            # Detect format type
            if self._is_key_value_format(df):
                logger.info("  → Detected key-value format")
                return self._convert_key_value_format(df)

            elif self._is_span_data_format(df):
                logger.info("  → Detected span data format")
                return self._convert_span_data_format(df)

            elif self._is_standard_format(df):
                logger.info("  → Detected standard 3-column format")
                return self._convert_standard_format(df)

            else:
                logger.warning("  → Unknown format, attempting intelligent parsing")
                return self._intelligent_parse(df)

        except Exception as e:
            logger.error(f"Error reading Excel file: {e}")
            # Return defaults if reading fails
            return self.DEFAULT_PARAMETERS.copy()

    def _is_key_value_format(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame is in key-value format"""
        cols_lower = [str(c).lower() for c in df.columns]
        return 'key' in cols_lower and 'value' in cols_lower

    def _is_span_data_format(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame contains span data"""
        cols_str = ' '.join([str(c).lower() for c in df.columns])
        return any(keyword in cols_str for keyword in ['length', 'span', 'width', 'thickness', 'pier'])

    def _is_standard_format(self, df: pd.DataFrame) -> bool:
        """Check if DataFrame is in standard 3-column format"""
        return len(df.columns) >= 3 and df.shape[0] > 5

    def _convert_key_value_format(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Convert key-value format to parameters dictionary"""
        params = self.DEFAULT_PARAMETERS.copy()

        # Find key and value columns
        key_col = None
        value_col = None

        for col in df.columns:
            col_lower = str(col).lower()
            if 'key' in col_lower:
                key_col = col
            elif 'value' in col_lower:
                value_col = col

        if key_col and value_col:
            for _, row in df.iterrows():
                key = str(row[key_col]).upper().strip()
                value = row[value_col]

                if pd.notna(value) and key:
                    try:
                        params[key] = float(value)
                    except (ValueError, TypeError):
                        params[key] = value

        logger.info(f"  ✅ Extracted {len(params)} parameters")
        return params

    def _convert_span_data_format(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Convert span data format to parameters dictionary"""
        params = self.DEFAULT_PARAMETERS.copy()

        # Extract span information
        if 'Length (m)' in df.columns or 'Length' in str(df.columns[0]):
            lengths = df[df.columns[0]].dropna().tolist()

            # Convert to mm and add to params
            total_length = sum(lengths) * 1000
            params['LBRIDGE'] = total_length
            params['NSPAN'] = len(lengths)

            # Add individual spans
            for i, length in enumerate(lengths, 1):
                params[f'SPAN{i}'] = length * 1000

        # Extract width
        width_cols = [c for c in df.columns if 'width' in str(c).lower()]
        if width_cols:
            width = df[width_cols[0]].iloc[0]
            if pd.notna(width):
                params['CCBR'] = float(width) * 1000

        # Extract thickness
        thickness_cols = [c for c in df.columns if 'thickness' in str(c).lower()]
        if thickness_cols:
            thickness = df[thickness_cols[0]].iloc[0]
            if pd.notna(thickness):
                params['SLABTH'] = float(thickness) * 1000

        # Extract pier width
        pier_cols = [c for c in df.columns if 'pier' in str(c).lower() and 'width' in str(c).lower()]
        if pier_cols:
            pier_width = df[pier_cols[0]].iloc[0]
            if pd.notna(pier_width):
                params['PIERTW'] = float(pier_width) * 1000

        logger.info(f"  ✅ Extracted {len(params)} parameters from span data")
        return params

    def _convert_standard_format(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Convert standard 3-column format to parameters dictionary"""
        params = self.DEFAULT_PARAMETERS.copy()

        # Assume columns are: Value, Variable, Description
        for _, row in df.iterrows():
            if len(row) >= 2:
                value = row.iloc[0]
                variable = str(row.iloc[1]).upper().strip()

                if pd.notna(value) and variable:
                    try:
                        params[variable] = float(value)
                    except (ValueError, TypeError):
                        params[variable] = value

        logger.info(f"  ✅ Extracted {len(params)} parameters from standard format")
        return params

    def _intelligent_parse(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Intelligent parsing for unknown formats"""
        params = self.DEFAULT_PARAMETERS.copy()

        # Try to extract any numeric data with labels
        for col in df.columns:
            col_name = str(col).upper().strip()

            # Skip if column name is too generic
            if col_name in ['UNNAMED', 'INDEX', '']:
                continue

            # Try to get first non-null value
            values = df[col].dropna()
            if len(values) > 0:
                try:
                    params[col_name] = float(values.iloc[0])
                except (ValueError, TypeError):
                    pass

        logger.info(f"  ⚠️  Intelligent parsing extracted {len(params)} parameters")
        return params

    def _read_csv_smart(self, file_path: Path) -> Dict[str, Any]:
        """Smart CSV reader with format detection"""
        try:
            df = pd.read_csv(file_path)

            # Use same detection logic as Excel
            if self._is_key_value_format(df):
                return self._convert_key_value_format(df)
            elif self._is_span_data_format(df):
                return self._convert_span_data_format(df)
            else:
                return self._convert_standard_format(df)

        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            return self.DEFAULT_PARAMETERS.copy()

    def _read_json(self, file_path: Path) -> Dict[str, Any]:
        """Read JSON configuration file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            # Convert all keys to uppercase
            params = {k.upper(): v for k, v in data.items()}

            # Merge with defaults
            result = self.DEFAULT_PARAMETERS.copy()
            result.update(params)

            logger.info(f"  ✅ Loaded {len(params)} parameters from JSON")
            return result

        except Exception as e:
            logger.error(f"Error reading JSON file: {e}")
            return self.DEFAULT_PARAMETERS.copy()

    def _read_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Read YAML configuration file"""
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)

            # Convert all keys to uppercase
            params = {k.upper(): v for k, v in data.items()}

            # Merge with defaults
            result = self.DEFAULT_PARAMETERS.copy()
            result.update(params)

            logger.info(f"  ✅ Loaded {len(params)} parameters from YAML")
            return result

        except Exception as e:
            logger.error(f"Error reading YAML file: {e}")
            return self.DEFAULT_PARAMETERS.copy()

    def _read_text(self, file_path: Path) -> Dict[str, Any]:
        """Read simple text file with key=value pairs"""
        params = self.DEFAULT_PARAMETERS.copy()

        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue

                    # Parse key=value or key: value
                    if '=' in line:
                        key, value = line.split('=', 1)
                    elif ':' in line:
                        key, value = line.split(':', 1)
                    else:
                        continue

                    key = key.strip().upper()
                    value = value.strip()

                    try:
                        params[key] = float(value)
                    except ValueError:
                        params[key] = value

            logger.info(f"  ✅ Loaded {len(params)} parameters from text file")
            return params

        except Exception as e:
            logger.error(f"Error reading text file: {e}")
            return self.DEFAULT_PARAMETERS.copy()

    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize parameters

        - Check for required parameters
        - Apply engineering constraints
        - Add calculated values
        """
        validated = params.copy()

        # Ensure required parameters exist
        required = ['SCALE1', 'SCALE2', 'DATUM', 'TOPRL', 'CCBR', 'SLABTH']
        for req in required:
            if req not in validated:
                validated[req] = self.DEFAULT_PARAMETERS[req]
                logger.warning(f"  ⚠️  Missing {req}, using default: {validated[req]}")

        # Calculate derived values
        if 'LBRIDGE' in validated and 'NSPAN' in validated:
            # Calculate span lengths if not provided
            nspan = int(validated['NSPAN'])
            lbridge = validated['LBRIDGE']

            for i in range(1, nspan + 1):
                if f'SPAN{i}' not in validated:
                    validated[f'SPAN{i}'] = lbridge / nspan

        # Calculate right chainage if not provided
        if 'RIGHT' not in validated and 'LEFT' in validated and 'LBRIDGE' in validated:
            validated['RIGHT'] = validated['LEFT'] + validated['LBRIDGE']

        logger.info(f"  ✅ Validated {len(validated)} parameters")
        return validated


# Convenience functions
def read_bridge_input(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Convenience function to read bridge input file

    Usage:
        params = read_bridge_input('input.xlsx')
    """
    processor = SmartInputProcessor()
    params = processor.read_input(file_path)
    return processor.validate_parameters(params)


def convert_to_standard_excel(input_file: Union[str, Path], output_file: Optional[Union[str, Path]] = None):
    """
    Convert any supported format to standard 3-column Excel format

    Usage:
        convert_to_standard_excel('input.json', 'output.xlsx')
    """
    processor = SmartInputProcessor()
    params = processor.read_input(input_file)

    if output_file is None:
        output_file = Path(input_file).with_suffix('.xlsx')

    # Create standard 3-column DataFrame
    data = []
    for key, value in params.items():
        description = key.replace('_', ' ').title()
        data.append([value, key, description])

    df = pd.DataFrame(data, columns=['Value', 'Variable', 'Description'])
    df.to_excel(output_file, index=False)

    logger.info(f"  ✅ Converted to standard format: {output_file}")
    return output_file
