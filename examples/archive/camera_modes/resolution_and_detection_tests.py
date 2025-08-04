#!/usr/bin/env python3
"""
Comprehensive Camera Resolution and Detection Testing Script

This script tests different camera formats and detection modes:
- Color (XBGR8888): Full color, 3-4 bytes/pixel, AI limited to 320x240
- YUV420: Full color, 1.5 bytes/pixel (50% memory reduction), AI works at ALL resolutions
- Grayscale: No color, 3-4 bytes/pixel, AI works at ALL resolutions
- Webcam: Standard webcam testing (placeholder)

Detection modes:
- No Detection: Basic frame capture only
- AI Detection: IMX500 hardware acceleration
- OpenCV Detection: Software-based face detection
"""

import time
import cv2
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from picamera2 import Picamera2

# Test configurations
RESOLUTIONS = [
    (320, 240),   # QVGA
    (640, 480),   # VGA
    (800, 600),   # SVGA
    (1024, 768),  # XGA
    (1280, 720),  # HD
    (1280, 960),  # High aspect ratio
    (1600, 1200), # UXGA
    (1920, 1080), # Full HD
    (2560, 1440), # 2K
]

FORMATS = {
    'color': {
        'name': 'Color (XBGR8888)',
        'format': 'XBGR8888',
        'description': 'Full color format, 3-4 bytes/pixel, AI detection limited to 320x240'
    },
    'yuv420': {
        'name': 'YUV420',
        'format': 'YUV420',
        'description': 'Full color format, 1.5 bytes/pixel (50% memory reduction), AI detection works at ALL resolutions'
    },
    'grayscale': {
        'name': 'Grayscale',
        'format': 'XBGR8888',  # We convert to grayscale in processing
        'description': 'Grayscale processing, 3-4 bytes/pixel, AI detection works at ALL resolutions'
    },
    'webcam': {
        'name': 'Webcam',
        'format': None,  # Will use OpenCV VideoCapture
        'description': 'Standard webcam testing (placeholder)'
    }
}

DETECTION_MODES = {
    'none': {
        'name': 'No Detection',
        'description': 'Basic frame capture only'
    },
    'ai': {
        'name': 'AI Detection',
        'description': 'IMX500 hardware acceleration'
    },
    'opencv': {
        'name': 'OpenCV Detection',
        'description': 'Software-based face detection'
    }
}

class CameraTester:
    """Comprehensive camera testing with multiple formats and detection modes."""
    
    def __init__(self):
        self.results = []
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
    def display_menu(self) -> Tuple[str, str]:
        """Display menu and get user selection."""
        print("\n" + "="*80)
        print("CAMERA RESOLUTION AND DETECTION TESTING")
        print("="*80)
        
        # Display format options
        print("\n📷 CAMERA FORMATS:")
        for key, format_info in FORMATS.items():
            print(f"  {key}: {format_info['name']}")
            print(f"     {format_info['description']}")
        
        # Display detection modes
        print("\n🔍 DETECTION MODES:")
        for key, mode_info in DETECTION_MODES.items():
            print(f"  {key}: {mode_info['name']}")
            print(f"     {mode_info['description']}")
        
        print("\n📋 TEST OPTIONS:")
        print("  single: Run a single format/detection combination")
        print("  all: Run all combinations")
        print("  quit: Exit")
        
        while True:
            choice = input("\nEnter your choice (single/all/quit): ").lower().strip()
            
            if choice == 'quit':
                return None, None
            elif choice == 'all':
                return 'all', 'all'
            elif choice == 'single':
                return self.get_single_test_choice()
            else:
                print("Invalid choice. Please enter 'single', 'all', or 'quit'.")
    
    def get_single_test_choice(self) -> Tuple[str, str]:
        """Get user selection for single test."""
        print("\nSelect format:")
        for key in FORMATS.keys():
            print(f"  {key}")
        
        while True:
            format_choice = input("Enter format: ").lower().strip()
            if format_choice in FORMATS:
                break
            print("Invalid format choice.")
        
        print("\nSelect detection mode:")
        for key in DETECTION_MODES.keys():
            print(f"  {key}")
        
        while True:
            detection_choice = input("Enter detection mode: ").lower().strip()
            if detection_choice in DETECTION_MODES:
                break
            print("Invalid detection mode choice.")
        
        return format_choice, detection_choice
    
    def test_resolution(self, format_key: str, detection_key: str, width: int, height: int) -> Dict:
        """Test a specific resolution with given format and detection mode."""
        print(f"\nTesting {FORMATS[format_key]['name']} - {DETECTION_MODES[detection_key]['name']} at {width}x{height}")
        print("-" * 60)
        
        result = {
            'format': format_key,
            'detection': detection_key,
            'resolution': f"{width}x{height}",
            'width': width,
            'height': height,
            'status': 'FAILED',
            'fps': 0,
            'steady_state_fps': 0,
            'time_to_first_frame': 0,
            'frames_captured': 0,
            'detection_fps': 0,
            'total_detections': 0,
            'error': None
        }
        
        try:
            if format_key == 'webcam':
                # Webcam testing (placeholder)
                result['error'] = "Webcam testing not yet implemented"
                return result
            
            # Initialize PiCamera2
            picam2 = Picamera2()
            
            # Configure camera based on format and detection mode
            if detection_key == 'ai':
                config = picam2.create_preview_configuration(
                    main={'format': FORMATS[format_key]['format'], 'size': (width, height)},
                    encode="main",
                    buffer_count=4
                )
            else:
                config = picam2.create_preview_configuration(
                    main={'format': FORMATS[format_key]['format'], 'size': (width, height)}
                )
            
            picam2.configure(config)
            picam2.start()
            
            # Test parameters
            frame_count = 0
            detection_count = 0
            start_time = time.time()
            first_frame_time = None
            
            # Capture frames for 10 seconds
            while time.time() - start_time < 10:
                frame_start = time.time()
                try:
                    # Capture frame
                    frame = picam2.capture_array()
                    
                    # Process based on format
                    if format_key == 'grayscale':
                        # Convert to grayscale
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    elif format_key == 'yuv420':
                        # Convert YUV420 to BGR for processing
                        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_I420)
                        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
                    else:
                        # Color format - convert to grayscale for detection
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    
                    # Process based on detection mode
                    if detection_key == 'ai':
                        # Check for AI detection results
                        metadata = picam2.capture_metadata()
                        if "DetectionResults" in metadata:
                            detections = metadata["DetectionResults"]
                            if detections:
                                detection_count += len(detections)
                    
                    elif detection_key == 'opencv':
                        # Perform OpenCV face detection
                        faces = face_cascade.detectMultiScale(
                            gray, 
                            scaleFactor=1.1, 
                            minNeighbors=5, 
                            minSize=(30, 30)
                        )
                        if len(faces) > 0:
                            detection_count += len(faces)
                    
                    # NO_DETECTION mode just captures frames
                    
                except Exception as e:
                    print(f"Error capturing frame: {e}")
                    break
                
                frame_end = time.time()
                frame_count += 1
                if first_frame_time is None:
                    first_frame_time = frame_end
            
            # Calculate results
            elapsed_time = time.time() - start_time
            actual_fps = frame_count / elapsed_time if elapsed_time > 0 else 0
            detection_fps = detection_count / elapsed_time if elapsed_time > 0 else 0
            
            if first_frame_time:
                time_to_first_frame = first_frame_time - start_time
            else:
                time_to_first_frame = 0
            
            if first_frame_time and frame_count > 1:
                steady_state_time = elapsed_time - time_to_first_frame
                steady_state_fps = (frame_count - 1) / steady_state_time if steady_state_time > 0 else 0
            else:
                steady_state_fps = actual_fps
            
            # Update result
            result.update({
                'status': 'SUCCESS',
                'fps': round(actual_fps, 2),
                'steady_state_fps': round(steady_state_fps, 2),
                'time_to_first_frame': round(time_to_first_frame, 3),
                'frames_captured': frame_count,
                'detection_fps': round(detection_fps, 2),
                'total_detections': detection_count
            })
            
            # Display results
            print(f"Captured {frame_count} frames in {elapsed_time:.2f} seconds")
            print(f"FPS: {actual_fps:.2f}")
            print(f"Steady State FPS: {steady_state_fps:.2f}")
            print(f"Time to first frame: {time_to_first_frame:.3f} seconds")
            
            if detection_key == 'ai':
                print(f"AI Detection FPS: {detection_fps:.2f} ({detection_count} total detections)")
            elif detection_key == 'opencv':
                print(f"Face Detection FPS: {detection_fps:.2f} ({detection_count} total faces)")
            else:
                print("No detection - frame capture only")
            
            picam2.stop()
            picam2.close()
            
        except Exception as e:
            result['error'] = str(e)
            print(f"ERROR: {e}")
        
        return result
    
    def run_single_test(self, format_key: str, detection_key: str) -> None:
        """Run a single format/detection combination across all resolutions."""
        print(f"\n{'='*80}")
        print(f"RUNNING: {FORMATS[format_key]['name']} - {DETECTION_MODES[detection_key]['name']}")
        print(f"{'='*80}")
        
        for width, height in RESOLUTIONS:
            result = self.test_resolution(format_key, detection_key, width, height)
            self.results.append(result)
            
            if result['status'] == 'SUCCESS':
                print(f"✅ SUCCESS: {width}x{height}")
            else:
                print(f"❌ FAILED: {width}x{height} - {result['error']}")
        
        print(f"\nCompleted {FORMATS[format_key]['name']} - {DETECTION_MODES[detection_key]['name']}")
    
    def run_all_tests(self) -> None:
        """Run all format/detection combinations."""
        print(f"\n{'='*80}")
        print("RUNNING ALL TESTS")
        print(f"{'='*80}")
        
        # Skip webcam for now (placeholder)
        test_combinations = [
            (format_key, detection_key) 
            for format_key in FORMATS.keys() 
            for detection_key in DETECTION_MODES.keys()
            if format_key != 'webcam'  # Skip webcam for now
        ]
        
        total_tests = len(test_combinations) * len(RESOLUTIONS)
        current_test = 0
        
        for format_key, detection_key in test_combinations:
            print(f"\n{'='*80}")
            print(f"TEST {current_test + 1}/{total_tests}: {FORMATS[format_key]['name']} - {DETECTION_MODES[detection_key]['name']}")
            print(f"{'='*80}")
            
            for width, height in RESOLUTIONS:
                current_test += 1
                print(f"\nProgress: {current_test}/{total_tests}")
                result = self.test_resolution(format_key, detection_key, width, height)
                self.results.append(result)
                
                if result['status'] == 'SUCCESS':
                    print(f"✅ SUCCESS: {width}x{height}")
                else:
                    print(f"❌ FAILED: {width}x{height} - {result['error']}")
        
        print(f"\n{'='*80}")
        print("ALL TESTS COMPLETED")
        print(f"{'='*80}")
    
    def save_results_to_markdown(self) -> None:
        """Save results to markdown file."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"camera_test_results_{timestamp}.md"
        
        with open(filename, 'w') as f:
            f.write(f"# Camera Resolution and Detection Test Results\n\n")
            f.write(f"**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Summary table
            f.write("## Summary\n\n")
            f.write("| Format | Detection | Status | Avg FPS | Max Resolution | Notes |\n")
            f.write("|--------|-----------|--------|---------|----------------|-------|\n")
            
            # Group results by format and detection
            summary_data = {}
            for result in self.results:
                key = (result['format'], result['detection'])
                if key not in summary_data:
                    summary_data[key] = {
                        'success_count': 0,
                        'total_count': 0,
                        'fps_values': [],
                        'max_resolution': '0x0'
                    }
                
                summary_data[key]['total_count'] += 1
                if result['status'] == 'SUCCESS':
                    summary_data[key]['success_count'] += 1
                    summary_data[key]['fps_values'].append(result['fps'])
                    # Track max resolution
                    current_res = result['width'] * result['height']
                    max_res = int(summary_data[key]['max_resolution'].split('x')[0]) * int(summary_data[key]['max_resolution'].split('x')[1])
                    if current_res > max_res:
                        summary_data[key]['max_resolution'] = result['resolution']
            
            # Write summary
            for (format_key, detection_key), data in summary_data.items():
                status = f"{data['success_count']}/{data['total_count']}" if data['total_count'] > 0 else "0/0"
                avg_fps = f"{sum(data['fps_values'])/len(data['fps_values']):.1f}" if data['fps_values'] else "0.0"
                format_name = FORMATS[format_key]['name']
                detection_name = DETECTION_MODES[detection_key]['name']
                
                f.write(f"| {format_name} | {detection_name} | {status} | {avg_fps} | {data['max_resolution']} | |\n")
            
            # Detailed results
            f.write("\n## Detailed Results\n\n")
            
            for format_key in FORMATS.keys():
                if format_key == 'webcam':
                    continue  # Skip webcam for now
                    
                f.write(f"### {FORMATS[format_key]['name']}\n\n")
                f.write(f"{FORMATS[format_key]['description']}\n\n")
                
                for detection_key in DETECTION_MODES.keys():
                    f.write(f"#### {DETECTION_MODES[detection_key]['name']}\n\n")
                    f.write("| Resolution | FPS | Steady State FPS | Time to First Frame | Frames | Detections | Status |\n")
                    f.write("|------------|-----|------------------|---------------------|--------|------------|--------|\n")
                    
                    format_results = [r for r in self.results if r['format'] == format_key and r['detection'] == detection_key]
                    format_results.sort(key=lambda x: (x['width'], x['height']))
                    
                    for result in format_results:
                        status_icon = "✅" if result['status'] == 'SUCCESS' else "❌"
                        f.write(f"| {result['resolution']} | {result['fps']} | {result['steady_state_fps']} | {result['time_to_first_frame']}s | {result['frames_captured']} | {result['total_detections']} | {status_icon} |\n")
                    
                    f.write("\n")
        
        print(f"\n📄 Results saved to: {filename}")
    
    def run(self) -> None:
        """Main execution method."""
        print("🎥 Camera Resolution and Detection Testing")
        print("=" * 50)
        
        format_choice, detection_choice = self.display_menu()
        
        if format_choice is None:
            print("Goodbye!")
            return
        
        if format_choice == 'all':
            self.run_all_tests()
        else:
            self.run_single_test(format_choice, detection_choice)
        
        if self.results:
            self.save_results_to_markdown()
        
        print("\n🎉 Testing completed!")

def main():
    """Main entry point."""
    tester = CameraTester()
    tester.run()

if __name__ == "__main__":
    main() 