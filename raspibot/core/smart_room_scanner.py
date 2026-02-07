"""Smart room scanner for efficient people detection.

This module provides the SmartRoomScanner class which orchestrates periodic
room scanning with tiered scan ranges, center-out ordering, and watch phase
adjustments. Heat map has been removed in favor of simpler tiered scanning.
"""

import logging
import time
from typing import Any, Dict, Final, List, Optional, Protocol, Tuple

from raspibot.core.event_tracker import EventTracker
from raspibot.core.position_calculator import OptimalPositionCalculator
from raspibot.core.tracking_events import EdgeEvent, ExitEvent, NewPersonEvent, TrackingEvent
from raspibot.core.watch_controller import WatchController
from raspibot.hardware.servos.servo_protocol import ServoControllerProtocol
from raspibot.settings import config

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_SCAN_INTERVAL: Final[float] = 30.0
DEFAULT_CONFIDENCE_THRESHOLD: Final[float] = 0.5
DEFAULT_SETTLING_TIME: Final[float] = 1.0
DEFAULT_FOV_DEGREES: Final[float] = 66.3
DEFAULT_FOV_VERTICAL: Final[float] = 50.0
DEFAULT_OVERLAP_DEGREES: Final[float] = 10.0
CENTER_PAN: Final[float] = 90.0
CENTER_TILT: Final[float] = 90.0
DEFAULT_FRAME_HEIGHT: Final[int] = 720

# Face detection thresholds
FACE_TOP_THRESHOLD: Final[float] = 0.05  # Person top within 5% of frame height
FACE_PARTIAL_THRESHOLD: Final[float] = 0.03  # Face at top 3% is partial
FACE_EXPECTED_POSITION: Final[float] = 0.15  # Face ~15% from person top


class CameraProtocol(Protocol):
    """Protocol for camera interface."""

    tracked_objects: List[Dict[str, Any]]
    face_detections: List[Dict[str, Any]]

    def start(self) -> bool:
        """Start the camera."""
        ...

    def stop(self) -> None:
        """Stop the camera."""
        ...

    def clear_tracked_objects(self) -> None:
        """Clear tracked objects list."""
        ...


class _HeatMapStub:
    """Stub class for backward compatibility with heat map interface."""

    def __init__(self) -> None:
        """Initialize stub."""
        self.heat_data: Dict[str, Any] = {}

    def record_detection(self, pan: float, tilt: float, confidence: float) -> None:
        """No-op stub for record_detection."""

    def record_event(
        self, pan: float, tilt: float, event_type: str, confidence: float
    ) -> None:
        """No-op stub for record_event."""

    def save(self) -> None:
        """No-op stub for save."""

    def get_ordered_positions(
        self, positions: List[Tuple[float, float]]
    ) -> List[Tuple[float, float]]:
        """Return positions unchanged."""
        return positions


class SmartRoomScanner:
    """Orchestrate smart room scanning with tiered ranges.

    The SmartRoomScanner coordinates periodic room scans using a tiered
    approach: primary range (40-140°) scanned center-out, then fallback
    extremes (0-40° and 140-180°) if nothing found.

    Key behaviors:
    - Tiered scanning: primary range first, fallback if empty
    - Center-out ordering within each range
    - Persistence filter: detections must be seen 3+ frames
    - Face priority: detections with faces ranked higher
    - Early stop when people detected
    - Optimal position calculation to see most people
    - Watch phase with minor adjustments
    - Extreme watch timeout: returns to center after 30s at extremes

    Args:
        camera: Camera instance for detection.
        servo_controller: Servo controller for pan/tilt movement.
        scan_interval: Seconds between scans. Default 30.
        confidence_threshold: Minimum detection confidence. Default 0.65.
        fov_degrees: Camera horizontal FOV. Default 66.3.

    Example:
        >>> scanner = SmartRoomScanner(camera, servo)
        >>> detections = scanner.run_scan_cycle()
        >>> if scanner.watch_controller.is_watching():
        ...     scanner.update_watch()  # Minor adjustments
    """

    def __init__(
        self,
        camera: CameraProtocol,
        servo_controller: ServoControllerProtocol,
        heat_map_path: str = "",  # Deprecated, kept for backward compatibility
        scan_interval: float = DEFAULT_SCAN_INTERVAL,
        confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
        fov_degrees: float = DEFAULT_FOV_DEGREES,
        inactivity_timeout: float = config.INACTIVITY_TIMEOUT_SECONDS
    ) -> None:
        """Initialize the smart room scanner."""
        self.camera = camera
        self.servo_controller = servo_controller
        self.scan_interval = scan_interval
        self.confidence_threshold = confidence_threshold
        self.fov_degrees = fov_degrees
        self.inactivity_timeout = inactivity_timeout

        # Initialize components (heat_map kept as stub for backward compatibility)
        self.heat_map = _HeatMapStub()
        self.position_calculator = OptimalPositionCalculator(
            fov_horizontal=fov_degrees
        )
        self.watch_controller = WatchController(
            servo_controller=servo_controller,
            fov_degrees=fov_degrees
        )
        self.event_tracker = EventTracker()

        # Track current pan angle for event tracking
        self._current_pan = CENTER_PAN

        # Extreme watch mode tracking
        self._watching_from_extreme = False
        self._extreme_watch_start: Optional[float] = None

        logger.info("SmartRoomScanner initialized with tiered scanning")

    def _calculate_base_positions(
        self, range_min: float = 0.0, range_max: float = 180.0
    ) -> List[Tuple[float, float]]:
        """Calculate base scan positions based on FOV within given range.

        Args:
            range_min: Minimum pan angle for range. Default 0.0.
            range_max: Maximum pan angle for range. Default 180.0.

        Returns:
            List of (pan, tilt) positions for coverage within range.
        """
        positions: List[Tuple[float, float]] = []
        step = self.fov_degrees - DEFAULT_OVERLAP_DEGREES

        # Calculate pan positions for coverage
        pan = range_min
        while pan <= range_max:
            positions.append((pan, CENTER_TILT))
            pan += step

        # Ensure we have the max edge if not already included
        if positions and positions[-1][0] < range_max:
            positions.append((range_max, CENTER_TILT))

        return positions

    def _get_ordered_positions(
        self, range_min: float = 0.0, range_max: float = 180.0
    ) -> List[Tuple[float, float]]:
        """Get scan positions ordered center-out within given range.

        Positions are ordered from center of the range outward to ensure
        the most likely detection area is scanned first.

        Args:
            range_min: Minimum pan angle for range. Default 0.0.
            range_max: Maximum pan angle for range. Default 180.0.

        Returns:
            List of (pan, tilt) positions ordered center-out.
        """
        positions = self._calculate_base_positions(range_min, range_max)
        center = (range_min + range_max) / 2
        return sorted(positions, key=lambda p: abs(p[0] - center))

    def run_scan_cycle(self) -> List[Dict[str, Any]]:
        """Execute one complete scan cycle with tiered ranges.

        Implements tiered scanning:
        - Tier 1: Primary range (40-140°) scanned center-out
        - Tier 2: Fallback extremes (0-40° and 140-180°) if nothing in primary
        - Tier 3: Center position if nothing found anywhere

        Returns:
            List of detected people with their positions.
        """
        logger.info("Starting tiered scan cycle")
        self.watch_controller.stop_watching()
        self._watching_from_extreme = False
        self._extreme_watch_start = None

        # Tier 1: Primary range (40-140°)
        detections = self._scan_range(
            config.SCAN_PRIMARY_MIN, config.SCAN_PRIMARY_MAX
        )
        if detections:
            return self._handle_people_found(detections, extreme=False)

        # Tier 2: Fallback extremes (if enabled)
        if config.SCAN_FALLBACK_ENABLED:
            # Try left extreme first
            detections = self._scan_range(*config.SCAN_FALLBACK_LEFT)
            if detections:
                return self._handle_people_found(detections, extreme=True)

            # Try right extreme
            detections = self._scan_range(*config.SCAN_FALLBACK_RIGHT)
            if detections:
                return self._handle_people_found(detections, extreme=True)

        # Tier 3: Nothing found - center and wait
        self._handle_no_people()
        return []

    def _scan_range(
        self, range_min: float, range_max: float
    ) -> List[Dict[str, Any]]:
        """Scan positions within a range, stop early on detection.

        Args:
            range_min: Minimum pan angle for range.
            range_max: Maximum pan angle for range.

        Returns:
            List of detections if found, empty list otherwise.
        """
        ordered_positions = self._get_ordered_positions(range_min, range_max)

        for position in ordered_positions:
            pan, tilt = position
            logger.debug("Scanning position (%.1f, %.1f)", pan, tilt)

            self.servo_controller.set_servo_angle("pan", pan)
            self.servo_controller.set_servo_angle("tilt", tilt)
            time.sleep(DEFAULT_SETTLING_TIME)

            detections = self._get_person_detections(pan)

            if detections:
                # Apply face tilt nudge if needed
                detections, tilt = self._apply_face_tilt_nudge(
                    detections, pan, tilt
                )
                # Prioritize detections with faces
                detections = self._prioritize_detections(detections)
                logger.info(
                    "Found %d people at position (%.1f, %.1f)",
                    len(detections), pan, tilt
                )
                return detections

        return []

    def _apply_face_tilt_nudge(
        self,
        detections: List[Dict[str, Any]],
        pan: float,
        tilt: float
    ) -> Tuple[List[Dict[str, Any]], float]:
        """Apply tilt nudge if faces may be cut off at top of frame.

        Checks each detected person to see if their face might be cut off.
        If so, adjusts tilt and re-detects to capture the face.

        Args:
            detections: Current person detections.
            pan: Current pan angle.
            tilt: Current tilt angle.

        Returns:
            Tuple of (updated detections, final tilt angle).
        """
        # Check if any detection needs tilt adjustment
        max_adjustment: Optional[float] = None

        for det in detections:
            box = det["box"]
            faces = det.get("faces", [])

            adjustment = self._calculate_face_tilt_adjustment(
                box, faces, DEFAULT_FRAME_HEIGHT, DEFAULT_FOV_VERTICAL
            )

            if adjustment is not None:
                if max_adjustment is None or adjustment < max_adjustment:
                    # Take the largest upward adjustment (most negative)
                    max_adjustment = adjustment

        if max_adjustment is not None:
            # Apply the tilt adjustment
            new_tilt = tilt + max_adjustment
            # Clamp to valid range
            new_tilt = max(0.0, min(180.0, new_tilt))

            logger.info(
                "Applying face tilt nudge: %.1f° -> %.1f° (adjustment: %.1f°)",
                tilt, new_tilt, max_adjustment
            )

            self.servo_controller.set_servo_angle("tilt", new_tilt)
            time.sleep(DEFAULT_SETTLING_TIME)

            # Re-detect with adjusted position
            detections = self._get_person_detections(pan)
            return detections, new_tilt

        return detections, tilt

    def _get_person_detections(self, pan_angle: float) -> List[Dict[str, Any]]:
        """Get person detections from camera at current position.

        Applies multiple filters:
        - Label must be "person"
        - Score must be above confidence threshold
        - Must be seen for 3+ frames (persistence filter)

        Args:
            pan_angle: Current pan angle for world angle calculation.

        Returns:
            List of person detections above confidence threshold with face data.
        """
        detections: List[Dict[str, Any]] = []

        # Get face detections from camera (may be empty list)
        face_detections = getattr(self.camera, 'face_detections', []) or []

        for tracked in self.camera.tracked_objects:
            last_det = tracked.get("last_detection", {})
            label = last_det.get("label", "")
            score = last_det.get("score", 0.0)
            box = last_det.get("box", [0, 0, 0, 0])

            # Filter: label must be person
            if label != "person":
                continue

            # Filter: confidence threshold
            if score < self.confidence_threshold:
                continue

            # Filter: persistence requirement - must be seen 3+ frames
            seen_count = tracked.get("seen_count", 0)
            if seen_count < config.DETECTION_PERSISTENCE_FRAMES:
                continue

            # Calculate world angle from box position
            box_center_x = box[0] + box[2] / 2
            frame_center_x = 640  # Assuming 1280 width
            offset_pixels = box_center_x - frame_center_x
            degrees_per_pixel = self.fov_degrees / 1280
            world_angle = pan_angle + offset_pixels * degrees_per_pixel

            # Associate faces that fall within person bounding box
            person_faces = self._associate_faces_with_person(box, face_detections)

            detection: Dict[str, Any] = {
                "label": "person",
                "confidence": score,
                "box": tuple(box),
                "pan_angle": pan_angle,
                "world_angle": world_angle,
                "timestamp": time.time(),
                "faces": person_faces
            }
            detections.append(detection)

        return detections

    def _associate_faces_with_person(
        self,
        person_box: List[int],
        face_detections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Associate face detections that fall within person bounding box.

        Args:
            person_box: Person bounding box [x, y, w, h].
            face_detections: List of face detections from camera.

        Returns:
            List of faces that overlap with the person bounding box.
        """
        associated_faces: List[Dict[str, Any]] = []
        px, py, pw, ph = person_box

        for face in face_detections:
            face_box = face.get("box", (0, 0, 0, 0))
            fx, fy, fw, fh = face_box

            # Check if face center is within person box
            face_center_x = fx + fw / 2
            face_center_y = fy + fh / 2

            if (px <= face_center_x <= px + pw and
                    py <= face_center_y <= py + ph):
                associated_faces.append(face)

        return associated_faces

    def _prioritize_detections(
        self, detections: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Sort detections: face-confirmed first, then by confidence.

        Args:
            detections: List of person detections.

        Returns:
            Sorted list with face detections first, then by confidence.
        """
        return sorted(
            detections,
            key=lambda d: (
                1 if d.get("faces") else 0,  # Face bonus (1=has face, 0=no face)
                d.get("confidence", 0)
            ),
            reverse=True
        )

    def _calculate_face_tilt_adjustment(
        self,
        person_box: Tuple[int, int, int, int],
        faces: List[Dict[str, Any]],
        frame_height: int = DEFAULT_FRAME_HEIGHT,
        fov_vertical: float = DEFAULT_FOV_VERTICAL
    ) -> Optional[float]:
        """Calculate tilt adjustment needed to capture face using FOV.

        Uses vertical FOV to calculate precise adjustment rather than
        arbitrary pixel thresholds. When a person is detected near the top
        of the frame and no face is visible (or face is partial), this
        calculates how much to tilt up to bring the face into view.

        Args:
            person_box: (x, y, w, h) of detected person.
            faces: List of face detections for this person.
            frame_height: Camera frame height in pixels. Default 720.
            fov_vertical: Vertical field of view in degrees. Default 50.

        Returns:
            Tilt adjustment in degrees (negative = up), or None if OK.
        """
        degrees_per_pixel = fov_vertical / frame_height
        frame_center_y = frame_height / 2
        top_threshold = frame_height * FACE_TOP_THRESHOLD
        partial_threshold = frame_height * FACE_PARTIAL_THRESHOLD

        person_x, person_y, person_w, person_h = person_box
        person_top = person_y

        # Estimate where face should be (top 15-20% of person box)
        expected_face_y = person_y + person_h * FACE_EXPECTED_POSITION

        # Calculate angle from frame center to expected face position
        # Negative offset = above center = need to tilt up (decrease tilt angle)
        offset_pixels = expected_face_y - frame_center_y
        offset_degrees = offset_pixels * degrees_per_pixel

        # Check if person's top is at the top edge of frame
        if person_top < top_threshold:
            if not faces:
                # No face detected - face is likely cut off
                # Return adjustment to bring expected face toward center
                return offset_degrees

            # Face detected but check if it's partial (very close to edge)
            face_top = faces[0]["box"][1]
            if face_top < partial_threshold:
                # Face might be partial, nudge up slightly (half adjustment)
                return offset_degrees * 0.5

        return None

    def _handle_people_found(
        self, detections: List[Dict[str, Any]], extreme: bool = False
    ) -> List[Dict[str, Any]]:
        """Handle case when people are found.

        Calculates optimal position and enters watch mode. If detection
        is from an extreme position, sets timeout to return to primary.

        Args:
            detections: List of detected people.
            extreme: Whether detections are from fallback extreme range.

        Returns:
            The detections list.
        """
        # Extract world angles for position calculation
        people_angles = [
            (d["world_angle"], CENTER_TILT) for d in detections
        ]

        # Calculate optimal position
        optimal_pan, optimal_tilt = self.position_calculator.calculate_optimal_position(
            people_angles
        )

        logger.info(
            "Moving to optimal position (%.1f, %.1f) for %d people%s",
            optimal_pan, optimal_tilt, len(detections),
            " (from extreme)" if extreme else ""
        )

        # Move to optimal position
        self.servo_controller.set_servo_angle("pan", optimal_pan)
        self.servo_controller.set_servo_angle("tilt", optimal_tilt)

        # Track if watching from extreme position
        self._watching_from_extreme = extreme
        if extreme:
            self._extreme_watch_start = time.time()

        # Enter watch mode
        self.watch_controller.start_watching((optimal_pan, optimal_tilt))

        return detections

    def _handle_no_people(self) -> None:
        """Handle case when no people are found.

        Returns camera to center position.
        """
        logger.info("No people found, returning to center")
        self.servo_controller.set_servo_angle("pan", CENTER_PAN)
        self.servo_controller.set_servo_angle("tilt", CENTER_TILT)

    def update_watch(self) -> None:
        """Update watch phase with current detections.

        Call this periodically during watch phase to make minor
        centering adjustments.
        """
        if not self.watch_controller.is_watching():
            return

        # Convert camera tracked objects to detection format
        detections: List[Dict[str, Any]] = []
        for tracked in self.camera.tracked_objects:
            last_det = tracked.get("last_detection", {})
            if last_det.get("label") == "person":
                detections.append({
                    "label": "person",
                    "box": last_det.get("box", [0, 0, 0, 0])
                })

        self.watch_controller.update(detections)

    def run_event_driven_watch(self) -> List[TrackingEvent]:
        """Run one iteration of event-driven watch mode.

        Processes current detections through the event tracker and handles
        any generated events (edge approaches, exits, new people).

        Returns:
            List of tracking events that were generated and handled.
        """
        if not self.watch_controller.is_watching():
            return []

        # Get current pan position
        self._current_pan = self.watch_controller.current_position[0]

        # Convert camera tracked objects to detection format for event tracker
        detections: List[Dict[str, Any]] = []
        for tracked in self.camera.tracked_objects:
            last_det = tracked.get("last_detection", {})
            if last_det.get("label") == "person":
                box = last_det.get("box", [0, 0, 0, 0])
                track_id = tracked.get("track_id", id(tracked))
                detections.append({
                    "track_id": track_id,
                    "box": box,
                    "confidence": last_det.get("score", 0.5),
                    "has_face": len(tracked.get("faces", [])) > 0
                })

        # Update event tracker and get events
        events = self.event_tracker.update(detections)

        # Check for exit events
        exit_events = self.event_tracker.detect_exit_events(self._current_pan)
        events.extend(exit_events)

        # Handle all events
        for event in events:
            self._handle_tracking_event(event)

        return events

    def _handle_tracking_event(self, event: TrackingEvent) -> None:
        """Dispatch and handle a tracking event.

        Args:
            event: The tracking event to handle.
        """
        if isinstance(event, EdgeEvent):
            self._handle_edge_event(event)
        elif isinstance(event, ExitEvent):
            self._handle_exit_event(event)
        elif isinstance(event, NewPersonEvent):
            self._handle_new_person_event(event)

    def _handle_edge_event(self, event: EdgeEvent) -> None:
        """Handle an edge approach event.

        Args:
            event: The edge event to handle.
        """
        person = self.event_tracker.tracking_state.tracked_people.get(
            event.track_id
        )
        velocity = person.velocity_x if person else event.velocity_toward_edge

        self.watch_controller.pan_to_keep_in_frame(
            event.edge_position, velocity
        )

        logger.debug(
            "Handled edge event: track_id=%d, position=%s",
            event.track_id, event.edge_position.value
        )

    def _handle_exit_event(self, event: ExitEvent) -> None:
        """Handle an exit event by attempting re-acquisition.

        Args:
            event: The exit event to handle.
        """
        reacq = self.event_tracker.attempt_reacquisition(event)

        if reacq is not None:
            # Pan toward exit direction to re-acquire
            pan_degrees = reacq["pan_degrees"]
            if reacq["pan_direction"] == "left":
                new_pan = self._current_pan - pan_degrees
            else:
                new_pan = self._current_pan + pan_degrees

            new_pan = max(0.0, min(180.0, new_pan))
            self.servo_controller.set_servo_angle("pan", new_pan)
            self._current_pan = new_pan
            self.watch_controller.current_position = (
                new_pan, self.watch_controller.current_position[1]
            )

            logger.info(
                "Re-acquisition attempt: panned %s to %.1f",
                reacq["pan_direction"], new_pan
            )

    def _handle_new_person_event(self, event: NewPersonEvent) -> None:
        """Handle a new person detection event.

        Args:
            event: The new person event to handle.
        """
        logger.info(
            "New person detected: track_id=%d, entry_edge=%s",
            event.track_id, event.entry_edge
        )
