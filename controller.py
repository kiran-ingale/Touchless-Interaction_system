import cv2
import mediapipe as mp
import pyautogui
import math
import time

# ── Screen ──────────────────────────────────────────────────────────────────
screen_width, screen_height = pyautogui.size()

# ── Mediapipe ────────────────────────────────────────────────────────────────
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.8,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

# ── Webcam ───────────────────────────────────────────────────────────────────
cap = cv2.VideoCapture(0)
cam_width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
cam_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# ── Smoothing ────────────────────────────────────────────────────────────────
prev_x, prev_y = 0, 0
SMOOTHING = 5

# ── Gesture timing ───────────────────────────────────────────────────────────
last_action_time = 0
ACTION_DELAY = 0.8

# ── Selection state ──────────────────────────────────────────────────────────
selecting = False

# ── Hand position tracking for swipe ─────────────────────────────────────────
prev_hand_x = 0


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def dist(ax, ay, bx, by):
    return math.hypot(ax - bx, ay - by)


def fingers_up(lm):
    """
    Returns [thumb, index, middle, ring, pinky]  — 1 = extended, 0 = folded.

    FIX: Uses MCP knuckle (not pip joint) as the reference for fingers 2-5.
    The MCP sits much lower on the hand, so even when two fingertips are
    close together (e.g. zoom-out V, or middle-thumb pinch) the tip still
    clearly clears the knuckle → finger correctly reads as UP.
    """
    tips = [4,  8,  12, 16, 20]
    mcps = [2,  5,   9, 13, 17]   # MCP knuckles — stable low reference

    up = []

    # Thumb: horizontal distance from wrist
    tx, t_joint_x, wrist_x = lm[4].x, lm[3].x, lm[0].x
    up.append(1 if abs(tx - wrist_x) > abs(t_joint_x - wrist_x) else 0)

    # Fingers: tip.y < MCP.y  (y increases downward in image coords)
    for tip, mcp in zip(tips[1:], mcps[1:]):
        up.append(1 if lm[tip].y < lm[mcp].y else 0)

    return up   # [thumb, index, middle, ring, pinky]


def map_to_screen(lm_x, lm_y, scr_w, scr_h,
                margin_x=0.15, margin_y=0.15):
    """Map inner 70% of camera frame → full screen."""
    x = (lm_x - margin_x) / (1 - 2 * margin_x)
    y = (lm_y - margin_y) / (1 - 2 * margin_y)
    x = max(0.0, min(1.0, x))
    y = max(0.0, min(1.0, y))
    return int(x * scr_w), int(y * scr_h)


# ─────────────────────────────────────────────────────────────────────────────
# Main loop
# ─────────────────────────────────────────────────────────────────────────────
while True:
    success, frame = cap.read()
    if not success:
        break

    frame  = cv2.flip(frame, 1)
    rgb    = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    gesture_label = ""

    if result.multi_hand_landmarks:
        lm = result.multi_hand_landmarks[0].landmark
        mp_draw.draw_landmarks(
            frame,
            result.multi_hand_landmarks[0],
            mp_hands.HAND_CONNECTIONS
        )

        # ── Finger states ──────────────────────────────────────────────────
        up = fingers_up(lm)
        # up = [thumb, index, middle, ring, pinky]

        # ── Key landmark positions ─────────────────────────────────────────
        ix, iy = map_to_screen(lm[8].x,  lm[8].y,  screen_width, screen_height)
        tx, ty = map_to_screen(lm[4].x,  lm[4].y,  screen_width, screen_height)
        mx, my = map_to_screen(lm[12].x, lm[12].y, screen_width, screen_height)

        now        = time.time()
        cooldown_ok = (now - last_action_time) > ACTION_DELAY

        # ══════════════════════════════════════════════════════════════════
        # GESTURE 1 — CURSOR MOVE / CLICK / SELECT
        #   Only index finger up  →  [*, 1, 0, 0, 0]
        # ══════════════════════════════════════════════════════════════════
        if up[1] == 1 and up[2] == 0 and up[3] == 0 and up[4] == 0:

            pinch = dist(lm[4].x, lm[4].y, lm[8].x, lm[8].y)
            if pinch < 0.05:
                if up[0] == 0:  # thumb down, click
                    if cooldown_ok:
                        pyautogui.click()
                        last_action_time = now
                        gesture_label = "Click!"
                else:  # thumb up, selection
                    if not selecting:
                        pyautogui.mouseDown(button='left')
                        selecting = True
                        gesture_label = "Select Start"
                    # Move cursor for selection
                    curr_x = prev_x + (ix - prev_x) / SMOOTHING
                    curr_y = prev_y + (iy - prev_y) / SMOOTHING
                    pyautogui.moveTo(curr_x, curr_y)
                    prev_x, prev_y = curr_x, curr_y
                    gesture_label = "Selecting"
            else:
                # Stop selection if was selecting
                if selecting:
                    pyautogui.mouseUp(button='left')
                    selecting = False
                    gesture_label = "Select End"
                # Normal cursor move
                curr_x = prev_x + (ix - prev_x) / SMOOTHING
                curr_y = prev_y + (iy - prev_y) / SMOOTHING
                pyautogui.moveTo(curr_x, curr_y)
                prev_x, prev_y = curr_x, curr_y
                gesture_label = "Move"

        # ══════════════════════════════════════════════════════════════════
        # GESTURE 2 — ZOOM IN / OUT
        #   Index + middle up, ring + pinky down  →  [*, 1, 1, 0, 0]
        #
        #   FIX: use raw normalised coords for spread distance so that
        #   tightly-held fingers (zoom-out) give a reliable small number
        #   instead of being amplified/noisy in screen-px space.
        #   Thresholds:  > 0.10 → zoom in   |   < 0.04 → zoom out
        # ══════════════════════════════════════════════════════════════════
        elif up[1] == 1 and up[2] == 1 and up[3] == 0 and up[4] == 0:
            raw_spread = dist(lm[8].x, lm[8].y, lm[12].x, lm[12].y)

            if raw_spread > 0.10 and cooldown_ok:
                pyautogui.hotkey("ctrl", "+")
                last_action_time = now
                gesture_label = "Zoom In"
            elif raw_spread < 0.04 and cooldown_ok:
                pyautogui.hotkey("ctrl", "-")
                last_action_time = now
                gesture_label = "Zoom Out"
            else:
                gesture_label = f"V  spread={raw_spread:.3f}"   # tune thresholds here

        # ══════════════════════════════════════════════════════════════════
        # GESTURE 3 — SLIDE NAVIGATION (SWIPE)
        #   All fingers up  →  [1, 1, 1, 1, 1]
        # ══════════════════════════════════════════════════════════════════
        elif up[0] == 1 and up[1] == 1 and up[2] == 1 and up[3] == 1 and up[4] == 1:
            current_hand_x = lm[9].x  # middle finger knuckle x position
            delta_x = current_hand_x - prev_hand_x

            if abs(delta_x) > 0.15 and cooldown_ok:
                if delta_x < -0.15:  # swipe left → next slide
                    pyautogui.press("right")
                    last_action_time = now
                    gesture_label = "Next Slide"
                elif delta_x > 0.15:  # swipe right → prev slide
                    pyautogui.press("left")
                    last_action_time = now
                    gesture_label = "Prev Slide"
            else:
                gesture_label = "Swipe Ready"

            prev_hand_x = current_hand_x

        

    # ── HUD ───────────────────────────────────────────────────────────────
    if gesture_label:
        color = (0, 200, 0) if any(k in gesture_label for k in ("Click", "Zoom", "Slide")) \
                            else (200, 200, 0)
        cv2.putText(frame, gesture_label, (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 2)

    cv2.imshow("Gesture Controller", frame)
    key = cv2.waitKey(1)

    if key == ord('n'):          pyautogui.press("right")   # next slide
    if key == ord('p'):          pyautogui.press("left")    # prev slide
    if key == ord('q') or key == 27: break

cap.release()
cv2.destroyAllWindows()