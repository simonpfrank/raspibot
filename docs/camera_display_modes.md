# Camera Display Modes

## Overview

The raspibot camera system supports three display modes that automatically adapt to your environment:

1. **Connected Screen** - Direct OpenCV windows when physical display is connected
2. **Raspberry Pi Connect** - X11 with WayVNC for remote desktop access
3. **Headless** - Logging only, no visual output (for operational mode)

## Supported Display Modes

### 1. Connected Screen Mode
- **When used**: Physical display is connected and accessible
- **Features**: Direct OpenCV windows, real-time display, keyboard input
- **Performance**: Best performance, lowest latency
- **Window positioning**: Centered on screen with proper sizing

### 2. Raspberry Pi Connect Mode
- **When used**: Raspberry Pi Connect (WayVNC) is active
- **Features**: Remote desktop display, X11 integration
- **Performance**: Good performance over network
- **Window positioning**: Centered on remote desktop

### 3. Headless Mode
- **When used**: No display available or operational mode
- **Features**: Logging only, no visual output
- **Performance**: Maximum performance, minimal resource usage
- **Use case**: Production deployment, CI/CD, background operation

## How Detection Works

The system automatically detects the best display mode in this order:

1. **Check for physical display** - Can we create OpenCV windows?
2. **Check for Raspberry Pi Connect** - Is WayVNC socket present?
3. **Fallback to headless** - Everything else

### Detection Logic

```python
def _detect_display_method(self) -> str:
    # 1. Try to create a test window
    try:
        cv2.namedWindow("test", cv2.WINDOW_AUTOSIZE)
        cv2.destroyWindow("test")
        return "connected_screen"
    except Exception:
        pass
    
    # 2. Check for Raspberry Pi Connect
    if os.path.exists('/tmp/wayvnc/wayvncctl.sock'):
        if os.path.exists('/tmp/.X11-unix/X0'):
            os.environ['DISPLAY'] = ':0'
            return "raspberry_connect"
    
    # 3. Fallback to headless
    return "headless"
```

## Window Positioning and Sizing

### Connected Screen Mode
- **Position**: Centered horizontally and vertically on screen
- **Size**: Adaptive based on camera resolution
- **Behavior**: Resizable, maintains aspect ratio

### Raspberry Pi Connect Mode
- **Position**: Centered on remote desktop
- **Size**: Optimized for remote viewing
- **Behavior**: Fixed size for consistent remote experience

## Adding a New Display Mode

To add support for a new display environment (e.g., SSH X11 forwarding):

### 1. Add Detection Logic

In `raspibot/vision/display_manager.py`, add detection logic:

```python
def _detect_display_method(self) -> str:
    # Existing detection logic...
    
    # TODO: Add new display mode here
    # Example: Add support for SSH X11 forwarding
    if self._is_ssh_x11_environment():
        return "ssh_x11"
    
    return "headless"

def _is_ssh_x11_environment(self) -> bool:
    """Check if running in SSH with X11 forwarding."""
    return (
        'SSH_CONNECTION' in os.environ and 
        'DISPLAY' in os.environ and
        os.environ.get('DISPLAY', '').startswith('localhost:')
    )
```

### 2. Create Display Handler

Create a new handler class in `raspibot/vision/display_handlers.py`:

```python
class SSHX11DisplayHandler(BaseDisplayHandler):
    """Display handler for SSH X11 forwarding."""
    
    def __init__(self, window_name: str = "Raspibot Camera"):
        super().__init__(window_name)
        self.display_name = "SSH X11 Forwarding"
        
    def setup_window(self) -> bool:
        """Set up window for SSH X11 environment."""
        try:
            # Create window with SSH-optimized settings
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            
            # Position window for SSH viewing
            self._position_window_ssh()
            
            self.logger.info(f"SSH X11 display window '{self.window_name}' created")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create SSH X11 window: {e}")
            return False
    
    def _position_window_ssh(self):
        """Position window optimally for SSH viewing."""
        # Get screen dimensions
        screen_width = 1920  # Default, could be detected
        screen_height = 1080
        
        # Calculate window size (smaller for SSH)
        window_width = min(800, screen_width // 2)
        window_height = min(600, screen_height // 2)
        
        # Center window
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Resize and position window
        cv2.resizeWindow(self.window_name, window_width, window_height)
        cv2.moveWindow(self.window_name, x, y)
```

### 3. Register the Handler

Add the handler to the display manager:

```python
# In DisplayManager.__init__
self.display_handlers = {
    'connected_screen': ConnectedDisplayHandler,
    'raspberry_connect': RaspberryConnectDisplayHandler,
    'headless': HeadlessDisplayHandler,
    'ssh_x11': SSHX11DisplayHandler,  # Add new handler
}
```

### 4. Update Documentation

Add the new mode to this documentation and update the supported modes list.

## Testing Display Modes

### Unit Tests

Test individual display handlers:

```python
def test_ssh_x11_display_handler():
    """Test SSH X11 display handler."""
    handler = SSHX11DisplayHandler("test")
    assert handler.display_name == "SSH X11 Forwarding"
    
    # Test window setup (mock environment)
    with patch('os.environ', {'SSH_CONNECTION': 'test', 'DISPLAY': 'localhost:10.0'}):
        assert handler.setup_window()
```

### Integration Tests

Test full display manager:

```python
def test_display_manager_ssh_detection():
    """Test display manager detects SSH X11 environment."""
    with patch('os.environ', {'SSH_CONNECTION': 'test', 'DISPLAY': 'localhost:10.0'}):
        manager = DisplayManager(auto_detect=True)
        assert manager.get_display_method() == "ssh_x11"
```

## Troubleshooting

### Common Issues

#### "Display Environment Not Supported"
**Cause**: Environment not recognized by detection logic
**Solution**: Check environment variables and add support for your environment

#### Window Positioned Incorrectly
**Cause**: Screen dimensions not detected properly
**Solution**: Check display handler positioning logic

#### Performance Issues
**Cause**: Wrong display mode selected
**Solution**: Force headless mode for production: `DisplayManager(auto_detect=False, mode="headless")`

### Debug Mode

Enable debug logging to see detection process:

```python
import logging
logging.getLogger('raspibot.vision.display_manager').setLevel(logging.DEBUG)
```

### Manual Mode Selection

Override automatic detection:

```python
# Force specific mode
display_manager = DisplayManager(auto_detect=False, mode="headless")
```

## Performance Considerations

### Mode Performance Ranking
1. **Headless** - Fastest, minimal resource usage
2. **Connected Screen** - Fast, direct display
3. **Raspberry Pi Connect** - Good, network overhead

### Memory Usage
- **Headless**: ~1MB additional memory
- **Connected Screen**: ~5-10MB additional memory
- **Raspberry Pi Connect**: ~10-15MB additional memory

### CPU Usage
- **Headless**: Minimal CPU overhead
- **Connected Screen**: Low CPU overhead
- **Raspberry Pi Connect**: Moderate CPU overhead (encoding)

## Best Practices

1. **Use headless mode** for production deployments
2. **Test all modes** in your target environment
3. **Monitor performance** when switching modes
4. **Add new modes** only when necessary
5. **Document environment requirements** for each mode

## Future Enhancements

Potential new display modes to consider:
- **Web Interface** - Browser-based display
- **Mobile App** - Phone/tablet display
- **VR/AR** - Virtual/augmented reality display
- **Multi-screen** - Multiple display support 