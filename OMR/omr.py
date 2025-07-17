import cv2
import numpy as np
import utils
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description="Process the arguments.")
parser.add_argument('--exam', type = str, help = 'The exam file', default = "4.jpg")
parser.add_argument('--answers', type = str, help = 'The answers file', default = "dbs/answers/BE0B55.tsv")
parser.add_argument('--questions', type = int, help = 'The number of questions', default = 20)
parser.add_argument('--size', type = int, help = 'The number of questions on answer sheet', default = 20)

args = parser.parse_args()

##############################################################################
# Code from https://github.com/murtazahassan/Optical-Mark-Recognition-OPENCV/
##############################################################################
pathImage = args.exam
questions = args.questions
choices = 5
heightImg = 75 * questions
widthImg  = 100 * choices

answers_path = Path(args.answers)
answers_records = answers_path.read_text(encoding='utf-8').split("\n")
answers_letters = [ord(record.split("\t")[2]) - ord('A') for record in answers_records if record.strip()]
answers_letters.append(-1)
print(f"Letters: {answers_letters}")
exam_answers = [1,2,2,1,3,2,1,1,2,3,0,2,0,1,0,0,1,1,1,2] # Answers for DBA exam...
exam_answers = answers_letters
W = 950
H = 1200
##############################################################################

img = cv2.imread(pathImage)
img = cv2.resize(img, (W, H))
height, width, channels = img.shape
print(f"Width: {width}, Height: {height}, Channels: {channels}")

imgFinal = img.copy()
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

rectCon = utils.rectContour(contours) # FILTER FOR RECTANGLE CONTOURS
biggestPoints= utils.getCornerPoints(rectCon[0]) # GET CORNER POINTS OF THE BIGGEST RECTANGLE
#gradePoints = utils.getCornerPoints(rectCon[1]) # GET CORNER POINTS OF THE SECOND BIGGEST RECTANGLE

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

# FIND THE USER ANSWERS AND PUT THEM IN A LIST
myIndex=[]
for x in range (0, questions):
    arr = myPixelVal[x]
    myIndexVal = np.where(arr == np.amax(arr))
    myIndex.append(myIndexVal[0][0])
user_answers = [int(x) for x in myIndex]
print("ANSWERS", user_answers)
print("CORRECT", exam_answers)

# COMPARE THE VALUES TO FIND THE CORRECT ANSWERS
grading = []
for x in range(0, questions):
    if exam_answers[x] == myIndex[x]:
        grading.append(1)
    else:
        grading.append(0)
print("GRADING", grading)
n = len([x for x in exam_answers if x != -1])
score = (sum(grading) / n) * 100 # FINAL GRADE
grade = (sum(grading) / n) * 5.0
print("SCORE  ",score)
print("GRADE  ",grade)

# DISPLAYING ANSWERS
utils.showAnswers(imgWarpColored, myIndex, grading, exam_answers, questions, choices) # DRAW DETECTED ANSWERS
utils.drawGrid(imgWarpColored, questions, choices) # DRAW GRID
cv2.imwrite('/tmp/grid.jpg', imgWarpColored)

imgRawDrawings = np.zeros_like(imgWarpColored) # NEW BLANK IMAGE WITH WARP IMAGE SIZE
utils.showAnswers(imgRawDrawings, myIndex, grading, exam_answers, questions, choices) # DRAW ON NEW IMAGE
invMatrix = cv2.getPerspectiveTransform(pts2, pts1) # INVERSE TRANSFORMATION MATRIX
imgRawFinal = cv2.warpPerspective(imgRawDrawings, invMatrix, (imgFinal.shape[1], imgFinal.shape[0])) # INV IMAGE WARP
cv2.imwrite('/tmp/raw.jpg', imgRawFinal)

# SHOW ANSWERS AND GRADE ON FINAL IMAGE
imgFinal = cv2.addWeighted(imgFinal, 1, imgRawFinal, 1, 0)
org = (W - 250, H - 100)  # Bottom-left corner of the text
font = cv2.FONT_HERSHEY_SIMPLEX
fontScale = 1
color = (255, 0, 0)  # White in BGR
thickness = 2

# Add text to image
cv2.putText(imgFinal, f"{score}% [{grade}]", org, font, fontScale, color, thickness)

cv2.imwrite('/tmp/final.jpg', imgFinal)
filename = Path(pathImage)
cv2.imwrite(f"{filename.parent}/{filename.stem}_graded.jpg", imgFinal)