"""
Test configuration and fixtures for EQDataScraper backend tests.
"""
import pytest
import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from datetime import datetime

# Set testing environment variables before importing app
os.environ['TESTING'] = '1'
os.environ['DATABASE_URL'] = ''  # Force file-based cache for tests
os.environ['PORT'] = '5999'
os.environ['CACHE_EXPIRY_HOURS'] = '1'
os.environ['PRICING_CACHE_EXPIRY_HOURS'] = '1'

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables before any tests run."""
    os.environ['TESTING'] = '1'
    os.environ['DATABASE_URL'] = ''
    yield
    # Cleanup after all tests
    if 'TESTING' in os.environ:
        del os.environ['TESTING']

@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory for testing."""
    temp_dir = tempfile.mkdtemp()
    cache_dir = os.path.join(temp_dir, 'cache')
    os.makedirs(cache_dir, exist_ok=True)
    
    with patch('app.CACHE_DIR', cache_dir):
        with patch('app.SPELLS_CACHE_FILE', os.path.join(cache_dir, 'spells_cache.json')):
            with patch('app.PRICING_CACHE_FILE', os.path.join(cache_dir, 'pricing_cache.json')):
                with patch('app.SPELL_DETAILS_CACHE_FILE', os.path.join(cache_dir, 'spell_details_cache.json')):
                    with patch('app.METADATA_CACHE_FILE', os.path.join(cache_dir, 'cache_metadata.json')):
                        yield cache_dir
    
    # Cleanup
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def mock_app():
    """Create a Flask test client."""
    # Import app after environment is set
    import app as flask_app
    
    # Clear any existing cache data
    flask_app.spells_cache.clear()
    flask_app.spell_details_cache.clear()
    flask_app.cache_timestamp.clear()
    flask_app.pricing_cache_timestamp.clear()
    flask_app.last_scrape_time.clear()
    flask_app.pricing_lookup.clear()
    
    flask_app.app.config['TESTING'] = True
    return flask_app.app.test_client()

@pytest.fixture
def sample_spell_data():
    """Sample spell data for testing."""
    return [
        {
            'name': 'Courage',
            'level': 1,
            'mana': '10',
            'skill': 'ABJURATION',
            'target_type': 'Single target',
            'spell_id': '202',
            'effects': 'Increase AC by 10.5 to 15',
            'icon': 'https://alla.clumsysworld.com/images/icons/spell_202.png',
            'pricing': None
        },
        {
            'name': 'Flash of Light',
            'level': 1,
            'mana': '10',
            'skill': 'EVOCATION',
            'target_type': 'Single target',
            'spell_id': '203',
            'effects': 'Decrease Hitpoints by 5 to 8',
            'icon': 'https://alla.clumsysworld.com/images/icons/spell_203.png',
            'pricing': None
        }
    ]

@pytest.fixture
def sample_pricing_data():
    """Sample pricing data for testing."""
    return {
        '202': {
            'platinum': 0,
            'gold': 0,
            'silver': 4,
            'bronze': 0,
            'unknown': False
        },
        '203': {
            'platinum': 0,
            'gold': 0,
            'silver': 4,
            'bronze': 0,
            'unknown': False
        },
        '999': {
            'platinum': 0,
            'gold': 0,
            'silver': 0,
            'bronze': 0,
            'unknown': True
        }
    }

@pytest.fixture
def sample_spell_details():
    """Sample spell details cache data."""
    return {
        '202': {
            'cast_time': '1.5 sec',
            'duration': '27 min (270 ticks)',
            'effects': ['Increase AC by 10.5 to 15'],
            'pricing': {
                'platinum': 0,
                'gold': 0,
                'silver': 4,
                'bronze': 0,
                'unknown': False
            },
            'range': '100',
            'resist': 'None',
            'skill': 'ABJURATION',
            'target_type': 'Single target'
        },
        '203': {
            'cast_time': '2.25 sec',
            'duration': 'Instant',
            'effects': ['Decrease Hitpoints by 5 to 8'],
            'pricing': {
                'platinum': 0,
                'gold': 0,
                'silver': 4,
                'bronze': 0,
                'unknown': False
            },
            'range': '200',
            'resist': 'Magic',
            'skill': 'EVOCATION',
            'target_type': 'Single target'
        }
    }

@pytest.fixture
def mock_requests():
    """Mock requests for external API calls."""
    with patch('requests.Session.get') as mock_get:
        # Default successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html>
            <body>
                <table>
                    <tr><td>Cast Time:</td><td>1.5 sec</td></tr>
                    <tr><td>Duration:</td><td>27 min (270 ticks)</td></tr>
                </table>
            </body>
        </html>
        """
        mock_get.return_value = mock_response
        yield mock_get

@pytest.fixture
def current_time():
    """Fixed current time for testing."""
    return datetime(2025, 1, 1, 12, 0, 0).isoformat()

@pytest.fixture
def setup_cache_data(temp_cache_dir):
    """Set up cache files with test data."""
    import app
    
    # Sample cache data
    spells_data = {
        'cleric': [
            {
                'name': 'Courage',
                'level': 1,
                'spell_id': '202',
                'pricing': {'silver': 4, 'unknown': False}
            },
            {
                'name': 'Flash of Light', 
                'level': 1,
                'spell_id': '203',
                'pricing': {'silver': 4, 'unknown': False}
            }
        ]
    }
    
    metadata = {
        'cache_timestamp': {'cleric': datetime.now().isoformat()},
        'pricing_cache_timestamp': {
            '202': datetime.now().isoformat(),
            '203': datetime.now().isoformat()
        },
        'last_scrape_time': {'cleric': datetime.now().isoformat()}
    }
    
    # Write test cache files
    with open(os.path.join(temp_cache_dir, 'spells_cache.json'), 'w') as f:
        json.dump(spells_data, f)
    
    with open(os.path.join(temp_cache_dir, 'cache_metadata.json'), 'w') as f:
        json.dump(metadata, f)
    
    return {
        'spells': spells_data,
        'metadata': metadata
    }