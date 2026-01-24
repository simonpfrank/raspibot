"""Unit tests for raspibot.movement.scanner module."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from raspibot.movement.scanner import ScanPattern


class TestScanPattern:
    """Test ScanPattern initialization and configuration."""
    
    def test_init_default_parameters(self):
        """Test default FOV and overlap initialization."""
        pattern = ScanPattern()
        
        assert pattern.fov_degrees == 66.3
        assert pattern.overlap_degrees == 10.0
    
    def test_init_custom_parameters(self):
        """Test custom parameter initialization."""
        pattern = ScanPattern(fov_degrees=90.0, overlap_degrees=15.0)
        
        assert pattern.fov_degrees == 90.0
        assert pattern.overlap_degrees == 15.0


class TestPositionCalculation:
    """Test scan position calculation logic."""
    
    def test_calculate_positions_default_settings(self):
        """Test position calculation with defaults."""
        pattern = ScanPattern()  # FOV=66.3, overlap=10.0
        positions = pattern.calculate_positions()
        
        # Should return a list of angles
        assert isinstance(positions, list)
        assert len(positions) > 0
        
        # All positions should be within servo range
        for pos in positions:
            assert 0 <= pos <= 180
        
        # Should be sorted
        assert positions == sorted(positions)
    
    def test_calculate_positions_custom_fov(self):
        """Test with different FOV values."""
        # Narrow FOV should need more positions
        narrow_pattern = ScanPattern(fov_degrees=30.0, overlap_degrees=5.0)
        narrow_positions = narrow_pattern.calculate_positions()
        
        # Wide FOV should need fewer positions
        wide_pattern = ScanPattern(fov_degrees=120.0, overlap_degrees=5.0)
        wide_positions = wide_pattern.calculate_positions()
        
        # Narrow FOV should require more positions for same coverage
        assert len(narrow_positions) > len(wide_positions)
    
    def test_calculate_positions_custom_overlap(self):
        """Test with different overlap values."""
        # High overlap should need more positions
        high_overlap = ScanPattern(fov_degrees=66.3, overlap_degrees=20.0)
        high_positions = high_overlap.calculate_positions()
        
        # Low overlap should need fewer positions
        low_overlap = ScanPattern(fov_degrees=66.3, overlap_degrees=5.0)
        low_positions = low_overlap.calculate_positions()
        
        # Higher overlap should require more positions
        assert len(high_positions) >= len(low_positions)
    
    def test_calculate_positions_edge_coverage(self):
        """Test full range coverage."""
        pattern = ScanPattern(fov_degrees=90.0, overlap_degrees=10.0)
        positions = pattern.calculate_positions()
        
        # Should start near minimum angle
        assert positions[0] <= 10  # Close to 0
        
        # Should end near maximum angle
        assert positions[-1] >= 170  # Close to 180
    
    def test_calculate_positions_boundary_conditions(self):
        """Test edge cases."""
        # Very wide FOV
        wide_pattern = ScanPattern(fov_degrees=180.0, overlap_degrees=0.0)
        wide_positions = wide_pattern.calculate_positions()
        
        # Should need only one position for full coverage
        assert len(wide_positions) <= 2
        
        # Very narrow FOV
        narrow_pattern = ScanPattern(fov_degrees=10.0, overlap_degrees=1.0)
        narrow_positions = narrow_pattern.calculate_positions()
        
        # Should need many positions
        assert len(narrow_positions) >= 15
    
    def test_calculate_positions_effective_fov_calculation(self):
        """Test effective FOV calculation logic."""
        pattern = ScanPattern(fov_degrees=60.0, overlap_degrees=10.0)
        positions = pattern.calculate_positions()
        
        # Effective FOV = 60 - 10 = 50 degrees
        # Range = 180 - 0 = 180 degrees
        # Expected positions = 180/50 + 1 = 4.6 + 1 = 5 positions
        expected_positions = int(180 / 50) + 1
        
        # Should be close to calculated value
        assert abs(len(positions) - expected_positions) <= 1


class TestMovement:
    """Test servo movement methods."""
    
    def test_move_to_position_direct(self):
        """Test direct servo movement."""
        pattern = ScanPattern()
        mock_controller = Mock()

        pattern.move_to_position(mock_controller, 90.0, 45.0)

        # Should call set_servo_angle for both servos
        assert mock_controller.set_servo_angle.call_count == 2

        # Check calls were made with correct servo names and angles
        calls = mock_controller.set_servo_angle.call_args_list

        # Pan servo to 90 degrees
        assert calls[0][0] == ("pan", 90.0)
        # Tilt servo to 45 degrees
        assert calls[1][0] == ("tilt", 45.0)

    @pytest.mark.asyncio
    async def test_move_to_position_async_with_smooth(self):
        """Test async movement with smooth capability."""
        pattern = ScanPattern()
        mock_controller = Mock()
        mock_controller.smooth_move_to_angle = AsyncMock()

        await pattern.move_to_position_async(mock_controller, 120.0, 60.0, speed=0.8)

        # Should call smooth_move_to_angle for both servos
        assert mock_controller.smooth_move_to_angle.call_count == 2

        # Check calls were made correctly
        calls = mock_controller.smooth_move_to_angle.call_args_list

        # Should move both servos concurrently
        assert calls[0][0] == ("pan", 120.0, 0.8)
        assert calls[1][0] == ("tilt", 60.0, 0.8)
    
    @pytest.mark.asyncio
    async def test_move_to_position_async_fallback(self):
        """Test async fallback to direct movement."""
        pattern = ScanPattern()
        mock_controller = Mock()
        
        # Remove the smooth_move_to_angle attribute to trigger fallback
        del mock_controller.smooth_move_to_angle
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            await pattern.move_to_position_async(mock_controller, 45.0, 90.0)
            
            # Should fallback to direct movement in thread
            mock_to_thread.assert_called_once()
            
            # Should have called the direct movement method
            assert mock_to_thread.call_args[0][0] == pattern.move_to_position
    
    def test_move_to_position_parameter_validation(self):
        """Test parameter validation in movement."""
        pattern = ScanPattern()
        mock_controller = Mock()
        
        # Test with boundary angles
        pattern.move_to_position(mock_controller, 0.0, 0.0)
        pattern.move_to_position(mock_controller, 180.0, 180.0)
        
        # Should complete without errors
        assert mock_controller.set_servo_angle.call_count == 4  # 2 calls each
    
    @pytest.mark.asyncio
    async def test_move_to_position_async_speed_parameter(self):
        """Test speed parameter handling."""
        pattern = ScanPattern()
        mock_controller = Mock()
        mock_controller.smooth_move_to_angle = AsyncMock()
        
        # Test default speed
        await pattern.move_to_position_async(mock_controller, 90.0, 90.0)
        
        calls = mock_controller.smooth_move_to_angle.call_args_list
        # Default speed should be 1.0
        assert calls[0][0][2] == 1.0
        assert calls[1][0][2] == 1.0
        
        # Reset and test custom speed
        mock_controller.reset_mock()
        await pattern.move_to_position_async(mock_controller, 90.0, 90.0, speed=0.5)
        
        calls = mock_controller.smooth_move_to_angle.call_args_list
        # Custom speed should be passed through
        assert calls[0][0][2] == 0.5
        assert calls[1][0][2] == 0.5


class TestScanPatternIntegration:
    """Test integration scenarios."""
    
    def test_full_scan_sequence(self):
        """Test a complete scan sequence."""
        pattern = ScanPattern(fov_degrees=60.0, overlap_degrees=10.0)
        mock_controller = Mock()
        
        positions = pattern.calculate_positions()
        
        # Simulate moving through all positions
        for i, pos in enumerate(positions):
            pattern.move_to_position(mock_controller, pos, 90.0)
        
        # Should have called set_servo_angle for each position (2 calls per position)
        expected_calls = len(positions) * 2
        assert mock_controller.set_servo_angle.call_count == expected_calls
    
    @pytest.mark.asyncio
    async def test_async_scan_sequence(self):
        """Test async scan sequence."""
        pattern = ScanPattern(fov_degrees=90.0, overlap_degrees=15.0)
        mock_controller = Mock()
        mock_controller.smooth_move_to_angle = AsyncMock()
        
        positions = pattern.calculate_positions()
        
        # Simulate async movement through positions
        for pos in positions:
            await pattern.move_to_position_async(mock_controller, pos, 90.0, speed=0.7)
        
        # Should have made smooth movements for each position
        expected_calls = len(positions) * 2  # 2 servos per position
        assert mock_controller.smooth_move_to_angle.call_count == expected_calls
    
    def test_position_spacing_consistency(self):
        """Test that positions are consistently spaced."""
        pattern = ScanPattern(fov_degrees=60.0, overlap_degrees=10.0)
        positions = pattern.calculate_positions()
        
        if len(positions) > 2:
            # Calculate spacing between consecutive positions
            spacings = []
            for i in range(1, len(positions)):
                spacing = positions[i] - positions[i-1]
                spacings.append(spacing)
            
            # Spacings should be roughly equal (within effective FOV range)
            effective_fov = pattern.fov_degrees - pattern.overlap_degrees
            
            for spacing in spacings[:-1]:  # Exclude last spacing which might be different
                assert abs(spacing - effective_fov) < 5  # Within 5 degrees tolerance
    
    def test_coverage_completeness(self):
        """Test that scan pattern provides complete coverage."""
        pattern = ScanPattern(fov_degrees=66.3, overlap_degrees=10.0)
        positions = pattern.calculate_positions()
        
        if len(positions) > 1:
            # First position should cover from 0 to FOV
            first_coverage_end = positions[0] + pattern.fov_degrees
            
            # Each subsequent position should have coverage that overlaps with previous
            for i in range(1, len(positions)):
                pos_coverage_start = positions[i]
                expected_overlap_start = positions[i-1] + (pattern.fov_degrees - pattern.overlap_degrees)
                
                # Should overlap appropriately
                assert pos_coverage_start <= expected_overlap_start + 5  # 5 degree tolerance
            
            # Last position should cover up to or beyond 180
            last_coverage_end = positions[-1] + pattern.fov_degrees
            assert last_coverage_end >= 175  # Should cover nearly to 180