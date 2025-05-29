import cv2

# Load image with a QR code
image = cv2.imread('qr2.jpg')

# Create a QRCode detector
qr_detector = cv2.QRCodeDetector()

# Detect and decode the QR code
data, bbox, _ = qr_detector.detectAndDecode(image)

if data:
    print(f"QR Code Data: {data} {bbox}")
else:
    print("No QR code found.")
