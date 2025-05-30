import cv2
from pyzbar.pyzbar import decode
from qr import BarcodeFrame

# Open the default camera
cap = cv2.VideoCapture(0)

print("Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    BarcodeFrame(frame)

    cv2.imshow("Barcode Scanner", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
