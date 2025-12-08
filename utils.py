import sqlite3
from typing import List, Dict, Any
import json
import streamlit as st
import logging
import yaml
import os
from datetime import datetime

logger = logging.getLogger(__name__)
import io
import csv

# --- Parsing Utils ---

def parse_csv_to_text(file_content: str) -> str:
    """
    Parses a CSV string into a readable text format for LLM context.
    assumes headers are present.
    """
    try:
        output_lines = []
        # Use io.StringIO to treat string as file-like for csv module
        csv_file = io.StringIO(file_content)
        reader = csv.DictReader(csv_file)
        
        if not reader.fieldnames:
             return "Error: CSV appears empty or malformed."

        for i, row in enumerate(reader):
            # Create a compact string representation of the row
            # e.g. "Item 1: Title='Foo', Category='Bar'"
            row_str = ", ".join(f"{k}='{v}'" for k, v in row.items() if v)
            output_lines.append(f"Entry {i+1}: {row_str}")
        
        return "\n".join(output_lines)
    except Exception as e:
        logger.error(f"CSV Parsing Error: {e}")
        return f"Error parsing CSV data: {e}"

def parse_json_to_text(file_content: str) -> str:
    """
    Parses various JSON structures into a flat readable text list.
    Handles list of objects, or single object.
    """
    try:
        data = json.loads(file_content)
        output_lines = []

        if isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    # Flat string for dict items
                    item_str = ", ".join(f"{k}='{v}'" for k, v in item.items() if isinstance(v, (str, int, float, bool)))
                    output_lines.append(f"Item {i+1}: {item_str}")
                else:
                    output_lines.append(f"Item {i+1}: {str(item)}")
        elif isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, list):
                    output_lines.append(f"Category '{k}': {', '.join(map(str, v))}")
                else:
                    output_lines.append(f"{k}: {v}")
        else:
            return str(data)

        return "\n".join(output_lines)
    except Exception as e:
        logger.error(f"JSON Parsing Error: {e}")
        return f"Error parsing JSON data: {e}"

OUTPUT_DIR = "pbt_outputs"

def save_output_to_json(data: Dict[str, Any], prefix: str) -> str:
    """Saves a dictionary to a timestamped JSON file in the output directory."""
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_prefix = "".join(c for c in prefix if c.isalnum() or c in ('_', '-')).rstrip()
        filename = f"{safe_prefix}_{timestamp}.json"
        filepath = os.path.join(OUTPUT_DIR, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        logger.info(f"Successfully saved output to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Failed to save output to JSON file: {e}", exc_info=True)
        return ""

def load_config(config_files: List[str]) -> Dict[str, Any]:
    """Load configuration from multiple YAML files."""
    config = {}
    try:
        for file in config_files:
            with open(file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                if config_data:
                    config.update(config_data)
        logger.info(f"Configuration loaded successfully from: {', '.join(config_files)}")
        return config
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e.filename}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML configuration: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading configuration: {e}")
        raise

def initialize_database(database_name: str):
    """Initializes the database and creates the prompts table if it doesn't exist."""
    try:
        with sqlite3.connect(database_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    style TEXT NOT NULL,
                    use_case TEXT NOT NULL,
                    template TEXT NOT NULL,
                    variables TEXT,  -- JSON stringified list
                    variable_explanations TEXT, -- JSON stringified dict
                    examples TEXT, -- JSON stringified list
                    tips TEXT, -- JSON stringified list
                    validation TEXT, -- JSON stringified dict
                    test_guidance TEXT, -- JSON stringified dict
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # New table for Market Data Knowledge Base
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    source TEXT,
                    tags TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {e}", exc_info=True)
        raise

def save_market_data(database_name: str, content: str, source: str = "manual", tags: str = ""):
    """Saves market trend data to the Knowledge Base."""
    try:
        with sqlite3.connect(database_name) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO market_data (content, source, tags) VALUES (?, ?, ?)", (content, source, tags))
            conn.commit()
            logger.info(f"Market data saved from source: {source}")
    except sqlite3.Error as e:
        logger.error(f"Error saving market data: {e}", exc_info=True)
        raise

def get_all_market_data(database_name: str) -> List[Dict[str, Any]]:
    """Fetches all market data entries."""
    try:
        with sqlite3.connect(database_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM market_data ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error as e:
        logger.error(f"Error fetching market data: {e}", exc_info=True)
        return []

def delete_market_data(database_name: str, data_id: int):
    """Deletes a specific market data entry."""
    try:
        with sqlite3.connect(database_name) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM market_data WHERE id = ?", (data_id,))
            conn.commit()
            logger.info(f"Deleted market data ID: {data_id}")
    except sqlite3.Error as e:
        logger.error(f"Error deleting market data: {e}", exc_info=True)
        raise

def save_prompt_to_db(database_name: str, prompt_data: Dict[str, Any]):
    """Saves prompt data to the SQLite database."""
    prompt_data_with_defaults = {
        "topic": prompt_data.get("topic", ""),
        "content_type": prompt_data.get("content_type", ""),
        "platform": prompt_data.get("platform", ""),
        "style": prompt_data.get("style", "") if isinstance(prompt_data.get("style"), str) else ", ".join(prompt_data.get("style", [])),
        "use_case": prompt_data.get("use_case", "") if isinstance(prompt_data.get("use_case"), str) else ", ".join(prompt_data.get("use_case", [])),
        "template": prompt_data.get("template", ""),
        "variables": prompt_data.get("variables", []),
        "variable_explanations": prompt_data.get("variable_explanations", {}),
        "examples": prompt_data.get("examples", []),
        "tips": prompt_data.get("tips", []),
        "validation": prompt_data.get("validation", {}),
        "test_guidance": prompt_data.get("test_guidance", {})
    }
    try:
        with sqlite3.connect(database_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO prompts (
                    topic, content_type, platform, style, use_case, template,
                    variables, variable_explanations, examples, tips, validation, test_guidance
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prompt_data_with_defaults["topic"],
                prompt_data_with_defaults["content_type"],
                prompt_data_with_defaults["platform"],
                prompt_data_with_defaults["style"],
                prompt_data_with_defaults["use_case"],
                prompt_data_with_defaults["template"],
                json.dumps(prompt_data_with_defaults["variables"]),
                json.dumps(prompt_data_with_defaults["variable_explanations"]),
                json.dumps(prompt_data_with_defaults["examples"]),
                json.dumps(prompt_data_with_defaults["tips"]),
                json.dumps(prompt_data_with_defaults["validation"]),
                json.dumps(prompt_data_with_defaults["test_guidance"])
            ))
            conn.commit()
            logger.info("Prompt saved successfully.")
    except sqlite3.Error as e:
        logger.error(f"Database Error: {e}", exc_info=True)
        raise

def update_prompt_in_db(database_name: str, prompt_id: int, updates: Dict[str, Any]):
    """Updates a specific prompt in the database."""
    if not updates:
        logger.warning("Update called with no data to update.")
        return

    try:
        with sqlite3.connect(database_name) as conn:
            cursor = conn.cursor()
            
            set_clause = []
            values = []
            for key, value in updates.items():
                set_clause.append(f"{key} = ?")
                # Serialize if the value is a list or dict
                if isinstance(value, (dict, list)):
                    values.append(json.dumps(value))
                else:
                    values.append(value)
            
            values.append(prompt_id)
            
            sql = f"UPDATE prompts SET {', '.join(set_clause)} WHERE id = ?"
            
            cursor.execute(sql, tuple(values))
            conn.commit()
            logger.info(f"Prompt ID {prompt_id} updated successfully with keys: {list(updates.keys())}")
    except sqlite3.Error as e:
        logger.error(f"Database update error for prompt ID {prompt_id}: {e}", exc_info=True)
        raise

def get_all_prompts_from_db(database_name: str) -> List[Dict[str, Any]]:
    """Fetches all prompts from the SQLite database and deserializes JSON fields."""
    try:
        with sqlite3.connect(database_name) as conn:
            conn.row_factory = sqlite3.Row # This allows accessing columns by name
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM prompts ORDER BY created_at DESC")
            rows = cursor.fetchall()
            prompts = []
            for row in rows:
                prompt_dict = dict(row)
                # Deserialize JSON fields
                for key in ["variables", "variable_explanations", "examples", "tips", "validation", "test_guidance"]:
                    if prompt_dict[key] and isinstance(prompt_dict[key], str):
                        try:
                            prompt_dict[key] = json.loads(prompt_dict[key])
                        except json.JSONDecodeError:
                            logger.warning(f"Could not decode JSON for key '{key}' in prompt ID {prompt_dict['id']}")
                            prompt_dict[key] = {}
                prompts.append(prompt_dict)
            return prompts
    except sqlite3.Error as e:
        st.error(f"Error fetching prompts from database: {e}")
        logger.error(f"Database Error: {e}", exc_info=True)
        return []
