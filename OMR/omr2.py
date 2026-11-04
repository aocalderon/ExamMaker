# OpenCV handles image capture and transforms; NumPy builds point and pixel arrays.
import cv2
import numpy as np
# Local helpers contain contour, box-splitting, and answer-overlay operations.
import utils
# argparse exposes the image, answer-key, and grading options on the command line.
import argparse
# Path handles input and output filenames without manual path concatenation.
from pathlib import Path
import matplotlib.pyplot as plt
from pyzbar.pyzbar import decode  # Imported for barcode recognition

# Define the command-line options used to configure one grading run.
parser = argparse.ArgumentParser(description="Process the arguments.")
parser.add_argument('--exam', '-e', type = str, help = 'The exam file', default = "4.jpg")
parser.add_argument('--answers', '-a', type = str, help = 'The answers file', default = "dbs/answers/BE0B55.tsv")
parser.add_argument('--questions', '-q', type = int, help = 'The number of questions', default = 20)
parser.add_argument('--choices', '-c', type = int, help = 'The number of choices per question', default = 5)
parser.add_argument('--camfeed', '-f', action=argparse.BooleanOptionalAction, default=False)  # Read frames from the default camera.
parser.add_argument('--debug', '-d', action=argparse.BooleanOptionalAction, default=False)  # Print capture and answer details.

# Parse the command-line options before initializing image processing.
args = parser.parse_args()

# Open the default camera and capture its reported properties for optional logging.
webCamFeed = args.camfeed
cap = cv2.VideoCapture(0)
actual_width = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
actual_height = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
actual_fps = cap.get(cv2.CAP_PROP_FPS)
if args.debug:
    print(f"Resolution: {actual_width}x{actual_height}")
    print(f"FPS: {actual_fps}")

# Compute the expected answer-sheet dimensions from the configured grid size.
pathImage = args.exam
questions = args.questions
choices = args.choices
heightImg = 75 * questions
widthImg  = 100 * choices

# Load the TSV answer key and convert each letter to a zero-based choice index.
answers_path = Path(args.answers)
answers_records = answers_path.read_text(encoding='utf-8').split("\n")
answers_letters = [ord(record.split("\t")[2]) - ord('A') for record in answers_records if record.strip()]
# Keep the sentinel used by the existing grading logic to exclude the trailing entry.
answers_letters.append(-1)
if args.debug:
    print(f"Letters: {answers_letters}")
exam_answers = answers_letters
# Set the fixed source-image size used for contour detection and output display.
W = 950
H = 1200

# Process each camera frame, or process the selected image once.
while True:
    if webCamFeed:
        # Stop cleanly when the camera cannot provide another frame.
        ret, img = cap.read()
        if not ret:
            print("Stream ended or failed to read frame.")
            break
    else:
        # Read the configured exam image when camera mode is disabled.
        img = cv2.imread(pathImage)

    # Normalize frame dimensions so contour coordinates and output overlays align.
    img = cv2.resize(img, (W, H))
    height, width, channels = img.shape
    if args.debug:
        print(f"Width: {width}, Height: {height}, Channels: {channels}")

    # Preserve a clean copy for the final annotated result.
    imgFinal = img.copy()
    
    # ---------------------------------------------------------
    # BARCODE RECOGNITION
    # ---------------------------------------------------------
    # Use a detected barcode as the exam identifier, falling back when absent.
    detected_barcodes = decode(img)
    exam_id = "UNKNOWN_EXAM"
    for barcode in detected_barcodes:
        (x, y, w, h) = barcode.rect
        cv2.rectangle(imgFinal, (x, y), (x + w, y + h), (255, 0, 0), 3)
        exam_id = barcode.data.decode("utf-8")
        barcode_type = barcode.type
        text = f"{exam_id}"
        cv2.putText(imgFinal, text, (x + 65, y + 80), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        print(f"Detected Barcode: {exam_id}")
    # ---------------------------------------------------------

    # Convert and filter the frame before edge detection to find the answer sheet.
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) # CONVERT IMAGE TO GRAY SCALE
    imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1) # ADD GAUSSIAN BLUR
    imgCanny = cv2.Canny(imgBlur, 10, 70) # APPLY CANNY
    cv2.imwrite('/tmp/canny.jpg', imgCanny)

    ## FIND ALL COUNTOURS
    imgContours = img.copy() # COPY IMAGE FOR DISPLAY PURPOSES
    imgBigContour = img.copy() # COPY IMAGE FOR DISPLAY PURPOSES
    contours, hierarchy = cv2.findContours(imgCanny, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE) # FIND ALL CONTOURS
    cv2.drawContours(imgContours, contours, -1, (0, 255, 0), 10) # DRAW ALL DETECTED CONTOURS
    cv2.imwrite('/tmp/countours.jpg', imgContours)

    # Continue with grading only if a suitable rectangular sheet is detected.
    try:
        rectCon = utils.rectContour(contours) # FILTER FOR RECTANGLE CONTOURS

        if len(rectCon) == 0:
            raise ValueError("No valid answer sheet contour found. Ensure the page borders are visible.")
        
        biggestPoints = utils.getCornerPoints(rectCon[0]) # GET CORNER POINTS OF THE BIGGEST RECTANGLE

        # BIGGEST RECTANGLE WARPING
        biggestPoints = utils.reorder(biggestPoints) # REORDER FOR WARPING
        cv2.drawContours(imgBigContour, biggestPoints, -1, (0, 255, 0), 20) # DRAW THE BIGGEST CONTOUR
        cv2.imwrite('/tmp/big_contour.jpg', imgBigContour)
        pts1 = np.float32(biggestPoints) # PREPARE POINTS FOR WARP
        pts2 = np.float32([[0, 0],[widthImg, 0], [0, heightImg],[widthImg, heightImg]]) # PREPARE POINTS FOR WARP
        matrix = cv2.getPerspectiveTransform(pts1, pts2) # GET TRANSFORMATION MATRIX
        imgWarpColored = cv2.warpPerspective(img, matrix, (widthImg, heightImg)) # APPLY WARP PERSPECTIVE
        cv2.imwrite('/tmp/warp.jpg', imgWarpColored)

        # APPLY THRESHOLD
        imgWarpGray = cv2.cvtColor(imgWarpColored,cv2.COLOR_BGR2GRAY) # CONVERT TO GRAYSCALE
        imgThresh = cv2.threshold(imgWarpGray, 170, 255,cv2.THRESH_BINARY_INV )[1] # APPLY THRESHOLD AND INVERSE
        cv2.imwrite('/tmp/thresh.jpg', imgThresh)

        # Split the thresholded sheet into choice cells and count filled pixels.
        boxes = utils.splitBoxes(imgThresh, questions, choices) # GET INDIVIDUAL BOXES
        countR = 0
        countC = 0
        myPixelVal = np.zeros((questions, choices)) # TO STORE THE NON ZERO VALUES OF EACH BOX
        for image in boxes:
            totalPixels = cv2.countNonZero(image)
            myPixelVal[countR][countC] = totalPixels
            countC += 1
            if (countC == choices): 
                countC = 0 
                countR += 1

        # Pick the choice with the largest filled-pixel count in each row.
        myIndex=[]
        for x in range (0, questions):
            arr = myPixelVal[x]
            myIndexVal = np.where(arr == np.amax(arr))
            myIndex.append(myIndexVal[0][0])
        user_answers = [int(x) for x in myIndex]
        if args.debug:
            print("ANSWERS", user_answers)
            print("CORRECT", exam_answers)

        # Compare each detected choice with the corresponding answer-key index.
        grading = []
        for x in range(0, questions):
            if exam_answers[x] == myIndex[x]:
                grading.append(1)
            else:
                grading.append(0)
        # Exclude the sentinel from the answer count used to calculate the score.
        n = len([x for x in exam_answers if x != -1])
        score = (sum(grading) / n) * 100 # FINAL GRADE
        print("SCORE  ",score)

        # Render the marked answers and grid on the rectified sheet for inspection.
        utils.showAnswers(imgWarpColored, myIndex, grading, exam_answers, questions, choices) # Draw detected answers on the warped image
        utils.drawGrid(imgWarpColored, questions, choices) # Draw a grid on the warped image for visual reference
        cv2.imwrite('/tmp/grid.jpg', imgWarpColored)

        # Draw on a blank warped canvas, then map those marks back to the source frame.
        imgRawDrawings = np.zeros_like(imgWarpColored) # NEW BLANK IMAGE WITH WARP IMAGE SIZE
        utils.showAnswers(imgRawDrawings, myIndex, grading, exam_answers, questions, choices) # DRAW ON NEW IMAGE
        invMatrix = cv2.getPerspectiveTransform(pts2, pts1) # INVERSE TRANSFORMATION MATRIX
        imgRawFinal = cv2.warpPerspective(imgRawDrawings, invMatrix, (imgFinal.shape[1], imgFinal.shape[0])) # INV IMAGE WARP
        cv2.imwrite('/tmp/raw.jpg', imgRawFinal)

        # SHOW ANSWERS AND GRADE ON FINAL IMAGE
        imgFinal = cv2.addWeighted(imgFinal, 1, imgRawFinal, 1, 0)
        org = (100, H - 100)  # Bottom-left corner of the text
        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 1
        color = (255, 0, 0)  # Blue in BGR
        thickness = 2

        # Add text to image showing score and barcode ID
        cv2.putText(imgFinal, f"{score:.2f}%", org, font, fontScale, color, thickness)

        # Save both a diagnostic copy and a named graded image beside the input.
        cv2.imwrite('/tmp/final.jpg', imgFinal)
        filename = Path(pathImage)
        cv2.imwrite(f"{filename.parent}/{filename.stem}_{exam_id}_graded.jpg", imgFinal)
        if not webCamFeed:
            break
    except Exception as e:
        # Report detection or processing failures and keep camera mode available.
        print("No exam detected or processing error:", e)
    
    # Allow interactive camera runs to end when the user presses q.
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release camera resources and show the final still-image result when applicable.
cap.release()
if not webCamFeed:
    # Scale the graded still for a more convenient on-screen preview.
    display_w, display_h = int(W/1.5), int(H/1.5)
    disp = cv2.resize(imgFinal, (display_w, display_h))
    cv2.imshow('Result', disp)
    cv2.waitKey(0)
cv2.destroyAllWindows()
