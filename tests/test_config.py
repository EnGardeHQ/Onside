import pytest
from unittest.mock import patch
import os
from src.config import load_config, Config

def test_config_loading_from_env():
    """Test loading configuration from environment variables"""
    test_env = {
        'DATABASE_URL': 'postgresql://test:test@localhost:5432/test_db',
        'SECRET_KEY': 'test_secret_key',
        'API_VERSION': 'v1',
        'ENVIRONMENT': 'test',
        'LOG_LEVEL': 'DEBUG'
    }
    
    with patch.dict(os.environ, test_env, clear=True):
        config = Config(_skip_post_init=True)  # Skip environment-specific config
        
        assert isinstance(config, Config)
        assert config.database_url == test_env['DATABASE_URL']
        assert config.secret_key == test_env['SECRET_KEY']
        assert config.api_version == test_env['API_VERSION']
        assert config.environment == test_env['ENVIRONMENT']
        assert config.log_level == test_env['LOG_LEVEL']

def test_config_default_values():
    """Test default configuration values when environment variables are not set"""
    with patch.dict(os.environ, {}, clear=True):
        config = Config(_skip_post_init=True)  # Skip environment-specific config
        
        assert isinstance(config, Config)
        assert config.database_url == 'sqlite:///test.db'  # Default for testing
        assert config.environment == 'development'
        assert config.log_level == 'INFO'
        assert config.api_version == 'v1'

def test_config_validation():
    """Test configuration validation"""
    # Test with missing required SECRET_KEY
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="SECRET_KEY must be set"):
            config = load_config(validate=True)

    # Test with invalid DATABASE_URL format
    with patch.dict(os.environ, {'SECRET_KEY': 'test', 'DATABASE_URL': 'invalid_url'}, clear=True):
        with pytest.raises(ValueError, match="Invalid DATABASE_URL format"):
            config = load_config(validate=True)

def test_config_environment_specific():
    """Test environment-specific configuration loading"""
    test_env = {
        'ENVIRONMENT': 'production',
        'SECRET_KEY': 'prod_secret',
        'DATABASE_URL': 'postgresql://prod:pwd@prod-db:5432/prod_db'
    }
    
    with patch.dict(os.environ, test_env, clear=True):
        config = Config()  # Allow environment-specific config
        
        assert config.environment == 'production'
        assert config.log_level == 'WARNING'  # Production default
        assert config.allowed_origins == ['https://api.capilytics.com']  # Production domains

    test_env['ENVIRONMENT'] = 'development'
    with patch.dict(os.environ, test_env, clear=True):
        config = Config()  # Allow environment-specific config
        
        assert config.environment == 'development'
        assert config.log_level == 'INFO'  # Development default
        assert config.allowed_origins == ['*']  # Development allows all origins
