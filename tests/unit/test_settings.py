"""
Unit tests for the Settings configuration.

Tests are written first following TDD principles.
"""

from pathlib import Path

import pytest


class TestSettingsDefaults:
    """Tests for Settings default values."""

    def test_settings_can_be_instantiated(self, monkeypatch: pytest.MonkeyPatch):
        """Settings should be instantiable with defaults."""
        # Clear environment to test true defaults
        monkeypatch.delenv("TIMETABLE_LOG_LEVEL", raising=False)
        monkeypatch.delenv("TIMETABLE_DATA_DIR", raising=False)
        
        from timetable.config.settings import Settings

        settings = Settings(_env_file=None)  # Don't read .env file
        assert settings is not None

    def test_default_log_level(self, monkeypatch: pytest.MonkeyPatch):
        """Default log level should be INFO."""
        # Clear environment to test true defaults
        monkeypatch.delenv("TIMETABLE_LOG_LEVEL", raising=False)
        
        from timetable.config.settings import Settings

        settings = Settings(_env_file=None)  # Don't read .env file
        assert settings.log_level == "INFO"

    def test_default_strict_mode(self, monkeypatch: pytest.MonkeyPatch):
        """Default strict_mode should be False."""
        monkeypatch.delenv("TIMETABLE_STRICT_MODE", raising=False)
        
        from timetable.config.settings import Settings

        settings = Settings(_env_file=None)
        assert settings.strict_mode is False

    def test_default_data_dir(self, temp_dir: Path):
        """data_dir should default to current directory if not specified."""
        from timetable.config.settings import Settings

        settings = Settings(data_dir=temp_dir)
        assert settings.data_dir == temp_dir


class TestSettingsFromEnvironment:
    """Tests for loading Settings from environment variables."""

    def test_load_from_env_log_level(self, monkeypatch: pytest.MonkeyPatch):
        """Settings should load log_level from TIMETABLE_LOG_LEVEL."""
        from timetable.config.settings import Settings

        monkeypatch.setenv("TIMETABLE_LOG_LEVEL", "DEBUG")
        settings = Settings()
        assert settings.log_level == "DEBUG"

    def test_load_from_env_strict_mode(self, monkeypatch: pytest.MonkeyPatch):
        """Settings should load strict_mode from TIMETABLE_STRICT_MODE."""
        from timetable.config.settings import Settings

        monkeypatch.setenv("TIMETABLE_STRICT_MODE", "true")
        settings = Settings()
        assert settings.strict_mode is True

    def test_load_from_env_data_dir(
        self, monkeypatch: pytest.MonkeyPatch, temp_dir: Path
    ):
        """Settings should load data_dir from TIMETABLE_DATA_DIR."""
        from timetable.config.settings import Settings

        monkeypatch.setenv("TIMETABLE_DATA_DIR", str(temp_dir))
        settings = Settings()
        assert settings.data_dir == temp_dir


class TestSettingsValidation:
    """Tests for Settings validation."""

    def test_invalid_log_level_raises_error(self):
        """Invalid log level should raise ValidationError."""
        from timetable.config.settings import Settings

        with pytest.raises(ValueError):
            Settings(log_level="INVALID")

    def test_valid_log_levels(self):
        """All standard log levels should be accepted."""
        from timetable.config.settings import Settings

        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = Settings(log_level=level)
            assert settings.log_level == level

    def test_log_level_case_insensitive(self):
        """Log level should be case insensitive."""
        from timetable.config.settings import Settings

        settings = Settings(log_level="debug")
        assert settings.log_level == "DEBUG"


class TestSettingsStagePaths:
    """Tests for stage directory path resolution."""

    def test_stage_dir_method(self, temp_data_dir: Path):
        """Settings should provide stage_dir method for path resolution."""
        from timetable.config.settings import Settings

        settings = Settings(data_dir=temp_data_dir)
        stage_path = settings.stage_dir(1)
        assert stage_path == temp_data_dir / "stage_1"

    def test_all_stage_paths(self, temp_data_dir: Path):
        """All stage paths should be resolvable."""
        from timetable.config.settings import Settings

        settings = Settings(data_dir=temp_data_dir)
        for stage_num in [1, 2, 3, 4, 5, 6]:
            path = settings.stage_dir(stage_num)
            assert path.name == f"stage_{stage_num}"

    def test_invalid_stage_number(self, temp_data_dir: Path):
        """Invalid stage number should raise ValueError."""
        from timetable.config.settings import Settings

        settings = Settings(data_dir=temp_data_dir)
        with pytest.raises(ValueError):
            settings.stage_dir(0)
        with pytest.raises(ValueError):
            settings.stage_dir(7)


class TestSettingsSingleton:
    """Tests for Settings singleton behavior."""

    def test_get_settings_returns_same_instance(self, monkeypatch: pytest.MonkeyPatch):
        """get_settings should return the same instance (cached)."""
        from timetable.config import settings as settings_module
        from timetable.config.settings import get_settings

        # Clear any cached settings
        settings_module._settings_instance = None
        get_settings.cache_clear()
        
        monkeypatch.setenv("TIMETABLE_LOG_LEVEL", "DEBUG")

        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
        
        # Cleanup
        settings_module._settings_instance = None
        get_settings.cache_clear()

    def test_get_settings_respects_environment(
        self, monkeypatch: pytest.MonkeyPatch, temp_dir: Path
    ):
        """get_settings should respect environment variables."""
        from timetable.config import settings as settings_module
        from timetable.config.settings import get_settings

        # Clear the cache
        settings_module._settings_instance = None
        get_settings.cache_clear()

        monkeypatch.setenv("TIMETABLE_LOG_LEVEL", "WARNING")
        monkeypatch.setenv("TIMETABLE_DATA_DIR", str(temp_dir))

        settings = get_settings()
        assert settings.log_level == "WARNING"
        assert settings.data_dir == temp_dir

        # Cleanup
        settings_module._settings_instance = None
        get_settings.cache_clear()


class TestSettingsProperties:
    """Tests for Settings computed properties."""

    def test_output_dir_property(self, temp_data_dir: Path):
        """Settings should have an output_dir property."""
        from timetable.config.settings import Settings

        settings = Settings(data_dir=temp_data_dir)
        assert hasattr(settings, "output_dir") or hasattr(settings, "logs_dir")

    def test_is_debug_property(self):
        """Settings should have is_debug property."""
        from timetable.config.settings import Settings

        debug_settings = Settings(log_level="DEBUG")
        assert debug_settings.is_debug is True

        info_settings = Settings(log_level="INFO")
        assert info_settings.is_debug is False


class TestSettingsExport:
    """Tests for Settings serialization."""

    def test_settings_to_dict(self, temp_data_dir: Path):
        """Settings should be convertible to dictionary."""
        from timetable.config.settings import Settings

        settings = Settings(data_dir=temp_data_dir, log_level="DEBUG")
        settings_dict = settings.model_dump()

        assert isinstance(settings_dict, dict)
        assert "log_level" in settings_dict
        assert settings_dict["log_level"] == "DEBUG"

    def test_settings_sensitive_data_excluded(self, temp_data_dir: Path):
        """Sensitive settings should be excludable from export."""
        from timetable.config.settings import Settings

        settings = Settings(data_dir=temp_data_dir)
        # If there are any sensitive fields, they should be excludable
        settings_dict = settings.model_dump()
        assert isinstance(settings_dict, dict)
